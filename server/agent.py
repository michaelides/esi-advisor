import os
from typing import List, Dict, Any, Optional
from langgraph.prebuilt import create_react_agent
from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_experimental.tools.python.tool import PythonREPLTool
from crawler import SimpleCrawl4AITool, AdvancedCrawl4AITool, SmartExtractionTool, BatchCrawl4AITool
from custom_tools import CustomSemanticScholarQueryRun
import json
import sys
from io import StringIO
import traceback
import re
from dotenv import load_dotenv
from pydantic import BaseModel, Field  # Import Pydantic at the top for BaseModel usage
load_dotenv()

# Import RAG tools
import asyncio
from rag import search_documents_tool, store_document_tool, get_document_tool

# Import Google Generative AI types for GenerationConfig and SafetySettings
from google.generativeai.types import GenerationConfig, HarmCategory, HarmBlockThreshold

# RAG tool functions for module-level access
from rag import search_documents_tool as search_documents
from rag import store_document_tool as store_document
from rag import get_document_tool as get_document_info
# Initialize the global list to store captured figures
_captured_figures: List[str] = []

def get_captured_figures() -> List[str]:
    """Get any captured Plotly figures as JSON strings."""
    global _captured_figures
    print(f"Getting captured figures: {len(_captured_figures)} available")
    return _captured_figures.copy()

def clear_captured_figures():
    """Clear the captured figures."""
    global _captured_figures
    count = len(_captured_figures)
    _captured_figures.clear()
    print(f"Cleared {count} captured figures")

def load_system_prompt() -> str:
    """Load the system prompt from the esi_agent_instruction.md file."""
    try:
        with open("server/esi_agent_instruction.md", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return """You are ESI, a helpful AI research assistant. You have access to web search, academic paper search, and document retrieval tools.
        
Your capabilities include:
1. Searching the web for current information using Tavily
2. Finding academic papers and research using Semantic Scholar
3. Creating data visualizations using Plotly (NOT matplotlib)
4. Searching and retrieving information from your document database (RAG)
5. Storing important information for future reference
6. Providing comprehensive, well-researched answers

Document Database (RAG) Tools:
- search_documents: Search for relevant documents using semantic search
- store_document: Save important information for future retrieval
- get_document_info: Retrieve specific documents by ID

When creating visualizations:
- ALWAYS use Plotly (plotly.express as px or plotly.graph_objects as go)
- NEVER use matplotlib.pyplot - it's not supported
- Use fig.show() to display plots - this will capture them for display
- Available libraries: pandas, numpy, plotly, scipy, sklearn

Always cite your sources and provide accurate, helpful information."""

def create_tavily_tool() -> Tool:
    """Create the Tavily search tool."""
    # Initialize Tavily search
    tavily_search = TavilySearch(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
        include_images=False
    )
    
    return Tool(
        name="tavily_search",
        description="Search the web for current information, news, and general knowledge. Use this for real-time information, current events, or when you need up-to-date web content.",
        func=tavily_search.run
    )


class DebugLogHandler:
    def __init__(self):
        self._indent = 0
    def _p(self, msg):
        print(f"[DEBUG] {'  '*self._indent}{msg}")
    # Tool lifecycle
    def on_tool_start(self, serialized, input_str, **kwargs):
        name = (serialized or {}).get('name') or 'tool'
        self._p(f"TOOL start: {name} args={input_str}")
        self._indent += 1
    def on_tool_end(self, output, **kwargs):
        self._indent = max(0, self._indent-1)
        out = str(output)
        if len(out) > 300: out = out[:300] + '...'
        self._p(f"TOOL end: output={out}")
    def on_tool_error(self, error, **kwargs):
        self._indent = max(0, self._indent-1)
        self._p(f"TOOL error: {error}")
    # LLM lifecycle
    def on_llm_start(self, serialized, prompts, **kwargs):
        name = None
        try:
            name = (serialized.get('kwargs') or {}).get('model')
        except Exception:
            name = 'llm'
        self._p(f"LLM start: {name} prompts={len(prompts) if prompts else 0}")
        self._indent += 1
    def on_llm_end(self, response, **kwargs):
        self._indent = max(0, self._indent-1)
        self._p("LLM end")
    def on_chain_start(self, *a, **k): pass
    def on_chain_end(self, *a, **k): pass
    def on_chain_error(self, *a, **k): pass


def create_agent(temperature: float = 0.5, model: str = "gemini-2.5-flash", verbosity: int = 3, llm: Optional[Runnable] = None, debug: Optional[bool] = None) -> Runnable:
    """Create and configure the React agent with tools.
    If `llm` is provided, it will be used instead of constructing a new one.
    """
    
    # Load environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
 
    
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY environment variable is required")
    
    # Initialize the LLM based on the selected model
    if llm is None:
        if model.startswith("gemini"):
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=google_api_key,
                callbacks=None if llm is None else llm.callbacks,  # Use callbacks from provided LLM if available
                # Explicitly define generation_config to avoid Modality error
                generation_config=GenerationConfig(
                    candidate_count=1,
                    stop_sequences=[],
                ),
                # Add default safety settings
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
            )
        else: # Assume OpenRouter model
            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required for OpenRouter models")
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=openrouter_api_key, # Use openai_api_key for OpenRouter
                base_url="https://openrouter.ai/api/v1",
                callbacks=None,
            )

    # Add debug callbacks if requested
    env_debug = os.getenv('DEBUG_TOOL_LOG', '').lower() in ('1','true','yes','on')
    is_debug_enabled = (debug is True) or env_debug
    
    # Create tools
    tools = [
        create_tavily_tool(),
        CustomSemanticScholarQueryRun(top_k_results=10),
        WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
        PythonREPLTool(),
    ]
    
    # Add RAG tools
    try:
        from langchain.tools import StructuredTool
        
        # For async functions, we need to create sync wrappers
        def sync_search_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
            """Synchronous wrapper for search_documents_tool"""
            return asyncio.run(search_documents(query, limit))
        
        def sync_store_document(content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
            """Synchronous wrapper for store_document_tool"""
            return asyncio.run(store_document(content, metadata))
        
        def sync_get_document_info(document_id: str) -> Optional[Dict[str, Any]]:
            """Synchronous wrapper for get_document_tool"""
            return asyncio.run(get_document_info(document_id))
        
        tools.extend([
            StructuredTool.from_function(
                name="search_documents",
                description="Search for documents in the RAG database using semantic search. Use this to find relevant information from previously ingested documents.",
                func=sync_search_documents,
                args_schema=type('SearchDocumentsArgs', (BaseModel,), {
                    'query': Field(..., description="Search query string"),
                    'limit': Field(5, description="Maximum number of results to return"),
                    '__annotations__': {'query': str, 'limit': int}
                })
            ),
            StructuredTool.from_function(
                name="store_document",
                description="Store a document in the RAG database for future retrieval. Use this to save important information for later use.",
                func=sync_store_document,
                args_schema=type('StoreDocumentArgs', (BaseModel,), {
                    'content': Field(..., description="Document content to store"),
                    'metadata': Field(None, description="Optional metadata for the document"),
                    '__annotations__': {'content': str, 'metadata': Optional[Dict[str, Any]]}
                })
            ),
            StructuredTool.from_function(
                name="get_document_info",
                description="Retrieve a specific document by ID from the RAG database. Use this to get detailed information about a specific document.",
                func=sync_get_document_info,
                args_schema=type('GetDocumentInfoArgs', (BaseModel,), {
                    'document_id': Field(..., description="ID of the document to retrieve"),
                    '__annotations__': {'document_id': str}
                })
            ),
        ])
    except Exception as e:
        print(f"Warning: Could not add RAG tools: {e}")

    # Prefer robust StructuredTool wrappers for custom crawler tools
    try:
        from langchain.tools import StructuredTool

        class CrawlArgs(BaseModel):
            url: str = Field(..., description="URL to scrape")
            css_selector: Optional[str] = Field(None, description="Optional CSS selector")
            extraction_strategy: str = Field("text", description="text | markdown | structured")
            word_count_threshold: int = Field(10, description="Minimum words per block")
            only_text: bool = Field(True, description="Whether to keep only text")

        # Bind to existing implementations but enforce schema and string return
        simple_tool = SimpleCrawl4AITool()
        def simple_crawl(url: str, css_selector: Optional[str] = None, extraction_strategy: str = "text", word_count_threshold: int = 10, only_text: bool = True) -> str:
            out = simple_tool.run(url=url, css_selector=css_selector, extraction_strategy=extraction_strategy, word_count_threshold=word_count_threshold, only_text=only_text)
            return out if isinstance(out, str) else str(out)

        advanced_tool = AdvancedCrawl4AITool()
        def advanced_crawl(url: str, css_selector: Optional[str] = None, extraction_strategy: str = "text", word_count_threshold: int = 10, only_text: bool = True) -> str:
            out = advanced_tool.run(url=url, css_selector=css_selector, extraction_strategy=extraction_strategy, word_count_threshold=word_count_threshold, only_text=only_text)
            return out if isinstance(out, str) else (json.dumps(out) if out is not None else "")

        class SmartArgs(BaseModel):
            url: str = Field(..., description="URL to scrape")
            extraction_prompt: str = Field(..., description="Instruction for extraction")

        smart_tool = SmartExtractionTool()
        def smart_extract(url: str, extraction_prompt: str) -> str:
            out = smart_tool.run(url=url, extraction_prompt=extraction_prompt)
            return out if isinstance(out, str) else (json.dumps(out) if out is not None else "")

        class BatchArgs(BaseModel):
            urls: List[str] = Field(..., description="List of URLs")
            max_concurrent: int = Field(3, description="Max concurrency")

        batch_tool = BatchCrawl4AITool()
        def batch_crawl(urls: List[str], max_concurrent: int = 3) -> str:
            out = batch_tool.run(urls=urls, max_concurrent=max_concurrent)
            return out if isinstance(out, str) else (json.dumps(out) if out is not None else "")

        tools.extend([
            StructuredTool.from_function(
                name="crawl4ai_scraper",
                description="Scrape a URL with Crawl4AI. Supports css_selector and extraction_strategy (text|markdown|structured).",
                func=simple_crawl,
                args_schema=CrawlArgs,
            ),
            StructuredTool.from_function(
                name="advanced_crawl4ai",
                description="Advanced Crawl4AI scrape returning structured content.",
                func=advanced_crawl,
                args_schema=CrawlArgs,
            ),
            StructuredTool.from_function(
                name="smart_extraction",
                description="LLM-guided extraction from a URL using Crawl4AI.",
                func=smart_extract,
                args_schema=SmartArgs,
            ),
            StructuredTool.from_function(
                name="batch_crawl4ai",
                description="Batch scrape multiple URLs using Crawl4AI.",
                func=batch_crawl,
                args_schema=BatchArgs,
            ),
        ])
    except Exception as _e:
        # If wrapping fails, fall back to the original tool classes
        tools.extend([
            SimpleCrawl4AITool(),
            AdvancedCrawl4AITool(),
            SmartExtractionTool(),
            BatchCrawl4AITool(),
        ])


    # Load system prompt
    system_prompt = load_system_prompt()

    # Adjust system prompt based on verbosity
    if verbosity == 1:
        system_prompt += "\n\nYour responses should be extremely concise and laconic. Get straight to the point."
    elif verbosity == 2:
        system_prompt += "\n\nYour responses should be concise and to the point, avoiding unnecessary details."
    elif verbosity == 4:
        system_prompt += "\n\nYour responses should be detailed and provide ample explanation."
    elif verbosity == 5:
        system_prompt += "\n\nYour responses should be extremely verbose, comprehensive, and elaborate on all points."
    
    # Build proper chat prompt with system + conversation placeholder
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # Create the React agent
    agent = create_react_agent(
        llm,
        tools=tools,
        prompt=prompt,
        debug=is_debug_enabled,
    )

    return agent

if __name__ == "__main__":
    # Test the agent creation
    try:
        # Set dummy API keys for testing purposes if not already set
        os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "YOUR_DUMMY_GOOGLE_API_KEY")
        os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "YOUR_DUMMY_TAVILY_API_KEY")
        os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY", "YOUR_DUMMY_OPENROUTER_API_KEY")


        print("Testing agent creation with default Gemini model...")
        agent = create_agent()
        print("Agent created successfully with Gemini model!")
        
        print("\nTesting agent creation with an OpenRouter model...")
        agent_openrouter = create_agent(model="mistralai/mistral-small-3.2-24b-instruct:free")
        print("Agent created successfully with OpenRouter model!")

        # Test query (this part might require actual API keys to run successfully)
        # test_query = "Create a simple scatter plot using plotly"
        # result = agent.invoke({"input": test_query})
        # print(f"Test result: {result}")
        
        # Check if figures were captured
        # figures = get_captured_figures()
        # print(f"Captured {len(figures)} figures during test")
        
    except Exception as e:
        print(f"Error creating agent: {e}")
        import traceback

# Top-level functions for backward compatibility with tests

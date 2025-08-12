from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler, AsyncCallbackHandler
import asyncio
#import os

#load_dotenv("../.env")
load_dotenv()

class Settings(BaseSettings):
    GOOGLE_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None


settings = Settings()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    messages: list[dict] | None = None  # Each: {"role": "user"|"assistant"|"tool", "content": str}
    user_input: str | None = None
    model: str | None = None
    temperature: float | None = None
    verbosity: int | None = None
    debug: bool | None = None


@app.post("/chat")
def chat(req: ChatRequest):
    # Accept either full messages history or legacy user_input
    messages = None
    if isinstance(req.messages, list) and len(req.messages) > 0:
        messages = req.messages
    elif isinstance(req.user_input, str) and req.user_input.strip():
        messages = [{"role": "user", "content": req.user_input.strip()}]
    else:
        return {"text": "Invalid request: provide 'messages' (list) or 'user_input' (string)."}

    # Basic env checks for required keys depending on model type happen in create_agent
    model = req.model or "gemini-2.5-flash"
    temperature = req.temperature if req.temperature is not None else 0.5
    verbosity = req.verbosity if req.verbosity is not None else 3

    try:
        agent = create_agent(temperature=temperature, model=model, verbosity=verbosity, debug=req.debug)
    except Exception as e:
        return {"text": f"Server not configured: {e}"}

    # Build LangGraph prebuilt chat payload
    payload = {"messages": messages}
    result = agent.invoke(payload)

    # Extract clean assistant markdown text
    from typing import Any
    try:
        from langchain_core.messages import AIMessage, ToolMessage, HumanMessage  # type: ignore
    except Exception:  # Fallback if types unavailable
        AIMessage = ToolMessage = HumanMessage = tuple()  # type: ignore

    def extract_markdown(r: Any) -> str:
        # Prefer traversing a message list
        msgs = None
        if hasattr(r, "messages"):
            msgs = getattr(r, "messages")
        elif isinstance(r, dict) and "messages" in r:
            msgs = r["messages"]

        if isinstance(msgs, list):
            last_text = None
            for m in msgs:
                if isinstance(m, AIMessage):
                    if isinstance(m.content, str) and m.content.strip():
                        last_text = m.content.strip()
                elif isinstance(m, dict):
                    role = m.get("role") or m.get("type")
                    content = m.get("content") or m.get("text")
                    if role in ("assistant", "ai") and isinstance(content, str) and content.strip():
                        last_text = content.strip()
                # Ignore HumanMessage and ToolMessage for user output
            if last_text:
                return last_text

        # Direct AIMessage
        if isinstance(r, AIMessage) and isinstance(r.content, str) and r.content.strip():
            return r.content.strip()

        # Dict shapes with content/output
        if isinstance(r, dict):
            for k in ("output", "content", "text"):
                v = r.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()

        return str(r)

    text = extract_markdown(result)
    return {"text": text}


class SSEQueueHandler(AsyncCallbackHandler):
    def __init__(self, queue: "asyncio.Queue[str]"):
        self.queue = queue
        self.count = 0

    async def on_llm_new_token(self, token: str, **kwargs):  # type: ignore[override]
        # Forward tokens into async queue for SSE loop
        self.count += 1
        await self.queue.put(token)

    async def on_llm_end(self, response, **kwargs):  # type: ignore[override]
        # Signal end of stream
        await self.queue.put(None)

    # No-ops to satisfy interface without raising
    async def on_chat_model_start(self, *args, **kwargs): return
    async def on_chain_start(self, *args, **kwargs): return
    async def on_chain_end(self, *args, **kwargs): return
    async def on_chain_error(self, *args, **kwargs): return
    async def on_llm_start(self, *args, **kwargs): return
    async def on_llm_error(self, *args, **kwargs):
        # Forward error to queue
        await self.queue.put(None)
    async def on_tool_start(self, *args, **kwargs): return
    async def on_tool_end(self, *args, **kwargs): return
    async def on_tool_error(self, *args, **kwargs): return
    async def on_text(self, *args, **kwargs): return
    async def on_agent_action(self, *args, **kwargs): return
    async def on_agent_finish(self, *args, **kwargs): return

@app.get("/thinking")
async def thinking():
    import os
    path = os.path.join(os.path.dirname(__file__), "thinking_phrases.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
        return {"phrases": lines}
    except Exception as e:
        return {"phrases": ["Thinking…"], "error": str(e)}

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    # Normalize input like /chat
    if isinstance(req.messages, list) and len(req.messages) > 0:
        messages = req.messages
    elif isinstance(req.user_input, str) and req.user_input.strip():
        messages = [{"role": "user", "content": req.user_input.strip()}]
    else:
        messages = [{"role": "user", "content": "(empty)"}]

    model = req.model or "gemini-2.5-flash"
    temperature = req.temperature if req.temperature is not None else 0.5
    verbosity = req.verbosity if req.verbosity is not None else 3

    async def sse_generator():
        import json
        
        # Simple streaming approach for all model types
        q: asyncio.Queue[str] = asyncio.Queue()
        handler = SSEQueueHandler(q)
        
        # Initialize LLM with streaming support
        if model.startswith("gemini"):
            llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=temperature,
                google_api_key=settings.GOOGLE_API_KEY,
                callbacks=[handler]
            )
        else:
            # OpenAI-compatible models
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                streaming=True,
                callbacks=[handler],
                openai_api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1"
            )
        
        # Create agent with streaming LLM
        agent_local = create_agent(temperature=temperature, model=model, verbosity=verbosity, llm=llm, debug=req.debug)
        
        # Run agent in background
        task = asyncio.create_task(asyncio.to_thread(agent_local.invoke, {"messages": messages}))
        
        # Stream tokens as they arrive
        while True:
            try:
                token = await q.get()
                if token is None:  # End of stream
                    break
                yield f"data: {json.dumps({'type':'delta','text': token})}\n\n"
            except Exception:
                break
        
        # Wait for task completion
        try:
            await task
        except Exception as e:
            yield f"data: {json.dumps({'type':'error','message': str(e)})}\n\n"
        
        yield "data: {\"type\": \"done\"}\n\n"
    
    return StreamingResponse(sse_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

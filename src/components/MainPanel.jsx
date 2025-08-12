import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ChatInput from './ChatInput';
import ChatMessage from './ChatMessage';
import Settings from './Settings';
import { getMessages, saveMessage, ingestFile } from '../api/chat';
import { extractCode } from '../utils/artifactExtractor';

const MainPanel = ({ selectedChat, settings, setSettings, setArtifacts, setIsRightPanelVisible }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [thinkingPhrases, setThinkingPhrases] = useState(["Thinking..."]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    const fetchThinkingPhrases = async () => {
      try {
        const response = await axios.get('/api/thinking');
        if (response.data.phrases && response.data.phrases.length > 0) {
            setThinkingPhrases(response.data.phrases);
        }
      } catch (error) {
        console.error('Error fetching thinking phrases:', error);
      }
    };
    fetchThinkingPhrases();
  }, []);

  useEffect(() => {
    if (selectedChat) {
      getMessages(selectedChat.id).then(setMessages);
      setIsRightPanelVisible(false);
      setArtifacts([]);
    } else {
      setMessages([]);
    }
  }, [selectedChat, setArtifacts, setIsRightPanelVisible]);

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleFileUpload = async (file) => {
    try {
      const result = await ingestFile(file);
      const successMessage = { role: 'system', content: result.message };
      setMessages(prevMessages => [...prevMessages, successMessage]);
    } catch (error) {
      const errorMessage = { role: 'system', content: `Error: ${error.message}` };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    }
  };

  const processArtifacts = async (aiResponseContent) => {
    const codeArtifacts = extractCode(aiResponseContent);

    const figuresResponse = await axios.get('/api/figures');
    const plotArtifacts = figuresResponse.data.figures.map(figJson => ({
      type: 'plot',
      content: JSON.parse(figJson),
    }));

    const allArtifacts = [...codeArtifacts, ...plotArtifacts];
    if (allArtifacts.length > 0) {
      setArtifacts(allArtifacts);
      setIsRightPanelVisible(true);
    } else {
      setArtifacts([]);
      setIsRightPanelVisible(false);
    }
  };

  const handleSubmit = async () => {
    if (!input.trim() || !selectedChat) return;

    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    await saveMessage(selectedChat.id, 'user', input);
    setInput('');
    setIsLoading(true);
    setIsRightPanelVisible(false);
    setArtifacts([]);

    const eventSource = new EventSource(`/api/chat/stream?user_input=${encodeURIComponent(input)}&model=${settings.model}&temperature=${settings.temperature}&verbosity=${settings.verbosity}`);

    let aiResponse = { role: 'ai', content: '' };
    setMessages(prevMessages => [...prevMessages, aiResponse]);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'delta') {
        aiResponse.content += data.text;
        setMessages(prevMessages => {
          const updatedMessages = [...prevMessages];
          updatedMessages[updatedMessages.length - 1] = { ...aiResponse };
          return updatedMessages;
        });
      } else if (data.type === 'done') {
        setIsLoading(false);
        saveMessage(selectedChat.id, 'ai', aiResponse.content);
        processArtifacts(aiResponse.content);
        eventSource.close();
      } else if (data.type === 'error') {
        aiResponse.content = `An error occurred: ${data.message}`;
        setMessages(prevMessages => {
            const updatedMessages = [...prevMessages];
            updatedMessages[updatedMessages.length - 1] = { ...aiResponse };
            return updatedMessages;
        });
        setIsLoading(false);
        eventSource.close();
      }
    };

    eventSource.onerror = (error) => {
      console.error('EventSource failed:', error);
      aiResponse.content = 'An error occurred while streaming the response.';
      setMessages(prevMessages => {
        const updatedMessages = [...prevMessages];
        updatedMessages[updatedMessages.length - 1] = { ...aiResponse };
        return updatedMessages;
      });
      setIsLoading(false);
      eventSource.close();
    };
  };

  return (
    <div className="main-panel">
      {isSettingsOpen && (
        <Settings
          settings={settings}
          setSettings={setSettings}
          onClose={() => setIsSettingsOpen(false)}
        />
      )}
      <div className="chat-display">
        {messages.map((msg, index) => (
          <ChatMessage key={index} message={msg} />
        ))}
        {isLoading && (
          <div className="chat-bubble ai thinking">
            <span>{thinkingPhrases[Math.floor(Math.random() * thinkingPhrases.length)]}</span>
            <div className="dot-flashing"></div>
          </div>
        )}
      </div>
      <ChatInput
        value={input}
        onChange={handleInputChange}
        onSubmit={handleSubmit}
        onSettingsClick={() => setIsSettingsOpen(true)}
        onFileUpload={handleFileUpload}
      />
    </div>
  );
};

export default MainPanel;

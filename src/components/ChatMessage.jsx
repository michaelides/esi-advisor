import React, { useState } from 'react';
import { marked } from 'marked';

const ChatMessage = ({ message }) => {
  const { role, content } = message;
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setIsCopied(true);
    setTimeout(() => {
      setIsCopied(false);
    }, 2000);
  };

  // Use marked to render markdown content for AI messages
  const renderContent = () => {
    if (role === 'ai') {
      return <div dangerouslySetInnerHTML={{ __html: marked(content) }} />;
    }
    return content;
  };

  if (role === 'system') {
    return (
      <div className="chat-message-container system">
        <div className="chat-bubble">
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className={`chat-message-container ${role}`}>
      <div className={`chat-bubble`}>
        {renderContent()}
      </div>
      <div className="button-container">
        {role === 'user' && (
          <>
            <button className="chat-btn"><i className="fa-solid fa-pencil"></i></button>
            <button onClick={handleCopy} className="chat-btn">
              {isCopied ? <i className="fa-solid fa-check"></i> : <i className="fa-solid fa-copy"></i>}
            </button>
          </>
        )}
        {role === 'ai' && (
          <>
            <button className="chat-btn"><i className="fa-solid fa-rotate-right"></i></button>
            <button onClick={handleCopy} className="chat-btn">
              {isCopied ? <i className="fa-solid fa-check"></i> : <i className="fa-solid fa-copy"></i>}
            </button>
            <button className="chat-btn"><i className="fa-solid fa-check-double"></i></button>
          </>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;

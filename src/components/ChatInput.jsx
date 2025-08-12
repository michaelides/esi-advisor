import React, { useRef } from 'react';

const ChatInput = ({ value, onChange, onSubmit, onSettingsClick, onFileUpload }) => {
  const fileInputRef = useRef(null);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onFileUpload(file);
    }
  };

  return (
    <div className="chat-input-container">
      <input
        type="file"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      <button onClick={handleUploadClick} className="upload-btn">+</button>
      <textarea
        className="chat-input"
        placeholder="Ask ESI..."
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        rows={1}
      />
      <button onClick={onSettingsClick} className="settings-btn">
        <i className="fa-solid fa-cog"></i>
      </button>
      <button onClick={onSubmit} className="send-btn">
        <i className="fa-solid fa-paper-plane"></i>
      </button>
    </div>
  );
};

export default ChatInput;

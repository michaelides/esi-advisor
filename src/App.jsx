import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import MainPanel from './components/MainPanel';
import RightPanel from './components/RightPanel';
import { isSupabaseConfigured } from './supabaseClient';
import './App.css';

function App() {
  const [selectedChat, setSelectedChat] = useState(null);
  const [settings, setSettings] = useState({
    model: 'gemini-1.5-flash',
    temperature: 0.5,
    verbosity: 3,
  });
  const [artifacts, setArtifacts] = useState([]);
  const [isRightPanelVisible, setIsRightPanelVisible] = useState(false);

  if (!isSupabaseConfigured) {
    return (
      <div className="app-container">
        <div className="error-message">
          <h1>Supabase not configured</h1>
          <p>Please set the VITE_SUPABASE_URL and VITE_SUPABASE_API environment variables in your .env file.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Sidebar selectedChat={selectedChat} setSelectedChat={setSelectedChat} />
      <MainPanel
        selectedChat={selectedChat}
        settings={settings}
        setSettings={setSettings}
        setArtifacts={setArtifacts}
        setIsRightPanelVisible={setIsRightPanelVisible}
      />
      {isRightPanelVisible && <RightPanel artifacts={artifacts} />}
    </div>
  );
}

export default App;

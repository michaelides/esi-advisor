import React from 'react';

const Settings = ({ settings, setSettings, onClose }) => {
  const handleModelChange = (e) => {
    setSettings({ ...settings, model: e.target.value });
  };

  const handleTemperatureChange = (e) => {
    setSettings({ ...settings, temperature: parseFloat(e.target.value) });
  };

  const handleVerbosityChange = (e) => {
    setSettings({ ...settings, verbosity: parseInt(e.target.value, 10) });
  };

  return (
    <div className="settings-modal">
      <div className="settings-content">
        <h2>Settings</h2>
        <div className="setting">
          <label>LLM Model</label>
          <select value={settings.model} onChange={handleModelChange}>
            <optgroup label="Google Gemini">
              <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            </optgroup>
            <optgroup label="OpenRouter">
              <option value="mistralai/mistral-7b-instruct:free">Mistral 7B Instruct (Free)</option>
              <option value="gryphe/mythomax-l2-13b">MythoMax L2 13B</option>
            </optgroup>
          </select>
        </div>
        <div className="setting">
          <label>Creativity (Temperature): {settings.temperature}</label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={settings.temperature}
            onChange={handleTemperatureChange}
          />
        </div>
        <div className="setting">
          <label>Verbosity: {settings.verbosity}</label>
          <input
            type="range"
            min="1"
            max="5"
            step="1"
            value={settings.verbosity}
            onChange={handleVerbosityChange}
          />
        </div>
        <button onClick={onClose} className="close-btn">Close</button>
      </div>
    </div>
  );
};

export default Settings;

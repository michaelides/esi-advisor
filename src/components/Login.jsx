import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { deleteAllChats } from '../api/chat';

const Login = () => {
  const { user, login, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogin = () => {
    login('github'); // Or any other provider
  };

  const handleLogout = () => {
    logout();
    setIsMenuOpen(false);
  };

  const handleDeleteAll = () => {
    if (window.confirm('Are you sure you want to delete all your chats? This action is irreversible.')) {
      if (user) {
        deleteAllChats(user.id);
        window.location.reload();
      }
    }
  };

  if (!user) {
    return (
      <button onClick={handleLogin} className="login-btn">
        <i className="fa-solid fa-right-to-bracket"></i> Login
      </button>
    );
  }

  return (
    <div className="user-menu-container">
      <button onClick={() => setIsMenuOpen(!isMenuOpen)} className="avatar-btn">
        <img src={user.user_metadata.avatar_url} alt="User Avatar" className="avatar" />
      </button>
      {isMenuOpen && (
        <div className="user-menu">
          <p>{user.user_metadata.full_name}</p>
          <p>{user.email}</p>
          <hr />
          <button onClick={toggleTheme} className="theme-toggle-btn">
            <i className={`fa-solid ${theme === 'light' ? 'fa-moon' : 'fa-sun'}`}></i>
            {theme === 'light' ? 'Dark' : 'Light'} Mode
          </button>
          <button onClick={handleDeleteAll} className="delete-all-btn">
            <i className="fa-solid fa-trash"></i> Delete All Chats
          </button>
          <hr />
          <button onClick={handleLogout} className="logout-btn">
            <i className="fa-solid fa-right-from-bracket"></i> Logout
          </button>
        </div>
      )}
    </div>
  );
};

export default Login;

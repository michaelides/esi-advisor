import React, { useState, useEffect } from 'react';
import Login from './Login';
import { useAuth } from '../contexts/AuthContext';
import { getChats, createChat } from '../api/chat';

const Sidebar = ({ selectedChat, setSelectedChat }) => {
  const { user } = useAuth();
  const [isExtended, setIsExtended] = useState(true);
  const [chats, setChats] = useState([]);

  useEffect(() => {
    if (user) {
      getChats(user.id).then(setChats);
    }
  }, [user]);

  const toggleSidebar = () => {
    setIsExtended(!isExtended);
  };

  const handleNewChat = async () => {
    if (user) {
      const newChat = await createChat(user.id, 'New Chat');
      if (newChat) {
        setChats([newChat, ...chats]);
        setSelectedChat(newChat);
      }
    }
  };

  return (
    <div className={`sidebar ${isExtended ? 'extended' : 'collapsed'}`}>
      <div className="sidebar-header">
        <button onClick={toggleSidebar} className="sidebar-toggle">
          <i className={`fa-solid ${isExtended ? 'fa-angle-left' : 'fa-angle-right'}`}></i>
        </button>
        {isExtended && (
          <>
            <button className="bookmarks-btn">
              <i className="fa-solid fa-bookmark"></i>
            </button>
            <button onClick={handleNewChat} className="new-chat-btn">
              <i className="fa-solid fa-plus"></i> New Chat
            </button>
          </>
        )}
      </div>
      <div className="chat-history">
        {isExtended && (
          <ul>
            {chats.map((chat) => (
              <li
                key={chat.id}
                className={`chat-history-item ${selectedChat?.id === chat.id ? 'selected' : ''}`}
                onClick={() => setSelectedChat(chat)}
              >
                {chat.title}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="sidebar-footer">
        <Login />
      </div>
    </div>
  );
};

export default Sidebar;

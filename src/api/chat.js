import { supabase, isSupabaseConfigured } from '../supabaseClient';

export const getChats = async (userId) => {
  if (!isSupabaseConfigured || !userId) return [];
  const { data, error } = await supabase
    .from('chats')
    .select('id, title, created_at')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });
  if (error) {
    console.error('Error fetching chats:', error);
    return [];
  }
  return data;
};

export const createChat = async (userId, title) => {
  if (!isSupabaseConfigured) return null;
  const { data, error } = await supabase
    .from('chats')
    .insert([{ user_id: userId, title }])
    .select();
  if (error) {
    console.error('Error creating chat:', error);
    return null;
  }
  return data[0];
};

export const getMessages = async (chatId) => {
  if (!isSupabaseConfigured || !chatId) return [];
  const { data, error } = await supabase
    .from('messages')
    .select('role, content')
    .eq('chat_id', chatId)
    .order('created_at', { ascending: true });
  if (error) {
    console.error('Error fetching messages:', error);
    return [];
  }
  return data;
};

export const saveMessage = async (chatId, role, content) => {
  if (!isSupabaseConfigured) return;
  const { error } = await supabase
    .from('messages')
    .insert([{ chat_id: chatId, role, content }]);
  if (error) {
    console.error('Error saving message:', error);
  }
};

export const deleteAllChats = async (userId) => {
    if (!isSupabaseConfigured || !userId) return;
    const { error } = await supabase
        .from('chats')
        .delete()
        .eq('user_id', userId);
    if (error) {
        console.error('Error deleting all chats:', error);
    }
};

export const ingestFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/api/ingest', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'File ingestion failed');
    }
    return await response.json();
  } catch (error) {
    console.error('Error ingesting file:', error);
    throw error;
  }
};

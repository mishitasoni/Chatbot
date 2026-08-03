import axios from 'axios';
import { Conversation, Message } from '../types';

const rawApiUrl = import.meta.env.VITE_API_URL;
const apiUrl = rawApiUrl ? rawApiUrl.replace(/\/+$/, '') : '/api';

const api = axios.create({
  baseURL: apiUrl,
});

api.interceptors.request.use((config) => {
  const userId = localStorage.getItem('user_id');
  if (userId) {
    config.headers['X-User-Id'] = userId;
  }
  return config;
});

export const authApi = {
  login: async (emailOrPhone: string) => {
    // Determine if it's an email or phone heuristically
    const isEmail = emailOrPhone.includes('@');
    const payload = isEmail ? { email: emailOrPhone } : { phone: emailOrPhone };
    const response = await api.post('/auth/login', payload);
    return { success: true, user: response.data };
  },
};

export const chatApi = {
  getConversations: async (platform: string): Promise<Conversation[]> => {
    const response = await api.get(`/conversations?platform=${platform}`);
    return response.data;
  },
  
  getMessages: async (conversationId: string): Promise<Message[]> => {
    const response = await api.get(`/conversations/${conversationId}/messages`);
    return response.data;
  },

  sendMessage: async (conversationId: string, message: string): Promise<Message> => {
    const response = await api.post(`/chat`, {
      conversation_id: conversationId,
      message,
    });
    return response.data;
  },
};

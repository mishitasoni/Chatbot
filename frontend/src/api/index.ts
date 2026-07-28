import axios from 'axios';
import { Conversation, Message } from '../types';

const api = axios.create({
  baseURL: '/api',
});

export const authApi = {
  login: async (emailOrPhone: string) => {
    // In real app, POST /api/auth/login
    // For now we mock it since we are missing this backend endpoint in the prompt
    return { success: true, user: { id: '1', emailOrPhone } };
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

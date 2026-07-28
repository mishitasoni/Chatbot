import { useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import { Message } from '../types';

export function useWebSocket() {
  const { user } = useAuth();
  const { addMessage } = useChat();
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!user) return;

    // Use relative path for Vite proxy or absolute if running directly
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${user.id}`;
    
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.current.onmessage = async (event) => {
      try {
        const message: Message = JSON.parse(event.data);
        console.log('New message received via WS:', message);
        
        // Add message to current view
        addMessage(message);
        
        // Trigger a custom event to tell the dashboard to refresh conversations
        window.dispatchEvent(new CustomEvent('chat:refresh_conversations'));
      } catch (error) {
        console.error('Error parsing WS message:', error);
      }
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [user, addMessage]);

  return ws.current;
}

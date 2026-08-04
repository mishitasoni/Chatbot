import React, { createContext, useContext, useState, ReactNode, useCallback, useRef, useEffect } from 'react';
import { ChannelType, Conversation, Message } from '../types';

interface ChatContextType {
  selectedChannel: ChannelType;
  setSelectedChannel: (channel: ChannelType) => void;
  conversations: Conversation[];
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>;
  currentConversation: Conversation | null;
  setCurrentConversation: React.Dispatch<React.SetStateAction<Conversation | null>>;
  messages: Message[];
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  addMessage: (message: Message) => void;
  isThinking: boolean;
  setIsThinking: React.Dispatch<React.SetStateAction<boolean>>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [selectedChannel, setSelectedChannel] = useState<ChannelType>(() => {
    const saved = localStorage.getItem('selectedChannel');
    return (saved as ChannelType) || 'general';
  });
  
  useEffect(() => {
    localStorage.setItem('selectedChannel', selectedChannel);
  }, [selectedChannel]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isThinking, setIsThinking] = useState(false);

  const currentConvRef = useRef(currentConversation);
  
  useEffect(() => {
    currentConvRef.current = currentConversation;
  }, [currentConversation]);

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => {
      // Only append if this message belongs to the currently active conversation
      // Or if it's an optimistic update for a new conversation (id 0 or "0")
      if (
        (currentConvRef.current && String(currentConvRef.current.id) === String(message.conversation_id)) ||
        String(message.conversation_id) === "0"
      ) {
        // Prevent duplicate messages if any
        if (prev.find(m => m.id === message.id)) return prev;
        return [...prev, message];
      }
      return prev;
    });
  }, []);

  return (
    <ChatContext.Provider
      value={{
        selectedChannel,
        setSelectedChannel,
        conversations,
        setConversations,
        currentConversation,
        setCurrentConversation,
        messages,
        setMessages,
        addMessage,
        isThinking,
        setIsThinking,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

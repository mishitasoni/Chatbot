import { useEffect, useRef } from 'react';
import { useChat } from '../context/ChatContext';
import ChatBubble from './ChatBubble';
import MessageComposer from './MessageComposer';

export default function ChatWindow() {
  const { messages, currentConversation, selectedChannel, isThinking } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col h-full bg-transparent relative">
      
      {/* Header */}
      <div className="absolute top-0 w-full h-16 bg-white/50 dark:bg-gray-900/50 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 flex items-center px-6 z-10 hidden md:flex">
        <h2 className="text-lg font-semibold capitalize bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300">
          {selectedChannel === 'general' ? 'General AI Chat' : `${selectedChannel} Integration`}
        </h2>
        {currentConversation && (
          <span className="ml-4 px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium">
            Conversation #{currentConversation.id}
          </span>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 pt-6 md:pt-24 pb-32">
        {(!currentConversation && messages.length === 0) ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500 dark:text-gray-400 space-y-4">
            <div className="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-2xl flex items-center justify-center">
              <svg className="w-8 h-8 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p>Select a conversation or start a new one.</p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} />
            ))}
            
            {/* Thinking Indicator */}
            {isThinking && (
              <div className="flex justify-start">
                <div className="glass text-gray-800 dark:text-gray-100 rounded-2xl rounded-bl-sm border border-gray-200 dark:border-gray-700 px-5 py-3.5 shadow-sm flex items-center space-x-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Composer Area */}
      {selectedChannel === 'general' && (
        <div className="absolute bottom-0 w-full p-4 md:p-6 bg-gradient-to-t from-background-light via-background-light to-transparent dark:from-background-dark dark:via-background-dark z-10">
          <div className="max-w-3xl mx-auto">
            <MessageComposer />
          </div>
        </div>
      )}
    </div>
  );
}

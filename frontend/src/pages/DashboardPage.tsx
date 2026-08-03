import { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import RightPanel from '../components/RightPanel';
import { Menu } from 'lucide-react';
import { useChat } from '../context/ChatContext';
import { chatApi } from '../api';
import { useWebSocket } from '../hooks/useWebSocket';

export default function DashboardPage() {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const { selectedChannel, currentConversation, setConversations, setMessages, setCurrentConversation } = useChat();

  // Initialize WebSockets
  useWebSocket();

  // Fetch Conversations when channel changes or refresh event occurs
  useEffect(() => {
    async function loadConversations() {
      try {
        const data = await chatApi.getConversations(selectedChannel);
        setConversations(data);
        
        // Auto-select the first conversation if none is selected
        if (data && data.length > 0) {
          setCurrentConversation(prev => prev ? prev : data[0]);
        } else {
          setCurrentConversation(null);
        }
      } catch (error) {
        console.error("Failed to load conversations", error);
      }
    }
    
    // Initial load and on channel change
    loadConversations();
    // Only reset current conversation if channel changed, not on refresh
    setCurrentConversation(null);

    // Listen for refresh event from websocket
    const handleRefresh = () => {
      loadConversations();
    };
    
    window.addEventListener('chat:refresh_conversations', handleRefresh);
    return () => {
      window.removeEventListener('chat:refresh_conversations', handleRefresh);
    };
  }, [selectedChannel, setConversations, setCurrentConversation]);

  // Fetch Messages when conversation changes
  useEffect(() => {
    async function loadMessages() {
      if (currentConversation) {
        try {
          const msgs = await chatApi.getMessages(currentConversation.id);
          setMessages(msgs);
        } catch (error) {
          console.error("Failed to load messages", error);
        }
      } else {
        setMessages([]);
      }
    }
    loadMessages();
  }, [currentConversation, setMessages]);

  return (
    <div className="flex h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-gray-100 overflow-hidden">
      
      {/* Mobile Header */}
      <div className="md:hidden absolute top-0 left-0 w-full h-14 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 flex items-center px-4 z-20">
        <button 
          onClick={() => setMobileSidebarOpen(true)}
          className="p-2 -ml-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
        >
          <Menu size={24} />
        </button>
        <div className="font-semibold ml-2">ChatFusion Chatbot</div>
      </div>

      {/* Left Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-30 w-72 transform transition-transform duration-300 ease-in-out
        md:relative md:translate-x-0 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800
        ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar onClose={() => setMobileSidebarOpen(false)} />
      </div>

      {/* Backdrop for mobile */}
      {mobileSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={() => setMobileSidebarOpen(false)}
        />
      )}

      {/* Middle Chat Window */}
      <div className="flex-1 flex flex-col pt-14 md:pt-0 relative min-w-0">
        <ChatWindow />
      </div>

      {/* Right Information Panel */}
      <div className="hidden lg:block w-80 bg-white/50 dark:bg-gray-900/50 border-l border-gray-200 dark:border-gray-800 overflow-y-auto">
        <RightPanel />
      </div>
      
    </div>
  );
}

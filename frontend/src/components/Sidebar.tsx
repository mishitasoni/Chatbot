import { MessageSquare, Settings, LogOut, Search, Plus, X, Moon, Sun, Send } from 'lucide-react';
import { FaTelegramPlane, FaWhatsapp } from 'react-icons/fa';
import { useChat } from '../context/ChatContext';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Sidebar({ onClose }: { onClose: () => void }) {
  const { selectedChannel, setSelectedChannel, conversations, currentConversation, setCurrentConversation } = useChat();
  const { theme, toggleTheme } = useTheme();
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const channels = [
    { id: 'general', name: 'General AI', icon: MessageSquare, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
    { id: 'telegram', name: 'Telegram', icon: FaTelegramPlane, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { id: 'whatsapp', name: 'WhatsApp', icon: FaWhatsapp, color: 'text-green-500', bg: 'bg-green-500/10' },
  ] as const;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2 font-bold text-xl text-purple-600 dark:text-purple-400">
          <BotIcon className="w-8 h-8" />
          <span>ChatFusion</span>
        </div>
        <button onClick={onClose} className="md:hidden p-2 text-gray-500">
          <X size={20} />
        </button>
      </div>

      {/* Search */}
      <div className="px-4 mb-4">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            type="text" 
            placeholder="Search conversations..." 
            className="w-full bg-gray-100 dark:bg-gray-800 text-sm rounded-xl pl-9 pr-4 py-2 outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
          />
        </div>
      </div>

      {/* Channels */}
      <div className="px-2 space-y-1 mb-6">
        <div className="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Channels</div>
        {channels.map((channel) => {
          const Icon = channel.icon;
          const isActive = selectedChannel === channel.id;
          return (
            <button
              key={channel.id}
              onClick={() => setSelectedChannel(channel.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl transition-all ${
                isActive 
                  ? 'bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-300' 
                  : 'hover:bg-gray-100 dark:hover:bg-gray-800/50 text-gray-700 dark:text-gray-300'
              }`}
            >
              <div className={`p-1.5 rounded-lg ${channel.bg} ${channel.color}`}>
                <Icon size={18} />
              </div>
              <span className="font-medium text-sm">{channel.name}</span>
            </button>
          );
        })}
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        <div className="px-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex justify-between items-center">
          <span>Recent</span>
          <button 
            onClick={() => setCurrentConversation(null)} 
            title="New Conversation"
            className="hover:text-purple-500"
          >
            <Plus size={14} />
          </button>
        </div>
        {conversations.filter(c => c.platform.startsWith(selectedChannel)).map(conv => (
          <button
            key={conv.id}
            onClick={() => setCurrentConversation(conv)}
            className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-colors ${
              currentConversation?.id === conv.id
                ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white font-medium'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50'
            }`}
          >
            {selectedChannel === 'telegram' && conv.platform.startsWith('telegram_') && conv.platform !== 'telegram_default' 
              ? conv.platform.substring(9) 
              : `Conversation #${conv.id}`}
          </button>
        ))}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800 space-y-2">
        <button onClick={toggleTheme} className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm text-gray-700 dark:text-gray-300">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
        <button onClick={() => navigate('/settings/channels')} className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm text-gray-700 dark:text-gray-300">
          <Settings size={18} />
          <span>Settings</span>
        </button>
        <button onClick={handleLogout} className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 transition-colors text-sm">
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}

function BotIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <line x1="8" y1="16" x2="8" y2="16" />
      <line x1="16" y1="16" x2="16" y2="16" />
    </svg>
  );
}

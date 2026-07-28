import { Message } from '../types';
import { motion } from 'framer-motion';

export default function ChatBubble({ message }: { message: Message }) {
  const isUser = message.sender === 'user';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div className={`
        max-w-[85%] md:max-w-[75%] rounded-2xl px-5 py-3.5 shadow-sm
        ${isUser 
          ? 'bg-gradient-to-br from-purple-600 to-indigo-600 text-white rounded-br-sm' 
          : 'glass text-gray-800 dark:text-gray-100 rounded-bl-sm border border-gray-200 dark:border-gray-700'
        }
      `}>
        <div className="whitespace-pre-wrap prose dark:prose-invert max-w-none text-sm md:text-base leading-relaxed break-words">
          {message.message}
        </div>
        <div className={`text-[10px] mt-2 font-medium ${isUser ? 'text-purple-200' : 'text-gray-400'}`}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </motion.div>
  );
}

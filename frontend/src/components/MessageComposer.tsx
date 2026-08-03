import { useState, FormEvent, useRef, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import { chatApi } from '../api';
import { Send, Paperclip, Smile, Mic, X } from 'lucide-react';

export default function MessageComposer() {
  const [input, setInput] = useState('');
  const { currentConversation, addMessage, selectedChannel, setConversations, setCurrentConversation, setIsThinking } = useChat();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !selectedImage) return;

    let text = input;
    if (selectedImage) {
      text = `![image](${selectedImage})\n\n${text}`;
    }
    
    setInput('');
    setSelectedImage(null);
    
    const convId = currentConversation ? currentConversation.id : "0";

    // Optimistic UI update
    const tempId = Date.now().toString();
    addMessage({
      id: tempId,
      conversation_id: convId,
      sender: 'user',
      message: text,
      created_at: new Date().toISOString(),
    });

    try {
      setIsThinking(true);
      // Actually send to backend API
      const reply = await chatApi.sendMessage(convId, text);
      addMessage(reply);

      // If we started a new conversation, fetch updated conversations and select it
      if (!currentConversation) {
         const updatedConvs = await chatApi.getConversations(selectedChannel);
         setConversations(updatedConvs);
         const newConv = updatedConvs.find(c => String(c.id) === String(reply.conversation_id));
         if (newConv) setCurrentConversation(newConv);
      }
    } catch (error: any) {
      console.error('Failed to send message:', error);
      // Show error in UI
      addMessage({
        id: Date.now().toString() + "_error",
        conversation_id: convId,
        sender: 'bot',
        message: `⚠️ Error: Could not connect to the backend server. Details: ${error.message || String(error)}. Make sure the backend is running.`,
        created_at: new Date().toISOString(),
      });
    } finally {
      setIsThinking(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative group">
      <div className="glass rounded-3xl p-2 flex items-end border border-gray-200 dark:border-gray-700 shadow-xl shadow-purple-500/5 focus-within:ring-2 focus-within:ring-purple-500/50 transition-all">
        {selectedImage && (
          <div className="absolute -top-20 left-2 p-1 bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700">
            <div className="relative">
              <img src={selectedImage} alt="Upload preview" className="h-16 w-auto rounded-md object-cover" />
              <button 
                type="button" 
                onClick={() => setSelectedImage(null)}
                className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-0.5 hover:bg-red-600 shadow-sm"
              >
                <X size={14} />
              </button>
            </div>
          </div>
        )}

        <input 
          type="file" 
          ref={fileInputRef} 
          hidden 
          accept="image/*"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              const reader = new FileReader();
              reader.onload = () => setSelectedImage(reader.result as string);
              reader.readAsDataURL(file);
            }
            if (e.target) e.target.value = '';
          }}
        />
        <button 
          type="button" 
          onClick={() => fileInputRef.current?.click()}
          className="p-3 text-gray-400 hover:text-purple-500 transition-colors rounded-xl"
        >
          <Paperclip size={20} />
        </button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message Maya..."
          className="flex-1 max-h-[200px] bg-transparent border-none outline-none resize-none py-3 px-2 text-gray-900 dark:text-gray-100 placeholder-gray-400"
          rows={1}
        />

        <div className="flex items-center p-2 space-x-1">
          <button type="button" className="p-2 text-gray-400 hover:text-purple-500 transition-colors rounded-xl hidden sm:block">
            <Smile size={20} />
          </button>
          {input.trim() === '' && !selectedImage ? (
            <button type="button" className="p-2 text-gray-400 hover:text-purple-500 transition-colors rounded-xl">
              <Mic size={20} />
            </button>
          ) : (
            <button 
              type="submit" 
              className="p-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl shadow-md shadow-purple-500/20 hover:shadow-purple-500/40 transition-all active:scale-95"
            >
              <Send size={18} />
            </button>
          )}
        </div>
      </div>
    </form>
  );
}

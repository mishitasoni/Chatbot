import { useState, useEffect } from 'react';
import { useChat } from '../context/ChatContext';
import { useAuth } from '../context/AuthContext';
import { MessageSquare, Hash, Clock, Activity, AlertCircle, Save, QrCode } from 'lucide-react';
import { api } from '../api';

export default function RightPanel() {
  const { selectedChannel, currentConversation } = useChat();
  const { user } = useAuth();
  
  const [telegramToken, setTelegramToken] = useState('');
  const [savingTelegram, setSavingTelegram] = useState(false);
  const [telegramSaved, setTelegramSaved] = useState(false);

  const [whatsappQR, setWhatsappQR] = useState<string | null>(null);
  const [loadingQR, setLoadingQR] = useState(false);

  const handleSaveTelegram = async () => {
    if (!telegramToken || !user) return;
    setSavingTelegram(true);
    try {
      await api.post('/integrations/telegram', {
        user_id: parseInt(user.id),
        token: telegramToken
      });
      setTelegramSaved(true);
      window.dispatchEvent(new CustomEvent('chat:refresh_conversations'));
      setTimeout(() => setTelegramSaved(false), 3000);
    } catch (error: any) {
      console.error("Failed to save telegram token", error);
      const backendMessage = error.response?.data?.detail || error.message || "Network Error";
      alert("Failed to link Telegram: " + backendMessage);
    } finally {
      setSavingTelegram(false);
    }
  };

  const handleLinkWhatsapp = async () => {
    if (!user) return;
    setLoadingQR(true);
    try {
      // Polling for QR code
      const checkQR = async () => {
        try {
          const response = await api.get(`/integrations/whatsapp/qr/${user.id}`);
          
          if (response.data.qr === 'CONNECTED' || response.data.status === 'connected') {
            setWhatsappQR('CONNECTED');
            setLoadingQR(false);
            return; // Stop polling
          }
          
          if (response.data.qr && response.data.qr !== 'LOADING...') {
            setWhatsappQR(response.data.qr);
            setLoadingQR(false);
          }
          
          // Keep polling every 3 seconds to catch QR rotations or connection success
          setTimeout(checkQR, 3000);
        } catch (e) {
          console.error(e);
          setTimeout(checkQR, 3000);
        }
      };
      checkQR();
    } catch (error) {
      console.error("Failed to get WhatsApp QR", error);
      alert("Failed to initiate WhatsApp linking.");
      setLoadingQR(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-6 border-b border-gray-200 dark:border-gray-800">
        <h2 className="text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-400 dark:to-indigo-400">
          Information
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {selectedChannel === 'general' && 'General AI Settings'}
          {selectedChannel === 'telegram' && 'Telegram Integration'}
          {selectedChannel === 'whatsapp' && 'WhatsApp Integration'}
        </p>
      </div>

      <div className="p-6 space-y-6 flex-1 overflow-y-auto">
        
        {/* Status Card */}
        <div className="glass rounded-xl p-4">
          <div className="flex items-center space-x-3 mb-4">
            <Activity className="text-green-500" size={20} />
            <h3 className="font-medium">Connection Status</h3>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">ChatFusion Gateway</span>
            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full font-medium">Connected</span>
          </div>
        </div>

        {/* Integration Hub Card */}
        <div className="glass rounded-xl p-4 space-y-4">
          <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100 uppercase tracking-wider">Integration Hub</h3>
          
          {selectedChannel === 'general' && (
            <>
              <DetailRow icon={<Hash size={16} />} label="Model" value="gemini-3.1-flash-lite" />
              <DetailRow icon={<MessageSquare size={16} />} label="Messages" value="12" />
              <DetailRow icon={<Clock size={16} />} label="Session Time" value="14m" />
            </>
          )}

          {selectedChannel === 'telegram' && (
            <div className="space-y-4">
              <div className="flex flex-col space-y-2">
                <label className="text-xs text-gray-500 dark:text-gray-400 uppercase font-medium">Telegram Bot Token</label>
                <input 
                  type="text" 
                  value={telegramToken}
                  onChange={(e) => setTelegramToken(e.target.value)}
                  placeholder="123456789:AAH..." 
                  className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <button 
                onClick={handleSaveTelegram}
                disabled={savingTelegram}
                className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white py-2 rounded-lg text-sm font-medium transition-all shadow-sm"
              >
                <Save size={16} />
                <span>{savingTelegram ? 'Linking...' : telegramSaved ? 'Linked Successfully!' : 'Link Telegram Bot'}</span>
              </button>
              
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <DetailRow icon={<Clock size={16} />} label="Last Synced" value="Just now" />
              </div>
            </div>
          )}

          {selectedChannel === 'whatsapp' && (
            <div className="space-y-4">
              <div className="flex flex-col space-y-3">
                <label className="text-xs text-gray-500 dark:text-gray-400 uppercase font-medium text-center">WhatsApp Integration</label>
                {!whatsappQR && !loadingQR && (
                  <button 
                    onClick={handleLinkWhatsapp}
                    className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white py-2 rounded-lg text-sm font-medium transition-all shadow-sm"
                  >
                    <QrCode size={16} />
                    <span>Connect WhatsApp</span>
                  </button>
                )}
                
                {loadingQR && !whatsappQR && (
                  <div className="text-center text-sm text-gray-500 p-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto mb-2"></div>
                    <p>Generating QR Code...</p>
                  </div>
                )}
                
                {whatsappQR && whatsappQR !== 'CONNECTED' && (
                  <div className="flex flex-col items-center bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <img src={whatsappQR} alt="WhatsApp QR Code" className="w-[200px] h-[200px]" />
                    <p className="text-xs text-gray-500 mt-3 text-center">
                      Open WhatsApp on your phone, go to Linked Devices, and scan this code.
                    </p>
                  </div>
                )}
                
                {whatsappQR === 'CONNECTED' && (
                  <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 rounded-xl font-medium border border-green-200 dark:border-green-800/50">
                    ✅ WhatsApp is Connected!
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

function DetailRow({ icon, label, value }: { icon: React.ReactNode, label: string, value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
        {icon}
        <span>{label}</span>
      </div>
      <span className="font-medium text-gray-900 dark:text-gray-100">{value}</span>
    </div>
  );
}

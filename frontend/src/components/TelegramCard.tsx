import React, { useState, useEffect } from 'react';
import { FaTelegramPlane } from 'react-icons/fa';
import { LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function TelegramCard() {
  const [status, setStatus] = useState<string>('disconnected');
  const [token, setToken] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  const handleConnect = async () => {
    if (!user || !token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/integrations/telegram`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, token })
      });
      if (res.ok) {
        setStatus('connected');
      } else {
        const data = await res.json();
        setError(data.detail || 'Invalid token');
      }
    } catch (e) {
      console.error(e);
      setError('Connection failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = () => {
    setStatus('disconnected');
    setToken('');
  };

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
      
      {status === 'connected' && (
        <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/20 blur-3xl rounded-full pointer-events-none"></div>
      )}

      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-xl ${status === 'connected' ? 'bg-blue-500/20 text-blue-500' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'}`}>
              <FaTelegramPlane size={24} />
            </div>
            <div>
              <h3 className="text-xl font-semibold">Telegram</h3>
              <div className="flex items-center space-x-2">
                <span className={`inline-block w-2 h-2 rounded-full ${status === 'connected' ? 'bg-blue-500' : 'bg-gray-400'}`}></span>
                <p className="text-sm text-gray-500 capitalize">{status}</p>
              </div>
            </div>
          </div>
        </div>

        {status === 'connected' ? (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-900/30">
            <p className="text-sm text-blue-800 dark:text-blue-300 font-medium">Successfully linked!</p>
          </div>
        ) : (
          <div className="mb-6">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Enter your Telegram Bot Token from BotFather to link your account.
            </p>
            <input 
              type="text"
              placeholder="e.g. 123456789:ABCdefGHIjklmNOPqrstUVwxyZ"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
            {error && <p className="text-red-500 text-xs mt-2">{error}</p>}
          </div>
        )}
      </div>
      
      {status === 'connected' ? (
        <button 
          onClick={handleDisconnect}
          disabled={loading}
          className="w-full flex items-center justify-center space-x-2 py-2.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 rounded-xl font-medium transition-colors"
        >
          <LogOut size={18} />
          <span>Disconnect</span>
        </button>
      ) : (
        <button 
          onClick={handleConnect}
          disabled={loading || !token.trim()}
          className="w-full py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-xl font-medium transition-colors shadow-sm shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Connecting...' : 'Connect Telegram'}
        </button>
      )}
    </div>
  );
}

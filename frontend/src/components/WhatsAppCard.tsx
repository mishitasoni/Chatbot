import React, { useState, useEffect, useRef } from 'react';
import { FaWhatsapp } from 'react-icons/fa';
import { RefreshCw, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { QRCodeSVG } from 'qrcode.react';

interface ChannelStatus {
  channel_type: string;
  status: string;
  phone_number: string | null;
}

export default function WhatsAppCard() {
  const [status, setStatus] = useState<string>('disconnected');
  const [phone, setPhone] = useState<string | null>(null);
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { user } = useAuth();
  const pollInterval = useRef<number | null>(null);

  const fetchStatus = async () => {
    if (!user) return;
    try {
      const res = await fetch(`http://localhost:8005/api/integrations/channels/status/${user.id}`);
      const data: ChannelStatus[] = await res.json();
      const wa = data.find(c => c.channel_type === 'whatsapp');
      if (wa) {
        setStatus(wa.status);
        setPhone(wa.phone_number);
        
        if (wa.status === 'connecting') {
            fetchQrCode();
        } else {
            setQrCode(null);
        }
      }
    } catch (e) {
      console.error('Failed to fetch status', e);
    }
  };

  const fetchQrCode = async () => {
    if (!user) return;
    try {
      const res = await fetch(`http://localhost:8005/api/integrations/whatsapp/qr/${user.id}`);
      if (res.status === 200) {
        const data = await res.json();
        if (data.qr && data.qr !== 'LOADING...') {
          setQrCode(data.qr);
        }
      }
    } catch (e) {
      console.error('Failed to fetch QR', e);
    }
  };

  useEffect(() => {
    fetchStatus();
    pollInterval.current = window.setInterval(fetchStatus, 3000);
    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
  }, [user]);

  const handleConnect = async () => {
    if (!user) return;
    setLoading(true);
    try {
      // Trigger QR generation
      await fetch(`http://localhost:8005/api/integrations/whatsapp/qr/${user.id}`);
      setStatus('connecting');
      fetchQrCode();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!user) return;
    setLoading(true);
    try {
      await fetch(`http://localhost:8005/api/integrations/channels/whatsapp/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id })
      });
      setStatus('disconnected');
      setPhone(null);
      setQrCode(null);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
      
      {/* Decorative gradient blur */}
      {status === 'connected' && (
        <div className="absolute -top-10 -right-10 w-32 h-32 bg-green-500/20 blur-3xl rounded-full pointer-events-none"></div>
      )}

      <div>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className={`p-3 rounded-xl ${status === 'connected' ? 'bg-green-500/20 text-green-500' : 'bg-gray-100 dark:bg-gray-800 text-gray-500'}`}>
              <FaWhatsapp size={24} />
            </div>
            <div>
              <h3 className="text-xl font-semibold">WhatsApp</h3>
              <div className="flex items-center space-x-2">
                <span className={`inline-block w-2 h-2 rounded-full ${status === 'connected' ? 'bg-green-500' : status === 'connecting' ? 'bg-yellow-500 animate-pulse' : 'bg-gray-400'}`}></span>
                <p className="text-sm text-gray-500 capitalize">{status}</p>
              </div>
            </div>
          </div>
        </div>

        {status === 'connected' ? (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/10 rounded-xl border border-green-100 dark:border-green-900/30">
            <p className="text-sm text-green-800 dark:text-green-300 font-medium">Successfully linked!</p>
            {phone && <p className="text-sm text-green-700 dark:text-green-400 mt-1">Phone: {phone}</p>}
          </div>
        ) : status === 'connecting' ? (
          <div className="mb-6 flex flex-col items-center justify-center p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-800">
            {qrCode ? (
              <div className="bg-white p-3 rounded-xl shadow-sm mb-3 overflow-hidden flex justify-center w-full">
                {/[▄█▀]/.test(qrCode) ? (
                  <pre className="text-[8px] leading-[8px] sm:text-[10px] sm:leading-[10px] whitespace-pre text-black font-mono tracking-tight text-center">
                    {qrCode}
                  </pre>
                ) : (
                  <QRCodeSVG value={qrCode} size={160} />
                )}
              </div>
            ) : (
              <div className="h-40 flex items-center justify-center">
                 <RefreshCw className="animate-spin text-gray-400" size={32} />
              </div>
            )}
            <p className="text-sm text-center text-gray-500">
              {qrCode ? "Scan this QR code with WhatsApp" : "Generating QR code..."}
            </p>
          </div>
        ) : (
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            Connect your WhatsApp account to chat with the AI assistant directly from your phone.
          </p>
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
      ) : status === 'connecting' ? (
        <button 
          onClick={handleDisconnect}
          className="w-full py-2.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl font-medium transition-colors"
        >
          Cancel
        </button>
      ) : (
        <button 
          onClick={handleConnect}
          disabled={loading}
          className="w-full py-2.5 bg-green-500 hover:bg-green-600 text-white rounded-xl font-medium transition-colors shadow-sm shadow-green-500/20"
        >
          Connect WhatsApp
        </button>
      )}
    </div>
  );
}

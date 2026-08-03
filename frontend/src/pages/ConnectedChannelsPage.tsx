import React, { useState, useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import WhatsAppCard from '../components/WhatsAppCard';
import TelegramCard from '../components/TelegramCard';

export default function ConnectedChannelsPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col h-screen bg-background-light dark:bg-background-dark text-gray-900 dark:text-gray-100 overflow-y-auto">
      <div className="p-6 md:p-10 max-w-5xl mx-auto w-full">
        <div className="flex items-center space-x-4 mb-8">
          <button 
            onClick={() => navigate('/dashboard')}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-3xl font-bold">Connected Channels</h1>
        </div>
        
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Manage your connected messaging accounts. Each account is isolated to your profile.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <WhatsAppCard />
          <TelegramCard />
        </div>
      </div>
    </div>
  );
}

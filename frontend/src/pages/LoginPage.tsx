import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Bot, Mail, Phone, Lock, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LoginPage() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(input);
      navigate('/dashboard');
    } catch (error: any) {
      alert("Login failed: " + (error.message || "Network Error"));
    } finally {
      setIsLoading(false);
    }
  };

  const isEmail = input.includes('@');

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-gray-900 dark:to-indigo-950 p-4">
      
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="glass rounded-3xl p-8 relative overflow-hidden">
          {/* Decorative gradients inside card */}
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl"></div>
          
          <div className="relative z-10">
            <div className="flex justify-center mb-8">
              <div className="w-20 h-20 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-xl shadow-purple-500/30">
                <Bot size={40} className="text-white" />
              </div>
            </div>

            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300">
                Welcome Back
              </h1>
              <p className="text-gray-500 dark:text-gray-400 mt-2">
                Sign in to your ChatFusion Dashboard
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Email or Phone Number
                </label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-gray-400 group-focus-within:text-purple-500 transition-colors">
                    {input.length === 0 ? <Mail size={20} /> : isEmail ? <Mail size={20} /> : <Phone size={20} />}
                  </div>
                  <input
                    type="text"
                    required
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    className="block w-full pl-12 pr-4 py-3.5 bg-white/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all placeholder-gray-400"
                    placeholder="name@company.com or +1234567890"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input type="checkbox" className="rounded border-gray-300 text-purple-600 focus:ring-purple-500 bg-white/50 dark:bg-gray-800/50" />
                  <span className="text-gray-600 dark:text-gray-400">Remember me</span>
                </label>
                <a href="#" className="text-purple-600 dark:text-purple-400 hover:text-purple-700 font-medium">
                  Forgot Login?
                </a>
              </div>

              <button
                type="submit"
                disabled={isLoading || !input}
                className="w-full py-3.5 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-xl font-medium shadow-lg shadow-purple-500/30 flex items-center justify-center space-x-2 disabled:opacity-70 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
              >
                <span>{isLoading ? 'Authenticating...' : 'Sign In'}</span>
                {!isLoading && <ChevronRight size={20} />}
              </button>
            </form>
          </div>
        </div>

        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-8">
          By signing in, you agree to our{' '}
          <a href="#" className="text-purple-600 dark:text-purple-400 hover:underline">Terms</a>
          {' '}and{' '}
          <a href="#" className="text-purple-600 dark:text-purple-400 hover:underline">Privacy Policy</a>.
        </p>
      </motion.div>

    </div>
  );
}

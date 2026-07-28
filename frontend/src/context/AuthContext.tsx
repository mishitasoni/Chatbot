import { createContext, useContext, useState, ReactNode } from 'react';

interface AuthContextType {
  user: { id: string; emailOrPhone: string } | null;
  login: (emailOrPhone: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<{ id: string; emailOrPhone: string } | null>({ id: '1', emailOrPhone: 'mock_user@example.com' });

  const login = async (emailOrPhone: string) => {
    // Mock login for now, we will connect this to backend later
    setUser({ id: '1', emailOrPhone });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

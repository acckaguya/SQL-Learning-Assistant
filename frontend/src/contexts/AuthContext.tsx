import React, { createContext, useContext, ReactNode, useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

export type User = {
  user_id: string;
  username: string;
  role: 'teacher' | 'student';
  created_at: string;
};

type AuthContextType = {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, password: string, role: string) => Promise<void>;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const api = useApi();

  const fetchUser = async () => {
    try {
      const userData = await api.get('/users/me');
      setUser(userData);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (localStorage.getItem('token')) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    setLoading(true);
    try {
      const data = await api.post('/users/login', { username, password });
      localStorage.setItem('token', data.access_token);
      await fetchUser();
    } finally {
      setLoading(false);
    }
  };

  const register = async (username: string, password: string, role: string) => {
    setLoading(true);
    try {
      await api.post('/users/register', { username, password, role });
      // 注册后自动登录
      await login(username, password);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
    register,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
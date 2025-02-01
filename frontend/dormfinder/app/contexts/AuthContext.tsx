// src/contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router';

type User = {
  id: string;
  username: string;
  role: 'student' | 'admin';
  school_id_number?: string;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
  secureFetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>;
};

const AuthContext = createContext<AuthContextType>(null!);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const getCSRFToken = () => {
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1] || '';
  };

  const secureFetch = useCallback(async (input: RequestInfo, init?: RequestInit) => {
    const response = await fetch(input, {
      ...init,
      credentials: 'include',
      headers: {
        ...init?.headers,
        'X-CSRFToken': getCSRFToken(),
        'Content-Type': 'application/json',
      },
    });

    if (response.status === 401 && !response.url.includes('/auth/refresh')) {
      try {
        const refreshResponse = await fetch('/api/auth/refresh/', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'X-CSRFToken': getCSRFToken(),
          },
        });

        if (!refreshResponse.ok) throw new Error('Refresh failed');
        return secureFetch(input, init);
      } catch (error) {
        logout();
        throw error;
      }
    }

    return response;
  }, []);

  const verifyAuth = useCallback(async () => {
    try {
      const response = await secureFetch('/api/auth/me/');
      if (response.ok) setUser(await response.json());
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [secureFetch]);

  const login = async (credentials: { username: string; password: string }) => {
    setLoading(true);
    try {
      await secureFetch('/api/auth/login/', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
      await verifyAuth();
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await secureFetch('/api/auth/logout/', { method: 'POST' });
    } finally {
      setUser(null);
      navigate('/login');
    }
  };

  useEffect(() => {
    verifyAuth();
  }, [verifyAuth]);

  const value = {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    logout,
    refreshAuth: verifyAuth,
    secureFetch
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
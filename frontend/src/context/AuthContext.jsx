import { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(() => !!localStorage.getItem('access'));

  useEffect(() => {
    const access = localStorage.getItem('access');
    if (!access) {
      return;
    }

    authApi
      .profile()
      .then((profile) => {
        setUser({ id: profile.id, username: profile.username, email: profile.email });
      })
      .catch(() => {
        localStorage.removeItem('access');
        localStorage.removeItem('refresh');
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = (access, refresh) => {
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
    return authApi.profile().then((profile) => {
      const nextUser = { id: profile.id, username: profile.username, email: profile.email };
      setUser(nextUser);
      return nextUser;
    });
  };

  const logout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

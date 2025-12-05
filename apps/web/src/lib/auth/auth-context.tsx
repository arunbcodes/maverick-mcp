'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { api, setTokens, clearTokens, getAccessToken } from '@/lib/api/client';

interface User {
  user_id: string;
  email: string;
  name?: string;
  tier: string;
  email_verified?: boolean;
  onboarding_completed?: boolean;
  is_demo_user?: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface APIResponse<T> {
  success: boolean;
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
  };
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  tier: string;
}

interface RegisterResponse {
  user_id: string;
  email: string;
  name?: string;
  tier: string;
}

interface UserProfileResponse {
  user_id: string;
  email: string;
  name?: string;
  tier: string;
  email_verified: boolean;
  onboarding_completed: boolean;
  is_demo_user: boolean;
  created_at: string;
  last_login_at: string | null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.get<APIResponse<UserProfileResponse>>(
        '/auth/me'
      );
      setUser({
        user_id: response.data.user_id,
        email: response.data.email,
        name: response.data.name,
        tier: response.data.tier,
        email_verified: response.data.email_verified,
        onboarding_completed: response.data.onboarding_completed,
        is_demo_user: response.data.is_demo_user,
      });
    } catch {
      clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.post<APIResponse<LoginResponse>>(
      '/auth/login',
      { email, password },
      { skipAuth: true }
    );

    setTokens(response.data.access_token, response.data.refresh_token);

    // Fetch full user profile
    const profileResponse = await api.get<APIResponse<UserProfileResponse>>(
      '/auth/me'
    );
    
    setUser({
      user_id: profileResponse.data.user_id,
      email: profileResponse.data.email,
      name: profileResponse.data.name,
      tier: profileResponse.data.tier,
      email_verified: profileResponse.data.email_verified,
      onboarding_completed: profileResponse.data.onboarding_completed,
      is_demo_user: profileResponse.data.is_demo_user,
    });
  }, []);

  const register = useCallback(async (email: string, password: string, name?: string) => {
    await api.post<APIResponse<RegisterResponse>>(
      '/auth/register',
      { email, password, name },
      { skipAuth: true }
    );
    
    // Auto-login after registration
    await login(email, password);
  }, [login]);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore logout errors
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}


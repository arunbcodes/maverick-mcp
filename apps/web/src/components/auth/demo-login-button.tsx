'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { api, setTokens } from '@/lib/api/client';
import { Play, Loader2 } from 'lucide-react';

interface DemoLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  tier: string;
}

interface APIResponse<T> {
  success: boolean;
  data: T;
}

export function DemoLoginButton() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleDemoLogin() {
    setIsLoading(true);
    setError('');

    try {
      const response = await api.post<APIResponse<DemoLoginResponse>>(
        '/auth/demo-login',
        {},
        { skipAuth: true }
      );

      setTokens(response.data.access_token, response.data.refresh_token);
      router.push('/dashboard');
    } catch (err) {
      console.error('Demo login failed:', err);
      setError('Demo mode is not available. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <Button
        onClick={handleDemoLogin}
        disabled={isLoading}
        variant="outline"
        className="w-full border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Loading demo...
          </>
        ) : (
          <>
            <Play className="w-4 h-4 mr-2" />
            Try Demo (No Sign Up)
          </>
        )}
      </Button>
      {error && (
        <p className="text-xs text-red-400 text-center">{error}</p>
      )}
    </div>
  );
}


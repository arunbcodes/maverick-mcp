'use client';

import { useAuth } from '@/lib/auth/auth-context';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Sparkles, X } from 'lucide-react';
import { useState } from 'react';

export function DemoBanner() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [isDismissed, setIsDismissed] = useState(false);

  // Only show for demo users
  if (!user?.is_demo_user || isDismissed) {
    return null;
  }

  async function handleCreateAccount() {
    await logout();
    router.push('/register');
  }

  return (
    <div className="bg-gradient-to-r from-amber-500/20 via-amber-600/20 to-amber-500/20 border-b border-amber-500/30">
      <div className="container mx-auto px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/30">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <p className="text-sm text-amber-100">
              <span className="font-medium">Demo Mode</span>
              <span className="hidden sm:inline text-amber-200/80">
                {' '}— You&apos;re exploring with sample data. Create an account to save your portfolio.
              </span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleCreateAccount}
              className="bg-amber-500 hover:bg-amber-400 text-slate-900 text-xs h-7 px-3"
            >
              Create Account
            </Button>
            <button
              onClick={() => setIsDismissed(true)}
              className="p-1 text-amber-400/60 hover:text-amber-400 transition-colors"
              aria-label="Dismiss banner"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


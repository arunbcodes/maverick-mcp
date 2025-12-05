'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth/auth-context';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  Briefcase,
  Search,
  BarChart3,
  ArrowRight,
  X,
  Sparkles,
} from 'lucide-react';
import { api } from '@/lib/api/client';

interface WelcomeModalProps {
  onClose?: () => void;
}

const features = [
  {
    icon: Briefcase,
    title: 'Track Your Portfolio',
    description: 'Add your holdings and watch your wealth grow with real-time P&L tracking.',
  },
  {
    icon: Search,
    title: 'Discover Opportunities',
    description: 'Find high-momentum stocks with our AI-powered screener.',
  },
  {
    icon: BarChart3,
    title: 'Technical Analysis',
    description: 'Get RSI, MACD, support/resistance levels for any stock.',
  },
  {
    icon: TrendingUp,
    title: 'Backtest Strategies',
    description: 'Test your trading ideas with historical data before investing.',
  },
];

export function WelcomeModal({ onClose }: WelcomeModalProps) {
  const { user, refreshUser } = useAuth();
  const [isVisible, setIsVisible] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Show modal for new users who haven't completed onboarding
    if (user && !user.onboarding_completed && !user.is_demo_user) {
      setIsVisible(true);
    }
  }, [user]);

  async function handleComplete() {
    setIsLoading(true);
    try {
      await api.post('/users/me/onboarding/complete');
      await refreshUser();
      setIsVisible(false);
      onClose?.();
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      // Still close the modal even if API fails
      setIsVisible(false);
      onClose?.();
    } finally {
      setIsLoading(false);
    }
  }

  function handleSkip() {
    // Just close without marking complete - will show again next time
    setIsVisible(false);
    onClose?.();
  }

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={handleSkip}
      />
      
      {/* Modal */}
      <div className="relative w-full max-w-lg mx-4 bg-slate-900 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden">
        {/* Close button */}
        <button
          onClick={handleSkip}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white transition-colors z-10"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header with gradient */}
        <div className="relative px-8 pt-8 pb-6 bg-gradient-to-b from-emerald-500/20 to-transparent">
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 rounded-full bg-emerald-500/30 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-emerald-400" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-center text-white mb-2">
            Welcome to Maverick! 🎉
          </h2>
          <p className="text-slate-400 text-center">
            {user?.name ? `Hey ${user.name.split(' ')[0]}, ` : ''}
            Let&apos;s set you up for smarter investing.
          </p>
        </div>

        {/* Features */}
        <div className="px-8 py-6 space-y-4">
          {features.map((feature, index) => (
            <div
              key={index}
              className="flex items-start space-x-4 p-3 rounded-lg hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <feature.icon className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <h3 className="text-sm font-medium text-white">{feature.title}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="px-8 pb-8 space-y-3">
          <Button
            onClick={handleComplete}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white"
            isLoading={isLoading}
          >
            Get Started
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
          <button
            onClick={handleSkip}
            className="w-full text-sm text-slate-400 hover:text-slate-300 py-2"
          >
            I&apos;ll explore on my own
          </button>
        </div>
      </div>
    </div>
  );
}


'use client';

import { useAuth } from './auth-context';
import { useCallback } from 'react';

/**
 * Hook to check if current user is in demo mode.
 * 
 * Returns:
 * - isDemoMode: boolean - true if user is demo user
 * - checkDemoRestriction: function - shows alert if action is restricted
 */
export function useDemoMode() {
  const { user } = useAuth();
  const isDemoMode = user?.is_demo_user ?? false;

  const checkDemoRestriction = useCallback((action: string = 'This action') => {
    if (isDemoMode) {
      // Could replace with a toast notification
      alert(`${action} is not available in demo mode. Create an account to unlock this feature.`);
      return true; // Action is restricted
    }
    return false; // Action is allowed
  }, [isDemoMode]);

  return {
    isDemoMode,
    checkDemoRestriction,
  };
}

/**
 * HOC to wrap actions that should be restricted in demo mode.
 * Shows upgrade prompt instead of performing the action.
 */
export function withDemoRestriction<T extends (...args: unknown[]) => unknown>(
  action: T,
  actionName: string,
  isDemoMode: boolean
): T {
  if (!isDemoMode) {
    return action;
  }

  return ((...args: unknown[]) => {
    alert(`${actionName} is not available in demo mode. Create an account to unlock this feature.`);
    return undefined;
  }) as T;
}


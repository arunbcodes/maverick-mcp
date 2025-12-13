'use client';

import { useState, useRef, useEffect } from 'react';
import { Bell, X, Check, CheckCheck, Sparkles, TrendingUp, TrendingDown, Target, AlertTriangle, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import {
  useAlerts,
  useUnreadAlertCount,
  useMarkAlertRead,
  useMarkAllAlertsRead,
  useDismissAlert,
  useAlertStream,
  type Alert,
  type AlertType,
  type AlertPriority,
} from '@/lib/api/hooks/use-alerts';
import { getAccessToken } from '@/lib/api/client';
import Link from 'next/link';

/**
 * Alert notification bell with dropdown
 */
export function AlertBell() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Check if user is logged in
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  useEffect(() => {
    // Check login status on mount and when token changes
    const checkLogin = () => setIsLoggedIn(!!getAccessToken());
    checkLogin();
    // Re-check periodically in case token changes
    const interval = setInterval(checkLogin, 5000);
    return () => clearInterval(interval);
  }, []);

  // Queries - only run when logged in
  const { data: unreadCount = 0, isLoading: countLoading } = useUnreadAlertCount();
  const { data: alerts = [], isLoading: alertsLoading } = useAlerts({ limit: 10 });

  // Mutations
  const markRead = useMarkAlertRead();
  const markAllRead = useMarkAllAlertsRead();
  const dismiss = useDismissAlert();

  // SSE subscription - ONLY enable when logged in and dropdown is open
  // This prevents connection storms on page load
  const { lastAlert, isConnected } = useAlertStream({
    enabled: isLoggedIn && isOpen,
    onAlert: (alert) => {
      console.log('New alert:', alert.title);
    },
  });

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <Button
        variant="ghost"
        size="icon"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Notifications"
      >
        <Bell className="h-5 w-5 text-slate-400" />
        
        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
        
        {/* Connection indicator */}
        <span
          className={cn(
            'absolute bottom-0 right-0 h-2 w-2 rounded-full',
            isConnected ? 'bg-emerald-500' : 'bg-slate-500'
          )}
        />
      </Button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-96 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
          <Card className="bg-slate-900 border-slate-700 shadow-xl">
            <CardHeader className="pb-2 flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-medium text-white">
                Notifications
              </CardTitle>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-slate-400 hover:text-white"
                    onClick={() => markAllRead.mutate()}
                    disabled={markAllRead.isPending}
                  >
                    <CheckCheck className="h-3 w-3 mr-1" />
                    Mark all read
                  </Button>
                )}
                <Link href="/settings?tab=alerts">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-slate-400 hover:text-white"
                    onClick={() => setIsOpen(false)}
                  >
                    Settings
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {alertsLoading ? (
                <div className="p-4 space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : alerts.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="h-8 w-8 text-slate-600 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">No notifications yet</p>
                  <p className="text-xs text-slate-600 mt-1">
                    Configure alerts to get notified about market opportunities
                  </p>
                </div>
              ) : (
                <div className="max-h-96 overflow-y-auto">
                  {alerts.map((alert) => (
                    <AlertItem
                      key={alert.alert_id}
                      alert={alert}
                      onMarkRead={() => markRead.mutate(alert.alert_id)}
                      onDismiss={() => dismiss.mutate(alert.alert_id)}
                      onClick={() => setIsOpen(false)}
                    />
                  ))}
                </div>
              )}

              {/* Footer */}
              {alerts.length > 0 && (
                <div className="border-t border-slate-800 p-2">
                  <Link href="/alerts">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full text-xs text-slate-400 hover:text-white"
                      onClick={() => setIsOpen(false)}
                    >
                      View all notifications
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

/**
 * Individual alert item in the dropdown
 */
function AlertItem({
  alert,
  onMarkRead,
  onDismiss,
  onClick,
}: {
  alert: Alert;
  onMarkRead: () => void;
  onDismiss: () => void;
  onClick: () => void;
}) {
  const isUnread = alert.status === 'unread';
  const icon = getAlertIcon(alert.alert_type);
  const priorityColor = getPriorityColor(alert.priority);

  const handleClick = () => {
    if (isUnread) {
      onMarkRead();
    }
    onClick();
  };

  return (
    <div
      className={cn(
        'relative flex gap-3 p-3 border-b border-slate-800 last:border-0 hover:bg-slate-800/50 cursor-pointer transition-colors',
        isUnread && 'bg-slate-800/30'
      )}
      onClick={handleClick}
    >
      {/* Unread indicator */}
      {isUnread && (
        <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-emerald-500" />
      )}

      {/* Icon */}
      <div className={cn('p-2 rounded-lg shrink-0', priorityColor.bg)}>
        {icon}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className={cn('text-sm font-medium', isUnread ? 'text-white' : 'text-slate-300')}>
              {alert.title}
            </p>
            <p className="text-xs text-slate-500 line-clamp-2 mt-0.5">
              {alert.message}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 shrink-0">
            {isUnread && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={(e) => {
                  e.stopPropagation();
                  onMarkRead();
                }}
              >
                <Check className="h-3 w-3 text-slate-500" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={(e) => {
                e.stopPropagation();
                onDismiss();
              }}
            >
              <X className="h-3 w-3 text-slate-500" />
            </Button>
          </div>
        </div>

        {/* AI Insight */}
        {alert.ai_insight && (
          <div className="mt-2 flex items-start gap-1 text-xs">
            <Sparkles className="h-3 w-3 text-emerald-400 shrink-0 mt-0.5" />
            <span className="text-emerald-400/80">{alert.ai_insight}</span>
          </div>
        )}

        {/* Timestamp */}
        <p className="text-[10px] text-slate-600 mt-1">
          {formatRelativeTime(alert.created_at)}
        </p>
      </div>
    </div>
  );
}

// ============================================
// Helpers
// ============================================

function getAlertIcon(type: AlertType) {
  switch (type) {
    case 'new_maverick_stock':
      return <TrendingUp className="h-4 w-4 text-emerald-400" />;
    case 'new_bear_stock':
      return <TrendingDown className="h-4 w-4 text-red-400" />;
    case 'new_breakout':
      return <Zap className="h-4 w-4 text-yellow-400" />;
    case 'rsi_oversold':
      return <TrendingDown className="h-4 w-4 text-emerald-400" />;
    case 'rsi_overbought':
      return <TrendingUp className="h-4 w-4 text-red-400" />;
    case 'price_target_hit':
      return <Target className="h-4 w-4 text-emerald-400" />;
    case 'stop_loss_hit':
      return <AlertTriangle className="h-4 w-4 text-red-400" />;
    default:
      return <Bell className="h-4 w-4 text-slate-400" />;
  }
}

function getPriorityColor(priority: AlertPriority) {
  switch (priority) {
    case 'critical':
      return { bg: 'bg-red-500/20', text: 'text-red-400' };
    case 'high':
      return { bg: 'bg-orange-500/20', text: 'text-orange-400' };
    case 'medium':
      return { bg: 'bg-yellow-500/20', text: 'text-yellow-400' };
    case 'low':
      return { bg: 'bg-slate-500/20', text: 'text-slate-400' };
    default:
      return { bg: 'bg-slate-500/20', text: 'text-slate-400' };
  }
}

function formatRelativeTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}


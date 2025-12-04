import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './button';
import { cn } from '@/lib/utils';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = 'Something went wrong',
  message = 'An error occurred while loading data.',
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 text-center',
        className
      )}
    >
      <div className="w-16 h-16 rounded-full bg-red-900/20 flex items-center justify-center mb-4">
        <AlertCircle className="h-8 w-8 text-red-400" />
      </div>
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      <p className="text-slate-400 max-w-sm mb-4">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          onClick={onRetry}
          className="border-slate-700 text-slate-300"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
}

interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export function ErrorBanner({ message, onDismiss, className }: ErrorBannerProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between p-4 rounded-lg bg-red-900/20 border border-red-800',
        className
      )}
    >
      <div className="flex items-center space-x-3">
        <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
        <p className="text-red-400 text-sm">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-400 hover:text-red-300 text-sm"
        >
          Dismiss
        </button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 text-center',
        className
      )}
    >
      {icon && (
        <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      {description && (
        <p className="text-slate-400 max-w-sm mb-4">{description}</p>
      )}
      {action && (
        <Button
          onClick={action.onClick}
          className="bg-emerald-600 hover:bg-emerald-500 text-white"
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}


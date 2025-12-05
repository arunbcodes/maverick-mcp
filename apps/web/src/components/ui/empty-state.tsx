'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
  secondaryAction?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
  className?: string;
  children?: ReactNode;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  className,
  children,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-12 px-6 text-center',
        className
      )}
    >
      <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-slate-400" />
      </div>
      
      <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
      
      <p className="text-sm text-slate-400 max-w-md mb-6">{description}</p>
      
      {children}
      
      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {action && (
            action.href ? (
              <Link href={action.href}>
                <Button className="bg-emerald-600 hover:bg-emerald-500 text-white">
                  {action.label}
                </Button>
              </Link>
            ) : (
              <Button
                className="bg-emerald-600 hover:bg-emerald-500 text-white"
                onClick={action.onClick}
              >
                {action.label}
              </Button>
            )
          )}
          
          {secondaryAction && (
            secondaryAction.href ? (
              <Link href={secondaryAction.href}>
                <Button
                  variant="outline"
                  className="border-slate-700 text-slate-300 hover:bg-slate-800"
                >
                  {secondaryAction.label}
                </Button>
              </Link>
            ) : (
              <Button
                variant="outline"
                className="border-slate-700 text-slate-300 hover:bg-slate-800"
                onClick={secondaryAction.onClick}
              >
                {secondaryAction.label}
              </Button>
            )
          )}
        </div>
      )}
    </div>
  );
}

// Pre-configured empty states for common use cases

export function EmptyPortfolioState({ onAddPosition }: { onAddPosition?: () => void }) {
  return (
    <EmptyState
      icon={require('lucide-react').Briefcase}
      title="No positions yet"
      description="Start building your portfolio by adding your first stock position. Track your investments and watch your wealth grow."
      action={{
        label: "Add Your First Position",
        onClick: onAddPosition,
      }}
      secondaryAction={{
        label: "Try Demo Portfolio",
        href: "/login",
      }}
    />
  );
}

export function EmptyScreenerState({ onRefresh }: { onRefresh?: () => void }) {
  return (
    <EmptyState
      icon={require('lucide-react').Search}
      title="No stocks match your criteria"
      description="Try adjusting your filters or check back later. Our screener updates regularly with new opportunities."
      action={{
        label: "Reset Filters",
        onClick: onRefresh,
      }}
    />
  );
}

export function EmptyWatchlistState() {
  return (
    <EmptyState
      icon={require('lucide-react').Star}
      title="Your watchlist is empty"
      description="Add stocks to your watchlist to track them easily. Click the star icon on any stock to add it."
      action={{
        label: "Explore Screener",
        href: "/screener",
      }}
    />
  );
}


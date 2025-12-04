'use client';

import { type UseQueryResult } from '@tanstack/react-query';
import { LoadingState, SkeletonCard } from './loading';
import { ErrorState } from './error';

interface DataStateProps<T> {
  query: UseQueryResult<T, Error>;
  loading?: React.ReactNode;
  error?: React.ReactNode;
  empty?: React.ReactNode;
  children: (data: T) => React.ReactNode;
  isEmpty?: (data: T) => boolean;
  loadingMessage?: string;
  errorMessage?: string;
}

/**
 * Generic wrapper for handling query loading/error/empty states
 * 
 * Usage:
 * ```tsx
 * <DataState query={portfolioQuery} loadingMessage="Loading portfolio...">
 *   {(data) => <PortfolioDisplay data={data} />}
 * </DataState>
 * ```
 */
export function DataState<T>({
  query,
  loading,
  error,
  empty,
  children,
  isEmpty,
  loadingMessage = 'Loading...',
  errorMessage = 'Failed to load data',
}: DataStateProps<T>) {
  const { data, isLoading, isError, error: queryError, refetch } = query;

  if (isLoading) {
    return loading ?? <LoadingState message={loadingMessage} />;
  }

  if (isError) {
    return (
      error ?? (
        <ErrorState
          message={queryError?.message || errorMessage}
          onRetry={() => refetch()}
        />
      )
    );
  }

  if (!data || (isEmpty && isEmpty(data))) {
    return empty ?? null;
  }

  return <>{children(data)}</>;
}

interface DataStateCardProps<T> extends Omit<DataStateProps<T>, 'loading'> {
  skeletonCount?: number;
}

/**
 * DataState variant with skeleton card loading state
 */
export function DataStateCard<T>({
  query,
  skeletonCount = 1,
  ...props
}: DataStateCardProps<T>) {
  return (
    <DataState
      query={query}
      loading={
        <div className="space-y-4">
          {Array.from({ length: skeletonCount }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      }
      {...props}
    />
  );
}

/**
 * Helper hook for combining multiple queries
 */
export function useCombinedQueryState<T extends UseQueryResult<unknown, Error>[]>(
  queries: T
) {
  const isLoading = queries.some((q) => q.isLoading);
  const isError = queries.some((q) => q.isError);
  const errors = queries.filter((q) => q.isError).map((q) => q.error);
  const isSuccess = queries.every((q) => q.isSuccess);

  return {
    isLoading,
    isError,
    isSuccess,
    errors,
    refetchAll: () => queries.forEach((q) => q.refetch()),
  };
}


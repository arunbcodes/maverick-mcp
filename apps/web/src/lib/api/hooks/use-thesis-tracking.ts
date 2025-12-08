/**
 * React Query hooks for Thesis Tracking API endpoints
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../client';
import type { APIResponse } from '../types';

// ============================================
// Types
// ============================================

export type ThesisStatus = 'active' | 'validated' | 'invalidated' | 'closed';
export type MilestoneStatus = 'pending' | 'hit' | 'missed' | 'cancelled';
export type MilestoneType = 'price_target' | 'stop_loss' | 'earnings' | 'dividend' | 'product_launch' | 'regulatory' | 'custom';
export type DecisionType = 'buy' | 'sell' | 'add' | 'trim' | 'hold';

export interface Milestone {
  milestone_id: string;
  type: MilestoneType;
  description: string;
  target_date: string | null;
  target_value: number | null;
  status: MilestoneStatus;
  actual_date: string | null;
  actual_value: number | null;
  notes: string | null;
}

export interface Decision {
  decision_id: string;
  type: DecisionType;
  date: string;
  shares: number;
  price: number;
  reasoning: string;
  thesis_reference: string | null;
  outcome: string | null;
}

export interface InvestmentThesis {
  thesis_id: string;
  user_id: string;
  ticker: string;
  title: string;
  summary: string;
  bull_case: string[];
  bear_case: string[];
  key_metrics: Record<string, unknown>;
  entry_price: number | null;
  entry_date: string | null;
  target_price: number | null;
  stop_price: number | null;
  time_horizon: string | null;
  milestones: Milestone[];
  decisions: Decision[];
  status: ThesisStatus;
  validation_notes: string | null;
  lessons_learned: string | null;
  created_at: string;
  updated_at: string | null;
  closed_at: string | null;
}

export interface ThesisSummary {
  thesis_id: string;
  ticker: string;
  title: string;
  status: ThesisStatus;
  entry_price: number | null;
  target_price: number | null;
  milestone_count: number;
  decision_count: number;
  created_at: string;
}

export interface CreateThesisRequest {
  ticker: string;
  title: string;
  summary: string;
  bull_case?: string[];
  bear_case?: string[];
  entry_price?: number;
  target_price?: number;
  stop_price?: number;
  time_horizon?: string;
  key_metrics?: Record<string, unknown>;
}

export interface WinLossAnalysis {
  total_closed: number;
  validated: number;
  invalidated: number;
  win_rate: number;
  common_winning_factors: [string, number][];
  common_losing_factors: [string, number][];
}

// ============================================
// Query Keys
// ============================================

export const thesisKeys = {
  all: ['thesis-tracking'] as const,
  lists: () => [...thesisKeys.all, 'lists'] as const,
  detail: (id: string) => [...thesisKeys.all, 'detail', id] as const,
  ticker: (ticker: string) => [...thesisKeys.all, 'ticker', ticker] as const,
  analytics: () => [...thesisKeys.all, 'analytics'] as const,
};

// ============================================
// Thesis CRUD Hooks
// ============================================

export function useTheses(status?: ThesisStatus) {
  const params = status ? `?status=${status}` : '';
  
  return useQuery({
    queryKey: [...thesisKeys.lists(), status],
    queryFn: async () => {
      const response = await api.get<APIResponse<ThesisSummary[]>>(
        `/thesis-tracking${params}`
      );
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useThesis(thesisId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: thesisKeys.detail(thesisId),
    queryFn: async () => {
      const response = await api.get<APIResponse<InvestmentThesis>>(
        `/thesis-tracking/${thesisId}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!thesisId,
    staleTime: 2 * 60 * 1000,
  });
}

export function useThesisForTicker(ticker: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: thesisKeys.ticker(ticker),
    queryFn: async () => {
      const response = await api.get<APIResponse<InvestmentThesis | null>>(
        `/thesis-tracking/ticker/${ticker}`
      );
      return response.data;
    },
    enabled: options?.enabled !== false && !!ticker,
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateThesis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateThesisRequest) => {
      const response = await api.post<APIResponse<InvestmentThesis>>(
        '/thesis-tracking',
        data
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.lists() });
    },
  });
}

export function useUpdateThesis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      thesisId,
      data,
    }: {
      thesisId: string;
      data: Partial<CreateThesisRequest>;
    }) => {
      const response = await api.patch<APIResponse<InvestmentThesis>>(
        `/thesis-tracking/${thesisId}`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.lists() });
      queryClient.invalidateQueries({ queryKey: thesisKeys.detail(variables.thesisId) });
    },
  });
}

export function useCloseThesis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      thesisId,
      status,
      validationNotes,
      lessonsLearned,
    }: {
      thesisId: string;
      status: ThesisStatus;
      validationNotes?: string;
      lessonsLearned?: string;
    }) => {
      const response = await api.post<APIResponse<InvestmentThesis>>(
        `/thesis-tracking/${thesisId}/close`,
        {
          status,
          validation_notes: validationNotes,
          lessons_learned: lessonsLearned,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.lists() });
      queryClient.invalidateQueries({ queryKey: thesisKeys.analytics() });
    },
  });
}

export function useDeleteThesis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (thesisId: string) => {
      await api.delete(`/thesis-tracking/${thesisId}`);
      return thesisId;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.lists() });
    },
  });
}

// ============================================
// Milestone Hooks
// ============================================

export function useAddMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      thesisId,
      type,
      description,
      targetDate,
      targetValue,
    }: {
      thesisId: string;
      type: MilestoneType;
      description: string;
      targetDate?: string;
      targetValue?: number;
    }) => {
      const response = await api.post<APIResponse<Milestone>>(
        `/thesis-tracking/${thesisId}/milestones`,
        {
          type,
          description,
          target_date: targetDate,
          target_value: targetValue,
        }
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.detail(variables.thesisId) });
    },
  });
}

export function useUpdateMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      thesisId,
      milestoneId,
      status,
      actualDate,
      actualValue,
      notes,
    }: {
      thesisId: string;
      milestoneId: string;
      status?: MilestoneStatus;
      actualDate?: string;
      actualValue?: number;
      notes?: string;
    }) => {
      const response = await api.patch<APIResponse<Milestone>>(
        `/thesis-tracking/${thesisId}/milestones/${milestoneId}`,
        {
          status,
          actual_date: actualDate,
          actual_value: actualValue,
          notes,
        }
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.detail(variables.thesisId) });
    },
  });
}

// ============================================
// Decision Hooks
// ============================================

export function useAddDecision() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      thesisId,
      type,
      shares,
      price,
      reasoning,
      thesisReference,
    }: {
      thesisId: string;
      type: DecisionType;
      shares: number;
      price: number;
      reasoning: string;
      thesisReference?: string;
    }) => {
      const response = await api.post<APIResponse<Decision>>(
        `/thesis-tracking/${thesisId}/decisions`,
        {
          type,
          shares,
          price,
          reasoning,
          thesis_reference: thesisReference,
        }
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.detail(variables.thesisId) });
    },
  });
}

export function useUpdateDecisionOutcome() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      thesisId,
      decisionId,
      outcome,
    }: {
      thesisId: string;
      decisionId: string;
      outcome: string;
    }) => {
      const response = await api.patch<APIResponse<Decision>>(
        `/thesis-tracking/${thesisId}/decisions/${decisionId}/outcome?outcome=${encodeURIComponent(outcome)}`
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: thesisKeys.detail(variables.thesisId) });
    },
  });
}

// ============================================
// Analytics Hooks
// ============================================

export function useWinLossAnalysis() {
  return useQuery({
    queryKey: thesisKeys.analytics(),
    queryFn: async () => {
      const response = await api.get<APIResponse<WinLossAnalysis>>(
        '/thesis-tracking/analytics/win-loss'
      );
      return response.data;
    },
    staleTime: 10 * 60 * 1000,
  });
}


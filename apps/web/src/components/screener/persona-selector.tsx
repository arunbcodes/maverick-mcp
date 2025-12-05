'use client';

import { useState, useEffect } from 'react';
import { Shield, TrendingUp, Flame, Check, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { InvestorPersona } from '@/lib/api/types';

interface PersonaOption {
  id: InvestorPersona;
  name: string;
  description: string;
  icon: typeof Shield;
  color: string;
  bgColor: string;
  criteria: string[];
}

const PERSONAS: PersonaOption[] = [
  {
    id: 'conservative',
    name: 'Conservative',
    description: 'Lower risk, stable growth',
    icon: Shield,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10 hover:bg-blue-500/20 border-blue-500/30',
    criteria: [
      'Lower volatility stocks',
      'Higher market cap',
      'Dividend paying',
      'Strong fundamentals',
    ],
  },
  {
    id: 'moderate',
    name: 'Moderate',
    description: 'Balanced risk & reward',
    icon: TrendingUp,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30',
    criteria: [
      'Balanced risk/reward',
      'Growth at reasonable price',
      'Mid-large cap focus',
      'Diversified signals',
    ],
  },
  {
    id: 'aggressive',
    name: 'Aggressive',
    description: 'High momentum, high risk',
    icon: Flame,
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10 hover:bg-orange-500/20 border-orange-500/30',
    criteria: [
      'High momentum plays',
      'Small/mid cap focus',
      'Breakout patterns',
      'Higher volatility',
    ],
  },
];

// Local storage key for persisting persona
const PERSONA_STORAGE_KEY = 'maverick_investor_persona';

interface PersonaSelectorProps {
  value?: InvestorPersona | null;
  onChange: (persona: InvestorPersona | null) => void;
  className?: string;
  showDescription?: boolean;
}

/**
 * Investor persona selector for personalized screening
 */
export function PersonaSelector({
  value,
  onChange,
  className,
  showDescription = true,
}: PersonaSelectorProps) {
  const [mounted, setMounted] = useState(false);

  // Load persisted persona on mount
  useEffect(() => {
    setMounted(true);
    if (value === undefined) {
      const stored = localStorage.getItem(PERSONA_STORAGE_KEY);
      if (stored && ['conservative', 'moderate', 'aggressive'].includes(stored)) {
        onChange(stored as InvestorPersona);
      }
    }
  }, []);

  // Persist when changed
  const handleChange = (persona: InvestorPersona | null) => {
    if (persona) {
      localStorage.setItem(PERSONA_STORAGE_KEY, persona);
    } else {
      localStorage.removeItem(PERSONA_STORAGE_KEY);
    }
    onChange(persona);
  };

  if (!mounted) return null;

  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-slate-400" />
          <span className="text-sm font-medium text-slate-300">
            Investor Profile
          </span>
        </div>
        {value && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleChange(null)}
            className="text-xs text-slate-500 hover:text-slate-300 h-auto py-1 px-2"
          >
            Clear
          </Button>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2">
        {PERSONAS.map((persona) => {
          const Icon = persona.icon;
          const isSelected = value === persona.id;

          return (
            <button
              key={persona.id}
              onClick={() => handleChange(persona.id)}
              className={cn(
                'relative flex flex-col items-center p-3 rounded-lg border transition-all text-center',
                isSelected
                  ? cn(persona.bgColor, 'border-2')
                  : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
              )}
            >
              {isSelected && (
                <div className="absolute top-1 right-1">
                  <Check className={cn('h-3 w-3', persona.color)} />
                </div>
              )}
              <div
                className={cn(
                  'p-2 rounded-lg mb-2',
                  isSelected ? persona.bgColor : 'bg-slate-700/50'
                )}
              >
                <Icon
                  className={cn(
                    'h-5 w-5',
                    isSelected ? persona.color : 'text-slate-400'
                  )}
                />
              </div>
              <span
                className={cn(
                  'text-sm font-medium',
                  isSelected ? 'text-white' : 'text-slate-300'
                )}
              >
                {persona.name}
              </span>
              {showDescription && (
                <span className="text-xs text-slate-500 mt-0.5">
                  {persona.description}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected persona details */}
      {value && showDescription && (
        <PersonaDetails persona={PERSONAS.find((p) => p.id === value)!} />
      )}
    </div>
  );
}

function PersonaDetails({ persona }: { persona: PersonaOption }) {
  return (
    <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/50">
      <h4 className="text-xs font-medium text-slate-400 mb-2">
        {persona.name} Screening Criteria
      </h4>
      <ul className="space-y-1">
        {persona.criteria.map((criterion, i) => (
          <li key={i} className="flex items-center gap-2 text-sm text-slate-400">
            <span className={persona.color}>•</span>
            {criterion}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Compact persona badge for display in results
 */
export function PersonaBadge({
  persona,
  className,
}: {
  persona: InvestorPersona;
  className?: string;
}) {
  const config = PERSONAS.find((p) => p.id === persona);
  if (!config) return null;

  const Icon = config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        config.bgColor.replace('hover:bg-', ''),
        config.color,
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {config.name}
    </span>
  );
}

/**
 * Get persona configuration
 */
export function getPersonaConfig(persona: InvestorPersona): PersonaOption | undefined {
  return PERSONAS.find((p) => p.id === persona);
}


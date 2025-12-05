'use client';

import { useState } from 'react';
import {
  Bell,
  Plus,
  Trash2,
  Edit,
  ToggleLeft,
  ToggleRight,
  Zap,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/loading';
import { cn } from '@/lib/utils';
import {
  useAlertRules,
  useAlertPresets,
  useCreateAlertRule,
  useUpdateAlertRule,
  useDeleteAlertRule,
  useToggleAlertRule,
  useEnablePreset,
  type AlertRule,
  type PresetRule,
  type AlertType,
  type AlertPriority,
  type CreateRuleRequest,
} from '@/lib/api/hooks/use-alerts';

/**
 * Alert rules settings component for the settings page
 */
export function AlertRulesSettings() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  // Queries
  const { data: rules = [], isLoading: rulesLoading } = useAlertRules();
  const { data: presets = [], isLoading: presetsLoading } = useAlertPresets();

  // Mutations
  const deleteRule = useDeleteAlertRule();
  const toggleRule = useToggleAlertRule();
  const enablePreset = useEnablePreset();

  const isLoading = rulesLoading || presetsLoading;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-white">Alert Rules</h3>
          <p className="text-sm text-slate-400">
            Configure when to receive notifications about market opportunities
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="bg-emerald-600 hover:bg-emerald-500"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Rule
        </Button>
      </div>

      {/* Quick Presets */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-400" />
            Quick Presets
          </CardTitle>
          <CardDescription className="text-xs">
            One-click enable popular alert configurations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {presetsLoading ? (
            <div className="flex gap-2">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-10 w-40" />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {presets.map((preset) => {
                const isEnabled = rules.some((r) => r.name === preset.name);
                return (
                  <Button
                    key={preset.name}
                    variant="outline"
                    size="sm"
                    disabled={isEnabled || enablePreset.isPending}
                    onClick={() => enablePreset.mutate(preset.name)}
                    className={cn(
                      'border-slate-600',
                      isEnabled && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    {getAlertTypeIcon(preset.alert_type as AlertType)}
                    <span className="ml-2">{preset.name}</span>
                    {isEnabled && <span className="ml-1 text-emerald-400">✓</span>}
                  </Button>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Current Rules */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-white flex items-center gap-2">
            <Bell className="h-4 w-4 text-emerald-400" />
            Your Alert Rules
          </CardTitle>
          <CardDescription className="text-xs">
            {rules.length} of 20 rules configured
          </CardDescription>
        </CardHeader>
        <CardContent>
          {rulesLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : rules.length === 0 ? (
            <div className="text-center py-8">
              <Bell className="h-10 w-10 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No alert rules configured</p>
              <p className="text-xs text-slate-500 mt-1">
                Create a rule or enable a preset to start receiving notifications
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {rules.map((rule) => (
                <RuleCard
                  key={rule.rule_id}
                  rule={rule}
                  onEdit={() => setEditingRule(rule)}
                  onDelete={() => deleteRule.mutate(rule.rule_id)}
                  onToggle={(enabled) =>
                    toggleRule.mutate({ ruleId: rule.rule_id, enabled })
                  }
                  isDeleting={deleteRule.isPending}
                  isToggling={toggleRule.isPending}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingRule) && (
        <RuleModal
          rule={editingRule}
          onClose={() => {
            setShowCreateModal(false);
            setEditingRule(null);
          }}
        />
      )}
    </div>
  );
}

/**
 * Individual rule card
 */
function RuleCard({
  rule,
  onEdit,
  onDelete,
  onToggle,
  isDeleting,
  isToggling,
}: {
  rule: AlertRule;
  onEdit: () => void;
  onDelete: () => void;
  onToggle: (enabled: boolean) => void;
  isDeleting: boolean;
  isToggling: boolean;
}) {
  return (
    <div
      className={cn(
        'flex items-center gap-4 p-4 rounded-lg border transition-colors',
        rule.enabled
          ? 'bg-slate-800/50 border-slate-700'
          : 'bg-slate-900/50 border-slate-800 opacity-60'
      )}
    >
      {/* Icon */}
      <div className="p-2 rounded-lg bg-slate-700/50">
        {getAlertTypeIcon(rule.alert_type)}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-white truncate">{rule.name}</p>
        <p className="text-xs text-slate-400 mt-0.5">
          {formatAlertType(rule.alert_type)} • {rule.priority} priority •{' '}
          {rule.cooldown_minutes}m cooldown
        </p>
        {Object.keys(rule.conditions).length > 0 && (
          <p className="text-xs text-slate-500 mt-1">
            Conditions: {formatConditions(rule.conditions)}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onEdit}
        >
          <Edit className="h-4 w-4 text-slate-400" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={onDelete}
          disabled={isDeleting}
        >
          <Trash2 className="h-4 w-4 text-red-400" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => onToggle(!rule.enabled)}
          disabled={isToggling}
        >
          {rule.enabled ? (
            <ToggleRight className="h-5 w-5 text-emerald-400" />
          ) : (
            <ToggleLeft className="h-5 w-5 text-slate-500" />
          )}
        </Button>
      </div>
    </div>
  );
}

/**
 * Create/Edit rule modal
 */
function RuleModal({
  rule,
  onClose,
}: {
  rule: AlertRule | null;
  onClose: () => void;
}) {
  const isEditing = !!rule;
  
  const [name, setName] = useState(rule?.name || '');
  const [alertType, setAlertType] = useState<AlertType>(
    rule?.alert_type || 'new_maverick_stock'
  );
  const [priority, setPriority] = useState<AlertPriority>(
    rule?.priority || 'medium'
  );
  const [cooldown, setCooldown] = useState(rule?.cooldown_minutes.toString() || '60');
  const [conditions, setConditions] = useState<Record<string, unknown>>(
    rule?.conditions || {}
  );

  const createRule = useCreateAlertRule();
  const updateRule = useUpdateAlertRule();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data = {
      name,
      alert_type: alertType,
      priority,
      cooldown_minutes: parseInt(cooldown),
      conditions,
    };

    if (isEditing) {
      await updateRule.mutateAsync({ ruleId: rule.rule_id, data });
    } else {
      await createRule.mutateAsync(data as CreateRuleRequest);
    }

    onClose();
  };

  const isLoading = createRule.isPending || updateRule.isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <Card className="relative z-10 w-full max-w-lg mx-4 bg-slate-900 border-slate-700 animate-fade-in">
        <CardHeader>
          <CardTitle className="text-white">
            {isEditing ? 'Edit Alert Rule' : 'Create Alert Rule'}
          </CardTitle>
          <CardDescription>
            Configure when to receive this notification
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Name</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Alert Rule"
                className="bg-slate-800 border-slate-700 text-white"
                required
              />
            </div>

            {/* Alert Type */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Alert Type</label>
              <select
                value={alertType}
                onChange={(e) => setAlertType(e.target.value as AlertType)}
                className="w-full px-3 py-2 rounded-md bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="new_maverick_stock">New Maverick Stock</option>
                <option value="new_bear_stock">New Bear Stock</option>
                <option value="new_breakout">New Breakout</option>
                <option value="rsi_oversold">RSI Oversold</option>
                <option value="rsi_overbought">RSI Overbought</option>
                <option value="price_target_hit">Price Target Hit</option>
                <option value="stop_loss_hit">Stop Loss Hit</option>
              </select>
            </div>

            {/* Priority */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value as AlertPriority)}
                className="w-full px-3 py-2 rounded-md bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            {/* Cooldown */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Cooldown (minutes)
              </label>
              <Input
                type="number"
                min="5"
                max="1440"
                value={cooldown}
                onChange={(e) => setCooldown(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
              />
              <p className="text-xs text-slate-500">
                Minimum time between alerts (5 min - 24 hours)
              </p>
            </div>

            {/* Type-specific conditions */}
            <ConditionsEditor
              alertType={alertType}
              conditions={conditions}
              onChange={setConditions}
            />

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                className="flex-1 border-slate-700 text-slate-300"
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-emerald-600 hover:bg-emerald-500"
                isLoading={isLoading}
              >
                {isEditing ? 'Save Changes' : 'Create Rule'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Dynamic conditions editor based on alert type
 */
function ConditionsEditor({
  alertType,
  conditions,
  onChange,
}: {
  alertType: AlertType;
  conditions: Record<string, unknown>;
  onChange: (conditions: Record<string, unknown>) => void;
}) {
  switch (alertType) {
    case 'new_maverick_stock':
    case 'new_bear_stock':
    case 'new_breakout':
      return (
        <div className="space-y-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Info className="h-4 w-4" />
            <span>Screening Alert Conditions</span>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              Minimum Score
            </label>
            <Input
              type="number"
              min="0"
              max="100"
              value={(conditions.min_score as number) || 70}
              onChange={(e) =>
                onChange({ ...conditions, min_score: parseInt(e.target.value) })
              }
              className="bg-slate-800 border-slate-700 text-white"
            />
          </div>
        </div>
      );

    case 'rsi_oversold':
    case 'rsi_overbought':
      return (
        <div className="space-y-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Info className="h-4 w-4" />
            <span>RSI Alert Conditions</span>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">
              RSI Threshold
            </label>
            <Input
              type="number"
              min="0"
              max="100"
              value={
                (conditions.threshold as number) ||
                (alertType === 'rsi_oversold' ? 30 : 70)
              }
              onChange={(e) =>
                onChange({ ...conditions, threshold: parseInt(e.target.value) })
              }
              className="bg-slate-800 border-slate-700 text-white"
            />
            <p className="text-xs text-slate-500">
              {alertType === 'rsi_oversold'
                ? 'Alert when RSI drops below this value'
                : 'Alert when RSI rises above this value'}
            </p>
          </div>
        </div>
      );

    case 'price_target_hit':
      return (
        <div className="space-y-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Info className="h-4 w-4" />
            <span>Price Target Conditions</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">Ticker</label>
              <Input
                value={(conditions.ticker as string) || ''}
                onChange={(e) =>
                  onChange({ ...conditions, ticker: e.target.value.toUpperCase() })
                }
                placeholder="AAPL"
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-300">
                Target Price
              </label>
              <Input
                type="number"
                step="0.01"
                value={(conditions.target_price as number) || ''}
                onChange={(e) =>
                  onChange({
                    ...conditions,
                    target_price: parseFloat(e.target.value),
                  })
                }
                placeholder="200.00"
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Direction</label>
            <select
              value={(conditions.direction as string) || 'above'}
              onChange={(e) =>
                onChange({ ...conditions, direction: e.target.value })
              }
              className="w-full px-3 py-2 rounded-md bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="above">Price rises above target</option>
              <option value="below">Price falls below target</option>
            </select>
          </div>
        </div>
      );

    default:
      return null;
  }
}

// ============================================
// Helpers
// ============================================

function getAlertTypeIcon(type: AlertType) {
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

function formatAlertType(type: AlertType): string {
  return type
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatConditions(conditions: Record<string, unknown>): string {
  const parts: string[] = [];
  
  if (conditions.min_score) {
    parts.push(`score ≥ ${conditions.min_score}`);
  }
  if (conditions.threshold) {
    parts.push(`threshold: ${conditions.threshold}`);
  }
  if (conditions.ticker) {
    parts.push(`ticker: ${conditions.ticker}`);
  }
  if (conditions.target_price) {
    parts.push(`target: $${conditions.target_price}`);
  }
  
  return parts.length > 0 ? parts.join(', ') : 'No conditions';
}


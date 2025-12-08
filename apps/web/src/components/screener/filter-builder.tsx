'use client';

import { useState } from 'react';
import { Plus, Trash2, GripVertical, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import {
  useFilterFields,
  FILTER_OPERATORS,
  type FilterCondition,
  type FilterFieldMeta,
} from '@/lib/api/hooks/use-custom-screeners';

interface FilterBuilderProps {
  conditions: FilterCondition[];
  onChange: (conditions: FilterCondition[]) => void;
  maxConditions?: number;
}

/**
 * Visual filter builder for custom screeners
 */
export function FilterBuilder({
  conditions,
  onChange,
  maxConditions = 15,
}: FilterBuilderProps) {
  const { data: fields = [] } = useFilterFields();

  // Group fields by category
  const fieldsByCategory = fields.reduce((acc, field) => {
    if (!acc[field.category]) {
      acc[field.category] = [];
    }
    acc[field.category].push(field);
    return acc;
  }, {} as Record<string, FilterFieldMeta[]>);

  const handleAddCondition = () => {
    if (conditions.length >= maxConditions) return;

    const defaultField = fields[0]?.field || 'price';
    onChange([
      ...conditions,
      {
        field: defaultField,
        operator: 'greater_than',
        value: null,
        value2: null,
      },
    ]);
  };

  const handleUpdateCondition = (index: number, updates: Partial<FilterCondition>) => {
    const updated = [...conditions];
    updated[index] = { ...updated[index], ...updates };
    onChange(updated);
  };

  const handleRemoveCondition = (index: number) => {
    onChange(conditions.filter((_, i) => i !== index));
  };

  const getFieldMeta = (fieldName: string): FilterFieldMeta | undefined => {
    return fields.find((f) => f.field === fieldName);
  };

  return (
    <div className="space-y-4">
      {/* Conditions List */}
      {conditions.length === 0 ? (
        <div className="text-center py-8 border border-dashed border-slate-700 rounded-lg">
          <Info className="h-8 w-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">No filters added yet</p>
          <p className="text-xs text-slate-600 mt-1">
            Add conditions to create your custom screen
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {conditions.map((condition, index) => (
            <FilterConditionRow
              key={index}
              condition={condition}
              index={index}
              fieldsByCategory={fieldsByCategory}
              fieldMeta={getFieldMeta(condition.field)}
              onUpdate={(updates) => handleUpdateCondition(index, updates)}
              onRemove={() => handleRemoveCondition(index)}
            />
          ))}
        </div>
      )}

      {/* Add Button */}
      <Button
        variant="outline"
        className="w-full border-dashed border-slate-600 text-slate-400 hover:text-white"
        onClick={handleAddCondition}
        disabled={conditions.length >= maxConditions}
      >
        <Plus className="h-4 w-4 mr-2" />
        Add Filter
        {conditions.length > 0 && (
          <span className="ml-2 text-xs text-slate-500">
            ({conditions.length}/{maxConditions})
          </span>
        )}
      </Button>
    </div>
  );
}

/**
 * Single filter condition row
 */
function FilterConditionRow({
  condition,
  index,
  fieldsByCategory,
  fieldMeta,
  onUpdate,
  onRemove,
}: {
  condition: FilterCondition;
  index: number;
  fieldsByCategory: Record<string, FilterFieldMeta[]>;
  fieldMeta: FilterFieldMeta | undefined;
  onUpdate: (updates: Partial<FilterCondition>) => void;
  onRemove: () => void;
}) {
  const fieldType = fieldMeta?.type || 'number';
  const availableOperators = FILTER_OPERATORS.filter((op) =>
    op.types.includes(fieldType)
  );

  const isBetween = condition.operator === 'between';

  return (
    <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-800/50 border border-slate-700 group">
      {/* Drag Handle (visual only for now) */}
      <GripVertical className="h-4 w-4 text-slate-600 cursor-grab opacity-0 group-hover:opacity-100" />

      {/* Field Select */}
      <select
        value={condition.field}
        onChange={(e) => onUpdate({ field: e.target.value })}
        className="px-2 py-1.5 rounded bg-slate-900 border border-slate-700 text-white text-sm min-w-[140px] focus:outline-none focus:ring-1 focus:ring-emerald-500"
      >
        {Object.entries(fieldsByCategory).map(([category, categoryFields]) => (
          <optgroup key={category} label={category}>
            {categoryFields.map((field) => (
              <option key={field.field} value={field.field}>
                {field.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>

      {/* Operator Select */}
      <select
        value={condition.operator}
        onChange={(e) => onUpdate({ operator: e.target.value })}
        className="px-2 py-1.5 rounded bg-slate-900 border border-slate-700 text-white text-sm min-w-[120px] focus:outline-none focus:ring-1 focus:ring-emerald-500"
      >
        {availableOperators.map((op) => (
          <option key={op.value} value={op.value}>
            {op.label}
          </option>
        ))}
      </select>

      {/* Value Input(s) */}
      <div className="flex items-center gap-2 flex-1">
        <Input
          type={fieldType === 'number' ? 'number' : 'text'}
          value={condition.value ?? ''}
          onChange={(e) =>
            onUpdate({
              value:
                fieldType === 'number'
                  ? e.target.value
                    ? parseFloat(e.target.value)
                    : null
                  : e.target.value,
            })
          }
          placeholder={isBetween ? 'Min' : 'Value'}
          className="bg-slate-900 border-slate-700 text-white text-sm h-8"
          min={fieldMeta?.min}
          max={fieldMeta?.max}
        />

        {isBetween && (
          <>
            <span className="text-slate-500 text-sm">to</span>
            <Input
              type="number"
              value={condition.value2 ?? ''}
              onChange={(e) =>
                onUpdate({
                  value2: e.target.value ? parseFloat(e.target.value) : null,
                })
              }
              placeholder="Max"
              className="bg-slate-900 border-slate-700 text-white text-sm h-8"
              min={fieldMeta?.min}
              max={fieldMeta?.max}
            />
          </>
        )}
      </div>

      {/* Remove Button */}
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={onRemove}
      >
        <Trash2 className="h-4 w-4 text-slate-500 hover:text-red-400" />
      </Button>
    </div>
  );
}

/**
 * Filter preview summary
 */
export function FilterSummary({ conditions }: { conditions: FilterCondition[] }) {
  const { data: fields = [] } = useFilterFields();

  const getFieldLabel = (fieldName: string) => {
    return fields.find((f) => f.field === fieldName)?.label || fieldName;
  };

  const getOperatorLabel = (op: string) => {
    return FILTER_OPERATORS.find((o) => o.value === op)?.label || op;
  };

  if (conditions.length === 0) {
    return <span className="text-slate-500">No filters</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {conditions.map((condition, index) => (
        <span
          key={index}
          className="inline-flex items-center px-2 py-1 rounded bg-slate-800 border border-slate-700 text-xs"
        >
          <span className="text-emerald-400">{getFieldLabel(condition.field)}</span>
          <span className="text-slate-500 mx-1">{getOperatorLabel(condition.operator)}</span>
          <span className="text-white">
            {condition.operator === 'between'
              ? `${condition.value} - ${condition.value2}`
              : String(condition.value)}
          </span>
        </span>
      ))}
    </div>
  );
}


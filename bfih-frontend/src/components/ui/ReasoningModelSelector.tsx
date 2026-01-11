import { useState, useEffect } from 'react';
import { cn } from '../../utils';
import { getReasoningModels } from '../../api';
import type { ReasoningModel } from '../../types';

interface ReasoningModelSelectorProps {
  value: string | null;
  onChange: (model: string | null) => void;
  className?: string;
}

const COST_COLORS = {
  low: 'text-green-400',
  medium: 'text-yellow-400',
  high: 'text-red-400',
};

const COST_LABELS = {
  low: '$',
  medium: '$$',
  high: '$$$',
};

export function ReasoningModelSelector({
  value,
  onChange,
  className,
}: ReasoningModelSelectorProps) {
  const [models, setModels] = useState<ReasoningModel[]>([]);
  const [defaultModel, setDefaultModel] = useState<string>('o3-mini');
  const [isLoading, setIsLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    async function loadModels() {
      try {
        const response = await getReasoningModels();
        setModels(response.models);
        setDefaultModel(response.default);
      } catch (error) {
        console.error('Failed to load reasoning models:', error);
        // Fallback models
        setModels([
          { id: 'o3-mini', name: 'o3-mini', description: 'Fast, cost-efficient (default)', cost: 'low' },
          { id: 'gpt-5.2', name: 'GPT-5.2', description: 'Most capable', cost: 'high' },
        ]);
      } finally {
        setIsLoading(false);
      }
    }
    loadModels();
  }, []);

  const selectedModel = models.find(m => m.id === value) || models.find(m => m.id === defaultModel);
  const displayName = value ? selectedModel?.name : `${selectedModel?.name || defaultModel} (default)`;

  if (isLoading) {
    return (
      <div className={cn('h-10 w-48 bg-surface-2 rounded-lg animate-pulse', className)} />
    );
  }

  return (
    <div className={cn('relative', className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg',
          'bg-surface-2 border border-border',
          'hover:bg-surface-3 transition-colors',
          'text-sm text-text-primary'
        )}
      >
        <span className="text-text-secondary">Model:</span>
        <span className="font-medium">{displayName}</span>
        {selectedModel && (
          <span className={cn('text-xs', COST_COLORS[selectedModel.cost])}>
            {COST_LABELS[selectedModel.cost]}
          </span>
        )}
        <svg
          className={cn('w-4 h-4 transition-transform', isOpen && 'rotate-180')}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className={cn(
            'absolute top-full left-0 mt-1 z-20',
            'min-w-[280px] p-1',
            'bg-surface-2 border border-border rounded-lg shadow-xl'
          )}>
            {/* Default option */}
            <button
              type="button"
              onClick={() => {
                onChange(null);
                setIsOpen(false);
              }}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2 rounded-md',
                'hover:bg-surface-3 transition-colors text-left',
                !value && 'bg-primary/10'
              )}
            >
              <div className="flex-1">
                <div className="text-sm font-medium text-text-primary">
                  Use Default ({defaultModel})
                </div>
                <div className="text-xs text-text-secondary">
                  Server-configured default model
                </div>
              </div>
              {!value && (
                <svg className="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>

            <div className="border-t border-border my-1" />

            {/* Model options */}
            {models.map((model) => (
              <button
                key={model.id}
                type="button"
                onClick={() => {
                  onChange(model.id);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2 rounded-md',
                  'hover:bg-surface-3 transition-colors text-left',
                  value === model.id && 'bg-primary/10'
                )}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">
                      {model.name}
                    </span>
                    <span className={cn('text-xs', COST_COLORS[model.cost])}>
                      {COST_LABELS[model.cost]}
                    </span>
                  </div>
                  <div className="text-xs text-text-secondary">
                    {model.description}
                  </div>
                </div>
                {value === model.id && (
                  <svg className="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

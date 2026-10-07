import React from 'react';
import { LucideIcon, Gem } from 'lucide-react';
import { Button } from './button';
import { cn } from '../../lib/utils';

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  actionVariant?: 'gold' | 'atelier' | 'outline';
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = Gem,
  actionLabel,
  onAction,
  actionVariant = 'gold',
  secondaryActionLabel,
  onSecondaryAction,
  className,
}) => {
  return (
    <div
      className={cn(
        'double-bezel text-center my-6 max-w-xl mx-auto',
        className
      )}
    >
      <div className="double-bezel-inner py-12 px-8 flex flex-col items-center justify-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-amber-400/10 border border-amber-400/25 text-amber-300 flex items-center justify-center shadow-lg shadow-amber-500/5">
          <Icon className="w-7 h-7 opacity-90" />
        </div>
        <div className="space-y-1.5 max-w-md">
          <h3 className="text-base font-serif font-bold text-white tracking-wide">{title}</h3>
          <p className="text-xs text-slate-400 font-light leading-relaxed">
            {description}
          </p>
        </div>
        {(actionLabel || secondaryActionLabel) && (
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            {actionLabel && onAction && (
              <Button
                variant={actionVariant}
                size="sm"
                onClick={onAction}
                className="font-bold tracking-wide"
              >
                {actionLabel}
              </Button>
            )}
            {secondaryActionLabel && onSecondaryAction && (
              <Button
                variant="outline"
                size="sm"
                onClick={onSecondaryAction}
              >
                {secondaryActionLabel}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmptyState;

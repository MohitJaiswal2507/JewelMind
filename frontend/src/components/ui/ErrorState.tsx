import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './button';
import { cn } from '../../lib/utils';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "We couldn't load this page",
  message = "The server may be temporarily unavailable or connectivity was interrupted. Please retry.",
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'double-bezel text-center my-6 max-w-lg mx-auto',
        className
      )}
    >
      <div className="double-bezel-inner py-10 px-8 flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/25 text-rose-400 flex items-center justify-center shadow-lg shadow-rose-500/5">
          <AlertTriangle className="w-6 h-6 opacity-90" />
        </div>
        <div className="space-y-1.5 max-w-sm">
          <h3 className="text-base font-serif font-bold text-white tracking-wide">{title}</h3>
          <p className="text-xs text-slate-400 font-light leading-relaxed">
            {message}
          </p>
        </div>
        {onRetry && (
          <div className="pt-2">
            <Button
              variant="atelier"
              size="sm"
              onClick={onRetry}
              className="gap-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Try Again
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ErrorState;

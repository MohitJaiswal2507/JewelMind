import * as React from 'react';
import { cn } from '../../lib/utils';

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          'flex min-h-[96px] w-full rounded-xl border bg-[#0B1210]/95 px-3.5 py-2.5 text-xs text-[#F4EFE5] placeholder:text-[#6F756F] transition-all duration-200 resize-y leading-relaxed shadow-inner',
          error
            ? 'border-rose-500/60 focus-visible:ring-2 focus-visible:ring-rose-400/60'
            : 'border-[#1C2621] hover:border-[#28362F] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D8AD55]/60 focus-visible:border-[#D8AD55]/60',
          'disabled:cursor-not-allowed disabled:opacity-40 disabled:bg-white/[0.02]',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = 'Textarea';

export { Textarea };

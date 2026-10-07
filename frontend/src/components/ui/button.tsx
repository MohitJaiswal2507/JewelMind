import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 select-none cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#D8AD55]/70 focus-visible:ring-offset-2 focus-visible:ring-offset-[#050806] disabled:pointer-events-none disabled:opacity-40 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        default:
          'bg-[#D8AD55] hover:bg-[#F1D28A] text-[#050806] font-bold shadow-md shadow-[#D8AD55]/15 hover:brightness-105 active:scale-[0.98] transition-all',
        gold:
          'bg-[#D8AD55] hover:bg-[#F1D28A] text-[#050806] font-bold shadow-md shadow-[#D8AD55]/15 hover:brightness-105 active:scale-[0.98] transition-all',
        atelier:
          'bg-[#0B1210] border border-[#D8AD55]/30 text-[#F1D28A] shadow-sm hover:bg-[#141D19] hover:border-[#D8AD55]/60 active:scale-[0.98]',
        destructive:
          'bg-[#D9534F]/15 border border-[#D9534F]/30 text-rose-300 hover:bg-[#D9534F]/25 active:scale-[0.98]',
        outline:
          'border border-white/10 bg-transparent text-[#F4EFE5] hover:bg-white/[0.04] hover:text-white hover:border-[#D8AD55]/40 active:scale-[0.98]',
        secondary:
          'bg-[#0B1210] border border-white/5 text-[#A9ADA7] hover:bg-[#141D19] hover:text-[#F4EFE5] active:scale-[0.98]',
        ghost:
          'text-[#A9ADA7] hover:bg-white/[0.06] hover:text-[#F4EFE5] active:scale-[0.98]',
        link:
          'text-[#D8AD55] underline-offset-4 hover:underline p-0 h-auto font-medium',
      },
      size: {
        default: 'h-9 px-4 py-2 min-h-[36px]',
        sm: 'h-8 px-3 text-[11px] min-h-[32px]',
        lg: 'h-11 px-7 text-sm tracking-normal min-h-[44px]',
        touch: 'h-12 px-6 text-sm min-h-[48px]', // Meets WCAG 44px+ touch target rule
        icon: 'h-9 w-9 p-0 min-w-[36px] min-h-[36px]',
        'icon-touch': 'h-11 w-11 p-0 min-w-[44px] min-h-[44px]',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  iconTrailing?: React.ReactNode;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, disabled, iconTrailing, children, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    const isDisabled = disabled || loading;

    if (asChild) {
      return (
        <Comp
          className={cn(buttonVariants({ variant, size, className }))}
          ref={ref}
          {...props}
        >
          {children}
        </Comp>
      );
    }

    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={isDisabled}
        aria-busy={loading ? 'true' : undefined}
        {...props}
      >
        {loading && <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin text-current" />}
        {children}
        {iconTrailing && !loading && (
          <span className="ml-2 inline-flex items-center justify-center w-6 h-6 rounded-full bg-black/10 dark:bg-white/10 text-current transition-transform duration-200 group-hover:translate-x-0.5">
            {iconTrailing}
          </span>
        )}
      </button>
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };

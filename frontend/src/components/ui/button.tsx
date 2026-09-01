import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber-400 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-amber-500 text-slate-950 font-semibold shadow hover:bg-amber-400 active:bg-amber-600',
        destructive:
          'bg-rose-500 text-slate-50 shadow-sm hover:bg-rose-600',
        outline:
          'border border-slate-700 bg-transparent text-slate-200 shadow-sm hover:bg-slate-800 hover:text-white',
        secondary:
          'bg-slate-800 text-slate-200 shadow-sm hover:bg-slate-700 hover:text-white',
        ghost:
          'text-slate-300 hover:bg-slate-800 hover:text-white',
        link:
          'text-amber-400 underline-offset-4 hover:underline',
        gold:
          'bg-gradient-to-r from-amber-500 via-amber-400 to-yellow-300 text-slate-950 font-bold shadow-lg shadow-amber-500/20 hover:brightness-110 active:brightness-95',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-10 rounded-md px-8 text-base',
        icon: 'h-9 w-9',
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
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };

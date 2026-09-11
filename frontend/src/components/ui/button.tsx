import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-xs font-semibold tracking-wide transition-all duration-200 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber-400/50 disabled:pointer-events-none disabled:opacity-40 select-none cursor-pointer',
  {
    variants: {
      variant: {
        default:
          'bg-gradient-to-r from-amber-400 via-amber-300 to-yellow-200 text-slate-950 font-bold shadow-md shadow-amber-500/10 hover:brightness-105 active:scale-[0.98]',
        gold:
          'bg-gradient-to-r from-amber-400 via-amber-300 to-yellow-200 text-slate-950 font-bold shadow-md shadow-amber-500/10 hover:brightness-105 active:scale-[0.98]',
        atelier:
          'bg-[#151A26] border border-amber-400/30 text-amber-200 shadow-sm hover:bg-[#1C2333] hover:border-amber-400/50 active:scale-[0.98]',
        destructive:
          'bg-rose-500/15 border border-rose-500/30 text-rose-300 hover:bg-rose-500/25 active:scale-[0.98]',
        outline:
          'border border-white/10 bg-transparent text-slate-200 hover:bg-white/[0.04] hover:text-white hover:border-white/20 active:scale-[0.98]',
        secondary:
          'bg-[#121622] border border-white/5 text-slate-300 hover:bg-[#181D2C] hover:text-white active:scale-[0.98]',
        ghost:
          'text-slate-300 hover:bg-white/[0.05] hover:text-white active:scale-[0.98]',
        link:
          'text-amber-300 underline-offset-4 hover:underline p-0 h-auto font-medium',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 px-3 text-[11px]',
        lg: 'h-11 px-7 text-sm tracking-normal',
        icon: 'h-9 w-9 p-0',
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

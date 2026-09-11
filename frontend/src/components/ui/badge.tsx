import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-wider uppercase transition-all duration-200',
  {
    variants: {
      variant: {
        default:
          'border-amber-400/30 bg-amber-400/10 text-amber-300',
        secondary:
          'border-white/10 bg-white/[0.04] text-slate-300',
        destructive:
          'border-rose-500/30 bg-rose-500/10 text-rose-300',
        outline:
          'border-white/15 text-slate-300 bg-transparent',
        success:
          'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
        gold:
          'border-amber-400/40 bg-gradient-to-r from-amber-400/15 via-yellow-400/10 to-amber-300/15 text-amber-200 shadow-sm shadow-amber-500/10',
        atelier:
          'border-white/10 bg-[#141824] text-slate-200',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };

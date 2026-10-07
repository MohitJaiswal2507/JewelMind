import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold tracking-[0.14em] uppercase transition-all duration-200 select-none',
  {
    variants: {
      variant: {
        default:
          'border-[#D8AD55]/30 bg-[#D8AD55]/10 text-[#F1D28A]',
        secondary:
          'border-white/10 bg-white/[0.04] text-[#A9ADA7]',
        destructive:
          'border-[#D9534F]/30 bg-[#D9534F]/10 text-rose-300',
        outline:
          'border-white/15 text-[#A9ADA7] bg-transparent',
        success:
          'border-[#18A879]/30 bg-[#18A879]/10 text-[#18A879]',
        warning:
          'border-[#D8AD55]/30 bg-[#D8AD55]/10 text-[#F1D28A]',
        info:
          'border-blue-500/30 bg-blue-500/10 text-blue-300',
        ai:
          'border-purple-400/30 bg-purple-500/10 text-purple-300',
        gold:
          'border-[#D8AD55]/40 bg-[#D8AD55]/10 text-[#F1D28A] shadow-sm shadow-[#D8AD55]/10',
        atelier:
          'border-[#1C2621] bg-[#0B1210] text-[#F4EFE5]',
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

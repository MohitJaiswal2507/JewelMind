import React from 'react';
import { cn } from '../../lib/utils';

export interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'value' | 'onChange'> {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onValueChange?: (value: number) => void;
  className?: string;
}

export const Slider: React.FC<SliderProps> = ({
  value,
  min = 0,
  max = 100,
  step = 1,
  onValueChange,
  className,
  disabled,
  ...props
}) => {
  const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));

  return (
    <div className={cn('relative flex items-center select-none touch-none w-full h-5', className)}>
      {/* Background Track */}
      <div className="relative w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
        {/* Filled Range */}
        <div
          className="h-full bg-gradient-to-r from-amber-500 to-amber-400 rounded-full transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Real Input */}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onValueChange && onValueChange(parseFloat(e.target.value))}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        {...props}
      />

      {/* Visual Thumb */}
      <div
        className={cn(
          'absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-amber-400 border-2 border-[#0b0f19] rounded-full shadow-md pointer-events-none transition-transform duration-75',
          'group-hover:scale-110'
        )}
        style={{ left: `calc(${percentage}% - 8px)` }}
      />
    </div>
  );
};

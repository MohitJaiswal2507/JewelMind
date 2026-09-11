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
    <div className={cn('relative flex items-center select-none touch-none w-full h-5 group', className)}>
      {/* Background Track */}
      <div className="relative w-full h-1.5 bg-[#161B26] border border-white/5 rounded-full overflow-hidden">
        {/* Filled Range */}
        <div
          className="h-full bg-gradient-to-r from-amber-500/80 via-amber-400 to-yellow-300 rounded-full transition-all"
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
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed z-10"
        {...props}
      />

      {/* Visual Thumb */}
      <div
        className={cn(
          'absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-gradient-to-tr from-amber-400 to-yellow-200 border-2 border-[#0E111A] rounded-full shadow-lg shadow-amber-500/20 pointer-events-none transition-transform duration-100',
          'group-hover:scale-115'
        )}
        style={{ left: `calc(${percentage}% - 8px)` }}
      />
    </div>
  );
};

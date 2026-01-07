import { forwardRef, type InputHTMLAttributes } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils';

interface SliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'onChange'> {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  showValue?: boolean;
  formatValue?: (value: number) => string;
  variant?: 'default' | 'paradigm';
  color?: string;
  onChange?: (value: number) => void;
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(
  (
    {
      value,
      min = 0,
      max = 100,
      step = 1,
      label,
      showValue = true,
      formatValue = (v) => String(v),
      variant = 'default',
      color,
      onChange,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const percentage = ((value - min) / (max - min)) * 100;
    const accentColor = color || (variant === 'paradigm' ? 'var(--color-paradigm-k1)' : 'var(--color-accent)');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange?.(Number(e.target.value));
    };

    return (
      <div className={cn('w-full', className)}>
        {(label || showValue) && (
          <div className="flex justify-between items-center mb-2">
            {label && (
              <span className="text-sm font-medium text-text-secondary">{label}</span>
            )}
            {showValue && (
              <motion.span
                key={value}
                initial={{ scale: 1 }}
                animate={{ scale: [1, 1.1, 1] }}
                transition={{ duration: 0.2 }}
                className="text-sm font-semibold text-text-primary"
              >
                {formatValue(value)}
              </motion.span>
            )}
          </div>
        )}
        <div className="relative">
          {/* Track background */}
          <div className="absolute inset-y-0 left-0 right-0 flex items-center">
            <div className="w-full h-2 bg-surface-2 rounded-full">
              {/* Filled track */}
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: accentColor }}
                initial={{ width: 0 }}
                animate={{ width: `${percentage}%` }}
                transition={{ duration: 0.1 }}
              />
            </div>
          </div>
          {/* Native range input */}
          <input
            ref={ref}
            type="range"
            value={value}
            min={min}
            max={max}
            step={step}
            onChange={handleChange}
            disabled={disabled}
            className={cn(
              'relative w-full h-6 appearance-none bg-transparent cursor-pointer',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              // Thumb styling
              '[&::-webkit-slider-thumb]:appearance-none',
              '[&::-webkit-slider-thumb]:w-5',
              '[&::-webkit-slider-thumb]:h-5',
              '[&::-webkit-slider-thumb]:rounded-full',
              '[&::-webkit-slider-thumb]:bg-white',
              '[&::-webkit-slider-thumb]:shadow-md',
              '[&::-webkit-slider-thumb]:border-2',
              '[&::-webkit-slider-thumb]:cursor-grab',
              '[&::-webkit-slider-thumb]:active:cursor-grabbing',
              '[&::-webkit-slider-thumb]:transition-transform',
              '[&::-webkit-slider-thumb]:hover:scale-110',
              // Firefox thumb
              '[&::-moz-range-thumb]:w-5',
              '[&::-moz-range-thumb]:h-5',
              '[&::-moz-range-thumb]:rounded-full',
              '[&::-moz-range-thumb]:bg-white',
              '[&::-moz-range-thumb]:border-2',
              '[&::-moz-range-thumb]:cursor-grab'
            )}
            style={{
              // @ts-ignore - CSS custom property
              '--thumb-border-color': accentColor,
            } as React.CSSProperties}
            {...props}
          />
        </div>
      </div>
    );
  }
);

Slider.displayName = 'Slider';

// Range slider with min/max handles
interface RangeSliderProps {
  minValue: number;
  maxValue: number;
  min?: number;
  max?: number;
  step?: number;
  label?: string;
  formatValue?: (value: number) => string;
  onChange?: (min: number, max: number) => void;
  className?: string;
}

export function RangeSlider({
  minValue,
  maxValue,
  min = 0,
  max = 100,
  step = 1,
  label,
  formatValue = (v) => String(v),
  onChange,
  className,
}: RangeSliderProps) {
  const minPercentage = ((minValue - min) / (max - min)) * 100;
  const maxPercentage = ((maxValue - min) / (max - min)) * 100;

  return (
    <div className={cn('w-full', className)}>
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-text-secondary">{label}</span>
          <span className="text-sm text-text-primary">
            {formatValue(minValue)} - {formatValue(maxValue)}
          </span>
        </div>
      )}
      <div className="relative h-6">
        {/* Track */}
        <div className="absolute inset-y-0 left-0 right-0 flex items-center">
          <div className="w-full h-2 bg-surface-2 rounded-full">
            <div
              className="h-full bg-accent rounded-full"
              style={{
                marginLeft: `${minPercentage}%`,
                width: `${maxPercentage - minPercentage}%`,
              }}
            />
          </div>
        </div>
        {/* Min slider */}
        <input
          type="range"
          value={minValue}
          min={min}
          max={max}
          step={step}
          onChange={(e) => {
            const newMin = Math.min(Number(e.target.value), maxValue - step);
            onChange?.(newMin, maxValue);
          }}
          className="absolute w-full h-full appearance-none bg-transparent cursor-pointer pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-accent"
        />
        {/* Max slider */}
        <input
          type="range"
          value={maxValue}
          min={min}
          max={max}
          step={step}
          onChange={(e) => {
            const newMax = Math.max(Number(e.target.value), minValue + step);
            onChange?.(minValue, newMax);
          }}
          className="absolute w-full h-full appearance-none bg-transparent cursor-pointer pointer-events-none [&::-webkit-slider-thumb]:pointer-events-auto [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-accent"
        />
      </div>
    </div>
  );
}

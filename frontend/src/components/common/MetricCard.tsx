import React from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: string;
  isPositive?: boolean;
  icon?: React.ReactNode;
  subtitle?: string;
  color?: 'emerald' | 'amber' | 'blue' | 'purple' | 'slate';
  sparkline?: number[];
  targetProgress?: {
    current: number;
    target: number;
    label?: string;
  };
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  change,
  isPositive,
  icon,
  subtitle,
  color = 'emerald',
  sparkline,
  targetProgress,
}) => {
  const colorStyles = {
    emerald: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    amber: 'text-amber-700 bg-amber-50 border-amber-200',
    blue: 'text-sky-700 bg-sky-50 border-sky-200',
    purple: 'text-indigo-700 bg-indigo-50 border-indigo-200',
    slate: 'text-slate-700 bg-slate-100 border-slate-200',
  };

  const sparklineStroke = {
    emerald: '#059669',
    amber: '#d97706',
    blue: '#0284c7',
    purple: '#6366f1',
    slate: '#64748b',
  }[color];

  // Generate SVG path for sparkline if points provided
  const renderSparkline = () => {
    if (!sparkline || sparkline.length < 2) return null;
    const width = 80;
    const height = 28;
    const min = Math.min(...sparkline);
    const max = Math.max(...sparkline);
    const range = max - min || 1;

    const points = sparkline.map((val, idx) => {
      const x = (idx / (sparkline.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 6) - 3;
      return `${x},${y}`;
    });

    return (
      <svg width={width} height={height} className="overflow-visible opacity-80 group-hover:opacity-100 transition-opacity">
        <polyline
          fill="none"
          stroke={sparklineStroke}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points.join(' ')}
        />
        <circle
          cx={width}
          cy={height - ((sparkline[sparkline.length - 1] - min) / range) * (height - 6) - 3}
          r="3"
          fill={sparklineStroke}
        />
      </svg>
    );
  };

  return (
    <div className="relative bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xs hover:shadow-sm hover:border-slate-300 transition-all duration-200 group overflow-hidden">
      {/* Header with Title and Icon */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider truncate">{title}</span>
        {icon && <div className={`p-2 rounded-lg border ${colorStyles[color]}`}>{icon}</div>}
      </div>

      {/* Main Metric Value and Sparkline */}
      <div className="mt-3 flex items-end justify-between gap-3">
        <div className="flex items-baseline gap-1.5 flex-wrap">
          <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 font-mono">
            {typeof value === 'number' ? value.toLocaleString('ru-RU') : value}
          </span>
          {unit && <span className="text-xs font-semibold text-slate-500">{unit}</span>}
        </div>
        {renderSparkline()}
      </div>

      {/* Progress Bar towards Target if defined */}
      {targetProgress && (
        <div className="mt-3 pt-2.5 border-t border-slate-100">
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="text-slate-500 font-medium">{targetProgress.label || 'Цель'}</span>
            <span className="text-slate-700 font-mono font-semibold">
              {Math.min(100, Math.round((targetProgress.current / targetProgress.target) * 100))}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                color === 'emerald' ? 'bg-emerald-600' : color === 'amber' ? 'bg-amber-500' : 'bg-sky-500'
              }`}
              style={{ width: `${Math.min(100, Math.round((targetProgress.current / targetProgress.target) * 100))}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer with Change badge and Subtitle */}
      {(change || subtitle) && (
        <div className="mt-3 flex items-center gap-2 text-xs flex-wrap">
          {change && (
            <span
              className={`inline-flex items-center px-1.5 py-0.5 rounded-md font-semibold text-[11px] border ${
                isPositive
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-rose-50 text-rose-700 border-rose-200'
              }`}
            >
              {change}
            </span>
          )}
          {subtitle && <span className="text-slate-500 text-[11px] truncate">{subtitle}</span>}
        </div>
      )}
    </div>
  );
};

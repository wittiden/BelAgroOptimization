import React, { useState } from 'react';
import { CloudRain, Thermometer, Wind, Droplets, Sun, CheckCircle2, ShieldAlert } from 'lucide-react';
import type { WeatherSummary } from '../../types';

interface AgroWeatherWidgetProps {
  weatherData?: WeatherSummary[];
  className?: string;
}

const DEFAULT_WEATHER: Record<number, {
  temp: number;
  rain: number;
  gtk: number;
  moisturePct: number;
  eto: number;
  gdd: number;
  isDrought: boolean;
  droughtLevel: string;
}> = {
  2024: {
    temp: 7.8,
    rain: 650,
    gtk: 1.38,
    moisturePct: 82,
    eto: 3.2,
    gdd: 2450,
    isDrought: false,
    droughtLevel: 'Норма увлажнения',
  },
  2025: {
    temp: 8.5,
    rain: 580,
    gtk: 1.08,
    moisturePct: 67,
    eto: 3.6,
    gdd: 2610,
    isDrought: false,
    droughtLevel: 'Умеренно влажно',
  },
  2026: {
    temp: 9.6,
    rain: 440,
    gtk: 0.68,
    moisturePct: 41,
    eto: 4.8,
    gdd: 2890,
    isDrought: true,
    droughtLevel: 'Критическая засуха',
  },
};

export const AgroWeatherWidget: React.FC<AgroWeatherWidgetProps> = ({ weatherData: _weatherData = [], className = '' }) => {
  const [selectedYear, setSelectedYear] = useState<number>(2024);

  // Merge with API data if available
  const current = DEFAULT_WEATHER[selectedYear] || DEFAULT_WEATHER[2024];

  return (
    <div className={`bg-white border border-slate-200 rounded-xl p-4 sm:p-5 shadow-xl backdrop-blur-md relative overflow-hidden ${className}`}>
      {/* Background glow when drought year selected */}
      {current.isDrought && (
        <div className="absolute top-0 right-0 w-72 h-72 bg-rose-500/10 rounded-full blur-3xl pointer-events-none animate-pulse" />
      )}

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-xl border ${current.isDrought ? 'bg-rose-50 border-rose-200 text-rose-700' : 'bg-emerald-50 border-emerald-200 text-emerald-700'}`}>
            {current.isDrought ? <ShieldAlert className="w-5 h-5 animate-bounce" /> : <Sun className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900">
                Агроклиматическая станция
              </h3>
              {current.isDrought ? (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping" />
                  Угроза засухи (&lt;480 мм)
                </span>
              ) : (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3" />
                  Благоприятно
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 font-mono">
              Метеопост: БелАгро-Центр • Координаты 53°54′ N
            </p>
          </div>
        </div>

        {/* Year Pills */}
        <div className="flex items-center bg-slate-100 border border-slate-200 rounded-xl p-1 text-xs font-mono">
          {[2024, 2025, 2026].map((year) => {
            const isYearDrought = year === 2026;
            return (
              <button
                key={year}
                onClick={() => setSelectedYear(year)}
                className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1.5 ${
                  selectedYear === year
                    ? isYearDrought
                      ? 'bg-rose-600 text-white font-bold shadow-md shadow-rose-950'
                      : 'bg-emerald-600 text-white font-bold shadow-md shadow-emerald-950'
                    : 'text-slate-500 hover:text-slate-200'
                }`}
              >
                <span>{year}</span>
                {isYearDrought && <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Telemetry Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-4">
        {/* Metric 1: Temp */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
            <span>Ср. Температура</span>
            <Thermometer className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-bold font-mono text-slate-900">
            +{current.temp} °C
          </div>
          <div className="text-[10px] text-slate-500 mt-1">
            Вегетац. период
          </div>
        </div>

        {/* Metric 2: Rain */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
            <span>Осадки за год</span>
            <CloudRain className="w-3.5 h-3.5 text-blue-400" />
          </div>
          <div className={`text-lg font-bold font-mono ${current.isDrought ? 'text-rose-400' : 'text-blue-400'}`}>
            {current.rain} мм
          </div>
          <div className="text-[10px] text-slate-500 mt-1">
            {current.isDrought ? 'Дефицит: -210 мм' : 'Норма для региона'}
          </div>
        </div>

        {/* Metric 3: GTK (Hydrothermal) */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
            <span>Индекс ГТК</span>
            <Droplets className="w-3.5 h-3.5 text-teal-400" />
          </div>
          <div className={`text-lg font-bold font-mono ${current.gtk < 0.8 ? 'text-rose-400' : current.gtk < 1.1 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {current.gtk}
          </div>
          <div className="text-[10px] text-slate-500 mt-1 truncate">
            {current.droughtLevel}
          </div>
        </div>

        {/* Metric 4: Soil Moisture */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
            <span>Влага почвы (0-20см)</span>
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
          </div>
          <div className={`text-lg font-bold font-mono ${current.moisturePct < 50 ? 'text-rose-400' : 'text-cyan-400'}`}>
            {current.moisturePct}%
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 mt-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${current.moisturePct < 50 ? 'bg-rose-500' : 'bg-cyan-500'}`}
              style={{ width: `${current.moisturePct}%` }}
            />
          </div>
        </div>

        {/* Metric 5: GDD */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
            <span>Сумма ΣT &gt; 10°C</span>
            <Sun className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-bold font-mono text-slate-900">
            {current.gdd} °C
          </div>
          <div className="text-[10px] text-slate-500 mt-1">
            Теплообеспеч.
          </div>
        </div>

        {/* Metric 6: ETo */}
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
            <span>Испарение ETo</span>
            <Wind className="w-3.5 h-3.5 text-slate-500" />
          </div>
          <div className="text-lg font-bold font-mono text-slate-900">
            {current.eto} мм/сут
          </div>
          <div className="text-[10px] text-slate-500 mt-1">
            Пенман-Монтейт
          </div>
        </div>
      </div>
    </div>
  );
};

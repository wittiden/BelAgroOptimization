import React, { useState } from 'react';
import { Layers, Eye, MapPin } from 'lucide-react';
import type { FieldData, CropAllocation } from '../../types';

export type MapLayer = 'crops' | 'fertility' | 'npk' | 'soil';

interface CadastralMapProps {
  fields: FieldData[];
  allocations?: CropAllocation[];
  selectedFieldId?: string | null;
  onSelectField?: (fieldCode: string) => void;
  initialLayer?: MapLayer;
  initialYear?: number;
  compact?: boolean;
}

// Visual definition for each field polygon in our 800x480 SVG coordinate system
interface FieldGeometry {
  code: string;
  name: string;
  path: string;
  center: { x: number; y: number };
}

const FIELD_GEOMETRIES: Record<string, FieldGeometry> = {
  field1: {
    code: 'field1',
    name: 'Участок №1 «Северный»',
    path: 'M 60,60 L 320,50 L 300,210 L 80,200 Z',
    center: { x: 190, y: 125 },
  },
  field2: {
    code: 'field2',
    name: 'Участок №2 «Восточный массив»',
    path: 'M 345,50 L 730,70 L 710,230 L 330,220 Z',
    center: { x: 530, y: 140 },
  },
  field3: {
    code: 'field3',
    name: 'Участок №3 «Приречный»',
    path: 'M 60,250 L 260,240 L 240,430 L 80,440 L 50,340 Z',
    center: { x: 150, y: 340 },
  },
  field4: {
    code: 'field4',
    name: 'Участок №4 «Центральный (Чернозём)»',
    path: 'M 285,250 L 490,260 L 470,430 L 265,420 Z',
    center: { x: 380, y: 340 },
  },
  field5: {
    code: 'field5',
    name: 'Участок №5 «Южная равнина»',
    path: 'M 515,260 L 740,250 L 730,440 L 495,435 Z',
    center: { x: 620, y: 345 },
  },
};

const CROP_COLOR_MAP: Record<string, { fill: string; stroke: string; label: string }> = {
  winter_wheat: { fill: '#059669', stroke: '#34d399', label: 'Озимая пшеница' },
  spring_wheat: { fill: '#0d9488', stroke: '#2dd4bf', label: 'Яровая пшеница' },
  barley: { fill: '#d97706', stroke: '#fbbf24', label: 'Ячмень' },
  rapeseed: { fill: '#eab308', stroke: '#fef08a', label: 'Озимый рапс' },
  potato: { fill: '#ea580c', stroke: '#fb923c', label: 'Картофель' },
  sugar_beet: { fill: '#db2777', stroke: '#f472b6', label: 'Сахарная свёкла' },
  corn_silage: { fill: '#65a30d', stroke: '#a3e635', label: 'Кукуруза на силос' },
  grass: { fill: '#16a34a', stroke: '#4ade80', label: 'Многолетние травы' },
  fallow: { fill: '#475569', stroke: '#94a3b8', label: 'Чистый пар' },
};

export const CadastralMap: React.FC<CadastralMapProps> = ({
  fields,
  allocations = [],
  selectedFieldId,
  onSelectField,
  initialLayer = 'crops',
  initialYear = 2024,
  compact = false,
}) => {
  const [activeLayer, setActiveLayer] = useState<MapLayer>(initialLayer);
  const [activeYear, setActiveYear] = useState<number>(initialYear);
  const [hoveredField, setHoveredField] = useState<string | null>(null);

  // Helper to find crop allocation for a given field & year
  const getAlloc = (fieldCode: string, year: number) => {
    return allocations.find((a) => a.field_code.toLowerCase() === fieldCode.toLowerCase() && a.year === year);
  };

  // Helper to get fill and stroke based on active layer
  const getFieldAppearance = (fieldCode: string) => {
    const field = fields.find((f) => f.code.toLowerCase() === fieldCode.toLowerCase());
    const alloc = getAlloc(fieldCode, activeYear);

    if (activeLayer === 'crops') {
      if (alloc && CROP_COLOR_MAP[alloc.crop_code]) {
        return CROP_COLOR_MAP[alloc.crop_code];
      }
      return { fill: '#1e293b', stroke: '#334155', label: 'Не засеяно' };
    }

    if (activeLayer === 'fertility') {
      const fertility = field?.soil_fertility ?? 1.0;
      if (fertility >= 1.15) {
        return { fill: '#047857', stroke: '#10b981', label: `Высокое (${fertility})` };
      }
      if (fertility >= 1.0) {
        return { fill: '#0f766e', stroke: '#14b8a6', label: `Среднее (${fertility})` };
      }
      return { fill: '#b45309', stroke: '#f59e0b', label: `Пониженное (${fertility})` };
    }

    if (activeLayer === 'npk') {
      const fertKg = alloc?.fert_kg ?? 120;
      if (fertKg > 150) {
        return { fill: '#7c3aed', stroke: '#a78bfa', label: `${fertKg} кг/га (Интенсивно)` };
      }
      if (fertKg >= 100) {
        return { fill: '#4338ca', stroke: '#818cf8', label: `${fertKg} кг/га (Оптимум)` };
      }
      return { fill: '#1e3a8a', stroke: '#60a5fa', label: `${fertKg} кг/га (Базовый)` };
    }

    if (activeLayer === 'soil') {
      const soil = field?.soil_type || 'суглинок';
      if (soil === 'чернозём') {
        return { fill: '#14532d', stroke: '#22c55e', label: 'Чернозём' };
      }
      if (soil === 'суглинок') {
        return { fill: '#1e3a8a', stroke: '#3b82f6', label: 'Суглинок' };
      }
      return { fill: '#78350f', stroke: '#d97706', label: 'Супесь' };
    }

    return { fill: '#1e293b', stroke: '#475569', label: 'Поле' };
  };

  const hoveredFieldData = hoveredField
    ? fields.find((f) => f.code.toLowerCase() === hoveredField.toLowerCase())
    : null;
  const hoveredAlloc = hoveredField ? getAlloc(hoveredField, activeYear) : null;

  return (
    <div className="relative bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
      {/* Top Map Toolbar */}
      <div className="flex flex-wrap items-center justify-between p-3.5 sm:p-4 bg-slate-50 border-b border-slate-200 gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
                Кадастровая карта угодий
              </span>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-50 border border-emerald-200 text-emerald-800 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                900 га
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono hidden sm:block">
              GIS: 53°54′12″N 27°34′30″E • Минская возвышенность
            </p>
          </div>
        </div>

        {/* Controls: Layers & Years */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Layer Switcher */}
          <div className="flex items-center bg-slate-100 border border-slate-200 rounded-lg p-0.5 text-xs font-medium">
            <button
              onClick={() => setActiveLayer('crops')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                activeLayer === 'crops'
                  ? 'bg-emerald-600 text-white font-semibold shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Севооборот
            </button>
            <button
              onClick={() => setActiveLayer('fertility')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                activeLayer === 'fertility'
                  ? 'bg-emerald-600 text-white font-semibold shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Плодородие
            </button>
            <button
              onClick={() => setActiveLayer('npk')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                activeLayer === 'npk'
                  ? 'bg-emerald-600 text-white font-semibold shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              NPK удобрения
            </button>
            <button
              onClick={() => setActiveLayer('soil')}
              className={`px-2.5 py-1 rounded-md transition-all ${
                activeLayer === 'soil'
                  ? 'bg-emerald-600 text-white font-semibold shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Тип почвы
            </button>
          </div>

          {/* Year selector (only visible for crops/npk layer) */}
          {(activeLayer === 'crops' || activeLayer === 'npk') && (
            <div className="flex items-center bg-slate-100 border border-slate-200 rounded-lg p-0.5 text-xs font-mono">
              {[2024, 2025, 2026].map((year) => (
                <button
                  key={year}
                  onClick={() => setActiveYear(year)}
                  className={`px-2 py-1 rounded-md transition-all ${
                    activeYear === year
                      ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/30'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {year}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* SVG Canvas */}
      <div className={`relative w-full ${compact ? 'h-64 sm:h-72' : 'h-80 sm:h-96 md:h-[400px]'} bg-[#f1f5f2] border border-slate-200 rounded-xl flex items-center justify-center select-none overflow-hidden`}>
        {/* Subtle grid pattern background */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(15, 23, 42, 0.12) 1px, transparent 0)`,
            backgroundSize: '24px 24px',
          }}
        />

        <svg
          viewBox="0 0 800 480"
          className="w-full h-full object-contain filter drop-shadow-md"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Filter for glowing selected parcel */}
            <filter id="neon-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="5" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
            {/* Soil texture patterns */}
            <pattern id="diagonalHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
            </pattern>
          </defs>

          {/* Background Landscape Elements */}
          {/* Drainage canal */}
          <path
            d="M 30,225 Q 280,235 480,245 T 780,240"
            fill="none"
            stroke="#0284c7"
            strokeWidth="5"
            strokeOpacity="0.4"
            strokeDasharray="8,4"
          />
          <text x="690" y="235" fill="#38bdf8" fontSize="9" opacity="0.6" fontFamily="monospace">
            Мелиоративный канал
          </text>

          {/* Farm Service Roadways */}
          <path
            d="M 40,50 L 760,50 M 325,40 L 325,450 M 500,40 L 500,450 M 40,445 L 760,445"
            fill="none"
            stroke="#475569"
            strokeWidth="3"
            strokeOpacity="0.3"
            strokeDasharray="4,6"
          />

          {/* Central Farm Complex / Elevator Hub */}
          <g transform="translate(400, 240)">
            <circle r="14" fill="#ffffff" stroke="#059669" strokeWidth="2" />
            <circle r="20" fill="none" stroke="#059669" strokeWidth="1" strokeDasharray="3,3" className="animate-spin" style={{ animationDuration: '20s' }} />
            <text x="0" y="4" textAnchor="middle" fill="#059669" fontSize="10" fontWeight="bold">
              HQ
            </text>
            <text x="0" y="24" textAnchor="middle" fill="#475569" fontSize="8" fontWeight="bold">
              Агрогородок / МТФ
            </text>
          </g>

          {/* FIELD PARCELS */}
          {Object.entries(FIELD_GEOMETRIES).map(([fieldCode, geo]) => {
            const field = fields.find((f) => f.code.toLowerCase() === fieldCode.toLowerCase());
            const isHovered = hoveredField === fieldCode;
            const isSelected = selectedFieldId?.toLowerCase() === fieldCode.toLowerCase();
            const alloc = getAlloc(fieldCode, activeYear);
            const appearance = getFieldAppearance(fieldCode);

            return (
              <g
                key={fieldCode}
                className="cursor-pointer transition-all duration-200"
                onMouseEnter={() => setHoveredField(fieldCode)}
                onMouseLeave={() => setHoveredField(null)}
                onClick={() => onSelectField?.(fieldCode)}
              >
                {/* Field Polygon */}
                <path
                  d={geo.path}
                  fill={appearance.fill}
                  fillOpacity={isHovered ? 0.95 : isSelected ? 0.9 : 0.75}
                  stroke={isSelected ? '#10b981' : isHovered ? '#f8fafc' : appearance.stroke}
                  strokeWidth={isSelected ? 4 : isHovered ? 3 : 1.5}
                  strokeDasharray={isSelected ? '6,3' : 'none'}
                  filter={isSelected ? 'url(#neon-glow)' : undefined}
                />

                {/* Subtle pattern overlay */}
                <path d={geo.path} fill="url(#diagonalHatch)" pointerEvents="none" />

                {/* Field Label Badge */}
                <g transform={`translate(${geo.center.x}, ${geo.center.y})`} pointerEvents="none">
                  {/* Field Code */}
                  <text
                    x="0"
                    y="-8"
                    textAnchor="middle"
                    fill="#0f172a"
                    fontSize="13"
                    fontWeight="800"
                    letterSpacing="0.05em"
                    className="drop-shadow-md font-mono"
                  >
                    {fieldCode.toUpperCase()}
                  </text>

                  {/* Area */}
                  <text
                    x="0"
                    y="7"
                    textAnchor="middle"
                    fill="#334155"
                    fontSize="10"
                    fontWeight="600"
                  >
                    {field?.area_ha || 0} га
                  </text>

                  {/* Dynamic Layer Info */}
                  <rect
                    x="-55"
                    y="14"
                    width="110"
                    height="18"
                    rx="9"
                    fill="rgba(15, 23, 42, 0.85)"
                    stroke={appearance.stroke}
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="26"
                    textAnchor="middle"
                    fill={appearance.stroke}
                    fontSize="9"
                    fontWeight="700"
                  >
                    {activeLayer === 'crops'
                      ? appearance.label
                      : activeLayer === 'fertility'
                      ? `Бонитет: ${field?.soil_fertility ?? 1.0}`
                      : activeLayer === 'npk'
                      ? `${alloc?.fert_kg ?? 120} кг NPK`
                      : field?.soil_type || 'суглинок'}
                  </text>
                </g>
              </g>
            );
          })}

          {/* Compass Rose */}
          <g transform="translate(740, 430)" opacity="0.6">
            <circle r="16" fill="#0f172a" stroke="#475569" strokeWidth="1" />
            <path d="M 0,-14 L 4,0 L 0,14 L -4,0 Z" fill="#334155" />
            <path d="M 0,-14 L 4,0 L 0,0 Z" fill="#ef4444" />
            <text x="0" y="-17" textAnchor="middle" fill="#ef4444" fontSize="8" fontWeight="bold">
              N
            </text>
          </g>

          {/* Scale Bar */}
          <g transform="translate(60, 450)" opacity="0.7">
            <line x1="0" y1="0" x2="60" y2="0" stroke="#94a3b8" strokeWidth="2" />
            <line x1="0" y1="-3" x2="0" y2="3" stroke="#94a3b8" strokeWidth="2" />
            <line x1="60" y1="-3" x2="60" y2="3" stroke="#94a3b8" strokeWidth="2" />
            <text x="30" y="-5" textAnchor="middle" fill="#475569" fontSize="8" fontFamily="monospace">
              500 м
            </text>
          </g>
        </svg>

        {/* Hover Inspection Popup (Overlay) */}
        {hoveredFieldData && (
          <div className="absolute top-3 left-3 pointer-events-none bg-slate-900/95 border border-emerald-500/40 rounded-xl p-3 shadow-2xl backdrop-blur-md max-w-xs text-xs space-y-1.5 animate-in fade-in zoom-in-95 duration-100 z-10">
            <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1.5">
              <span className="font-bold text-slate-900 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                {FIELD_GEOMETRIES[hoveredFieldData.code]?.name || hoveredFieldData.code.toUpperCase()}
              </span>
              <span className="font-mono text-emerald-400 font-bold">
                {hoveredFieldData.area_ha} га
              </span>
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px]">
              <span className="text-slate-500">Тип почвы:</span>
              <span className="font-medium text-slate-800 capitalize">{hoveredFieldData.soil_type || 'суглинок'}</span>
              <span className="text-slate-500">Бонитет:</span>
              <span className="font-medium text-slate-800 font-mono">×{hoveredFieldData.soil_fertility}</span>
              {hoveredAlloc && (
                <>
                  <span className="text-slate-500">Культура ({activeYear}):</span>
                  <span className="font-semibold text-amber-300">
                    {CROP_COLOR_MAP[hoveredAlloc.crop_code]?.label || hoveredAlloc.crop_code}
                  </span>
                  <span className="text-slate-500">Сбор:</span>
                  <span className="font-medium text-slate-800 font-mono">
                    {hoveredAlloc.yield_ts ? `${hoveredAlloc.yield_ts.toLocaleString()} ц` : '—'}
                  </span>
                  <span className="text-slate-500">Внесение NPK:</span>
                  <span className="font-medium text-emerald-400 font-mono">
                    {hoveredAlloc.fert_kg} кг/га
                  </span>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Map Legend Footer */}
      <div className="p-3 bg-slate-900/90 border-t border-slate-800/60 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1">
            <Eye className="w-3.5 h-3.5 text-emerald-400" />
            Легенда:
          </span>
          {activeLayer === 'crops' && (
            <div className="flex items-center gap-2 flex-wrap text-[11px]">
              {Object.entries(CROP_COLOR_MAP).slice(0, 6).map(([key, style]) => (
                <div key={key} className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: style.fill }} />
                  <span className="text-slate-700">{style.label}</span>
                </div>
              ))}
            </div>
          )}
          {activeLayer === 'fertility' && (
            <div className="flex items-center gap-3 text-[11px]">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-600" />
                <span className="text-slate-700">&gt; 1.15 (Чернозём)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-teal-600" />
                <span className="text-slate-700">1.00 (Суглинок)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-600" />
                <span className="text-slate-700">&lt; 0.95 (Супесь)</span>
              </div>
            </div>
          )}
          {activeLayer === 'npk' && (
            <div className="flex items-center gap-3 text-[11px]">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-purple-600" />
                <span className="text-slate-700">&gt;150 кг/га</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-indigo-600" />
                <span className="text-slate-700">100–150 кг/га</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-blue-700" />
                <span className="text-slate-700">&lt;100 кг/га</span>
              </div>
            </div>
          )}
          {activeLayer === 'soil' && (
            <div className="flex items-center gap-3 text-[11px]">
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-green-800" />
                <span className="text-slate-700">Чернозём</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-blue-800" />
                <span className="text-slate-700">Суглинок</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-800" />
                <span className="text-slate-700">Супесь</span>
              </div>
            </div>
          )}
        </div>

        <div className="text-[11px] text-slate-500 font-mono hidden md:block">
          Нажмите на участок для детального инспектирования
        </div>
      </div>
    </div>
  );
};

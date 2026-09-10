import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Sprout, Info } from 'lucide-react';
import { Card } from '../common/Card';

interface CropProfile {
  name: string;
  code: string;
  baseYield: number;
  maxYield: number;
  costPerKgNpk: number;
  cropPricePerTs: number;
  soils: {
    name: string;
    color: string;
    b0: number;
    b1: number;
    b2: number;
    optimalKg: number;
  }[];
}

const CROP_PROFILES: Record<string, CropProfile> = {
  winter_wheat: {
    name: 'Озимая пшеница',
    code: 'winter_wheat',
    baseYield: 48,
    maxYield: 70,
    costPerKgNpk: 2.7,
    cropPricePerTs: 46.0,
    soils: [
      { name: 'Чернозём типичный', color: '#10b981', b0: 38, b1: 0.26, b2: 0.00062, optimalKg: 175 },
      { name: 'Дерново-подзолистый суглинок', color: '#38bdf8', b0: 27, b1: 0.22, b2: 0.00058, optimalKg: 155 },
      { name: 'Супесь связная', color: '#f59e0b', b0: 19, b1: 0.17, b2: 0.00052, optimalKg: 130 },
    ],
  },
  barley: {
    name: 'Ячмень фуражный',
    code: 'barley',
    baseYield: 40,
    maxYield: 60,
    costPerKgNpk: 2.7,
    cropPricePerTs: 40.0,
    soils: [
      { name: 'Чернозём типичный', color: '#10b981', b0: 32, b1: 0.23, b2: 0.00060, optimalKg: 160 },
      { name: 'Дерново-подзолистый суглинок', color: '#38bdf8', b0: 24, b1: 0.20, b2: 0.00056, optimalKg: 145 },
      { name: 'Супесь связная', color: '#f59e0b', b0: 17, b1: 0.15, b2: 0.00050, optimalKg: 120 },
    ],
  },
  rapeseed: {
    name: 'Рапс масличный',
    code: 'rapeseed',
    baseYield: 28,
    maxYield: 42,
    costPerKgNpk: 2.7,
    cropPricePerTs: 98.0,
    soils: [
      { name: 'Чернозём типичный', color: '#10b981', b0: 22, b1: 0.16, b2: 0.00042, optimalKg: 165 },
      { name: 'Дерново-подзолистый суглинок', color: '#38bdf8', b0: 16, b1: 0.14, b2: 0.00040, optimalKg: 150 },
      { name: 'Супесь связная', color: '#f59e0b', b0: 11, b1: 0.11, b2: 0.00038, optimalKg: 125 },
    ],
  },
  corn_silage: {
    name: 'Кукуруза на силос',
    code: 'corn_silage',
    baseYield: 360,
    maxYield: 520,
    costPerKgNpk: 2.7,
    cropPricePerTs: 8.5,
    soils: [
      { name: 'Чернозём типичный', color: '#10b981', b0: 280, b1: 1.85, b2: 0.0042, optimalKg: 200 },
      { name: 'Дерново-подзолистый суглинок', color: '#38bdf8', b0: 220, b1: 1.60, b2: 0.0040, optimalKg: 180 },
      { name: 'Супесь связная', color: '#f59e0b', b0: 160, b1: 1.25, b2: 0.0036, optimalKg: 150 },
    ],
  },
};

const DOSES = [0, 30, 60, 90, 120, 150, 180, 210, 240];

export const NPKResponseChart: React.FC = () => {
  const [selectedCrop, setSelectedCrop] = useState<string>('winter_wheat');
  const crop = CROP_PROFILES[selectedCrop] || CROP_PROFILES.winter_wheat;

  const series = crop.soils.map((s) => {
    const data = DOSES.map((x) => {
      const y = s.b0 + s.b1 * x - s.b2 * Math.pow(x, 2);
      return Number(Math.max(0, y).toFixed(1));
    });

    return {
      name: s.name,
      type: 'line',
      smooth: true,
      data,
      lineStyle: { width: 3, color: s.color },
      itemStyle: { color: s.color },
      markPoint: {
        symbol: 'pin',
        symbolSize: 42,
        data: [
          {
            name: 'Агрономический оптимум',
            coord: [
              s.optimalKg.toString(),
              Number((s.b0 + s.b1 * s.optimalKg - s.b2 * Math.pow(s.optimalKg, 2)).toFixed(1)),
            ],
            value: `${s.optimalKg} кг`,
          },
        ],
      },
    };
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#ffffff',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#0f172a', fontSize: 12 }, extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
      formatter: (params: any) => {
        const dose = params[0].axisValue;
        let str = `<div class="font-semibold text-emerald-700 mb-1">Доза NPK: ${dose} кг д.в./га</div>`;
        params.forEach((p: any) => {
          str += `<div style="display:flex; justify-content:space-between; gap:16px; margin-top:2px;">
            <span style="color:#64748b">${p.marker} ${p.seriesName}:</span>
            <span style="font-weight:600; color:#0f172a">${p.value} ц/га</span>
          </div>`;
        });
        return str;
      },
    },
    legend: {
      data: crop.soils.map((s) => s.name),
      textStyle: { color: '#475569', fontSize: 11 },
      top: 0,
      icon: 'roundRect',
    },
    grid: { left: '3%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      name: 'Доза NPK (кг д.в./га)',
      nameLocation: 'middle',
      nameGap: 28,
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      data: DOSES.map(String),
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: '#f1f5f9' } },
    },
    yAxis: {
      type: 'value',
      name: 'Урожайность (ц/га)',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    series,
  };

  return (
    <Card className="border-slate-200 bg-white p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700">
              <Sprout className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-900 text-base">
              Кривая агрономического отклика урожайности на дозы NPK
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Модель Митчерлиха-Бауле с эффектом убывающей отдачи по гранулометрическим типам почв РБ
          </p>
        </div>

        {/* Crop Selector */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200 rounded-lg self-start sm:self-auto overflow-x-auto">
          {Object.values(CROP_PROFILES).map((cp) => (
            <button
              key={cp.code}
              onClick={() => setSelectedCrop(cp.code)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
                selectedCrop === cp.code
                  ? 'bg-emerald-700 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white'
              }`}
            >
              {cp.name}
            </button>
          ))}
        </div>
      </div>

      <div className="h-72 w-full">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} notMerge={true} />
      </div>

      {/* Soil metrics cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 pt-3 border-t border-slate-100">
        {crop.soils.map((s) => (
          <div
            key={s.name}
            className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium text-slate-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
                {s.name}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 text-slate-700 font-mono">
                Оптимум: {s.optimalKg} кг/га
              </span>
            </div>
            <div className="mt-2 text-slate-500 text-[11px] leading-relaxed">
              Предельная окупаемость: 1 кг NPK даёт{' '}
              <span className="text-emerald-400 font-medium">
                {((s.b1 - 2 * s.b2 * 120) * 100).toFixed(0)} кг зерна
              </span>{' '}
              при дозе 120 кг/га.
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex items-center gap-2 text-[11px] text-slate-500 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/40">
        <Info className="w-4 h-4 text-emerald-400 shrink-0" />
        <span>
          При превышении точки перегиба (&gt;180 кг/га) маржинальные затраты на удобрения превышают стоимость
          дополнительного прироста зерна (закон убывающего плодородия Либиха-Митчерлиха).
        </span>
      </div>
    </Card>
  );
};

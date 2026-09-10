import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Layers, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Card } from '../common/Card';
import type { OptimizationResult } from '../../types';

interface FeedBalanceChartProps {
  results: OptimizationResult | null;
}

const FEED_NAMES: Record<string, string> = {
  silage: 'Силос кукурузный',
  hay: 'Сено злаково-бобовое',
  concentrate: 'Концентраты (комбикорм)',
  pasture: 'Пастбищный зелёный корм',
};

export const FeedBalanceChart: React.FC<FeedBalanceChartProps> = ({ results }) => {
  const [selectedYearIndex, setSelectedYearIndex] = useState<number>(0);

  if (!results || !results.years || results.years.length === 0) {
    return null;
  }

  const currentYear = results.years[selectedYearIndex] || results.years[0];
  const feedBalances = currentYear.feed_balances || {};
  const feedKeys = Object.keys(feedBalances);

  const categories = feedKeys.map((k) => FEED_NAMES[k] || k);
  const producedData = feedKeys.map((k) => feedBalances[k].produced);
  const neededData = feedKeys.map((k) => feedBalances[k].needed);
  const purchasedData = feedKeys.map((k) => feedBalances[k].purchased);

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#ffffff',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#0f172a', fontSize: 12 }, extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
      formatter: (params: any) => {
        let str = `<div class="font-semibold text-slate-800 mb-1">${params[0].axisValue}</div>`;
        params.forEach((p: any) => {
          str += `<div style="display:flex; justify-content:space-between; gap:16px; margin-top:2px;">
            <span style="color:#94a3b8">${p.marker} ${p.seriesName}:</span>
            <span style="font-weight:600; color:#f8fafc">${p.value.toLocaleString('ru-RU')} ц</span>
          </div>`;
        });
        return str;
      },
    },
    legend: {
      data: ['Произведено в хозяйстве', 'Потребно стаду', 'Закуплено со стороны'],
      textStyle: { color: '#64748b', fontSize: 11 },
      top: 0,
    },
    grid: { left: '3%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#cbd5e1', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: 'Центнеры (ц)',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    series: [
      {
        name: 'Произведено в хозяйстве',
        type: 'bar',
        data: producedData,
        itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] },
      },
      {
        name: 'Потребно стаду',
        type: 'bar',
        data: neededData,
        itemStyle: { color: '#38bdf8', borderRadius: [4, 4, 0, 0] },
      },
      {
        name: 'Закуплено со стороны',
        type: 'bar',
        data: purchasedData,
        itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] },
      },
    ],
  };

  return (
    <Card className="border-slate-200 bg-white p-5 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700">
              <Layers className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-900 text-base">
              Баланс кормопроизводства и самообеспеченности стада
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Соотношение собственной кормовой базы и коммерческих закупок кормов
          </p>
        </div>

        {/* Year Selector */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 border border-slate-200 rounded-lg">
          {results.years.map((y, idx) => (
            <button
              key={y.year}
              onClick={() => setSelectedYearIndex(idx)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                selectedYearIndex === idx
                  ? 'bg-emerald-700 text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-800/60'
              }`}
            >
              {y.year} год
            </button>
          ))}
        </div>
      </div>

      <div className="h-72 w-full">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} notMerge={true} />
      </div>

      {/* Breakdown indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 mt-4 pt-3 border-t border-slate-100">
        {feedKeys.map((k) => {
          const item = feedBalances[k];
          const sufficiency = item.needed > 0 ? (item.produced / item.needed) * 100 : 100;
          const isFullySupplied = sufficiency >= 100;

          return (
            <div
              key={k}
              className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-800 truncate">{FEED_NAMES[k] || k}</span>
                {isFullySupplied ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5 text-amber-700 shrink-0" />
                )}
              </div>

              <div className="mt-2 space-y-1">
                <div className="flex justify-between text-slate-500 text-[11px]">
                  <span>Обеспеченность:</span>
                  <span className={`font-mono font-semibold ${isFullySupplied ? 'text-emerald-700' : 'text-amber-700'}`}>
                    {sufficiency.toFixed(0)}%
                  </span>
                </div>
                {item.purchased > 0 && (
                  <div className="flex justify-between text-slate-500 text-[11px]">
                    <span>Закупка:</span>
                    <span className="font-mono text-amber-700 font-semibold">{item.purchased} ц</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

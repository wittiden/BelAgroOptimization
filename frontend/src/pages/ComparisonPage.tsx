import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { GitCompare, Scale } from 'lucide-react';
import { Card } from '../components/common/Card';
import { useScenario } from '../context/ScenarioContext';

export const ComparisonPage: React.FC = () => {
  const { scenarios } = useScenario();

  const [scenarioA, setScenarioA] = useState<string>(scenarios[0]?.scenario_id || '');
  const [scenarioB, setScenarioB] = useState<string>(scenarios[1]?.scenario_id || scenarios[0]?.scenario_id || '');

  const scA = scenarios.find((s) => s.scenario_id === scenarioA) || scenarios[0];
  const scB = scenarios.find((s) => s.scenario_id === scenarioB) || scenarios[0];

  const profitA = scA?.last_profit || 2854300;
  const profitB = scB?.last_profit || 2510000;
  const profitDelta = profitA - profitB;
  const profitDeltaPct = profitB ? ((profitDelta / profitB) * 100).toFixed(1) : '0';

  // Radar Spider Chart Option (Multicriteria Tradeoff)
  const getRadarChartOption = () => {
    return {
      backgroundColor: 'transparent',
      tooltip: {
        backgroundColor: '#ffffff',
        borderColor: '#e2e8f0',
        textStyle: { color: '#0f172a' }, extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
      },
      legend: {
        data: [scA?.name || 'Сценарий A', scB?.name || 'Сценарий B'],
        textStyle: { color: '#475569' },
        bottom: 0,
      },
      radar: {
        indicator: [
          { name: 'Рентабельность (ROI)', max: 100 },
          { name: 'Устойчивость к засухе', max: 100 },
          { name: 'Сохранение плодородия', max: 100 },
          { name: 'Кормовая автономность', max: 100 },
          { name: 'Диверсификация культур', max: 100 },
        ],
        shape: 'polygon',
        splitNumber: 4,
        axisName: {
          color: '#cbd5e1',
          fontSize: 11,
          fontWeight: 600,
        },
        splitLine: {
          lineStyle: {
            color: ['#1e293b', '#334155', '#475569', '#64748b'].reverse(),
          },
        },
        splitArea: {
          show: true,
          areaStyle: {
            color: ['rgba(15, 23, 42, 0.4)', 'rgba(30, 41, 59, 0.4)'],
          },
        },
        axisLine: {
          lineStyle: { color: '#334155' },
        },
      },
      series: [
        {
          name: 'Сравнение профилей устойчивости',
          type: 'radar',
          data: [
            {
              value: [88, 75, 92, 85, 80],
              name: scA?.name || 'Сценарий A',
              symbol: 'circle',
              symbolSize: 4,
              lineStyle: { width: 2, color: '#10b981' },
              areaStyle: { color: 'rgba(16, 185, 129, 0.25)' },
              itemStyle: { color: '#10b981' },
            },
            {
              value: [72, 88, 78, 90, 70],
              name: scB?.name || 'Сценарий B',
              symbol: 'rect',
              symbolSize: 4,
              lineStyle: { width: 2, color: '#3b82f6' },
              areaStyle: { color: 'rgba(59, 130, 246, 0.25)' },
              itemStyle: { color: '#3b82f6' },
            },
          ],
        },
      ],
    };
  };

  // Financial Bar Chart
  const getComparisonChartOption = () => {
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#ffffff',
        borderColor: '#e2e8f0',
        textStyle: { color: '#0f172a' }, extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
      },
      legend: {
        data: [scA?.name || 'Сценарий A', scB?.name || 'Сценарий B'],
        textStyle: { color: '#475569' },
        top: 0,
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: ['Общая прибыль (тыс. BYN)', 'Растениеводство (тыс. BYN)', 'Животноводство (тыс. BYN)', 'Расход NPK (т)'],
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisLabel: { color: '#64748b', fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
        axisLabel: { color: '#64748b' },
      },
      series: [
        {
          name: scA?.name || 'Сценарий A',
          type: 'bar',
          data: [2854, 1547, 1307, 135],
          itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] },
        },
        {
          name: scB?.name || 'Сценарий B',
          type: 'bar',
          data: [2510, 1320, 1190, 120],
          itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] },
        },
      ],
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <GitCompare className="w-6 h-6 text-emerald-700" />
            <span>Сравнительный What-if анализ сценариев</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Многокритериальное сопоставление производственных стратегий бок о бок по маржинальности, климатическим рискам и ресурсоемкости
          </p>
        </div>
      </div>

      {/* Selectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="bg-white/80 border border-emerald-500/30 rounded-2xl p-4 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Сценарий А (Базовый)
            </label>
            <span className="text-[11px] font-mono text-emerald-700 font-bold">
              {profitA.toLocaleString()} BYN
            </span>
          </div>
          <select
            value={scenarioA}
            onChange={(e) => setScenarioA(e.target.value)}
            className="w-full bg-slate-50/80 border border-slate-200 rounded-xl p-2.5 text-sm text-slate-900 outline-none focus:border-emerald-500 font-medium"
          >
            {scenarios.map((s) => (
              <option key={s.scenario_id} value={s.scenario_id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="bg-white/80 border border-blue-500/30 rounded-2xl p-4 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs font-bold text-sky-700 uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-400" />
              Сценарий Б (Сравниваемый)
            </label>
            <span className="text-[11px] font-mono text-sky-700 font-bold">
              {profitB.toLocaleString()} BYN
            </span>
          </div>
          <select
            value={scenarioB}
            onChange={(e) => setScenarioB(e.target.value)}
            className="w-full bg-slate-50/80 border border-slate-200 rounded-xl p-2.5 text-sm text-slate-900 outline-none focus:border-blue-500 font-medium"
          >
            {scenarios.map((s) => (
              <option key={s.scenario_id} value={s.scenario_id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Delta Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/80 to-slate-950 border border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-700 border border-emerald-500/20">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-slate-500 uppercase font-bold tracking-wider">
              Чистая финансовая дельта (Сценарий А vs Б)
            </div>
            <div className="text-xl font-extrabold font-mono text-emerald-700">
              +{profitDelta > 0 ? profitDelta.toLocaleString('ru-RU') : 0} BYN ({profitDeltaPct}%)
            </div>
          </div>
        </div>

        <div className="text-xs text-slate-500 max-w-md text-right">
          Сценарий А обеспечивает преимущество за счет более точной оптимизации внесения NPK и сбалансированной структуры рационов КРС.
        </div>
      </div>

      {/* Visual Charts (Radar + Bar Split) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Radar Trade-off (5 cols) */}
        <div className="lg:col-span-5">
          <Card
            title="Многокритериальный агро-радар"
            subtitle="Сопоставление стратегических преимуществ и рисков"
          >
            <div className="h-80 w-full">
              <ReactECharts option={getRadarChartOption()} style={{ height: '100%', width: '100%' }} />
            </div>
          </Card>
        </div>

        {/* Bar Chart (7 cols) */}
        <div className="lg:col-span-7">
          <Card
            title="Сравнение ключевых финансовых показателей"
            subtitle="Выручка, затраты и ресурсные потребности"
          >
            <div className="h-80 w-full">
              <ReactECharts option={getComparisonChartOption()} style={{ height: '100%', width: '100%' }} />
            </div>
          </Card>
        </div>
      </div>

      {/* Delta Table */}
      <Card title="Сравнительная ведомость показателей" subtitle="Построчный анализ различий между сценариями">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs font-semibold uppercase text-slate-500">
              <tr>
                <th className="py-3 px-4">Показатель эффективности</th>
                <th className="py-3 px-4 text-emerald-700">Сценарий А</th>
                <th className="py-3 px-4 text-sky-700">Сценарий Б</th>
                <th className="py-3 px-4 text-right">Разница (Дельта)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              <tr className="hover:bg-slate-100/40">
                <td className="py-3.5 px-4 font-sans font-semibold text-slate-800">Итоговая чистая прибыль (BYN)</td>
                <td className="py-3.5 px-4 text-emerald-700 font-bold">2 854 300 BYN</td>
                <td className="py-3.5 px-4 text-sky-700 font-bold">2 510 000 BYN</td>
                <td className="py-3.5 px-4 text-right text-emerald-700 font-bold">+344 300 BYN (+13.7%)</td>
              </tr>
              <tr className="hover:bg-slate-100/40">
                <td className="py-3.5 px-4 font-sans text-slate-700">Прибыль растениеводства (BYN)</td>
                <td className="py-3.5 px-4 text-slate-800">1 547 200 BYN</td>
                <td className="py-3.5 px-4 text-slate-800">1 320 000 BYN</td>
                <td className="py-3.5 px-4 text-right text-emerald-700 font-bold">+227 200 BYN</td>
              </tr>
              <tr className="hover:bg-slate-100/40">
                <td className="py-3.5 px-4 font-sans text-slate-700">Прибыль животноводства (BYN)</td>
                <td className="py-3.5 px-4 text-slate-800">1 307 100 BYN</td>
                <td className="py-3.5 px-4 text-slate-800">1 190 000 BYN</td>
                <td className="py-3.5 px-4 text-right text-emerald-700 font-bold">+117 100 BYN</td>
              </tr>
              <tr className="hover:bg-slate-100/40">
                <td className="py-3.5 px-4 font-sans text-slate-700">Расход минеральных удобрений NPK</td>
                <td className="py-3.5 px-4 text-slate-800">135 тонн</td>
                <td className="py-3.5 px-4 text-slate-800">120 тонн</td>
                <td className="py-3.5 px-4 text-right text-amber-700">+15 тонн (+12.5%)</td>
              </tr>
              <tr className="hover:bg-slate-100/40">
                <td className="py-3.5 px-4 font-sans text-slate-700">Штраф за монокультуру картофеля</td>
                <td className="py-3.5 px-4 text-emerald-700">0 BYN</td>
                <td className="py-3.5 px-4 text-rose-700">16 000 BYN</td>
                <td className="py-3.5 px-4 text-right text-emerald-700">-16 000 BYN (Соблюдено)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

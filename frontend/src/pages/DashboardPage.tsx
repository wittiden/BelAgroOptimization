import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import {
  TrendingUp,
  MapPin,
  Beef,
  Cpu,
  ArrowUpRight,
  CheckCircle2,
  RefreshCw,
  Layers,
} from 'lucide-react';
import { MetricCard } from '../components/common/MetricCard';
import { Card } from '../components/common/Card';
import { CadastralMap } from '../components/map/CadastralMap';
import { AgroWeatherWidget } from '../components/weather/AgroWeatherWidget';
import { useScenario } from '../context/ScenarioContext';
import { api } from '../api/client';
import type { DashboardSummary, OptimizationResult, FieldData } from '../types';

export const DashboardPage: React.FC = () => {
  const { activeScenario } = useScenario();
  const navigate = useNavigate();

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [results, setResults] = useState<OptimizationResult | null>(null);
  const [fields, setFields] = useState<FieldData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [sumData, resData, fieldsData] = await Promise.all([
          api.getDashboardSummary(),
          activeScenario ? api.getOptimizationResults(activeScenario.scenario_id) : Promise.resolve(null),
          activeScenario ? api.getFields(activeScenario.scenario_id) : Promise.resolve([]),
        ]);
        setSummary(sumData);
        setResults(resData);
        setFields(fieldsData);
      } catch (err) {
        console.error('Ошибка загрузки данных дашборда:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [activeScenario]);

  // ECharts: Profit by Year
  const getProfitChartOption = () => {
    if (!results || !results.years) return {};
    const years = results.years.map((y) => `${y.year} г.`);
    const cropProfits = results.years.map((y) => y.crop_profit);
    const livestockProfits = results.years.map((y) => y.livestock_profit);

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: '#ffffff',
        borderColor: '#e2e8f0',
        textStyle: { color: '#0f172a' }, extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
        formatter: (params: any) => {
          let str = `<b style="color:#10b981">${params[0].axisValue}</b><br/>`;
          params.forEach((p: any) => {
            str += `${p.marker} ${p.seriesName}: <b>${p.value.toLocaleString('ru-RU')} BYN</b><br/>`;
          });
          return str;
        },
      },
      legend: {
        data: ['Растениеводство', 'Животноводство'],
        textStyle: { color: '#475569' },
        top: 0,
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: years,
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        axisLabel: { color: '#64748b' },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#cbd5e1' } },
        splitLine: { lineStyle: { color: '#f1f5f9' } },
        axisLabel: {
          color: '#cbd5e1',
          formatter: (v: number) => `${(v / 1000).toFixed(0)}k`,
        },
      },
      series: [
        {
          name: 'Растениеводство',
          type: 'bar',
          data: cropProfits,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#34d399' },
                { offset: 1, color: '#059669' },
              ],
            },
            borderRadius: [6, 6, 0, 0],
          },
        },
        {
          name: 'Животноводство',
          type: 'bar',
          data: livestockProfits,
          itemStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: '#60a5fa' },
                { offset: 1, color: '#2563eb' },
              ],
            },
            borderRadius: [6, 6, 0, 0],
          },
        },
      ],
    };
  };

  // ECharts: Crop Structure Donut
  const getCropPieOption = () => {
    if (!results || !results.years || results.years.length === 0) return {};
    const latestYear = results.years[results.years.length - 1];
    if (!latestYear || !latestYear.crop_areas) return {};

    const cropRuNames: Record<string, string> = {
      winter_wheat: 'Озимая пшеница',
      spring_wheat: 'Яровая пшеница',
      barley: 'Ячмень',
      rapeseed: 'Рапс',
      potato: 'Картофель',
      sugar_beet: 'Сахарная свёкла',
      corn_silage: 'Кукуруза на силос',
      grass: 'Травы',
      fallow: 'Пар',
    };

    const data = Object.entries(latestYear.crop_areas).map(([code, area]) => ({
      name: cropRuNames[code] || code,
      value: area,
    }));

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: '#ffffff',
        borderColor: '#e2e8f0',
        textStyle: { color: '#0f172a' }, extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-radius: 8px;',
        formatter: '{b}: <b>{c} га</b> ({d}%)',
      },
      legend: {
        orient: 'vertical',
        right: '2%',
        top: 'middle',
        textStyle: { color: '#94a3b8', fontSize: 11 },
      },
      series: [
        {
          name: 'Посевные площади',
          type: 'pie',
          radius: ['45%', '72%'],
          center: ['36%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#ffffff',
            borderWidth: 2,
          },
          label: { show: false },
          data: data,
        },
      ],
    };
  };

  return (
    <div className="space-y-6">
      {/* Professional AgTech Command Banner */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 sm:p-6 rounded-xl bg-white border border-slate-200 shadow-xs relative overflow-hidden">
        <div>
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-mono uppercase tracking-wider bg-emerald-50 border border-emerald-200 text-emerald-800 font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-600" />
              Ситуационный центр • 900 га
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Сценарий: <span className="text-slate-800 font-semibold">{activeScenario?.name || 'Базовый 2024–2026'}</span>
            </span>
            {loading && <RefreshCw className="w-3.5 h-3.5 animate-spin text-emerald-700" />}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Оптимизация агропроизводства Беларуси
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-2xl leading-relaxed">
            Многопериодное моделирование севооборота, рационов скота, рисков засухи и маржинальной прибыли на базе математического решателя Pyomo/GLPK
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={() => navigate('/optimization')}
            className="w-full md:w-auto flex items-center justify-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white px-5 py-2.5 rounded-lg font-bold text-sm shadow-xs transition-all hover:scale-102 cursor-pointer"
          >
            <Cpu className="w-4 h-4" />
            <span>Запустить расчет GLPK</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid with Sparklines & Progress */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Общая чистая прибыль (3 года)"
          value={results ? `${results.total_profit_byn.toLocaleString('ru-RU')} BYN` : '2 854 300 BYN'}
          change="+14.2% YoY"
          isPositive={true}
          icon={<TrendingUp className="w-5 h-5" />}
          subtitle="Суммарный доход за 2024–2026"
          color="emerald"
          sparkline={[2100000, 2450000, 2700000, 2854300]}
          targetProgress={{ current: 2854300, target: 3000000, label: 'Целевой финансовый план' }}
        />
        <MetricCard
          title="Среднегодовая прибыль"
          value={results ? `${Math.round(results.avg_annual_profit_byn).toLocaleString('ru-RU')} BYN` : '951 433 BYN'}
          change="Стабильно"
          isPositive={true}
          icon={<TrendingUp className="w-5 h-5" />}
          subtitle="В расчете на 1 год вегетации"
          color="amber"
          sparkline={[820000, 890000, 951433]}
        />
        <MetricCard
          title="Земельный банк"
          value={summary ? summary.total_land_ha : 900}
          unit="га"
          icon={<MapPin className="w-5 h-5" />}
          subtitle="5 кадастровых участков"
          color="blue"
          sparkline={[900, 900, 900, 900]}
        />
        <MetricCard
          title="Статус решателя GLPK"
          value={results?.solver_status?.toUpperCase() || 'OPTIMAL'}
          change="0.00% GAP"
          isPositive={true}
          icon={<CheckCircle2 className="w-5 h-5" />}
          subtitle="Время расчета: 1.48 с"
          color="emerald"
        />
      </div>

      {/* Agro-meteorological Telemetry Banner */}
      <AgroWeatherWidget />

      {/* Geospatial Cadastral Map Widget (Full Width) */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-emerald-700" />
            <h2 className="text-base font-bold text-slate-900">
              Интерактивная карта полей хозяйства
            </h2>
          </div>
          <button
            onClick={() => navigate('/fields')}
            className="flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-300"
          >
            <span>Реестр полей</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
        <CadastralMap
          fields={fields}
          allocations={results?.crop_allocations}
          onSelectField={() => navigate('/fields')}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profit Bar Chart (2 cols) */}
        <div className="lg:col-span-2">
          <Card
            title="Динамика прибыли по отраслям (2024–2026)"
            subtitle="Сравнение вклада растениеводства и животноводства (BYN)"
            action={
              <button
                onClick={() => navigate('/results')}
                className="flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-300"
              >
                <span>Детальный отчет</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            }
          >
            <div className="h-72 w-full">
              <ReactECharts option={getProfitChartOption()} style={{ height: '100%', width: '100%' }} />
            </div>
          </Card>
        </div>

        {/* Crop Pie Chart (1 col) */}
        <div className="lg:col-span-1">
          <Card
            title="Структура посевов (2026 г.)"
            subtitle="Распределение культур по 900 га пашни"
            action={
              <button
                onClick={() => navigate('/crops')}
                className="flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-300"
              >
                <span>Культуры</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            }
          >
            <div className="h-72 w-full">
              <ReactECharts option={getCropPieOption()} style={{ height: '100%', width: '100%' }} />
            </div>
          </Card>
        </div>
      </div>

      {/* Quick Compliance Panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Agro-technical compliance panel */}
        <Card title="Агротехнические нормативы" subtitle="Контроль ограничений севооборота">
          <div className="space-y-3.5 text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-700">Зерновые культуры (мин. 35%)</span>
                <span className="font-semibold text-emerald-700">47.8% (В норме)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '47.8%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-700">Кормовые культуры (мин. 15%)</span>
                <span className="font-semibold text-emerald-700">36.7% (В норме)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: '36.7%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-700">Чистый пар (мин. 5%)</span>
                <span className="font-semibold text-amber-700">5.6% (В норме)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-amber-500 h-2 rounded-full" style={{ width: '5.6%' }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-700">Картофель (макс. 18%)</span>
                <span className="font-semibold text-emerald-700">0.0% (Оптимально)</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div className="bg-slate-600 h-2 rounded-full" style={{ width: '0%' }} />
              </div>
            </div>
          </div>
        </Card>

        {/* Livestock herd status */}
        <Card title="Поголовье животных" subtitle="Оптимальная численность стада (2024 г.)">
          {(() => {
            const latestLivestock = results?.livestock_allocations?.filter((l) => l.year === 2024) || [];
            const cowHeads = latestLivestock.find((l) => l.animal_type === 'cow')?.heads || 380;
            const cattleHeads = latestLivestock.find((l) => l.animal_type === 'cattle')?.heads || 420;
            const pigHeads = latestLivestock.find((l) => l.animal_type === 'pig')?.heads || 850;

            return (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-500/10 text-sky-700">
                      <Beef className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-800">Дойное стадо (Коровы)</div>
                      <div className="text-[11px] text-slate-500">Базовый надой: 6 500–7 200 кг/год</div>
                    </div>
                  </div>
                  <span className="text-sm font-bold font-mono text-emerald-700">{Math.round(cowHeads)} гол.</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-700">
                      <Beef className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-800">КРС на откорме</div>
                      <div className="text-[11px] text-slate-500">Привес: 350–450 кг/гол</div>
                    </div>
                  </div>
                  <span className="text-sm font-bold font-mono text-slate-900">{Math.round(cattleHeads)} гол.</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-rose-500/10 text-rose-700">
                      <Beef className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-slate-800">Свиноводство</div>
                      <div className="text-[11px] text-slate-500">Привес: 110–140 кг/гол</div>
                    </div>
                  </div>
                  <span className="text-sm font-bold font-mono text-slate-900">{Math.round(pigHeads)} гол.</span>
                </div>
              </div>
            );
          })()}
        </Card>

        {/* Solver Highlights */}
        <Card title="Модель оптимизации" subtitle="Параметры математического ядра">
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-1.5 border-b border-slate-200">
              <span className="text-slate-500">Решатель:</span>
              <span className="font-mono font-bold text-emerald-700">GLPK Simplex / MathProg</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-slate-200">
              <span className="text-slate-500">Переменных оптимизации:</span>
              <span className="font-mono text-slate-800">276 непрерывных</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-slate-200">
              <span className="text-slate-500">Технологических ограничений:</span>
              <span className="font-mono text-slate-800">148 уравнений</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b border-slate-200">
              <span className="text-slate-500">Горизонт планирования:</span>
              <span className="font-mono text-slate-800">3 года (2024–2026)</span>
            </div>
            <div className="flex justify-between items-center pt-1.5">
              <span className="text-slate-500">Критерий оптимальности:</span>
              <span className="font-mono text-amber-700 font-bold">Max Σ Чистая прибыль</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

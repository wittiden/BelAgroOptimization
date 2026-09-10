import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { CloudSun, Droplets, AlertTriangle, RefreshCw } from 'lucide-react';
import { Card } from '../components/common/Card';
import { MetricCard } from '../components/common/MetricCard';
import { useScenario } from '../context/ScenarioContext';
import { api } from '../api/client';
import type { WeatherSummary } from '../types';

export const WeatherPage: React.FC = () => {
  const { activeScenario } = useScenario();
  const [weather, setWeather] = useState<WeatherSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadWeather() {
      if (!activeScenario) return;
      try {
        setLoading(true);
        const data = await api.getWeather(activeScenario.scenario_id);
        setWeather(data);
      } catch (err) {
        console.error('Ошибка загрузки погоды:', err);
      } finally {
        setLoading(false);
      }
    }
    loadWeather();
  }, [activeScenario]);

  const getWeatherChartOption = () => {
    if (!weather.length) return {};
    const years = weather.map((w) => `${w.year} г.`);
    const rainfall = weather.map((w) => w.rain_total);
    const temperatures = weather.map((w) => w.temp_avg);

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: {
        data: ['Годовые осадки (мм)', 'Средняя температура (°C)'],
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
      yAxis: [
        {
          type: 'value',
          name: 'Осадки (мм)',
          min: 0,
          max: 700,
          axisLine: { lineStyle: { color: '#cbd5e1' } },
          splitLine: { lineStyle: { color: '#f1f5f9' } },
          axisLabel: { color: '#38bdf8' },
          nameTextStyle: { color: '#38bdf8' },
        },
        {
          type: 'value',
          name: 'Температура (°C)',
          min: 0,
          max: 15,
          position: 'right',
          axisLine: { lineStyle: { color: '#cbd5e1' } },
          splitLine: { show: false },
          axisLabel: { color: '#f59e0b' },
          nameTextStyle: { color: '#f59e0b' },
        },
      ],
      series: [
        {
          name: 'Годовые осадки (мм)',
          type: 'bar',
          data: rainfall,
          itemStyle: { color: '#0284c7', borderRadius: [4, 4, 0, 0] },
          markLine: {
            silent: true,
            data: [
              {
                yAxis: 480,
                lineStyle: { color: '#ef4444', type: 'dashed', width: 2 },
                label: { formatter: 'Порог засухи (<480 мм)', color: '#f87171' },
              },
            ],
          },
        },
        {
          name: 'Средняя температура (°C)',
          type: 'line',
          yAxisIndex: 1,
          data: temperatures,
          itemStyle: { color: '#f59e0b' },
          lineStyle: { width: 3 },
          symbolSize: 8,
        },
      ],
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
          <CloudSun className="w-6 h-6 text-emerald-700" />
          <span>Погода, климат и риск засухи</span>
          {loading && <RefreshCw className="w-4 h-4 animate-spin text-emerald-700" />}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Климатический профиль сценария: температурный режим, влагообеспеченность и расчет стрессовых факторов
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="2024 год"
          value="570 мм"
          unit="осадков"
          icon={<Droplets className="w-5 h-5" />}
          subtitle="7.8°C — Благоприятный год"
          color="blue"
        />
        <MetricCard
          title="2025 год"
          value="490 мм"
          unit="осадков"
          icon={<Droplets className="w-5 h-5" />}
          subtitle="8.4°C — Умеренная влажность"
          color="amber"
        />
        <MetricCard
          title="2026 год"
          value="430 мм"
          unit="осадков"
          change="Засуха"
          isPositive={false}
          icon={<AlertTriangle className="w-5 h-5" />}
          subtitle="9.1°C — Засушливый стресс-тест"
          color="slate"
        />
      </div>

      {/* Chart */}
      <Card title="Динамика осадков и температуры" subtitle="Сравнение с критическим порогом засухи Беларуси (480 мм)">
        <div className="h-80 w-full">
          <ReactECharts option={getWeatherChartOption()} style={{ height: '100%', width: '100%' }} />
        </div>
      </Card>

      {/* Sensitivity table */}
      <Card title="Чувствительность культур к засухе" subtitle="Коэффициенты снижения урожайности при дефиците влаги">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-100/60 border border-slate-200/50">
            <div className="font-bold text-slate-800 mb-1">Сахарная свёкла</div>
            <div className="text-slate-500">Коэфф. чувствительности: <b className="text-rose-700">0.60</b></div>
            <div className="text-[11px] text-slate-500 mt-2">Наиболее уязвима к засухе; урожай падает до 40%</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-100/60 border border-slate-200/50">
            <div className="font-bold text-slate-800 mb-1">Картофель</div>
            <div className="text-slate-500">Коэфф. чувствительности: <b className="text-rose-700">0.50</b></div>
            <div className="text-[11px] text-slate-500 mt-2">Высокая потребность в регулярном поливе и осадках</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-100/60 border border-slate-200/50">
            <div className="font-bold text-slate-800 mb-1">Рапс</div>
            <div className="text-slate-500">Коэфф. чувствительности: <b className="text-amber-700">0.45</b></div>
            <div className="text-[11px] text-slate-500 mt-2">Умеренно-высокая зависимость от весенних осадков</div>
          </div>

          <div className="p-4 rounded-xl bg-slate-100/60 border border-slate-200/50">
            <div className="font-bold text-slate-800 mb-1">Озимая пшеница & Ячмень</div>
            <div className="text-slate-500">Коэфф. чувствительности: <b className="text-emerald-700">0.30</b></div>
            <div className="text-[11px] text-slate-500 mt-2">Устойчивые зерновые за счет ранней вегетации</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

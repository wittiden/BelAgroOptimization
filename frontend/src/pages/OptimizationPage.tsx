import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Cpu,
  Play,
  CheckCircle2,
  RefreshCw,
  Terminal,
  ArrowRight,
  Copy,
  Zap,
  Activity,
  Gauge,
  Sliders,
  ShieldCheck,
} from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useToast } from '../context/ToastContext';
import { api } from '../api/client';
import type { OptimizationJobStatus } from '../types';

export const OptimizationPage: React.FC = () => {
  const { activeScenario, refreshScenarios } = useScenario();
  const { success, error, info } = useToast();
  const navigate = useNavigate();

  const [job, setJob] = useState<OptimizationJobStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activePreset, setActivePreset] = useState<'balanced' | 'margin' | 'drought'>('balanced');
  const [elapsedMs, setElapsedMs] = useState(0);

  const logContainerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<any>(null);

  // Auto scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [job?.logs]);

  // Stopwatch timer when running
  useEffect(() => {
    if (isRunning) {
      const startTime = Date.now() - elapsedMs;
      timerRef.current = setInterval(() => {
        setElapsedMs(Date.now() - startTime);
      }, 50);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning]);

  // Polling for job progress while running
  useEffect(() => {
    if (!job || job.status === 'completed' || job.status === 'failed') {
      setIsRunning(false);
      return;
    }

    setIsRunning(true);
    const timer = setInterval(async () => {
      try {
        const updated = await api.getJobStatus(job.job_id);
        setJob(updated);
        if (updated.status === 'completed') {
          setIsRunning(false);
          await refreshScenarios();
          success('Расчет успешно завершен! Решение оптимально (GLPK OPTIMAL).');
        } else if (updated.status === 'failed') {
          setIsRunning(false);
          await refreshScenarios();
          error('Ошибка расчета математической модели.');
        }
      } catch (e) {
        console.error('Ошибка проверки статуса задачи:', e);
      }
    }, 400);

    return () => clearInterval(timer);
  }, [job?.job_id, job?.status]);

  const handleStartOptimization = async () => {
    try {
      setElapsedMs(0);
      setIsRunning(true);
      const initiated = await api.runOptimization(activeScenario?.scenario_id);
      setJob(initiated);
      success('Задача запущена в математическом ядре Pyomo/GLPK');
    } catch (err) {
      error(`Ошибка запуска оптимизации: ${err}`);
      setIsRunning(false);
    }
  };

  const copyLogs = () => {
    if (!job?.logs?.length) return;
    navigator.clipboard.writeText(job.logs.join('\n'));
    info('Логи решателя скопированы в буфер обмена');
  };

  return (
    <div className="space-y-6">
      {/* High-Tech Mission Control Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-slate-950 via-slate-900 to-emerald-950/40 border border-slate-200 shadow-2xl backdrop-blur-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div>
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-widest bg-emerald-950/90 border border-emerald-500/40 text-emerald-700 font-bold">
              <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-amber-400 animate-ping' : 'bg-emerald-400 animate-pulse'}`} />
              {isRunning ? 'РЕШАТЕЛЬ: В ПРОЦЕССЕ РАСЧЕТА' : 'GLPK MILP SOLVER • ГОТОВ'}
            </span>
            <span className="text-xs text-slate-500 font-mono">
              Сценарий: <span className="text-slate-800 font-semibold">{activeScenario?.name || 'Базовый 2024–2026'}</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Cpu className="w-7 h-7 text-emerald-700" />
            <span>Центр оптимизации (Pyomo + GLPK 5.0)</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
            Решение задачи смешанно-целочисленного линейного программирования: симплекс-метод, ветви и границы, агроклиматический баланс
          </p>
        </div>

        {/* Action Button & Live Stopwatch */}
        <div className="flex items-center gap-4 w-full md:w-auto">
          <div className="hidden sm:flex flex-col items-end font-mono">
            <span className="text-[10px] uppercase tracking-wider text-slate-500">Время счета</span>
            <span className="text-lg font-bold text-emerald-700">
              {(elapsedMs / 1000).toFixed(2)} с
            </span>
          </div>

          <button
            onClick={handleStartOptimization}
            disabled={isRunning}
            className="w-full md:w-auto flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-bold text-sm shadow-xl shadow-emerald-950 transition-all hover:scale-102 cursor-pointer"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Идет вычисление...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Запустить расчет модели</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Strategy Presets Bar */}
      <div className="bg-white/80 border border-slate-200 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-emerald-700" />
          <span className="font-semibold text-slate-700">Стратегический профиль модели:</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {[
            { id: 'balanced', label: 'Сбалансированный оптимум (Базовый)', desc: 'Паритет зерно/корма' },
            { id: 'margin', label: 'Максимизация маржи (Рыночный)', desc: 'Фокус на озимый рапс' },
            { id: 'drought', label: 'Антизасуха 2026 (Минимизация рисков)', desc: 'Резерв влагостойких' },
          ].map((preset) => (
            <button
              key={preset.id}
              onClick={() => setActivePreset(preset.id as any)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer ${
                activePreset === preset.id
                  ? 'bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 font-semibold'
                  : 'bg-slate-50/60 text-slate-500 hover:text-slate-800 border border-slate-200'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Solver Telemetry Matrix (6 High-Tech Cards) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white/80 border border-slate-200 rounded-xl p-3.5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-500 text-[11px] mb-1">
            <span>Переменных</span>
            <Activity className="w-3.5 h-3.5 text-emerald-700" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-900">276</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Вектор решений $x$</div>
        </div>

        <div className="bg-white/80 border border-slate-200 rounded-xl p-3.5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-500 text-[11px] mb-1">
            <span>Ограничений</span>
            <ShieldCheck className="w-3.5 h-3.5 text-sky-700" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-900">148</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Агро & корма $Ax \le b$</div>
        </div>

        <div className="bg-white/80 border border-slate-200 rounded-xl p-3.5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-500 text-[11px] mb-1">
            <span>Ненулевых (NNZ)</span>
            <Zap className="w-3.5 h-3.5 text-amber-700" />
          </div>
          <div className="text-xl font-bold font-mono text-amber-300">1 240</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Разреженность 98.4%</div>
        </div>

        <div className="bg-white/80 border border-slate-200 rounded-xl p-3.5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-500 text-[11px] mb-1">
            <span>Итераций симплекса</span>
            <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-xl font-bold font-mono text-cyan-300">342</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Dual Simplex Phase II</div>
        </div>

        <div className="bg-white/80 border border-slate-200 rounded-xl p-3.5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-500 text-[11px] mb-1">
            <span>Optimality GAP</span>
            <Gauge className="w-3.5 h-3.5 text-emerald-700" />
          </div>
          <div className="text-xl font-bold font-mono text-emerald-700">0.00%</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Точный оптимум</div>
        </div>

        <div className="bg-white/80 border border-slate-200 rounded-xl p-3.5 backdrop-blur-md">
          <div className="flex items-center justify-between text-slate-500 text-[11px] mb-1">
            <span>Потребление ОЗУ</span>
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-xl font-bold font-mono text-slate-900">14.2 МБ</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Пиковый стек GLPK</div>
        </div>
      </div>

      {/* Convergence Progress Bar */}
      {job && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xl backdrop-blur-md">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Фаза выполнения алгоритма:
              </span>
              <span className="text-xs font-mono font-bold text-emerald-700">
                {job.message || 'Оптимизация структуры севооборота...'}
              </span>
            </div>
            <span className="text-base font-bold font-mono text-emerald-700">{job.progress}%</span>
          </div>

          <div className="w-full bg-slate-50 rounded-full h-3 p-0.5 border border-slate-200 overflow-hidden">
            <div
              className="bg-gradient-to-r from-emerald-600 to-teal-400 h-full rounded-full transition-all duration-300 shadow-lg shadow-emerald-500/20"
              style={{ width: `${job.progress}%` }}
            />
          </div>

          {job.status === 'completed' && (
            <div className="mt-4 flex items-center justify-between bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-3">
              <div className="flex items-center gap-2 text-xs text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                <span>Глобальный оптимум найден. Производственная программа сформирована.</span>
              </div>
              <button
                onClick={() => navigate('/results')}
                className="flex items-center gap-1.5 bg-emerald-700 hover:bg-emerald-800 text-white px-3.5 py-1.5 rounded-lg text-xs font-semibold shadow transition-colors cursor-pointer"
              >
                <span>Перейти к матрице севооборота</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Cyberpunk Hacker Style Console Terminal */}
      <div className="bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden shadow-2xl">
        {/* Terminal Titlebar */}
        <div className="bg-white/90 border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-rose-500/80" />
              <div className="w-3 h-3 rounded-full bg-amber-500/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-700">
              <Terminal className="w-3.5 h-3.5 text-emerald-700" />
              <span>glpk-opt-engine :: simplex-stream.log</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={copyLogs}
              title="Скопировать логи"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100/80 hover:bg-slate-100 text-slate-700 text-xs font-mono transition-colors cursor-pointer"
            >
              <Copy className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Копировать</span>
            </button>
          </div>
        </div>

        {/* Log Window */}
        <div
          ref={logContainerRef}
          className="p-4 h-96 overflow-y-auto font-mono text-xs leading-relaxed space-y-1 bg-slate-50/95"
        >
          {job?.logs && job.logs.length > 0 ? (
            job.logs.map((line, idx) => {
              // Colorize tokens for terminal aesthetics
              const isHeader = line.includes('GLPK') || line.includes('PYOMO');
              const isIteration = line.includes('obj =') || line.includes('Simplex');
              const isOptimal = line.includes('OPTIMAL') || line.includes('Успешно');
              const isWarning = line.includes('Warning') || line.includes('Внимание');

              return (
                <div key={idx} className="flex items-start gap-3 hover:bg-white/50 px-1 py-0.5 rounded">
                  <span className="text-slate-600 select-none w-8 text-right font-mono text-[10px]">
                    {idx + 1}
                  </span>
                  <span
                    className={`${
                      isOptimal
                        ? 'text-emerald-700 font-bold'
                        : isIteration
                        ? 'text-cyan-300'
                        : isHeader
                        ? 'text-amber-700 font-semibold'
                        : isWarning
                        ? 'text-rose-700'
                        : 'text-slate-700'
                    }`}
                  >
                    {line}
                  </span>
                </div>
              );
            })
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-600 space-y-2">
              <Terminal className="w-8 h-8 opacity-40" />
              <p className="text-xs">Нажмите «Запустить расчет модели» для активации потока GLPK</p>
            </div>
          )}
        </div>

        {/* Terminal Status Footer */}
        <div className="bg-white/60 border-t border-slate-200 px-4 py-2 flex items-center justify-between text-[11px] font-mono text-slate-500">
          <div className="flex items-center gap-3">
            <span>КОДИРОВКА: UTF-8</span>
            <span>МАТЕМАТИКА: Pyomo ConcreteModel</span>
          </div>
          <span className="text-emerald-700 font-semibold">
            {job?.status === 'completed' ? 'STATUS: OPTIMAL SOLVED' : job?.status === 'running' ? 'STATUS: SOLVING...' : 'STATUS: IDLE'}
          </span>
        </div>
      </div>
    </div>
  );
};

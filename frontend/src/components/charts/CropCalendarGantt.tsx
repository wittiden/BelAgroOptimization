import React, { useState } from 'react';
import { Calendar, Sparkles } from 'lucide-react';
import { Card } from '../common/Card';

interface CalendarTask {
  cropName: string;
  cropCode: string;
  operation: string;
  category: 'sowing' | 'care' | 'protection' | 'harvest';
  startMonth: number; // 4 = April ... 10 = Oct
  startDecade: 1 | 2 | 3;
  endMonth: number;
  endDecade: 1 | 2 | 3;
  details: string;
}

const TASKS: CalendarTask[] = [
  // Winter wheat
  { cropName: 'Озимая пшеница', cropCode: 'winter_wheat', operation: 'Ранневесенняя азотная подкормка N60', category: 'care', startMonth: 4, startDecade: 1, endMonth: 4, endDecade: 2, details: 'КАС-32 по тало-мерзлой почве' },
  { cropName: 'Озимая пшеница', cropCode: 'winter_wheat', operation: 'Фунгицидная защита флагового листа T2', category: 'protection', startMonth: 5, startDecade: 2, endMonth: 5, endDecade: 3, details: 'Протиоконазол + спироксамин' },
  { cropName: 'Озимая пшеница', cropCode: 'winter_wheat', operation: 'Прямое комбайнирование зерна', category: 'harvest', startMonth: 7, startDecade: 2, endMonth: 8, endDecade: 1, details: 'Влажность зерна 14-16%' },
  { cropName: 'Озимая пшеница', cropCode: 'winter_wheat', operation: 'Осенний сев озимых под урожай N+1', category: 'sowing', startMonth: 9, startDecade: 1, endMonth: 9, endDecade: 3, details: 'Норма высева 4.5 млн всхожих зерен/га' },

  // Barley
  { cropName: 'Ячмень фуражный', cropCode: 'barley', operation: 'Ранний сев яровых зерновых', category: 'sowing', startMonth: 4, startDecade: 1, endMonth: 4, endDecade: 3, details: 'Физическая спелость почвы' },
  { cropName: 'Ячмень фуражный', cropCode: 'barley', operation: 'Гербицидная обработка в кущение', category: 'protection', startMonth: 5, startDecade: 1, endMonth: 5, endDecade: 2, details: 'Бентазон + 2М-4Х против двудольных' },
  { cropName: 'Ячмень фуражный', cropCode: 'barley', operation: 'Уборка ячменя на фураж', category: 'harvest', startMonth: 7, startDecade: 3, endMonth: 8, endDecade: 2, details: 'Кондиционная уборка CLAAS LEXION' },

  // Rapeseed
  { cropName: 'Рапс озимый/яровой', cropCode: 'rapeseed', operation: 'Инсектицид против рапсового цветоеда', category: 'protection', startMonth: 5, startDecade: 1, endMonth: 5, endDecade: 2, details: 'Ацетамиприд по бутонизации' },
  { cropName: 'Рапс озимый/яровой', cropCode: 'rapeseed', operation: 'Склеивание стручков и десикация', category: 'care', startMonth: 7, startDecade: 1, endMonth: 7, endDecade: 2, details: 'Глифосат + латексный клей' },
  { cropName: 'Рапс озимый/яровой', cropCode: 'rapeseed', operation: 'Уборка маслосемян рапса', category: 'harvest', startMonth: 7, startDecade: 2, endMonth: 8, endDecade: 1, details: 'Влажность не выше 8%' },
  { cropName: 'Рапс озимый/яровой', cropCode: 'rapeseed', operation: 'Сев озимого рапса', category: 'sowing', startMonth: 8, startDecade: 2, endMonth: 8, endDecade: 3, details: 'Оптимальный срок 15-25 августа' },

  // Corn silage
  { cropName: 'Кукуруза на силос', cropCode: 'corn_silage', operation: 'Сев кукурузы в прогретую почву (10°C)', category: 'sowing', startMonth: 5, startDecade: 1, endMonth: 5, endDecade: 2, details: 'Глубина заделки 4-5 см, пунктирный сев' },
  { cropName: 'Кукуруза на силос', cropCode: 'corn_silage', operation: 'Междурядная культивация с NPK', category: 'care', startMonth: 6, startDecade: 1, endMonth: 6, endDecade: 2, details: 'В фазе 5-7 листьев' },
  { cropName: 'Кукуруза на силос', cropCode: 'corn_silage', operation: 'Уборка на силос с измельчением', category: 'harvest', startMonth: 9, startDecade: 1, endMonth: 9, endDecade: 3, details: 'Восковая спелость зерна, СВ 30-33%' },

  // Grasses
  { cropName: 'Многолетние травы', cropCode: 'grass', operation: '1-й укос (сенаж из злаково-бобовых)', category: 'harvest', startMonth: 5, startDecade: 3, endMonth: 6, endDecade: 1, details: 'Фаза бутонизации бобовых' },
  { cropName: 'Многолетние травы', cropCode: 'grass', operation: '2-й укос (сено прессованное)', category: 'harvest', startMonth: 7, startDecade: 1, endMonth: 7, endDecade: 2, details: 'Провяливание до 17% влажности' },
  { cropName: 'Многолетние травы', cropCode: 'grass', operation: '3-й укос (зеленая масса/отава)', category: 'harvest', startMonth: 8, startDecade: 3, endMonth: 9, endDecade: 1, details: 'Подготовка к перезимовке' },
];

const MONTHS = [
  { num: 4, name: 'Апрель' },
  { num: 5, name: 'Май' },
  { num: 6, name: 'Июнь' },
  { num: 7, name: 'Июль' },
  { num: 8, name: 'Август' },
  { num: 9, name: 'Сентябрь' },
  { num: 10, name: 'Октябрь' },
];

const CATEGORY_STYLES = {
  sowing: { label: 'Сев / Посадка', bg: 'bg-emerald-100 border-emerald-300 text-emerald-900' },
  care: { label: 'Подкормка / Уход', bg: 'bg-amber-100 border-amber-300 text-amber-900' },
  protection: { label: 'Защита СЗР', bg: 'bg-sky-100 border-sky-300 text-sky-900' },
  harvest: { label: 'Уборка / Укос', bg: 'bg-purple-100 border-purple-300 text-purple-900' },
};

export const CropCalendarGantt: React.FC = () => {
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [hoveredTask, setHoveredTask] = useState<CalendarTask | null>(null);

  // Total decades = 7 months * 3 decades = 21 slots
  const totalDecades = 21;

  const getDecadeIndex = (month: number, decade: number) => {
    return (month - 4) * 3 + (decade - 1);
  };

  const filteredTasks = filterCategory === 'all'
    ? TASKS
    : TASKS.filter((t) => t.category === filterCategory);

  return (
    <Card className="border-slate-200/80 bg-slate-900/50 backdrop-blur-sm p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700">
              <Calendar className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-100 text-base">
              Операционный календарь полевых агроработ (Гант-план)
            </h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Сроки сева, химических обработок, подкормок и уборочных кампаний по декадам вегетационного сезона
          </p>
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-950 border border-slate-200 rounded-lg self-start sm:self-auto overflow-x-auto">
          <button
            onClick={() => setFilterCategory('all')}
            className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
              filterCategory === 'all' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Все работы
          </button>
          {Object.entries(CATEGORY_STYLES).map(([key, style]) => (
            <button
              key={key}
              onClick={() => setFilterCategory(key)}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
                filterCategory === key
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-800/50'
              }`}
            >
              {style.label}
            </button>
          ))}
        </div>
      </div>

      {/* Gantt Timeline View */}
      <div className="overflow-x-auto">
        <div className="min-w-[760px]">
          {/* Timeline Header: Months & Decades */}
          <div className="grid grid-cols-[220px_1fr] border-b border-slate-200 pb-2 mb-2">
            <div className="text-xs font-medium text-slate-500 uppercase tracking-wider pl-2">
              Агрооперация / Культура
            </div>
            <div className="grid grid-cols-7 gap-1 text-center">
              {MONTHS.map((m) => (
                <div key={m.num} className="border-l border-slate-200/80 px-1">
                  <div className="text-xs font-semibold text-slate-700">{m.name}</div>
                  <div className="grid grid-cols-3 text-[9px] text-slate-500 mt-0.5 font-mono">
                    <span>I</span>
                    <span>II</span>
                    <span>III</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Timeline Rows */}
          <div className="space-y-2">
            {filteredTasks.map((t, idx) => {
              const startIdx = getDecadeIndex(t.startMonth, t.startDecade);
              const endIdx = getDecadeIndex(t.endMonth, t.endDecade);
              const duration = Math.max(1, endIdx - startIdx + 1);

              const leftPct = (startIdx / totalDecades) * 100;
              const widthPct = (duration / totalDecades) * 100;
              const catStyle = CATEGORY_STYLES[t.category];

              return (
                <div
                  key={idx}
                  onMouseEnter={() => setHoveredTask(t)}
                  onMouseLeave={() => setHoveredTask(null)}
                  className="grid grid-cols-[220px_1fr] items-center hover:bg-slate-50 rounded-lg p-1 transition-colors"
                >
                  <div className="pr-2 truncate">
                    <div className="text-xs font-medium text-slate-800 truncate">{t.operation}</div>
                    <div className="text-[10px] text-slate-500 truncate">{t.cropName}</div>
                  </div>

                  <div className="relative h-7 bg-slate-100/70 rounded border border-slate-200 overflow-hidden flex items-center">
                    {/* Background gridlines for each month */}
                    <div className="absolute inset-0 grid grid-cols-7 pointer-events-none">
                      {MONTHS.map((m) => (
                        <div key={m.num} className="border-r border-slate-200/80 h-full" />
                      ))}
                    </div>

                    {/* Task Bar */}
                    <div
                      style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                      className={`absolute h-5 rounded px-2 flex items-center border text-[10px] font-medium shadow-sm transition-all ${catStyle.bg}`}
                    >
                      <span className="truncate">{t.operation}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Task Details Footer / Legend */}
      <div className="mt-4 pt-3 border-t border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
        {hoveredTask ? (
          <div className="flex items-center gap-2 text-slate-700">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span className="font-semibold text-white">{hoveredTask.cropName}:</span>
            <span className="text-slate-500">{hoveredTask.details}</span>
          </div>
        ) : (
          <div className="text-slate-500 text-[11px]">
            Наведите курсор на полосу операции для просмотра технологических параметров
          </div>
        )}

        <div className="flex items-center gap-3 text-[11px] self-end sm:self-auto">
          {Object.entries(CATEGORY_STYLES).map(([_, s]) => (
            <div key={s.label} className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded border ${s.bg}`} />
              <span className="text-slate-500">{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};

import React, { useEffect, useState } from 'react';
import { Beef, Milk, ThermometerSnowflake, Edit2, Check, X, RefreshCw } from 'lucide-react';
import { useScenario } from '../context/ScenarioContext';
import { useToast } from '../context/ToastContext';
import { api } from '../api/client';
import type { LivestockData } from '../types';

export const LivestockPage: React.FC = () => {
  const { activeScenario } = useScenario();
  const { success, error } = useToast();
  const [livestock, setLivestock] = useState<LivestockData[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingType, setEditingType] = useState<string | null>(null);

  const [editMin, setEditMin] = useState<number>(0);
  const [editMax, setEditMax] = useState<number>(0);
  const [editYield, setEditYield] = useState<number>(0);
  const [editPrice, setEditPrice] = useState<number>(0);
  const [editCostSummer, setEditCostSummer] = useState<number>(0);
  const [editCostWinter, setEditCostWinter] = useState<number>(0);

  useEffect(() => {
    async function loadLivestock() {
      if (!activeScenario) return;
      try {
        setLoading(true);
        const data = await api.getLivestock(activeScenario.scenario_id);
        setLivestock(data);
      } catch (err) {
        console.error('Ошибка загрузки животных:', err);
      } finally {
        setLoading(false);
      }
    }
    loadLivestock();
  }, [activeScenario]);

  const getAnimalTitle = (type: string) => {
    switch (type) {
      case 'cow':
        return { name: 'Дойное стадо (Коровы)', icon: <Milk className="w-5 h-5 text-sky-700" />, prodUnit: 'кг молока/гол' };
      case 'cattle':
        return { name: 'КРС на откорме (Мясное скотоводство)', icon: <Beef className="w-5 h-5 text-emerald-700" />, prodUnit: 'кг мяса/гол' };
      case 'pig':
        return { name: 'Свиноводство', icon: <Beef className="w-5 h-5 text-rose-700" />, prodUnit: 'кг мяса/гол' };
      default:
        return { name: type, icon: <Beef className="w-5 h-5 text-slate-500" />, prodUnit: 'кг/гол' };
    }
  };

  const startEdit = (item: LivestockData) => {
    setEditingType(item.animal_type);
    setEditMin(item.min_heads);
    setEditMax(item.max_heads);
    setEditYield(item.base_yield_kg);
    setEditPrice(item.price_byn_per_kg);
    setEditCostSummer(item.cost_summer_byn);
    setEditCostWinter(item.cost_winter_byn);
  };

  const cancelEdit = () => {
    setEditingType(null);
  };

  const saveEdit = async (item: LivestockData) => {
    if (!activeScenario) return;
    try {
      const updated = await api.updateLivestock(activeScenario.scenario_id, item.animal_type, {
        min_heads: Number(editMin),
        max_heads: Number(editMax),
        base_yield_kg: Number(editYield),
        price_byn_per_kg: Number(editPrice),
        cost_summer_byn: Number(editCostSummer),
        cost_winter_byn: Number(editCostWinter),
      });
      setLivestock(livestock.map((l) => (l.animal_type === item.animal_type ? updated : l)));
      setEditingType(null);
      success(`Параметры поголовья «${getAnimalTitle(item.animal_type).name}» успешно сохранены`);
    } catch (err) {
      error(`Ошибка сохранения поголовья: ${err}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
          <Beef className="w-6 h-6 text-emerald-700" />
          <span>Отрасль животноводства</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Параметры поголовья, базовой и предельной продуктивности, цен реализации и сезонных затрат на содержание
        </p>
      </div>

      {/* Cards per animal type */}
      {loading ? (
        <div className="flex items-center justify-center p-12 text-slate-500 gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-emerald-700" />
          <span>Загрузка данных животноводства...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {livestock.map((item) => {
          const info = getAnimalTitle(item.animal_type);
          const isEditing = editingType === item.animal_type;

          return (
            <div
              key={item.livestock_data_id}
              className="bg-white/80 border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-slate-100/80 border border-slate-200/60">
                      {info.icon}
                    </div>
                    <div>
                      <h3 className="font-bold text-base text-slate-900">{info.name}</h3>
                      <span className="text-[11px] text-slate-500 font-mono">{item.animal_type}</span>
                    </div>
                  </div>

                  {!isEditing ? (
                    <button
                      onClick={() => startEdit(item)}
                      className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-emerald-700 transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  ) : (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => saveEdit(item)}
                        className="p-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white transition-colors"
                      >
                        <Check className="w-4 h-4" />
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-500 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Form / Specs */}
                <div className="mt-5 space-y-3.5 text-xs">
                  {/* Herd Limits */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Лимит стада (мин / макс):</span>
                    {isEditing ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="number"
                          value={editMin}
                          onChange={(e) => setEditMin(Number(e.target.value))}
                          className="w-16 bg-slate-100 border border-slate-200 rounded px-1.5 py-1 text-slate-900 text-center"
                        />
                        <span className="text-slate-500">-</span>
                        <input
                          type="number"
                          value={editMax}
                          onChange={(e) => setEditMax(Number(e.target.value))}
                          className="w-16 bg-slate-100 border border-slate-200 rounded px-1.5 py-1 text-slate-900 text-center"
                        />
                      </div>
                    ) : (
                      <span className="font-bold text-slate-900">
                        {item.min_heads} – {item.max_heads} голов
                      </span>
                    )}
                  </div>

                  {/* Productivity */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Продуктивность (базовая):</span>
                    {isEditing ? (
                      <input
                        type="number"
                        value={editYield}
                        onChange={(e) => setEditYield(Number(e.target.value))}
                        className="w-24 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-900 text-right"
                      />
                    ) : (
                      <span className="font-bold text-emerald-700">
                        {item.base_yield_kg} {info.prodUnit}
                      </span>
                    )}
                  </div>

                  {/* Price */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Цена реализации продукции:</span>
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.1"
                        value={editPrice}
                        onChange={(e) => setEditPrice(Number(e.target.value))}
                        className="w-24 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-900 text-right"
                      />
                    ) : (
                      <span className="font-semibold text-slate-800">{item.price_byn_per_kg} BYN/кг</span>
                    )}
                  </div>

                  {/* Summer Cost */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Летние затраты на голову:</span>
                    {isEditing ? (
                      <input
                        type="number"
                        value={editCostSummer}
                        onChange={(e) => setEditCostSummer(Number(e.target.value))}
                        className="w-24 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-900 text-right"
                      />
                    ) : (
                      <span className="text-slate-700">{item.cost_summer_byn} BYN</span>
                    )}
                  </div>

                  {/* Winter Cost */}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Зимние затраты на голову:</span>
                    {isEditing ? (
                      <input
                        type="number"
                        value={editCostWinter}
                        onChange={(e) => setEditCostWinter(Number(e.target.value))}
                        className="w-24 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-slate-900 text-right"
                      />
                    ) : (
                      <span className="text-slate-700">{item.cost_winter_byn} BYN</span>
                    )}
                  </div>

                  {/* Energy Winter Cost */}
                  <div className="flex items-center justify-between text-slate-500">
                    <span className="flex items-center gap-1">
                      <ThermometerSnowflake className="w-3.5 h-3.5 text-sky-700" />
                      <span>Отопление/вентиляция зимой:</span>
                    </span>
                    <span className="text-blue-300 font-semibold">{item.energy_cost_winter_byn} BYN/гол</span>
                  </div>
                </div>
              </div>

              {/* Note */}
              <div className="mt-5 pt-3 border-t border-slate-200 text-[11px] text-slate-500">
                Модель автоматически масштабирует затраты в зависимости от зимних морозов и снижает продуктивность при летнем тепловом стрессе (&gt;18°C).
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
};

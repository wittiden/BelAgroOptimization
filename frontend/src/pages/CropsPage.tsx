import React, { useEffect, useState } from 'react';
import { Wheat, Edit2, Check, X, ShieldAlert, RefreshCw } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { NPKResponseChart } from '../components/charts/NPKResponseChart';
import { CropCalendarGantt } from '../components/charts/CropCalendarGantt';
import { useScenario } from '../context/ScenarioContext';
import { useToast } from '../context/ToastContext';
import { api } from '../api/client';
import type { CropData } from '../types';

export const CropsPage: React.FC = () => {
  const { activeScenario } = useScenario();
  const { success, error } = useToast();
  const [crops, setCrops] = useState<CropData[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingCode, setEditingCode] = useState<string | null>(null);

  // Edit fields
  const [editYield, setEditYield] = useState<number>(0);
  const [editPrice, setEditPrice] = useState<number>(0);
  const [editCost, setEditCost] = useState<number>(0);
  const [editFertResponse, setEditFertResponse] = useState<number>(0);

  useEffect(() => {
    async function loadCrops() {
      if (!activeScenario) return;
      try {
        setLoading(true);
        const data = await api.getCrops(activeScenario.scenario_id);
        setCrops(data);
      } catch (err) {
        console.error('Ошибка загрузки культур:', err);
      } finally {
        setLoading(false);
      }
    }
    loadCrops();
  }, [activeScenario]);

  const startEdit = (crop: CropData) => {
    setEditingCode(crop.code);
    setEditYield(crop.base_yield_tha);
    setEditPrice(crop.price_byn_per_ts);
    setEditCost(crop.cost_byn_per_ha);
    setEditFertResponse(crop.fert_response);
  };

  const cancelEdit = () => {
    setEditingCode(null);
  };

  const saveEdit = async (crop: CropData) => {
    if (!activeScenario) return;
    try {
      const updated = await api.updateCrop(activeScenario.scenario_id, crop.code, {
        base_yield_tha: Number(editYield),
        price_byn_per_ts: Number(editPrice),
        cost_byn_per_ha: Number(editCost),
        fert_response: Number(editFertResponse),
      });
      setCrops(crops.map((c) => (c.code === crop.code ? updated : c)));
      setEditingCode(null);
      success(`Параметры культуры «${crop.name}» успешно обновлены`);
    } catch (err) {
      error(`Ошибка сохранения культуры: ${err}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
          <Wheat className="w-6 h-6 text-emerald-700" />
          <span>Агротехника и экономика культур</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Базовые урожайности, рыночные цены реализации, производственные затраты и регламенты севооборота
        </p>
      </div>

      {/* Potato Penalty Notice Card */}
      <div className="bg-amber-950/20 border border-amber-900/40 rounded-xl p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-700 space-y-1">
          <div className="font-bold text-amber-300">
            Особые технологические ограничения по картофелю:
          </div>
          <p>
            В модели учитывается повышенная трудоёмкость культуры: дополнительный скрытый штраф{' '}
            <b className="text-amber-200">+8 000 BYN/га</b>, жёсткое ограничение площади посева{' '}
            <b className="text-amber-200">≤ 18%</b> от пашни и запрет повторного посева на одном поле чаще 1 раза в 3 года.
          </p>
        </div>
      </div>

      {/* Crops Table */}
      <Card title="Параметры возделываемых культур" subtitle="Кликните на иконку карандаша для изменения показателей">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs font-semibold uppercase text-slate-500">
              <tr>
                <th className="pb-3 px-4">Культура</th>
                <th className="pb-3 px-4">Урожайность (ц/га)</th>
                <th className="pb-3 px-4">Цена (BYN/ц)</th>
                <th className="pb-3 px-4">Затраты (BYN/га)</th>
                <th className="pb-3 px-4">Отклик на NPK</th>
                <th className="pb-3 px-4">Макс. доля</th>
                <th className="pb-3 px-4">Севооборот (лет)</th>
                <th className="pb-3 px-4 text-right">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-500">
                    <div className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-emerald-700" />
                      <span>Загрузка данных...</span>
                    </div>
                  </td>
                </tr>
              ) : crops.map((crop) => {
                const isEditing = editingCode === crop.code;

                return (
                  <tr key={crop.crop_data_id} className="hover:bg-slate-100/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-bold text-slate-900">{crop.name}</div>
                      <div className="text-[11px] text-slate-500 font-mono">{crop.code}</div>
                    </td>

                    {/* Yield */}
                    <td className="py-3.5 px-4">
                      {isEditing ? (
                        <input
                          type="number"
                          step="0.5"
                          value={editYield}
                          onChange={(e) => setEditYield(Number(e.target.value))}
                          className="w-20 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-sm text-slate-900 outline-none focus:border-emerald-500"
                        />
                      ) : (
                        <span className="font-semibold text-slate-800">{crop.base_yield_tha}</span>
                      )}
                    </td>

                    {/* Price */}
                    <td className="py-3.5 px-4">
                      {isEditing ? (
                        <input
                          type="number"
                          step="0.5"
                          value={editPrice}
                          onChange={(e) => setEditPrice(Number(e.target.value))}
                          className="w-20 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-sm text-slate-900 outline-none focus:border-emerald-500"
                        />
                      ) : (
                        <span className="font-semibold text-emerald-700">{crop.price_byn_per_ts} BYN</span>
                      )}
                    </td>

                    {/* Cost */}
                    <td className="py-3.5 px-4">
                      {isEditing ? (
                        <input
                          type="number"
                          step="50"
                          value={editCost}
                          onChange={(e) => setEditCost(Number(e.target.value))}
                          className="w-24 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-sm text-slate-900 outline-none focus:border-emerald-500"
                        />
                      ) : (
                        <span className="text-slate-700">{crop.cost_byn_per_ha} BYN</span>
                      )}
                    </td>

                    {/* Fert response */}
                    <td className="py-3.5 px-4">
                      {isEditing ? (
                        <input
                          type="number"
                          step="0.005"
                          value={editFertResponse}
                          onChange={(e) => setEditFertResponse(Number(e.target.value))}
                          className="w-20 bg-slate-100 border border-slate-200 rounded px-2 py-1 text-sm text-slate-900 outline-none focus:border-emerald-500"
                        />
                      ) : (
                        <span className="text-xs text-slate-500">+{crop.fert_response} ц/кг</span>
                      )}
                    </td>

                    {/* Max Area % */}
                    <td className="py-3.5 px-4">
                      {crop.max_area_pct < 100 ? (
                        <Badge variant="amber">до {crop.max_area_pct}%</Badge>
                      ) : (
                        <Badge variant="slate">Без лимита</Badge>
                      )}
                    </td>

                    {/* Rotation gap */}
                    <td className="py-3.5 px-4 text-xs text-slate-500">
                      {crop.rotation_gap_years > 0 ? `≥ ${crop.rotation_gap_years} года` : '0 (бессменно)'}
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      {isEditing ? (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => saveEdit(crop)}
                            className="p-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white transition-colors"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={cancelEdit}
                            className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-500 transition-colors"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => startEdit(crop)}
                          className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 hover:text-emerald-700 transition-colors"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Advanced Agronomy Visualizations */}
      <div className="space-y-6">
        <NPKResponseChart />
        <CropCalendarGantt />
      </div>
    </div>
  );
};

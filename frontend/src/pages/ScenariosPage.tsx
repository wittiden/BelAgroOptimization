import React, { useState } from 'react';
import { Layers, Plus, Copy, Trash2, CheckCircle2, Calendar, TrendingUp } from 'lucide-react';
import { Badge } from '../components/common/Badge';
import { ConfirmModal } from '../components/common/ConfirmModal';
import { useScenario } from '../context/ScenarioContext';
import { useToast } from '../context/ToastContext';
import { api } from '../api/client';

export const ScenariosPage: React.FC = () => {
  const { scenarios, refreshScenarios, setSelectedScenarioId } = useScenario();
  const { success, error } = useToast();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newScenarioName, setNewScenarioName] = useState('');
  const [newScenarioDesc, setNewScenarioDesc] = useState('');
  const [makeActive, setMakeActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Deletion modal state
  const [scenarioToDelete, setScenarioToDelete] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newScenarioName.trim()) return;

    try {
      setIsSubmitting(true);
      const created = await api.createScenario({
        name: newScenarioName,
        description: newScenarioDesc,
        is_active: makeActive,
      });
      setIsModalOpen(false);
      setNewScenarioName('');
      setNewScenarioDesc('');
      await refreshScenarios();
      if (makeActive) {
        setSelectedScenarioId(created.scenario_id);
      }
      success(`Сценарий «${created.name}» успешно создан`);
    } catch (err) {
      error(`Ошибка создания: ${err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleActivate = async (id: string) => {
    try {
      const activated = await api.activateScenario(id);
      setSelectedScenarioId(id);
      await refreshScenarios();
      success(`Сценарий «${activated.name}» назначен активным`);
    } catch (err) {
      error(`Ошибка активации: ${err}`);
    }
  };

  const handleClone = async (id: string) => {
    try {
      const cloned = await api.cloneScenario(id);
      await refreshScenarios();
      success(`Создана копия: «${cloned.name}»`);
    } catch (err) {
      error(`Ошибка клонирования: ${err}`);
    }
  };

  const confirmDelete = async () => {
    if (!scenarioToDelete) return;
    try {
      await api.deleteScenario(scenarioToDelete);
      await refreshScenarios();
      success('Сценарий успешно удален');
    } catch (err) {
      error(`Ошибка удаления: ${err}`);
    } finally {
      setScenarioToDelete(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Create Button */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-emerald-700" />
            <span>Управление сценариями оптимизации</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Создавайте альтернативные сценарии («What-if» анализ) для моделирования различных агроклиматических и экономических условий
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-md shadow-emerald-950 transition-all hover:scale-102"
        >
          <Plus className="w-4 h-4" />
          <span>Новый сценарий</span>
        </button>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {scenarios.map((s) => (
          <div
            key={s.scenario_id}
            className={`bg-white/80 rounded-xl border p-5 flex flex-col justify-between transition-all ${
              s.is_active
                ? 'border-emerald-500/50 shadow-lg shadow-emerald-950/20 ring-1 ring-emerald-500/30'
                : 'border-slate-200 hover:border-slate-200'
            }`}
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-3">
                <h3 className="font-bold text-base text-slate-900 line-clamp-1">{s.name}</h3>
                {s.is_active ? (
                  <Badge variant="emerald" className="gap-1 flex items-center">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>Активный</span>
                  </Badge>
                ) : (
                  <Badge variant="slate">Черновик</Badge>
                )}
              </div>

              <p className="text-xs text-slate-500 min-h-[36px] line-clamp-2">
                {s.description || 'Описание не указано'}
              </p>

              <div className="mt-4 pt-3 border-t border-slate-200 space-y-2 text-xs text-slate-500">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Итоговая прибыль:</span>
                  </span>
                  <span className="font-bold text-slate-800">
                    {s.last_profit ? `${s.last_profit.toLocaleString('ru-RU')} BYN` : 'Не рассчитан'}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    <span>Создан:</span>
                  </span>
                  <span>{new Date(s.created_at).toLocaleDateString('ru-RU')}</span>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500">
                  <span>Полей: {s.fields_count || 5}</span>
                  <span>Культур: {s.crops_count || 9}</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-5 pt-3 border-t border-slate-200 flex items-center justify-between gap-2">
              {!s.is_active && (
                <button
                  onClick={() => handleActivate(s.scenario_id)}
                  className="text-xs font-semibold text-emerald-700 hover:text-emerald-300 bg-emerald-950/40 hover:bg-emerald-900/50 px-3 py-1.5 rounded-lg transition-colors"
                >
                  Сделать активным
                </button>
              )}
              {s.is_active && (
                <span className="text-xs font-medium text-emerald-700/80">Используется в расчетах</span>
              )}

              <div className="flex items-center gap-1">
                <button
                  title="Клонировать сценарий"
                  onClick={() => handleClone(s.scenario_id)}
                  className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <Copy className="w-4 h-4" />
                </button>
                <button
                  title="Удалить сценарий"
                  onClick={() => setScenarioToDelete(s.scenario_id)}
                  className="p-1.5 text-rose-700 hover:text-rose-300 hover:bg-rose-950/40 rounded-lg transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <ConfirmModal
        isOpen={scenarioToDelete !== null}
        title="Удаление сценария"
        message="Вы уверены, что хотите удалить данный сценарий оптимизации? Все связанные расчеты и параметры будут безвозвратно удалены."
        confirmLabel="Удалить"
        cancelLabel="Отмена"
        isDestructive={true}
        onConfirm={confirmDelete}
        onCancel={() => setScenarioToDelete(null)}
      />

      {/* Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Создание сценария</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Название сценария *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Например: Засушливое лето 2026 / Высокие цены на молоко"
                  value={newScenarioName}
                  onChange={(e) => setNewScenarioName(e.target.value)}
                  className="w-full bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Описание и гипотеза
                </label>
                <textarea
                  rows={3}
                  placeholder="Опишите предпосылки сценария (климат, цены, технологии)..."
                  value={newScenarioDesc}
                  onChange={(e) => setNewScenarioDesc(e.target.value)}
                  className="w-full bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder-slate-500 outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="makeActive"
                  checked={makeActive}
                  onChange={(e) => setMakeActive(e.target.checked)}
                  className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500 bg-slate-100 border-slate-200"
                />
                <label htmlFor="makeActive" className="text-xs text-slate-700 select-none cursor-pointer">
                  Сразу назначить сценарий активным
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white shadow-md shadow-emerald-950 transition-all disabled:opacity-50"
                >
                  {isSubmitting ? 'Создание...' : 'Создать сценарий'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

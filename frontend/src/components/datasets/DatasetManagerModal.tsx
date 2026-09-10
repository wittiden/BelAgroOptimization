import React, { useState, useRef } from 'react';
import { createPortal } from 'react-dom';
import * as XLSX from 'xlsx';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Database,
  Check,
  X,
  FileText,
  Building2,
} from 'lucide-react';
import { useToast } from '../../context/ToastContext';
import { useScenario } from '../../context/ScenarioContext';
import type { FieldData } from '../../types';

interface DatasetManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDatasetApplied?: (fields: Partial<FieldData>[]) => void;
}

interface ParsedFieldRow {
  code: string;
  area_ha: number;
  soil_type: string;
  soil_fertility: number;
  isValid: boolean;
  validationErrors: string[];
}

interface FarmPreset {
  id: string;
  name: string;
  region: string;
  areaHa: number;
  fieldsCount: number;
  soilType: string;
  description: string;
  fields: Array<{
    code: string;
    area_ha: number;
    soil_type: string;
    soil_fertility: number;
  }>;
}

const FARM_PRESETS: FarmPreset[] = [
  {
    id: 'optimum_agro',
    name: 'СПК «Оптимум-Агро»',
    region: 'Минская обл., Несвижский р-н',
    areaHa: 900,
    fieldsCount: 5,
    soilType: 'Чернозёмы окультуренные / суглинки',
    description: 'Эталонное семеноводческое хозяйство центральной Беларуси с интенсивной химизацией.',
    fields: [
      { code: 'field1', area_ha: 150.0, soil_type: 'чернозём', soil_fertility: 1.2 },
      { code: 'field2', area_ha: 200.0, soil_type: 'суглинок', soil_fertility: 1.0 },
      { code: 'field3', area_ha: 180.0, soil_type: 'супесь', soil_fertility: 0.9 },
      { code: 'field4', area_ha: 120.0, soil_type: 'чернозём', soil_fertility: 1.1 },
      { code: 'field5', area_ha: 250.0, soil_type: 'суглинок', soil_fertility: 1.0 },
    ],
  },
  {
    id: 'snov_agro',
    name: 'Агрокомбинат «Снов»',
    region: 'Минская обл., Несвижский р-н',
    areaHa: 1450,
    fieldsCount: 8,
    soilType: 'Высокоплодородные тяжелосуглинистые почвы',
    description: 'Крупнейший агрохолдинг мясо-молочного направления с замкнутым кормовым циклом.',
    fields: [
      { code: 'поле_север_1', area_ha: 220.0, soil_type: 'суглинок', soil_fertility: 1.25 },
      { code: 'поле_север_2', area_ha: 180.0, soil_type: 'чернозём', soil_fertility: 1.30 },
      { code: 'поле_пойменное', area_ha: 260.0, soil_type: 'чернозём', soil_fertility: 1.20 },
      { code: 'поле_центральное', area_ha: 190.0, soil_type: 'суглинок', soil_fertility: 1.15 },
      { code: 'поле_южное_1', area_ha: 150.0, soil_type: 'суглинок', soil_fertility: 1.10 },
      { code: 'поле_южное_2', area_ha: 140.0, soil_type: 'супесь', soil_fertility: 0.95 },
      { code: 'поле_запад_клин', area_ha: 170.0, soil_type: 'суглинок', soil_fertility: 1.05 },
      { code: 'поле_восток_травы', area_ha: 140.0, soil_type: 'суглинок', soil_fertility: 1.00 },
    ],
  },
  {
    id: 'vasilishki',
    name: 'ОАО «Василишки»',
    region: 'Гродненская обл., Щучинский р-н',
    areaHa: 1100,
    fieldsCount: 6,
    soilType: 'Дерново-подзолистые супеси и суглинки',
    description: 'Типичное хозяйство Принеманья со сложным почвенным рельефом и высокой долей озимого рапса.',
    fields: [
      { code: 'участок_1', area_ha: 210.0, soil_type: 'суглинок', soil_fertility: 1.05 },
      { code: 'участок_2', area_ha: 190.0, soil_type: 'супесь', soil_fertility: 0.88 },
      { code: 'участок_3', area_ha: 230.0, soil_type: 'суглинок', soil_fertility: 1.00 },
      { code: 'участок_4', area_ha: 160.0, soil_type: 'супесь', soil_fertility: 0.92 },
      { code: 'участок_5', area_ha: 170.0, soil_type: 'суглинок', soil_fertility: 1.02 },
      { code: 'участок_6', area_ha: 140.0, soil_type: 'чернозём', soil_fertility: 1.12 },
    ],
  },
];

export const DatasetManagerModal: React.FC<DatasetManagerModalProps> = ({
  isOpen,
  onClose,
  onDatasetApplied,
}) => {
  const { success, error, info } = useToast();
  const { activeScenario } = useScenario();

  const [activeTab, setActiveTab] = useState<'upload' | 'presets'>('upload');
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [parsedRows, setParsedRows] = useState<ParsedFieldRow[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  // Process File (Excel or CSV)
  const handleFileProcess = async (file: File) => {
    setIsProcessing(true);
    setFileName(file.name);

    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];
      const json: any[] = XLSX.utils.sheet_to_json(worksheet, { defval: '' });

      if (!json || json.length === 0) {
        throw new Error('Файл пуст или содержит нераспознанную структуру табличных данных');
      }

      const rows: ParsedFieldRow[] = json.map((row: any, idx: number) => {
        // Auto-match columns
        const code = String(
          row['code'] ||
            row['Код поля'] ||
            row['Поле'] ||
            row['Номер поля'] ||
            row['Название'] ||
            `field_${idx + 1}`
        ).trim();

        const rawArea =
          row['area_ha'] ||
          row['area'] ||
          row['Площадь (га)'] ||
          row['Площадь'] ||
          row['Площадь, га'] ||
          '0';
        const area_ha = parseFloat(String(rawArea).replace(',', '.')) || 0;

        const rawSoil =
          row['soil_type'] ||
          row['soil'] ||
          row['Тип почвы'] ||
          row['Почва'] ||
          'суглинок';
        const soil_type = String(rawSoil).trim().toLowerCase();

        const rawFert =
          row['soil_fertility'] ||
          row['fertility'] ||
          row['Балл плодородия'] ||
          row['Плодородие'] ||
          '1.0';
        let soil_fertility = parseFloat(String(rawFert).replace(',', '.')) || 1.0;
        // Normalize if given in bonitet scale (e.g. 38 -> 1.15)
        if (soil_fertility > 10) {
          soil_fertility = Number((soil_fertility / 35.0).toFixed(2));
        }

        const errors: string[] = [];
        if (!code) errors.push('Отсутствует код поля');
        if (area_ha <= 0) errors.push('Площадь должна быть > 0 га');
        if (soil_fertility < 0.4 || soil_fertility > 2.0)
          errors.push('Коэф. плодородия вне диапазона [0.4 ... 2.0]');

        return {
          code,
          area_ha,
          soil_type,
          soil_fertility,
          isValid: errors.length === 0,
          validationErrors: errors,
        };
      });

      setParsedRows(rows);
      const validCount = rows.filter((r) => r.isValid).length;
      if (validCount === rows.length) {
        success(`Успешно обработано ${rows.length} полей из файла «${file.name}»`);
      } else {
        info(`Файл прочитан: ${validCount} из ${rows.length} полей валидны. Исправьте ошибки перед применением.`);
      }
    } catch (err: any) {
      error(`Ошибка разбора файла: ${err.message || err}`);
      setParsedRows([]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  // Download Sample XLSX Template
  const handleDownloadXlsxTemplate = () => {
    const templateData = [
      {
        'Код поля': 'field_nord_1',
        'Площадь (га)': 180.5,
        'Тип почвы': 'суглинок',
        'Балл плодородия': 1.15,
      },
      {
        'Код поля': 'field_nord_2',
        'Площадь (га)': 220.0,
        'Тип почвы': 'чернозём',
        'Балл плодородия': 1.28,
      },
      {
        'Код поля': 'field_south_3',
        'Площадь (га)': 140.0,
        'Тип почвы': 'супесь',
        'Балл плодородия': 0.90,
      },
      {
        'Код поля': 'field_east_4',
        'Площадь (га)': 260.0,
        'Тип почвы': 'суглинок',
        'Балл плодородия': 1.05,
      },
    ];

    const ws = XLSX.utils.json_to_sheet(templateData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Поля_Шаблон');
    XLSX.writeFile(wb, 'belagro_fields_template.xlsx');
    success('Шаблон таблицы полей .XLSX загружен');
  };

  // Download Sample CSV Template
  const handleDownloadCsvTemplate = () => {
    const csvContent = [
      '\uFEFFКод поля;Площадь (га);Тип почвы;Балл плодородия',
      'field_nord_1;180.5;суглинок;1.15',
      'field_nord_2;220.0;чернозём;1.28',
      'field_south_3;140.0;супесь;0.90',
      'field_east_4;260.0;суглинок;1.05',
    ].join('\r\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'belagro_fields_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    success('Шаблон таблицы полей .CSV загружен');
  };

  // Apply parsed rows
  const handleApplyDataset = () => {
    const validRows = parsedRows.filter((r) => r.isValid);
    if (validRows.length === 0) {
      error('Нет валидных строк для применения');
      return;
    }

    if (onDatasetApplied) {
      onDatasetApplied(validRows);
    }
    success(`Датасет (${validRows.length} полей) успешно применён к текущей сессии!`);
    onClose();
  };

  // Apply Preset Farm
  const handleApplyPreset = (preset: FarmPreset) => {
    if (onDatasetApplied) {
      onDatasetApplied(preset.fields);
    }
    success(`Датасет хозяйства «${preset.name}» (${preset.areaHa} га) успешно загружен!`);
    onClose();
  };

  const totalAreaParsed = parsedRows.reduce((acc, r) => acc + (r.isValid ? r.area_ha : 0), 0);
  const validCount = parsedRows.filter((r) => r.isValid).length;

  return createPortal(
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 backdrop-blur-xs flex justify-center items-center p-4 sm:p-6">
      <div className="relative w-full max-w-3xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Менеджер агрономических датасетов</h2>
              <p className="text-xs text-slate-500">
                Загрузка собственных контуров полей (Excel / CSV) или выбор эталонных хозяйств Беларуси
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6 pt-2">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'upload'
                ? 'border-emerald-600 text-emerald-700 font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <UploadCloud className="w-4 h-4" />
            <span>Загрузка файла (Excel / CSV)</span>
          </button>

          <button
            onClick={() => setActiveTab('presets')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'presets'
                ? 'border-emerald-600 text-emerald-700 font-semibold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>Готовые датасеты хозяйств РБ</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {activeTab === 'upload' ? (
            <>
              {/* Drag and drop area */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                  dragActive
                    ? 'border-emerald-500 bg-emerald-50/50'
                    : 'border-slate-200 hover:border-emerald-500 bg-slate-50/50 hover:bg-emerald-50/20'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileProcess(e.target.files[0]);
                    }
                  }}
                  className="hidden"
                />

                <div className="flex flex-col items-center justify-center gap-2">
                  <div className="p-3 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div className="text-sm font-semibold text-slate-800">
                    {isProcessing ? 'Обработка файла...' : 'Перетащите файл .XLSX или .CSV сюда'}
                  </div>
                  <p className="text-xs text-slate-500 max-w-sm">
                    Поддерживаются файлы Excel Microsoft 365, LibreOffice Calc и CSV с разделителями «;» или «,»
                  </p>
                </div>
              </div>

              {/* Template Download Chips */}
              <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                <span className="text-slate-500">Нужен пример структуры колонок?</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleDownloadXlsxTemplate}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-md transition-colors font-medium text-xs"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-700" />
                    <span>Шаблон Excel (.xlsx)</span>
                  </button>
                  <button
                    onClick={handleDownloadCsvTemplate}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-md transition-colors font-medium text-xs"
                  >
                    <FileText className="w-3.5 h-3.5 text-sky-700" />
                    <span>Шаблон CSV</span>
                  </button>
                </div>
              </div>

              {/* Table Preview */}
              {parsedRows.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-800">
                        Предпросмотр данных ({fileName}):
                      </span>
                      <span className="px-2 py-0.5 rounded text-[11px] bg-emerald-950/80 text-emerald-700 border border-emerald-500/30">
                        {validCount} валидных из {parsedRows.length}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 font-mono">
                        {totalAreaParsed.toFixed(1)} га суммарно
                      </span>
                    </div>
                  </div>

                  <div className="border border-slate-200 rounded-lg overflow-hidden max-h-56 overflow-y-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-slate-950 text-slate-500 font-medium sticky top-0 border-b border-slate-200">
                        <tr>
                          <th className="py-2 px-3">Код поля</th>
                          <th className="py-2 px-3 text-right">Площадь (га)</th>
                          <th className="py-2 px-3">Тип почвы</th>
                          <th className="py-2 px-3 text-right">Плодородие</th>
                          <th className="py-2 px-3 text-center">Статус</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                        {parsedRows.map((r, i) => (
                          <tr key={i} className="hover:bg-slate-100/30">
                            <td className="py-2 px-3 font-mono font-medium text-slate-800">
                              {r.code}
                            </td>
                            <td className="py-2 px-3 text-right font-mono text-slate-700">
                              {r.area_ha.toFixed(1)}
                            </td>
                            <td className="py-2 px-3 text-slate-700 capitalize">{r.soil_type}</td>
                            <td className="py-2 px-3 text-right font-mono text-slate-700">
                              {r.soil_fertility.toFixed(2)}
                            </td>
                            <td className="py-2 px-3 text-center">
                              {r.isValid ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-700 inline" />
                              ) : (
                                <span
                                  title={r.validationErrors.join(', ')}
                                  className="inline-flex items-center gap-1 text-rose-400 cursor-help"
                                >
                                  <AlertTriangle className="w-4 h-4" />
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Presets Tab */
            <div className="space-y-4">
              <p className="text-xs text-slate-500">
                Выберите агропромышленный комплекс с предварительно откалиброванными контурами пашни и
                почвенно-климатическими паспортами:
              </p>

              <div className="grid grid-cols-1 gap-3.5">
                {FARM_PRESETS.map((farm) => (
                  <div
                    key={farm.id}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50 hover:border-emerald-500 hover:bg-emerald-50/20 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">{farm.name}</span>
                        <span className="text-[11px] px-2 py-0.5 rounded-md font-mono bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                          {farm.areaHa} га • {farm.fieldsCount} полей
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 flex items-center gap-1.5">
                        <span>{farm.region}</span>
                        <span>•</span>
                        <span className="text-slate-700">{farm.soilType}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 max-w-lg">{farm.description}</p>
                    </div>

                    <button
                      onClick={() => handleApplyPreset(farm)}
                      className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold transition-colors shrink-0 flex items-center gap-1.5 shadow-sm"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Загрузить хозяйство</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100 bg-slate-50">
          <div className="text-xs text-slate-500">
            {activeScenario && (
              <span>
                Активный сценарий: <b className="text-slate-800">{activeScenario.name}</b>
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-700 hover:text-slate-900 hover:bg-slate-200 rounded-lg transition-colors"
            >
              Отмена
            </button>
            {activeTab === 'upload' && parsedRows.length > 0 && (
              <button
                onClick={handleApplyDataset}
                disabled={validCount === 0}
                className="px-4 py-2 text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
              >
                <Check className="w-4 h-4" />
                <span>Применить ({validCount} полей)</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

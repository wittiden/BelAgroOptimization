import type {
  Scenario,
  FieldData,
  CropData,
  LivestockData,
  FeedData,
  WeatherSummary,
  OptimizationResult,
  OptimizationJobStatus,
  DashboardSummary,
} from '../types';

const BASE_URL = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Ошибка запроса (${res.status}): ${errorBody || res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => fetchJson<DashboardSummary>('/dashboard/summary'),

  // Scenarios
  getScenarios: () => fetchJson<Scenario[]>('/scenarios'),
  getScenario: (id: string) => fetchJson<Scenario>(`/scenarios/${id}`),
  createScenario: (data: { name: string; description?: string; is_active?: boolean }) =>
    fetchJson<Scenario>('/scenarios', { method: 'POST', body: JSON.stringify(data) }),
  updateScenario: (id: string, data: Partial<{ name: string; description: string; is_active: boolean }>) =>
    fetchJson<Scenario>(`/scenarios/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  activateScenario: (id: string) =>
    fetchJson<Scenario>(`/scenarios/${id}/activate`, { method: 'POST' }),
  cloneScenario: (id: string) =>
    fetchJson<Scenario>(`/scenarios/${id}/clone`, { method: 'POST' }),
  deleteScenario: async (id: string) => {
    await fetch(`${BASE_URL}/scenarios/${id}`, { method: 'DELETE' });
  },

  // Data / Parameters
  getFields: (scenarioId: string) => fetchJson<FieldData[]>(`/scenarios/${scenarioId}/fields`),
  updateField: (scenarioId: string, fieldId: string, data: Partial<FieldData>) =>
    fetchJson<FieldData>(`/scenarios/${scenarioId}/fields/${fieldId}`, { method: 'PUT', body: JSON.stringify(data) }),

  getCrops: (scenarioId: string) => fetchJson<CropData[]>(`/scenarios/${scenarioId}/crops`),
  updateCrop: (scenarioId: string, cropCode: string, data: Partial<CropData>) =>
    fetchJson<CropData>(`/scenarios/${scenarioId}/crops/${cropCode}`, { method: 'PUT', body: JSON.stringify(data) }),

  getLivestock: (scenarioId: string) => fetchJson<LivestockData[]>(`/scenarios/${scenarioId}/livestock`),
  updateLivestock: (scenarioId: string, animalType: string, data: Partial<LivestockData>) =>
    fetchJson<LivestockData>(`/scenarios/${scenarioId}/livestock/${animalType}`, { method: 'PUT', body: JSON.stringify(data) }),

  getFeeds: (scenarioId: string) => fetchJson<FeedData[]>(`/scenarios/${scenarioId}/feeds`),
  updateFeed: (scenarioId: string, feedType: string, data: Partial<FeedData>) =>
    fetchJson<FeedData>(`/scenarios/${scenarioId}/feeds/${feedType}`, { method: 'PUT', body: JSON.stringify(data) }),

  getWeather: (scenarioId: string) => fetchJson<WeatherSummary[]>(`/scenarios/${scenarioId}/weather`),

  // Optimization
  runOptimization: (scenarioId?: string) =>
    fetchJson<OptimizationJobStatus>('/optimization/run', {
      method: 'POST',
      body: JSON.stringify({ scenario_id: scenarioId }),
    }),
  getJobStatus: (jobId: string) => fetchJson<OptimizationJobStatus>(`/optimization/status/${jobId}`),
  getOptimizationResults: (scenarioId: string) => fetchJson<OptimizationResult>(`/optimization/results/${scenarioId}`),
  getPlots: () => fetchJson<{ plots: Array<{ name: string; url: string }> }>('/optimization/plots'),
};

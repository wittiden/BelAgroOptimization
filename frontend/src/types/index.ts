export interface Scenario {
  scenario_id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  last_profit: number | null;
  fields_count: number;
  crops_count: number;
}

export interface FieldData {
  field_data_id: string;
  scenario_id: string;
  field_id: string;
  code: string;
  area_ha: number;
  soil_type: string | null;
  soil_fertility: number;
}

export interface CropData {
  crop_data_id: string;
  crop_id: string;
  code: string;
  name: string | null;
  base_yield_tha: number;
  price_byn_per_ts: number;
  cost_byn_per_ha: number;
  seed_cost_byn_per_ha: number | null;
  max_area_pct: number;
  max_fert_kg: number;
  fert_cost_byn_per_kg: number;
  fert_response: number;
  sowing_months: number[] | null;
  harvest_months: number[] | null;
  vegetation_days: number | null;
  rotation_gap_years: number;
}

export interface LivestockData {
  livestock_data_id: string;
  scenario_id: string;
  animal_type: string;
  min_heads: number;
  max_heads: number;
  base_yield_kg: number;
  max_yield_kg: number;
  price_byn_per_kg: number;
  cost_summer_byn: number;
  cost_winter_byn: number;
  energy_cost_winter_byn: number;
}

export interface FeedData {
  feed_data_id: string;
  scenario_id: string;
  feed_type: string;
  price_byn_per_centner: number;
  cow_need: number;
  cattle_need: number;
  pig_need: number;
  cow_max: number;
  cattle_max: number;
  pig_max: number;
  milk_efficiency: number;
  beef_efficiency: number;
  pork_efficiency: number;
  diminishing_beta: number;
  winter_price_multiplier: number;
  summer_price_multiplier: number;
}

export interface WeatherSummary {
  year: number;
  temp_avg: number;
  rain_total: number;
  is_drought: boolean;
}

export interface CropAllocation {
  year: number;
  field_code: string;
  crop_code: string;
  area_ha: number;
  yield_ts: number;
  fert_kg: number;
}

export interface LivestockAllocation {
  year: number;
  animal_type: string;
  heads: number;
  milk_yield_summer_kg: number | null;
  milk_yield_winter_kg: number | null;
}

export interface FeedAllocation {
  year: number;
  feed_type: string;
  produced: number;
  consumed: number;
  surplus: number;
}

export interface YearResult {
  year: number;
  crop_profit: number;
  livestock_profit: number;
  total_profit: number;
  weather_temp?: number;
  weather_rain?: number;
  crop_areas: Record<string, number>;
  crop_profits: Record<string, number>;
  livestock_profits: Record<string, number>;
  livestock_heads: Record<string, number>;
  feed_balances: Record<string, { produced: number; needed: number; purchased: number; surplus: number }>;
}

export interface OptimizationResult {
  result_id: string;
  scenario_id: string;
  scenario_name: string;
  total_profit_byn: number;
  avg_annual_profit_byn: number;
  solver_status: string;
  solution_time_sec: number | null;
  created_at: string;
  years: YearResult[];
  crop_allocations: CropAllocation[];
  livestock_allocations: LivestockAllocation[];
  feed_allocations: FeedAllocation[];
  plots: string[];
}

export interface OptimizationJobStatus {
  job_id: string;
  scenario_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  logs: string[];
  started_at: string;
  finished_at?: string;
  execution_time_sec?: number;
}

export interface DashboardSummary {
  active_scenario_id: string | null;
  active_scenario_name: string | null;
  total_land_ha: number;
  fields_count: number;
  crops_count: number;
  livestock_types_count: number;
  last_optimized_at: string | null;
  last_total_profit: number | null;
  last_avg_profit: number | null;
  solver_status: string | null;
}

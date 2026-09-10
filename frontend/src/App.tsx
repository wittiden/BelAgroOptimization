import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ScenarioProvider } from './context/ScenarioContext';
import { ToastProvider } from './context/ToastContext';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ScenariosPage } from './pages/ScenariosPage';
import { FieldsPage } from './pages/FieldsPage';
import { CropsPage } from './pages/CropsPage';
import { LivestockPage } from './pages/LivestockPage';
import { FeedsPage } from './pages/FeedsPage';
import { WeatherPage } from './pages/WeatherPage';
import { OptimizationPage } from './pages/OptimizationPage';
import { ResultsPage } from './pages/ResultsPage';
import { ComparisonPage } from './pages/ComparisonPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ToastProvider>
        <ScenarioProvider>
          <Routes>
            <Route path="/" element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="scenarios" element={<ScenariosPage />} />
            <Route path="fields" element={<FieldsPage />} />
            <Route path="crops" element={<CropsPage />} />
            <Route path="livestock" element={<LivestockPage />} />
            <Route path="feeds" element={<FeedsPage />} />
            <Route path="weather" element={<WeatherPage />} />
            <Route path="optimization" element={<OptimizationPage />} />
            <Route path="results" element={<ResultsPage />} />
            <Route path="comparison" element={<ComparisonPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </ScenarioProvider>
    </ToastProvider>
  </BrowserRouter>
);
};

export default App;

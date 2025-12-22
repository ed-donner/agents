import React from 'react';
import ForecastChart from '../components/ForecastChart';

type Point = { date: string; forecastQuantity: number; };
const DashboardPage: React.FC = () => {
  const sample: Point[] = [
    { date: '2025-01-01', forecastQuantity: 120 },
    { date: '2025-02-01', forecastQuantity: 135 },
    { date: '2025-03-01', forecastQuantity: 150 },
    { date: '2025-04-01', forecastQuantity: 170 }
  ];
  return (
    <div>
      <h1>Dashboard</h1>
      <ForecastChart data={sample} />
    </div>
  );
};
export default DashboardPage;
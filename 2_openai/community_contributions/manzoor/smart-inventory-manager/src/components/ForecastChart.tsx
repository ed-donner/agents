import React from 'react';
type Point = { date: string; forecastQuantity: number; };
interface Props { data: Point[]; }
const ForecastChart: React.FC<Props> = ({ data }) => {
  const max = Math.max(...data.map(d => d.forecastQuantity), 1);
  return (
   <svg width="100%" height="150" viewBox={`0 0 ${data.length * 40} 150`} style={{ display: 'block' }}>
      {data.map((p, i) => (
        <rect key={i} x={i * 40 + 10} y={150 - (p.forecastQuantity / max) * 120} width={20} height={(p.forecastQuantity / max) * 120} fill="#4caf50" />
      ))}
    </svg>
  );
};
export default ForecastChart;
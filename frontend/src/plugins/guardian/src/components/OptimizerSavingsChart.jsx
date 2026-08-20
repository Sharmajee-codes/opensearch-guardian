import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

const OptimizerSavingsChart = ({ data }) => {
  // Transform data for charting - expect array of { category, monthly_savings, priority }
  const chartData = Array.isArray(data) ? data : [];

  // Sort by savings descending
  const sortedData = [...chartData].sort((a, b) =>
    (b.monthly_savings || 0) - (a.monthly_savings || 0)
  );

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={sortedData} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis dataKey="category" width={120} />
        <Tooltip formatter={(value: number) => [`$${value.toLocaleString()}/month`, 'Monthly Savings']} />
        <Legend verticalAlign="top" height={36} />
        <Bar
          dataKey="monthly_savings"
          radius={[0, 4, 4, 0]}
          fill="currentColor"
        >
          {sortedData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.priority === 'high' ? '#ef4444' : entry.priority === 'medium' ? '#f59e0b' : '#10b981'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default OptimizerSavingsChart;
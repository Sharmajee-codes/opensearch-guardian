import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

const CapacityProjectionChart = ({ data, metric, color = '#3b82f6' }) => {
  // data should be array of { date, current, projected_3m, projected_6m, projected_12m }
  const chartData = Array.isArray(data) ? data : [];

  // Transform to time-series format
  const timeSeriesData = chartData.map((d: any) => ({
    date: d.date || d.timestamp,
    current: d.current,
    projected_3m: d.projected_3_months || d.projected_3m,
    projected_6m: d.projected_6_months || d.projected_6m,
    projected_12m: d.projected_12_months || d.projected_12m
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={timeSeriesData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tickFormatter={(val) => new Date(val).toLocaleDateString()}
        />
        <YAxis />
        <Tooltip
          formatter={(value: number, name: string) => [
            value,
            name.replace('_', ' ').replace('m', ' months')
          ]}
        />
        <Legend verticalAlign="top" height={36} />
        <Line
          type="monotone"
          dataKey="current"
          stroke={color}
          strokeWidth={2}
          dot={false}
          name="Current"
        />
        <Line
          type="monotone"
          dataKey="projected_3m"
          stroke="#10b981"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="3 Months"
        />
        <Line
          type="monotone"
          dataKey="projected_6m"
          stroke="#f59e0b"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="6 Months"
        />
        <Line
          type="monotone"
          dataKey="projected_12m"
          stroke="#ef4444"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="12 Months"
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default CapacityProjectionChart;
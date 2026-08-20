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

const NodeMetricsChart = ({ data, metric, title, color = '#3b82f6' }) => {
  // Transform data for charting - data should be an array of { timestamp, value } objects
  const chartData = Array.isArray(data) ? data : [];

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" tickFormatter={(val) => new Date(val).toLocaleTimeString()} />
        <YAxis />
        <Tooltip />
        <Legend verticalAlign="top" height={36} />
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 6 }}
          name={title}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default NodeMetricsChart;
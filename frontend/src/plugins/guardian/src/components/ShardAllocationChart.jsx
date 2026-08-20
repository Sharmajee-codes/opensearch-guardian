import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend
} from 'recharts';

const COLORS = [
  '#10b981', // green - STARTED
  '#f59e0b', // yellow - RELOCATING
  '#8b5cf6', // purple - INITIALIZING
  '#ef4444', // red - UNASSIGNED
  '#3b82f6', // blue - other
];

const ShardAllocationChart = ({ data }) => {
  // Transform data for charting
  const stateCounts: Record<string, number> = {};

  if (Array.isArray(data)) {
    data.forEach((shard: any) => {
      const state = shard.routing?.state || 'unknown';
      stateCounts[state] = (stateCounts[state] || 0) + 1;
    });
  }

  const chartData = Object.entries(stateCounts).map(([name, value], index) => ({
    name,
    value,
    fill: COLORS[index % COLORS.length]
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={2}
          dataKey="value"
          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => [value, 'shards']} />
        <Legend verticalAlign="bottom" height={36} />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default ShardAllocationChart;
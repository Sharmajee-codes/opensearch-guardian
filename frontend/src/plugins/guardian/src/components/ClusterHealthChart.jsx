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

const ClusterHealthChart = ({ data }) => {
  // Transform data for charting
  const chartData = [
    {
      name: 'Active Primary',
      value: data.active_primary_shards || 0,
      fill: '#10b981' // green
    },
    {
      name: 'Active',
      value: data.active_shards || 0,
      fill: '#3b82f6' // blue
    },
    {
      name: 'Relocating',
      value: data.relocating_shards || 0,
      fill: '#f59e0b' // yellow
    },
    {
      name: 'Initializing',
      value: data.initializing_shards || 0,
      fill: '#8b5cf6' // purple
    },
    {
      name: 'Unassigned',
      value: data.unassigned_shards || 0,
      fill: '#ef4444' // red
    }
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend verticalAlign="top" height={36} />
        {chartData.map((entry, index) => (
          <Bar key={index} dataKey="value" fill={entry.fill} radius={[4, 4, 0, 0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

export default ClusterHealthChart;
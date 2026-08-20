import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LiveMonitoringPage } from '../src/pages/LiveMonitoring';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getLiveMonitoringData: jest.fn()
  }
}));

describe('LiveMonitoringPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getLiveMonitoringData.mockResolvedValueOnce({});
    
    render(<LiveMonitoringPage />);
    expect(screen.getByText(/loading live monitoring data/i)).toBeInTheDocument();
  });

  it('displays live monitoring data', async () => {
    const mockData = {
      timestamp: '2026-08-20T00:00:00Z',
      cluster: { status: 'green', node_count: 3 },
      nodes: [
        { name: 'node-1', cpu: 25, heap: 45, disk: 60 },
        { name: 'node-2', cpu: 30, heap: 50, disk: 55 }
      ],
      shards: { active: 50, unassigned: 0, relocating: 2 }
    };
    
    guardianApi.getLiveMonitoringData.mockResolvedValueOnce(mockData);
    
    render(<LiveMonitoringPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/live monitoring/i)).toBeInTheDocument();
      expect(screen.getByText('node-1')).toBeInTheDocument();
      expect(screen.getByText('node-2')).toBeInTheDocument();
      expect(screen.getByText('25%')).toBeInTheDocument(); // CPU
      expect(screen.getByText('45%')).toBeInTheDocument(); // Heap
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getLiveMonitoringData.mockRejectedValueOnce(new Error('API Error'));
    
    render(<LiveMonitoringPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

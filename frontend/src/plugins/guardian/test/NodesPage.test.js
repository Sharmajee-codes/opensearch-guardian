import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { NodesPage } from '../src/pages/Nodes';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getNodesStats: jest.fn()
  }
}));

describe('NodesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getNodesStats.mockResolvedValueOnce({ nodes: [] });
    
    render(<NodesPage />);
    expect(screen.getByText(/loading node statistics/i)).toBeInTheDocument();
  });

  it('renders empty state when no nodes', async () => {
    guardianApi.getNodesStats.mockResolvedValueOnce({ nodes: [] });
    
    render(<NodesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('No nodes found')).toBeInTheDocument();
    });
  });

  it('displays node statistics', async () => {
    // Use 95% heap usage to trigger CRITICAL (> 0.9)
    const mockNodes = {
      nodes: [
        {
          name: 'node-1',
          jvm: {
            mem_heap_used_in_bytes: 9500000000,
            mem_heap_max_in_bytes: 10000000000
          },
          os: {
            cpu: 87,
            load_average: { '1m': 4.5 }
          },
          fs: [
            {
              total_in_bytes: 100000000000,
              available_in_bytes: 5000000000
            }
          ],
          transport: {
            tx_count: 1000,
            rx_count: 5000
          }
        }
      ]
    };
    
    guardianApi.getNodesStats.mockResolvedValueOnce(mockNodes);
    
    render(<NodesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('node-1')).toBeInTheDocument();
      expect(screen.getByText(/jvm heap/i)).toBeInTheDocument();
      expect(screen.getByText(/95\.0/i)).toBeInTheDocument();
      expect(screen.getByText('CRITICAL')).toBeInTheDocument();
      expect(screen.getByText(/cpu usage/i)).toBeInTheDocument();
      expect(screen.getByText('87%')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getNodesStats.mockRejectedValueOnce(new Error('API Error'));
    
    render(<NodesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ShardsPage } from '../src/pages/Shards';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getShardsStats: jest.fn()
  }
}));

describe('ShardsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getShardsStats.mockResolvedValueOnce({ shards: [] });
    
    render(<ShardsPage />);
    expect(screen.getByText(/loading shards statistics/i)).toBeInTheDocument();
  });

  it('renders empty state when no shards', async () => {
    guardianApi.getShardsStats.mockResolvedValueOnce({ shards: [] });
    
    render(<ShardsPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no shards found/i)).toBeInTheDocument();
    });
  });

  it('displays shard statistics', async () => {
    const mockShards = {
      shards: [
        {
          index: 'test-index-1',
          shard: 0,
          primary: true,
          state: 'STARTED',
          node: 'node-1'
        }
      ]
    };
    
    guardianApi.getShardsStats.mockResolvedValueOnce(mockShards);
    
    render(<ShardsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-index-1')).toBeInTheDocument();
      expect(screen.getByText(/STARTED/i)).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getShardsStats.mockRejectedValueOnce(new Error('API Error'));
    
    render(<ShardsPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

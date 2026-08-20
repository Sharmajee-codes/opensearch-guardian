import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { IndicesPage } from '../src/pages/Indices';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getIndicesStats: jest.fn()
  }
}));

describe('IndicesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getIndicesStats.mockResolvedValueOnce({ indices: [] });
    
    render(<IndicesPage />);
    expect(screen.getByText(/loading indices statistics/i)).toBeInTheDocument();
  });

  it('renders empty state when no indices', async () => {
    guardianApi.getIndicesStats.mockResolvedValueOnce({ indices: [] });
    
    render(<IndicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no indices found/i)).toBeInTheDocument();
    });
  });

  it('displays index statistics', async () => {
    const mockIndices = {
      indices: [
        {
          name: 'test-index-1',
          health: 'green',
          status: 'open',
          docs_count: 10000,
          store_size: '1gb',
          primary_shards: 5,
          replica_shards: 1
        }
      ]
    };
    
    guardianApi.getIndicesStats.mockResolvedValueOnce(mockIndices);
    
    render(<IndicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('test-index-1')).toBeInTheDocument();
      expect(screen.getByText(/green/i)).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getIndicesStats.mockRejectedValueOnce(new Error('API Error'));
    
    render(<IndicesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

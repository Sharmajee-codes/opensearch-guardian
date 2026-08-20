import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { HealthPage } from '../src/pages/Health';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getClusterHealth: jest.fn()
  }
}));

describe('HealthPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getClusterHealth.mockResolvedValueOnce({});
    
    render(<HealthPage />);
    expect(screen.getByText(/loading health data/i)).toBeInTheDocument();
  });

  it('renders cluster health data', async () => {
    const mockHealth = {
      status: 'yellow',
      number_of_nodes: 5,
      active_shards: 90,
      unassigned_shards: 5
    };
    
    guardianApi.getClusterHealth.mockResolvedValueOnce(mockHealth);
    
    render(<HealthPage />);
    
    await waitFor(() => {
      // The description text is inside the EuiCardDescription div
      expect(screen.getByText(/nodes: 5/i)).toBeInTheDocument();
      expect(screen.getByText(/shards: 95/i)).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getClusterHealth.mockRejectedValueOnce(new Error('API Error'));
    
    render(<HealthPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

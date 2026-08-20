import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { CapacityPage } from '../src/pages/Capacity';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getCapacityPlanning: jest.fn()
  }
}));

describe('CapacityPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getCapacityPlanning.mockResolvedValueOnce({});
    
    render(<CapacityPage />);
    expect(screen.getByText(/loading capacity planning data/i)).toBeInTheDocument();
  });

  it('renders with forecast period control', async () => {
    const mockData = {
      utilization: {},
      recommendations: []
    };
    guardianApi.getCapacityPlanning.mockResolvedValueOnce(mockData);
    
    render(<CapacityPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Forecast period:')).toBeInTheDocument();
      expect(screen.getByText('Update Forecast')).toBeInTheDocument();
    });
  });

  it('updates forecast when number input changes', async () => {
    const mockData = { utilization: {}, recommendations: [] };
    guardianApi.getCapacityPlanning.mockResolvedValueOnce(mockData);
    
    render(<CapacityPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Forecast period:')).toBeInTheDocument();
    });
    
    const input = screen.getByRole('spinbutton');
    fireEvent.change(input, { target: { value: '60' } });
    
    expect(guardianApi.getCapacityPlanning).toHaveBeenCalledWith(60);
  });

  it('displays utilization data', async () => {
    const mockData = {
      utilization: {
        'cpu': { current: 45.2, projected: 62.1 },
        'memory': { current: 78.5, projected: 85.3 },
        'disk': { current: 55.0, projected: 60.2 }
      },
      recommendations: []
    };
    
    guardianApi.getCapacityPlanning.mockResolvedValueOnce(mockData);
    
    render(<CapacityPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/resource utilization/i)).toBeInTheDocument();
      expect(screen.getByText('45.2%')).toBeInTheDocument(); // CPU current
      expect(screen.getByText('62.1%')).toBeInTheDocument(); // CPU projected
    });
  });

  it('displays scaling recommendations', async () => {
    const mockData = {
      utilization: {},
      recommendations: [
        {
          title: 'Scale up data nodes',
          type: 'scale_up',
          urgency: 'high',
          impact: 'high',
          action: 'Increase node count',
          safety_level: 'approval_required'
        }
      ]
    };
    
    guardianApi.getCapacityPlanning.mockResolvedValueOnce(mockData);
    
    render(<CapacityPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Scale up data nodes')).toBeInTheDocument();
      expect(screen.getByText('SCALE UP')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getCapacityPlanning.mockRejectedValueOnce(new Error('API Error'));
    
    render(<CapacityPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

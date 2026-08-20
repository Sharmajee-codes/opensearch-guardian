import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { OptimizerPage } from '../src/pages/Optimizer';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getOptimizationAdvice: jest.fn(),
    runOptimizationAnalysis: jest.fn()
  }
}));

describe('OptimizerPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getOptimizationAdvice.mockResolvedValueOnce({ recommendations: [] });
    
    render(<OptimizerPage />);
    expect(screen.getByText(/loading optimization recommendations/i)).toBeInTheDocument();
  });

  it('renders empty state when no recommendations', async () => {
    guardianApi.getOptimizationAdvice.mockResolvedValueOnce({ recommendations: [] });
    
    render(<OptimizerPage />);
    
    await waitFor(() => {
      expect(screen.getByText('No optimization recommendations available')).toBeInTheDocument();
    });
  });

  it('displays optimization recommendations', async () => {
    const mockRecommendations = {
      recommendations: [
        {
          title: 'Reduce shard count',
          type: 'shard',
          impact: 'high',
          estimated_monthly_savings_usd: 150,
          confidence: 0.85,
          confidence_level: 'high',
          safety_level: 'safe_reversible',
          description: 'Merge small shards to reduce overhead'
        }
      ]
    };
    
    guardianApi.getOptimizationAdvice.mockResolvedValueOnce(mockRecommendations);
    
    render(<OptimizerPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Reduce shard count')).toBeInTheDocument();
      expect(screen.getByText(/Total Recommendations:/i)).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText(/Estimated Monthly Savings:/i)).toBeInTheDocument();
      expect(screen.getByText('$150')).toBeInTheDocument();
    });
  });

  it('calls runOptimizationAnalysis when button is clicked', async () => {
    const mockRecommendations = { recommendations: [] };
    guardianApi.getOptimizationAdvice.mockResolvedValueOnce(mockRecommendations);
    guardianApi.runOptimizationAnalysis.mockResolvedValueOnce(mockRecommendations);
    
    render(<OptimizerPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Run Optimization')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByText('Run Optimization'));
    
    expect(guardianApi.runOptimizationAnalysis).toHaveBeenCalledTimes(1);
  });

  it('shows error when API fails', async () => {
    guardianApi.getOptimizationAdvice.mockRejectedValueOnce(new Error('API Error'));
    
    render(<OptimizerPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

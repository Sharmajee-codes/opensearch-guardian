import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { RecommendationsPage } from '../src/pages/Recommendations';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getRecommendations: jest.fn()
  }
}));

describe('RecommendationsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getRecommendations.mockResolvedValueOnce({ recommendations: [] });
    
    render(<RecommendationsPage />);
    expect(screen.getByText(/loading recommendations/i)).toBeInTheDocument();
  });

  it('renders empty state when no recommendations', async () => {
    guardianApi.getRecommendations.mockResolvedValueOnce({ recommendations: [] });
    
    render(<RecommendationsPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no recommendations/i)).toBeInTheDocument();
    });
  });

  it('displays recommendations list', async () => {
    const mockRecs = {
      recommendations: [
        {
          title: 'Merge small shards',
          type: 'shard',
          impact: 'high',
          estimated_monthly_savings_usd: 200,
          confidence: 0.9,
          confidence_level: 'high',
          safety_level: 'safe_reversible',
          action: 'Run forcemerge'
        }
      ]
    };
    
    guardianApi.getRecommendations.mockResolvedValueOnce(mockRecs);
    
    render(<RecommendationsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Merge small shards')).toBeInTheDocument();
      expect(screen.getByText('SHARD')).toBeInTheDocument();
      expect(screen.getByText('HIGH')).toBeInTheDocument();
      expect(screen.getByText('$200')).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getRecommendations.mockRejectedValueOnce(new Error('API Error'));
    
    render(<RecommendationsPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

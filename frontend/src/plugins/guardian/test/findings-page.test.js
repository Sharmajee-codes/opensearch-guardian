import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FindingsPage } from '../src/pages/Findings';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getFindings: jest.fn()
  }
}));

describe('FindingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getFindings.mockResolvedValueOnce({ findings: [] });
    
    render(<FindingsPage />);
    expect(screen.getByText(/loading findings/i)).toBeInTheDocument();
  });

  it('renders empty state when no findings', async () => {
    guardianApi.getFindings.mockResolvedValueOnce({ findings: [] });
    
    render(<FindingsPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no findings/i)).toBeInTheDocument();
    });
  });

  it('displays findings list', async () => {
    const mockFindings = {
      findings: [
        {
          finding_id: 'find-1',
          rule_id: 'RULE-001',
          rule_name: 'Cluster health is red',
          severity: 'critical',
          entity_type: 'cluster',
          entity_id: 'test-cluster',
          first_seen_at: '2026-08-20T00:00:00Z'
        }
      ]
    };
    
    guardianApi.getFindings.mockResolvedValueOnce(mockFindings);
    
    render(<FindingsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('RULE-001')).toBeInTheDocument();
      expect(screen.getByText('Cluster health is red')).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getFindings.mockRejectedValueOnce(new Error('API Error'));
    
    render(<FindingsPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument();
    });
  });
});

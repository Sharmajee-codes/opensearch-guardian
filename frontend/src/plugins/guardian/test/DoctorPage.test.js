import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DoctorPage } from '../src/pages/Doctor';
import { guardianApi } from '../src/services/apiService';

// Mock the API service
jest.mock('../src/services/apiService', () => ({
  guardianApi: {
    getDiagnosisFindings: jest.fn(),
    runDiagnosis: jest.fn()
  }
}));

describe('DoctorPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    guardianApi.getDiagnosisFindings.mockResolvedValueOnce({ findings: [] });
    
    render(<DoctorPage />);
    expect(screen.getByText(/loading diagnostic findings/i)).toBeInTheDocument();
  });

  it('renders empty state when no findings match filters', async () => {
    guardianApi.getDiagnosisFindings.mockResolvedValueOnce({ findings: [] });
    
    render(<DoctorPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no findings match your filters/i)).toBeInTheDocument();
    });
  });

  it('displays findings when they exist', async () => {
    const mockFindings = {
      findings: [
        {
          id: 'find-1',
          title: 'Cluster health is red',
          severity: 'critical',
          status: 'active',
          type: 'health',
          confidence: 0.98,
          description: 'Cluster health is red with 3 unassigned shards',
          evidence: [
            { metric: '_cluster/health status', value: 'red' }
          ],
          remediation: 'Investigate unassigned shards',
          root_cause: 'unassigned shards'
        }
      ]
    };
    
    guardianApi.getDiagnosisFindings.mockResolvedValueOnce(mockFindings);
    
    render(<DoctorPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Cluster health is red')).toBeInTheDocument();
      expect(screen.getByText('critical')).toBeInTheDocument();
      expect(screen.getByText(/confidence: 1\.0%/i)).toBeInTheDocument();
      expect(screen.getByText('Investigate unassigned shards')).toBeInTheDocument();
    });
  });

  it('shows error when API fails', async () => {
    guardianApi.getDiagnosisFindings.mockRejectedValueOnce(new Error('API Error'));
    
    render(<DoctorPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/error loading data: api error/i)).toBeInTheDocument();
    });
  });
});

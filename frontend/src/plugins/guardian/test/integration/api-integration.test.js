/**
 * Integration tests for frontend-backend API communication
 * Tests all API endpoints in apiService.js
 */

import { guardianApi } from '../../src/services/apiService';

// Mock fetch globally
global.fetch = jest.fn();

describe('Frontend-Backend API Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // =====================
  // Cluster Health APIs
  // =====================
  describe('Cluster Health APIs', () => {
    it('should call getClusterHealth endpoint', async () => {
      const mockResponse = {
        status: 'green',
        number_of_nodes: 3,
        active_shards: 100
      };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getClusterHealth();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/cluster/health');
      expect(result).toEqual(mockResponse);
    });

    it('should call getClusterOverview endpoint', async () => {
      const mockResponse = { overview: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getClusterOverview();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/cluster/overview');
      expect(result).toEqual(mockResponse);
    });

    it('should call getClusterStats endpoint', async () => {
      const mockResponse = { stats: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getClusterStats();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/cluster/stats');
      expect(result).toEqual(mockResponse);
    });

    it('should throw error on failed cluster health request', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      });

      await expect(guardianApi.getClusterHealth()).rejects.toThrow('Failed to fetch cluster health: 500');
    });
  });

  // =====================
  // Diagnosis APIs
  // =====================
  describe('Diagnosis APIs', () => {
    it('should call runDiagnosis endpoint with POST', async () => {
      const mockResponse = { findings: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.runDiagnosis();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/diagnosis/run', { method: 'POST' });
      expect(result).toEqual(mockResponse);
    });

    it('should call getDiagnosisFindings endpoint', async () => {
      const mockResponse = { findings: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getDiagnosisFindings();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/diagnosis/findings');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Nodes APIs
  // =====================
  describe('Nodes APIs', () => {
    it('should call getNodesStats endpoint', async () => {
      const mockResponse = { nodes: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getNodesStats();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/nodes/stats');
      expect(result).toEqual(mockResponse);
    });

    it('should call getNodesOverview endpoint', async () => {
      const mockResponse = { overview: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getNodesOverview();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/nodes/overview');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Indices APIs
  // =====================
  describe('Indices APIs', () => {
    it('should call getIndicesStats endpoint', async () => {
      const mockResponse = { indices: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getIndicesStats();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/indices/stats');
      expect(result).toEqual(mockResponse);
    });

    it('should call getIndicesOverview endpoint', async () => {
      const mockResponse = { overview: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getIndicesOverview();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/indices/overview');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Shards APIs
  // =====================
  describe('Shards APIs', () => {
    it('should call getShardsStats endpoint', async () => {
      const mockResponse = { shards: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getShardsStats();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/shards/stats');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Live Monitoring APIs
  // =====================
  describe('Live Monitoring APIs', () => {
    it('should call getLiveMonitoringData endpoint', async () => {
      const mockResponse = { data: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getLiveMonitoringData();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/live/monitoring');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Optimization APIs
  // =====================
  describe('Optimization APIs', () => {
    it('should call getOptimizationAdvice endpoint', async () => {
      const mockResponse = { advice: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getOptimizationAdvice();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/optimization/advice');
      expect(result).toEqual(mockResponse);
    });

    it('should call getOptimizerSuggestions endpoint', async () => {
      const mockResponse = { suggestions: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getOptimizerSuggestions();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/optimizer/suggestions');
      expect(result).toEqual(mockResponse);
    });

    it('should call runOptimizationAnalysis with POST', async () => {
      const mockResponse = { status: 'completed' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.runOptimizationAnalysis();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/optimization/run', { method: 'POST' });
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Capacity APIs
  // =====================
  describe('Capacity APIs', () => {
    it('should call getCapacityPlanning with days parameter', async () => {
      const mockResponse = { planning: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getCapacityPlanning(60);
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/capacity/planning?days=60');
      expect(result).toEqual(mockResponse);
    });

    it('should call getCapacityCurrent endpoint', async () => {
      const mockResponse = { current: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getCapacityCurrent();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/capacity/current');
      expect(result).toEqual(mockResponse);
    });

    it('should call getCapacityProjections endpoint', async () => {
      const mockResponse = { projections: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getCapacityProjections();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/capacity/projections');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Findings APIs
  // =====================
  describe('Findings APIs', () => {
    it('should call getFindings endpoint', async () => {
      const mockResponse = { findings: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getFindings();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/findings');
      expect(result).toEqual(mockResponse);
    });

    it('should call getFindingsList endpoint', async () => {
      const mockResponse = { list: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getFindingsList();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/findings/list');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Recommendations APIs
  // =====================
  describe('Recommendations APIs', () => {
    it('should call getRecommendations endpoint', async () => {
      const mockResponse = { recommendations: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getRecommendations();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/recommendations');
      expect(result).toEqual(mockResponse);
    });

    it('should call getRecommendationsList endpoint', async () => {
      const mockResponse = { list: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getRecommendationsList();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/recommendations/list');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Settings APIs
  // =====================
  describe('Settings APIs', () => {
    it('should call getSettings endpoint', async () => {
      const mockResponse = { settings: {} };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getSettings();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/settings');
      expect(result).toEqual(mockResponse);
    });

    it('should call updateSettings with PUT', async () => {
      const mockResponse = { updated: true };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.updateSettings({ key: 'value' });
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: { key: 'value' } })
      });
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Provisioning APIs
  // =====================
  describe('Provisioning APIs', () => {
    it('should call getProvisioningPlans endpoint', async () => {
      const mockResponse = { plans: [] };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getProvisioningPlans();
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/provisioning/plans');
      expect(result).toEqual(mockResponse);
    });

    it('should call createProvisioningPlan with POST', async () => {
      const mockResponse = { plan: { id: 'plan-1' } };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.createProvisioningPlan({ name: 'test' });
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/provisioning/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'test' })
      });
      expect(result).toEqual(mockResponse);
    });

    it('should call runProvisioningPreflight with POST', async () => {
      const mockResponse = { preflight: 'data' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.runProvisioningPreflight('plan-1');
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/provisioning/plans/plan-1/preflight', {
        method: 'POST'
      });
      expect(result).toEqual(mockResponse);
    });

    it('should call applyProvisioningPlan with POST', async () => {
      const mockResponse = { status: 'applied' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.applyProvisioningPlan('plan-1');
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/provisioning/plans/plan-1/apply', {
        method: 'POST'
      });
      expect(result).toEqual(mockResponse);
    });

    it('should call verifyProvisioningPlan with POST', async () => {
      const mockResponse = { verified: true };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.verifyProvisioningPlan('plan-1');
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/provisioning/plans/plan-1/verify', {
        method: 'POST'
      });
      expect(result).toEqual(mockResponse);
    });

    it('should call rollbackProvisioningPlan with POST', async () => {
      const mockResponse = { rolled_back: true };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.rollbackProvisioningPlan('plan-1');
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/provisioning/plans/plan-1/rollback', {
        method: 'POST'
      });
      expect(result).toEqual(mockResponse);
    });

    it('should call getProvisioningPlanStatus endpoint', async () => {
      const mockResponse = { status: 'completed' };
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await guardianApi.getProvisioningPlanStatus('plan-1');
      
      expect(global.fetch).toHaveBeenCalledWith('/api/guardian/provisioning/plans/plan-1/status');
      expect(result).toEqual(mockResponse);
    });
  });

  // =====================
  // Error Handling Tests
  // =====================
  describe('Error Handling', () => {
    it('should throw error on network failure', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));
      
      await expect(guardianApi.getClusterHealth()).rejects.toThrow('Network error');
    });

    it('should throw error on 404 response', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 404
      });
      
      await expect(guardianApi.getClusterHealth()).rejects.toThrow('Failed to fetch cluster health: 404');
    });

    it('should throw error on 403 response', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 403
      });
      
      await expect(guardianApi.getClusterHealth()).rejects.toThrow('Failed to fetch cluster health: 403');
    });
  });
});

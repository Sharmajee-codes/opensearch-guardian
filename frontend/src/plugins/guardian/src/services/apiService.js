// Service for communicating with the Guardian backend plugin API
export const guardianApi = {
  // Cluster health
  getClusterHealth: async () => {
    const response = await fetch('/api/guardian/cluster/health');
    if (!response.ok) {
      throw new Error(`Failed to fetch cluster health: ${response.status}`);
    }
    return response.json();
  },

  getClusterOverview: async () => {
    const response = await fetch('/api/guardian/cluster/overview');
    if (!response.ok) {
      throw new Error(`Failed to fetch cluster overview: ${response.status}`);
    }
    return response.json();
  },

  getClusterStats: async () => {
    const response = await fetch('/api/guardian/cluster/stats');
    if (!response.ok) {
      throw new Error(`Failed to fetch cluster stats: ${response.status}`);
    }
    return response.json();
  },

  // Diagnosis
  runDiagnosis: async () => {
    const response = await fetch('/api/guardian/diagnosis/run', { method: 'POST' });
    if (!response.ok) {
      throw new Error(`Failed to run diagnosis: ${response.status}`);
    }
    return response.json();
  },

  getDiagnosisFindings: async () => {
    const response = await fetch('/api/guardian/diagnosis/findings');
    if (!response.ok) {
      throw new Error(`Failed to get diagnosis findings: ${response.status}`);
    }
    return response.json();
  },

  // Nodes
  getNodesStats: async () => {
    const response = await fetch('/api/guardian/nodes/stats');
    if (!response.ok) {
      throw new Error(`Failed to get nodes stats: ${response.status}`);
    }
    return response.json();
  },

  getNodesOverview: async () => {
    const response = await fetch('/api/guardian/nodes/overview');
    if (!response.ok) {
      throw new Error(`Failed to get nodes overview: ${response.status}`);
    }
    return response.json();
  },

  // Indices
  getIndicesStats: async () => {
    const response = await fetch('/api/guardian/indices/stats');
    if (!response.ok) {
      throw new Error(`Failed to get indices stats: ${response.status}`);
    }
    return response.json();
  },

  getIndicesOverview: async () => {
    const response = await fetch('/api/guardian/indices/overview');
    if (!response.ok) {
      throw new Error(`Failed to get indices overview: ${response.status}`);
    }
    return response.json();
  },

  // Shards
  getShardsStats: async () => {
    const response = await fetch('/api/guardian/shards/stats');
    if (!response.ok) {
      throw new Error(`Failed to get shards stats: ${response.status}`);
    }
    return response.json();
  },

  // Live Monitoring
  getLiveMonitoringData: async () => {
    const response = await fetch('/api/guardian/live/monitoring');
    if (!response.ok) {
      throw new Error(`Failed to get live monitoring data: ${response.status}`);
    }
    return response.json();
  },

  // Optimization
  getOptimizationAdvice: async () => {
    const response = await fetch('/api/guardian/optimization/advice');
    if (!response.ok) {
      throw new Error(`Failed to get optimization advice: ${response.status}`);
    }
    return response.json();
  },

  getOptimizerSuggestions: async () => {
    const response = await fetch('/api/guardian/optimizer/suggestions');
    if (!response.ok) {
      throw new Error(`Failed to get optimizer suggestions: ${response.status}`);
    }
    return response.json();
  },

  runOptimizationAnalysis: async () => {
    const response = await fetch('/api/guardian/optimization/run', { method: 'POST' });
    if (!response.ok) {
      throw new Error(`Failed to run optimization analysis: ${response.status}`);
    }
    return response.json();
  },

  // Capacity
  getCapacityPlanning: async (days = 30) => {
    const response = await fetch(`/api/guardian/capacity/planning?days=${days}`);
    if (!response.ok) {
      throw new Error(`Failed to get capacity planning: ${response.status}`);
    }
    return response.json();
  },

  getCapacityCurrent: async () => {
    const response = await fetch('/api/guardian/capacity/current');
    if (!response.ok) {
      throw new Error(`Failed to get capacity current: ${response.status}`);
    }
    return response.json();
  },

  getCapacityProjections: async () => {
    const response = await fetch('/api/guardian/capacity/projections');
    if (!response.ok) {
      throw new Error(`Failed to get capacity projections: ${response.status}`);
    }
    return response.json();
  },

  // Findings
  getFindings: async () => {
    const response = await fetch('/api/guardian/findings');
    if (!response.ok) {
      throw new Error(`Failed to get findings: ${response.status}`);
    }
    return response.json();
  },

  getFindingsList: async () => {
    const response = await fetch('/api/guardian/findings/list');
    if (!response.ok) {
      throw new Error(`Failed to get findings list: ${response.status}`);
    }
    return response.json();
  },

  // Recommendations
  getRecommendations: async () => {
    const response = await fetch('/api/guardian/recommendations');
    if (!response.ok) {
      throw new Error(`Failed to get recommendations: ${response.status}`);
    }
    return response.json();
  },

  getRecommendationsList: async () => {
    const response = await fetch('/api/guardian/recommendations/list');
    if (!response.ok) {
      throw new Error(`Failed to get recommendations list: ${response.status}`);
    }
    return response.json();
  },

  // Settings
  getSettings: async () => {
    const response = await fetch('/api/guardian/settings');
    if (!response.ok) {
      throw new Error(`Failed to get settings: ${response.status}`);
    }
    return response.json();
  },

  updateSettings: async (settings: any) => {
    const response = await fetch('/api/guardian/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ settings })
    });
    if (!response.ok) {
      throw new Error(`Failed to update settings: ${response.status}`);
    }
    return response.json();
  },

  // Provisioning
  getProvisioningPlans: async () => {
    const response = await fetch('/api/guardian/provisioning/plans');
    if (!response.ok) {
      throw new Error(`Failed to get provisioning plans: ${response.status}`);
    }
    return response.json();
  },

  createProvisioningPlan: async (planData: any) => {
    const response = await fetch('/api/guardian/provisioning/plans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(planData)
    });
    if (!response.ok) {
      throw new Error(`Failed to create provisioning plan: ${response.status}`);
    }
    return response.json();
  },

  runProvisioningPreflight: async (planId: string) => {
    const response = await fetch(`/api/guardian/provisioning/plans/${planId}/preflight`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`Failed to run preflight checks: ${response.status}`);
    }
    return response.json();
  },

  applyProvisioningPlan: async (planId: string) => {
    const response = await fetch(`/api/guardian/provisioning/plans/${planId}/apply`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`Failed to apply provisioning plan: ${response.status}`);
    }
    return response.json();
  },

  verifyProvisioningPlan: async (planId: string) => {
    const response = await fetch(`/api/guardian/provisioning/plans/${planId}/verify`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`Failed to verify provisioning plan: ${response.status}`);
    }
    return response.json();
  },

  rollbackProvisioningPlan: async (planId: string) => {
    const response = await fetch(`/api/guardian/provisioning/plans/${planId}/rollback`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`Failed to rollback provisioning plan: ${response.status}`);
    }
    return response.json();
  },

  getProvisioningPlanStatus: async (planId: string) => {
    const response = await fetch(`/api/guardian/provisioning/plans/${planId}/status`);
    if (!response.ok) {
      throw new Error(`Failed to get provisioning plan status: ${response.status}`);
    }
    return response.json();
  }
};

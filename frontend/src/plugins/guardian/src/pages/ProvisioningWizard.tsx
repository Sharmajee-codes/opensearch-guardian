import React, { useState, useEffect } from 'react';

type ProvisioningStage = 'preflight' | 'review' | 'approval' | 'applying' | 'verification' | 'completed';

interface PreflightCheck {
  id: string;
  name: string;
  description: string;
  category: string;
  status: 'pending' | 'running' | 'pass' | 'warn' | 'fail';
  details?: string;
  remediation?: string;
}

interface DiffItem {
  path: string;
  type: 'added' | 'modified' | 'removed';
  oldValue?: any;
  newValue?: any;
  description: string;
}

interface VerificationStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'pass' | 'fail';
  details?: string;
}

const INITIAL_PREFLIGHT_CHECKS: PreflightCheck[] = [
  { id: 'docker-access', name: 'Docker Engine Access', description: 'Verify Docker daemon is accessible and responding', category: 'docker', status: 'pending' },
  { id: 'write-permission', name: 'Write Permissions', description: 'Confirm write access to Docker socket and volumes', category: 'docker', status: 'pending' },
  { id: 'image-availability', name: 'OpenSearch Image', description: 'Verify target OpenSearch image exists or can be pulled', category: 'docker', status: 'pending' },
  { id: 'volume-driver', name: 'Volume Driver', description: 'Check volume driver supports required operations', category: 'docker', status: 'pending' },
  { id: 'network-config', name: 'Network Configuration', description: 'Validate overlay network can be created/attached', category: 'network', status: 'pending' },
  { id: 'port-availability', name: 'Port Availability', description: 'Check required ports (9200, 9300) are free', category: 'network', status: 'pending' },
  { id: 'tls-config', name: 'TLS Configuration', description: 'Verify TLS certificates and CA bundle validity', category: 'security', status: 'pending' },
  { id: 'security-plugin', name: 'Security Plugin', description: 'Check OpenSearch Security plugin compatibility', category: 'security', status: 'pending' },
  { id: 'disk-space', name: 'Disk Space', description: 'Ensure sufficient disk space for data volumes', category: 'resources', status: 'pending' },
  { id: 'memory-limits', name: 'Memory Limits', description: 'Validate container memory limits match JVM heap', category: 'resources', status: 'pending' },
  { id: 'cpu-limits', name: 'CPU Limits', description: 'Verify CPU limits are appropriate for node roles', category: 'resources', status: 'pending' },
  { id: 'opensearch-version', name: 'OpenSearch Version', description: 'Validate target version compatibility', category: 'version', status: 'pending' },
  { id: 'plugin-compatibility', name: 'Plugin Compatibility', description: 'Check installed plugins compatibility with target version', category: 'version', status: 'pending' },
  { id: 'cluster-health', name: 'Cluster Health', description: 'Verify current cluster is in green/yellow state', category: 'cluster', status: 'pending' },
  { id: 'single-node-guard', name: 'Single-Node Guard', description: 'Ensure not operating on single-node production cluster', category: 'cluster', status: 'pending' },
  { id: 'data-integrity', name: 'Data Integrity', description: 'Verify no unassigned primary shards', category: 'cluster', status: 'pending' },
];

const INITIAL_VERIFICATION_STEPS: VerificationStep[] = [
  { id: 'container-health', name: 'Container Health', description: 'Verify all containers are healthy and running', status: 'pending' },
  { id: 'node-join', name: 'Node Join', description: 'Confirm new nodes have joined the cluster', status: 'pending' },
  { id: 'rebalance-status', name: 'Rebalance Status', description: 'Check shard rebalancing has completed', status: 'pending' },
  { id: 'health-stability', name: 'Health Stability', description: 'Validate cluster health remains stable', status: 'pending' },
];

const MOCK_DIFF: DiffItem[] = [
  { path: 'services.opensearch-node-1.image', type: 'modified', oldValue: 'opensearchproject/opensearch:2.11.0', newValue: 'opensearchproject/opensearch:2.14.0', description: 'Upgrade OpenSearch image to 2.14.0' },
  { path: 'services.opensearch-node-1.environment.OPENSEARCH_JAVA_OPTS', type: 'modified', oldValue: '-Xms2g -Xmx2g', newValue: '-Xms4g -Xmx4g', description: 'Increase JVM heap to 4GB' },
  { path: 'services.opensearch-node-1.deploy.resources.limits.memory', type: 'modified', oldValue: '4g', newValue: '8g', description: 'Increase container memory limit to 8GB' },
  { path: 'services.opensearch-node-3', type: 'added', newValue: '{...}', description: 'Add new data node (opensearch-node-3)' },
  { path: 'volumes.opensearch-data-3', type: 'added', newValue: '{ driver: local }', description: 'Create new volume for node-3 data' },
  { path: 'networks.guardian-network.driver', type: 'modified', oldValue: 'bridge', newValue: 'overlay', description: 'Change network driver to overlay for multi-host' },
];

export const ProvisioningWizard: React.FC = () => {
  const [currentStage, setCurrentStage] = useState<ProvisioningStage>('preflight');
  const [preflightChecks, setPreflightChecks] = useState<PreflightCheck[]>(INITIAL_PREFLIGHT_CHECKS);
  const [verificationSteps, setVerificationSteps] = useState<VerificationStep[]>(INITIAL_VERIFICATION_STEPS);
  const [diff, setDiff] = useState<DiffItem[]>(MOCK_DIFF);
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [approvalConfirmed, setApprovalConfirmed] = useState(false);
  const [progress, setProgress] = useState(0);

  const stages: { id: ProvisioningStage; label: string; description: string }[] = [
    { id: 'preflight', label: 'Preflight Checks', description: 'Validate environment and prerequisites' },
    { id: 'review', label: 'Review Changes', description: 'Review the planned changes before applying' },
    { id: 'approval', label: 'Approval', description: 'Human approval required before proceeding' },
    { id: 'applying', label: 'Applying', description: 'Execute the provisioning plan' },
    { id: 'verification', label: 'Verification', description: 'Verify the changes were applied correctly' },
    { id: 'completed', label: 'Completed', description: 'Provisioning completed successfully' },
  ];

  const currentStageIndex = stages.findIndex(s => s.id === currentStage);

  const runPreflightChecks = async () => {
    setLoading(true);
    setError(null);
    try {
      // Simulate running preflight checks
      const updatedChecks = [...preflightChecks];
      for (let i = 0; i < updatedChecks.length; i++) {
        updatedChecks[i] = { ...updatedChecks[i], status: 'running' };
        setPreflightChecks([...updatedChecks]);
        await new Promise(resolve => setTimeout(resolve, 200));

        // Simulate results (most pass, some warn, rarely fail)
        const rand = Math.random();
        if (rand < 0.8) {
          updatedChecks[i] = { ...updatedChecks[i], status: 'pass' };
        } else if (rand < 0.95) {
          updatedChecks[i] = { ...updatedChecks[i], status: 'warn', details: 'Minor configuration deviation detected' };
        } else {
          updatedChecks[i] = { ...updatedChecks[i], status: 'fail', details: 'Critical requirement not met', remediation: 'Review Docker daemon configuration' };
        }
        setPreflightChecks([...updatedChecks]);
      }

      // Add audit entry
      const passed = updatedChecks.filter(c => c.status === 'pass').length;
      const warnings = updatedChecks.filter(c => c.status === 'warn').length;
      const failed = updatedChecks.filter(c => c.status === 'fail').length;

      if (failed === 0) {
        setCurrentStage('review');
      } else {
        setError(`${failed} critical preflight check(s) failed. Please review and remediate before proceeding.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preflight checks failed');
    } finally {
      setLoading(false);
    }
  };

  const proceedToApproval = () => {
    setCurrentStage('approval');
  };

  const handleApprove = async () => {
    setShowApprovalModal(false);
    setApprovalConfirmed(true);
    setCurrentStage('applying');
    setProgress(0);

    // Simulate apply process
    const applySteps = [
      { stage: 'applying', progress: 20, message: 'Creating Docker Compose override...' },
      { stage: 'applying', progress: 40, message: 'Starting new containers...' },
      { stage: 'applying', progress: 60, message: 'Waiting for containers to become healthy...' },
      { stage: 'applying', progress: 80, message: 'Running docker compose up...' },
      { stage: 'verification', progress: 100, message: 'Apply complete, starting verification...' },
    ];

    for (const step of applySteps) {
      setProgress(step.progress);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    setCurrentStage('verification');
    startVerification();
  };

  const startVerification = async () => {
    const updatedSteps = [...verificationSteps];
    for (let i = 0; i < updatedSteps.length; i++) {
      updatedSteps[i] = { ...updatedSteps[i], status: 'running' };
      setVerificationSteps([...updatedSteps]);
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Simulate verification results
      updatedSteps[i] = { ...updatedSteps[i], status: 'pass', details: 'Verification passed' };
      setVerificationSteps([...updatedSteps]);
    }

    setCurrentStage('completed');
  };

  const handleNewPlan = () => {
    setCurrentStage('preflight');
    setPreflightChecks(INITIAL_PREFLIGHT_CHECKS.map(c => ({ ...c, status: 'pending', details: undefined })));
    setVerificationSteps(INITIAL_VERIFICATION_STEPS.map(s => ({ ...s, status: 'pending' })));
    setPlan(null);
    setError(null);
    setApprovalConfirmed(false);
    setProgress(0);
  };

  const getStageStatus = (stageId: ProvisioningStage) => {
    const index = stages.findIndex(s => s.id === stageId);
    if (index < currentStageIndex) return 'completed';
    if (index === currentStageIndex) return 'current';
    return 'pending';
  };

  const getPreflightStats = () => {
    const passed = preflightChecks.filter(c => c.status === 'pass').length;
    const warnings = preflightChecks.filter(c => c.status === 'warn').length;
    const failed = preflightChecks.filter(c => c.status === 'fail').length;
    const pending = preflightChecks.filter(c => c.status === 'pending').length;
    return { passed, warnings, failed, pending };
  };

  const preflightStats = getPreflightStats();

  return (
    <div>
      <h1>Provisioning Wizard</h1>
      <p>Preflight checklist, diff review, approval gate, and live verification</p>

      {/* Progress Indicator */}
      {currentStage !== 'completed' && (
        <div>
          <div>
            {stages.map((stage, index) => (
              <div key={stage.id} style={{ display: 'inline-flex', alignItems: 'center', margin: '0 10px' }}>
                <div style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  backgroundColor: getStageStatus(stage.id) === 'completed' ? '#28a745' :
                                getStageStatus(stage.id) === 'current' ? '#007bff' :
                                '#dee2e6',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 'bold'
                }}>
                  {index + 1}
                </div>
                <div style={{ marginLeft: '8px', fontSize: '14px' }}>
                  <span style={{
                    color: getStageStatus(stage.id) === 'current' ? '#007bff' :
                            getStageStatus(stage.id) === 'completed' ? '#28a745' :
                            '#6c757d',
                    fontWeight: getStageStatus(stage.id) === 'current' ? 'bold' : 'normal'
                  }}>
                    {stage.label}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <br />
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div style={{ backgroundColor: '#f8d7da', color: '#721c24', padding: '12px', borderRadius: '4px', margin: '16px 0' }}>
          {error}
        </div>
      )}

      {/* Stage Content */}
      {currentStage === 'preflight' && (
        <div>
          <h2>Preflight Checks</h2>
          <p>Validate environment and prerequisites before provisioning</p>

          <div style={{ display: 'flex', gap: '16px', margin: '16px 0' }}>
            <div>
              <div style={{ width: '40px', height: '40px', backgroundColor: '#28a745', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {preflightStats.passed}
              </div>
              <div style={{ marginLeft: '8px' }}>
                <div>Passed</div>
              </div>
            </div>
            <div>
              <div style={{ width: '40px', height: '40px', backgroundColor: '#ffc107', color: '#212529', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {preflightStats.warnings}
              </div>
              <div style={{ marginLeft: '8px' }}>
                <div>Warnings</div>
              </div>
            </div>
            <div>
              <div style={{ width: '40px', height: '40px', backgroundColor: '#dc3545', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {preflightStats.failed}
              </div>
              <div style={{ marginLeft: '8px' }}>
                <div>Failed</div>
              </div>
            </div>
            <div>
              <div style={{ width: '40px', height: '40px', backgroundColor: '#6c757d', color: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {preflightStats.pending}
              </div>
              <div style={{ marginLeft: '8px' }}>
                <div>Pending</div>
              </div>
            </div>
          </div>

          {/* Preflight checks grouped by category */}
          {[...new Set(preflightChecks.map(c => c.category))].map(category => {
            const categoryChecks = preflightChecks.filter(c => c.category === category);
            return (
              <div key={category} style={{ margin: '16px 0' }}>
                <h3>{category.charAt(0).toUpperCase() + category.slice(1)} Checks ({categoryChecks.length})</h3>
                <div style={{ border: '1px solid #dee2e6', borderRadius: '4px', padding: '16px' }}>
                  {categoryChecks.map(check => (
                    <div key={check.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #f8f9fa' }}>
                      <div>
                        <div style={{ fontWeight: 'bold' }}>{check.name}</div>
                        <div style={{ fontSize: '14px', color: '#6c757d' }}>{check.description}</div>
                      </div>
                      <div>
                        <span style={{
                          display: 'inline-block',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          backgroundColor: check.status === 'pass' ? '#d4edda' :
                                       check.status === 'warn' ? '#fff3cd' :
                                       check.status === 'fail' ? '#f8d7da' :
                                       '#e2e3e5',
                          color: check.status === 'pass' ? '#155724' :
                                  check.status === 'warn' ? '#856404' :
                                  check.status === 'fail' ? '#721c24' :
                                  '#6c757d'
                        }}>
                          {check.status.toUpperCase()}
                        </span>
                        {check.status === 'fail' && check.remediation && (
                          <div style={{ marginTop: '4px', fontSize: '13px', color: '#dc3545' }}>
                            Remediation: {check.remediation}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          {preflightStats.failed === 0 && preflightStats.passed > 0 && (
            <button
              onClick={proceedToApproval}
              style={{
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '4px',
                fontSize: '16px',
                cursor: 'pointer'
              }}
            >
              Proceed to Review
            </button>
          )}

          {!loading && preflightStats.pending === preflightChecks.length && (
            <button
              onClick={runPreflightChecks}
              style={{
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '4px',
                fontSize: '16px',
                cursor: 'pointer',
                marginLeft: '16px'
              }}
            >
              Run Preflight Checks
            </button>
          )}

          {loading && (
            <button
              disabled
              style={{
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '4px',
                fontSize: '16px',
                cursor: 'not-allowed'
              }}
            >
              Running Checks...
            </button>
          )}
        </div>
      )}

      {currentStage === 'review' && (
        <div>
          <h2>Review Changes</h2>
          <p>Review the planned changes before applying. This diff shows what will be modified.</p>

          <div style={{ margin: '16px 0' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Action</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Path</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Description</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Old Value</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>New Value</th>
                </tr>
              </thead>
              <tbody>
                {diff.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #dee2e6' }}>
                    <td style={{ padding: '8px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: item.type === 'added' ? '#d4edda' :
                                     item.type === 'modified' ? '#fff3cd' :
                                     item.type === 'removed' ? '#f8d7da' :
                                     '#e2e3e5',
                        color: item.type === 'added' ? '#155724' :
                               item.type === 'modified' ? '#856404' :
                               item.type === 'removed' ? '#721c24' :
                               '#6c757d'
                      }}>
                        {item.type.toUpperCase()}
                      </span>
                    </td>
                    <td style={{ padding: '8px', fontFamily: 'monospace' }}>{item.path}</td>
                    <td style={{ padding: '8px' }}>{item.description}</td>
                    <td style={{ padding: '8px', fontFamily: 'monospace' }}>
                      {item.oldValue !== undefined ? JSON.stringify(item.oldValue) : '—'}
                    </td>
                    <td style={{ padding: '8px', fontFamily: 'monospace' }}>
                      {item.newValue !== undefined ? JSON.stringify(item.newValue) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ backgroundColor: '#d1ecf1', color: '#0c5460', padding: '12px', borderRadius: '4px', margin: '16px 0' }}>
            {diff.length} changes will be applied: {diff.filter(d => d.type === 'added').length} additions, {diff.filter(d => d.type === 'modified').length} modifications, {diff.filter(d => d.type === 'removed').length} removals
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
            <button
              onClick={() => setCurrentStage('preflight')}
              style={{
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Back
            </button>
            <button
              onClick={proceedToApproval}
              style={{
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '4px',
                fontSize: '16px',
                cursor: 'pointer'
              }}
            >
              Proceed to Approval
            </button>
          </div>
        </div>
      )}

      {currentStage === 'approval' && (
        <div>
          <h2>Approval Required</h2>
          <p>This provisioning operation will modify the cluster infrastructure. Please confirm you have reviewed the changes and authorize proceeding.</p>

          <div style={{ margin: '16px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <strong>Plan ID:</strong> {plan?.id || 'plan-' + Date.now()}
              </div>
              <div>
                <strong>Type:</strong> {plan?.type || 'Docker Compose'}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div>
                <strong>Target Version:</strong> {plan?.targetVersion || '2.14.0'}
              </div>
              <div>
                <strong>Node Count:</strong> {plan?.nodeCount || 3} nodes ({plan?.nodeRoles?.join(', ') || 'data, master'})
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <strong>Changes:</strong> {diff.length} modifications planned
            </div>

            <div style={{ marginBottom: '16px' }}>
              <strong>Rollback:</strong> Enabled - volumes will be preserved on rollback
            </div>
          </div>

          <div style={{ backgroundColor: '#fff3cd', color: '#856404', padding: '12px', borderRadius: '4px', margin: '16px 0' }}>
            <strong>⚠️ Important</strong><br/>
            This action requires explicit human approval. Once approved, the provisioning will begin and cannot be cancelled mid-operation. A full rollback is available but will require manual intervention.
          </div>

          <div style={{ margin: '16px 0' }}>
            <label htmlFor="approval-input" style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
              Type 'APPROVE' to confirm
            </label>
            <input
              type="text"
              id="approval-input"
              value={approvalConfirmed ? 'APPROVE' : ''}
              onChange={(e) => setApprovalConfirmed(e.target.value === 'APPROVE')}
              style={{
                padding: '8px',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '16px',
                width: '200px'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '24px' }}>
            <button
              onClick={() => setCurrentStage('review')}
              style={{
                backgroundColor: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '4px',
                fontSize: '14px',
                cursor: 'pointer'
              }}
            >
              Back to Review
            </button>
            <button
              onClick={handleApprove}
              disabled={!approvalConfirmed}
              style={{
                backgroundColor: approvalConfirmed ? '#dc3545' : '#6c757d',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '4px',
                fontSize: '16px',
                cursor: approvalConfirmed ? 'pointer' : 'not-allowed'
              }}
            >
              APPROVE AND PROCEED
            </button>
          </div>
        </div>
      )}

      {currentStage === 'applying' && (
        <div>
          <h2>Applying Provisioning Plan</h2>
          <p>Executing the approved changes. This may take several minutes.</p>

          <div style={{ margin: '16px 0' }}>
            <div style={{ width: '100%', backgroundColor: '#e9ecef', borderRadius: '4px', height: '8px' }}>
              <div
                style={{
                  width: `${progress}%`,
                  backgroundColor: '#007bff',
                  height: '100%',
                  borderRadius: '4px',
                  transition: 'width 0.3s ease'
                }}
              ></div>
            </div>
            <div style={{ textAlign: 'right', marginTop: '4px', fontSize: '14px', color: '#6c757d' }}>
              {progress}%
            </div>
          </div>

          <div style={{ margin: '16px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <strong>Status:</strong> Applying changes via Docker Compose override...
              </div>
              <div>
                <strong>Progress:</strong> {progress}%
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
              <div>
                <strong>Mode:</strong> Docker Compose Override
              </div>
              <div>
                <strong>Rollback Available:</strong> Yes - volumes preserved
              </div>
            </div>
          </div>
        </div>
      )}

      {currentStage === 'verification' && (
        <div>
          <h2>Verification</h2>
          <p>Validating that the provisioning completed successfully and the cluster is healthy.</p>

          <div style={{ margin: '16px 0' }}>
            {verificationSteps.map((step, idx) => (
              <div key={step.id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px 0',
                borderBottom: idx < verificationSteps.length - 1 ? '1px solid #f8f9fa' : 'none'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: step.status === 'pass' ? '#d4edda' :
                                  step.status === 'running' ? '#d1ecf1' :
                                  step.status === 'fail' ? '#f8d7da' :
                                  '#e2e3e5',
                    color: step.status === 'pass' ? '#155724' :
                            step.status === 'running' ? '#0c5460' :
                            step.status === 'fail' ? '#721c24' :
                            '#6c757d'
                  }}>
                    {step.status === 'pass' ? '✓' : step.status === 'running' ? '⟳' : step.status === 'fail' ? '✗' : '○'}
                  </div>
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{step.name}</div>
                    <div style={{ fontSize: '14px', color: '#6c757d' }}>{step.description}</div>
                  </div>
                </div>
                <div>
                  {step.status === 'running' && <div style={{ color: '#0c5460', fontStyle: 'italic' }}>In progress...</div>}
                  {step.details && <div style={{ fontSize: '14px', color: '#6c757d', marginTop: '4px' }}>{step.details}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {currentStage === 'completed' && (
        <div>
          <div style={{ backgroundColor: '#d4edda', color: '#155724', padding: '16px', borderRadius: '4px', margin: '16px 0' }}>
            <strong>✓ Provisioning Completed Successfully</strong><br/>
            The provisioning operation has completed and all verification checks have passed. The cluster is healthy and the new nodes have joined successfully.
          </div>

          <div style={{ margin: '16px 0' }}>
            <h3>Summary</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '8px 16px' }}>
              <div><strong>Plan:</strong></div> <div>{plan?.name || 'Provisioning Plan'}</div>
              <div><strong>Type:</strong></div> <div>Docker Compose Override</div>
              <div><strong>Changes Applied:</strong></div> <div>{diff.length} modifications</div>
              <div><strong>Preflight Checks:</strong></div> <div>{preflightStats.passed} passed, {preflightStats.warnings} warnings</div>
              <div><strong>Verification Steps:</strong></div> <div>{verificationSteps.filter(s => s.status === 'pass').length} of {verificationSteps.length} passed</div>
              <div><strong>Rollback:</strong></div> <div>Available - volumes preserved</div>
              <div><strong>Completed At:</strong></div> <div>{new Date().toISOString()}</div>
            </div>
          </div>

          <div style={{ margin: '16px 0' }}>
            <h3>Audit Trail</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Timestamp</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Action</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>User</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Result</th>
                  <th style={{ padding: '8px', textAlign: 'left' }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {/* Mock audit log */}
                <tr style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: '8px', fontSize: '14px' }}>2026-08-20T10:00:00Z</td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>plan_created</td>
                  <td style={{ padding: '8px' }}>admin</td>
                  <td style={{ padding: '8px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      backgroundColor: '#d4edda',
                      color: '#155724',
                      fontSize: '12px'
                    }}>
                      SUCCESS
                    </span>
                  </td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>{JSON.stringify({ planId: 'plan-123' })}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: '8px', fontSize: '14px' }}>2026-08-20T10:02:30Z</td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>preflight_completed</td>
                  <td style={{ padding: '8px' }}>system</td>
                  <td style={{ padding: '8px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      backgroundColor: '#d4edda',
                      color: '#155724',
                      fontSize: '12px'
                    }}>
                      SUCCESS
                    </span>
                  </td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>{JSON.stringify({ passed: 15, warnings: 2, failed: 0 })}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: '8px', fontSize: '14px' }}>2026-08-20T10:05:00Z</td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>plan_reviewed</td>
                  <td style={{ padding: '8px' }}>admin</td>
                  <td style={{ padding: '8px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      backgroundColor: '#d4edda',
                      color: '#155724',
                      fontSize: '12px'
                    }}>
                      SUCCESS
                    </span>
                  </td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>{JSON.stringify({ diffItems: 6 })}</td>
                </tr>
                <tr style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: '8px', fontSize: '14px' }}>2026-08-20T10:10:00Z</td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>provisioning_approved</td>
                  <td style={{ padding: '8px' }}>admin</td>
                  <td style={{ padding: '8px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      backgroundColor: '#d4edda',
                      color: '#155724',
                      fontSize: '12px'
                    }}>
                      SUCCESS
                    </span>
                  </td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>{JSON.stringify({ approvedBy: 'admin' })}</td>
                </tr>
                <tr>
                  <td style={{ padding: '8px', fontSize: '14px' }}>2026-08-20T10:10:15Z</td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>apply_started</td>
                  <td style={{ padding: '8px' }}>system</td>
                  <td style={{ padding: '8px' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      backgroundColor: '#fff3cd',
                      color: '#856404',
                      fontSize: '12px'
                    }}>
                      PENDING
                    </span>
                  </td>
                  <td style={{ padding: '8px', fontFamily: 'monospace' }}>{JSON.stringify({ mode: 'compose_override' })}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: '24px', textAlign: 'center' }}>
            <button
              onClick={handleNewPlan}
              style={{
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '4px',
                fontSize: '16px',
                cursor: 'pointer'
              }}
            >
              Start New Provisioning
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProvisioningWizard;
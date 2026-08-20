import React, { useEffect, useState } from 'react';
import {
  EuiTitle,
  EuiText,
  EuiFlexGroup,
  EuiFlexItem,
  EuiSpacer,
  EuiCard,
  EuiCardBody,
  EuiBadge,
  EuiButtonEmpty,
} from '@elastic/eui';
import { guardianApi } from '../services/apiService';

export const OverviewPage: React.FC = () => {
  const [clusterHealth, setClusterHealth] = useState<any>(null);
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [healthResponse, findingsResponse] = await Promise.all([
          guardianApi.getClusterHealth(),
          guardianApi.getDiagnosisFindings()
        ]);
        setClusterHealth(healthResponse);
        setFindings(findingsResponse.findings || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Guardian Overview</EuiTitle>
        <EuiText>Loading cluster health data...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Guardian Overview</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Guardian Overview</EuiTitle>
      <EuiText>Cluster health monitoring and diagnostic insights.</EuiText>
      <EuiSpacer />
      
      <EuiFlexGroup justifyContent="spaceBetween" wrap>
        <EuiFlexItem grow={false} shrink={false} basis={400}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"m"}>Cluster Status</EuiTitle>
              {clusterHealth ? (
                <>
                  <EuiText><strong>Status:</strong> {clusterHealth.status || 'unknown'}</EuiText>
                  <EuiText><strong>Node Count:</strong> {clusterHealth.node_count || 0}</EuiText>
                  <EuiText><strong>Shard Count:</strong> {clusterHealth.shard_count || 0}</EuiText>
                </>
              ) : <EuiText>No data available</EuiText>}
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>
        
        <EuiFlexItem grow={false} shrink={false} basis={400}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"m"}>Recent Findings</EuiTitle>
              {findings.length > 0 ? (
                findings.slice(0, 5).map((finding: any, index: number) => (
                  <div key={index} style={{ marginBottom: '16px' }}>
                    <EuiBadge color={finding.severity === 'critical' ? 'danger' : finding.severity === 'high' ? 'warning' : 'accent'}>
                      {finding.rule_id}
                    </EuiBadge>
                    <EuiText size="s">{finding.condition_description}</EuiText>
                  </div>
                ))
              ) : <EuiText>No findings - cluster is healthy!</EuiText>}
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>
      </EuiFlexGroup>
      
      <EuiFlexGroup justifyContent="flexEnd">
        <EuiButtonEmpty onClick={() => window.location.reload()}>Refresh</EuiButtonEmpty>
      </EuiFlexGroup>
    </>
  );
};

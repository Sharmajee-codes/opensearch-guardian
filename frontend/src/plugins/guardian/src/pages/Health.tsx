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
import ClusterHealthChart from '../components/ClusterHealthChart';

export const HealthPage: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await guardianApi.getClusterHealth();
        setHealth(response);
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
        <EuiTitle size={"l"}>Cluster Health</EuiTitle>
        <EuiText>Loading health data...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Cluster Health</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Cluster Health</EuiTitle>
      <EuiText>Real-time cluster health monitoring.</EuiText>
      <EuiSpacer />
      
      <EuiCard
        title={<EuiBadge color={health.status === 'green' ? 'success' : health.status === 'yellow' ? 'warning' : 'danger'}>{health.status}</EuiBadge>}
        description={`Nodes: ${health.number_of_nodes} | Shards: ${health.active_shards + health.unassigned_shards}`}
      />
      
      <EuiSpacer />
      
      {health && (
        <EuiSpacer />
      )}
      
      <EuiFlexGroup justifyContent="flexEnd">
        <EuiButtonEmpty onClick={() => window.location.reload()}>Refresh</EuiButtonEmpty>
      </EuiFlexGroup>
    </>
  );
};

export default HealthPage;

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
  EuiTable,
  EuiTableHeader,
  EuiTableHeaderContent,
  EuiTableRow,
  EuiTableCell,
  EuiChartContainer,
  EuiSuperString,
  EuiClickableText
} from '@elastic/eui';

export const LiveMonitoringPage: React.FC = () => {
  const [clusterStats, setClusterStats] = useState<any>(null);
  const [nodeStats, setNodeStats] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch cluster stats and node stats
        const [clusterResp, nodesResp] = await Promise.all([
          fetch('/api/guardian/cluster/stats'),
          fetch('/api/guardian/nodes/stats')
        ]);

        if (!clusterResp.ok) throw new Error(`Cluster stats failed: ${clusterResp.status}`);
        if (!nodesResp.ok) throw new Error(`Node stats failed: ${nodesResp.status}`);

        const [clusterData, nodesData] = await Promise.all([
          clusterResp.json(),
          nodesResp.json()
        ]);

        setClusterStats(clusterData);
        setNodeStats(nodesData.nodes || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };

    // Fetch initial data
    fetchData();
    // Set up interval for real-time updates (every 5 seconds)
    const intervalId = setInterval(fetchData, 5000);
    return () => clearInterval(intervalId);
  }, []);

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Live Monitoring</EuiTitle>
        <EuiText>Loading live monitoring data...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Live Monitoring</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Live Monitoring</EuiTitle>
      <EuiText>
        Real-time monitoring of cluster and node metrics.
      </EuiText>
      <EuiSpacer />

      {/* Cluster Overview */}
      <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="m">
        <EuiFlexItem grow={false} shrink={false} basis={250}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"m"}>Cluster Status</EuiTitle>
              {clusterStats ? (
                <>
                  <EuiText>
                    <strong>Status:</strong>
                    <EuiBadge color={clusterStats.status === 'green' ? 'success' : clusterStats.status === 'yellow' ? 'warning' : 'danger'}>
                      {(clusterStats.status || 'unknown').toUpperCase()}
                    </EuiBadge>
                  </EuiText>
                  <EuiText>
                    <strong>Timestamp:</strong> {new Date(clusterStats.timestamp || Date.now()).toLocaleString()}
                  </EuiText>
                </>
              ) : (
                <EuiText>No data available</EuiText>
              )}
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>

        <EuiFlexItem grow={false} shrink={false} basis={250}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"m"}>Key Metrics</EuiTitle>
              {clusterStats ? (
                <EuiTable responsive={false}>
                  <EuiTableHeader>
                    <EuiTableHeaderContent>
                      <EuiTableCell>Metric</EuiTableCell>
                      <EuiTableCell>Value</EuiTableCell>
                    </EuiTableHeaderContent>
                  </EuiTableHeader>
                  <EuiTableRow>
                    <EuiTableCell>Active Primary Shards</EuiTableCell>
                    <EuiTableCell>{clusterStats.active_primary_shards || 0}</EuiTableCell>
                  </EuiTableRow>
                  <EuiTableRow>
                    <EuiTableCell>Active Shards</EuiTableCell>
                    <EuiTableCell>{clusterStats.active_shards || 0}</EuiTableCell>
                  </EuiTableRow>
                  <EuiTableRow>
                    <EuiTableCell>Relocating Shards</EuiTableCell>
                    <EuiTableCell>{clusterStats.relocating_shards || 0}</EuiTableCell>
                  </EuiTableRow>
                  <EuiTableRow>
                    <EuiTableCell>Initializing Shards</EuiTableCell>
                    <EuiTableCell>{clusterStats.initializing_shards || 0}</EuiTableCell>
                  </EuiTableRow>
                  <EuiTableRow>
                    <EuiTableCell>Unassigned Shards</EuiTableCell>
                    <EuiTableCell color={clusterStats.unassigned_shards > 0 ? 'danger' : undefined}>
                      {clusterStats.unassigned_shards || 0}
                    </EuiTableCell>
                  </EuiTableRow>
                  <EuiTableRow>
                    <EuiTableCell>Number of Nodes</EuiTableCell>
                    <EuiTableCell>{clusterStats.number_of_nodes || 0}</EuiTableCell>
                  </EuiTableRow>
                </EuiTable>
              ) : (
                <EuiText>No data available</EuiText>
              )}
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>

        <EuiFlexItem grow={false} shrink={false} basis={250}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"m"}>Node Overview</EuiTitle>
              {nodeStats.length > 0 ? (
                <EuiTable responsive={false}>
                  <EuiTableHeader>
                    <EuiTableHeaderContent>
                      <EuiTableCell>Node</EuiTableCell>
                      <EuiTableCell>CPU %</EuiTableCell>
                      <EuiTableCell>Heap Used %</EuiTableCell>
                      <EuiTableCell>Load Avg</EuiTableCell>
                    </EuiTableHeaderContent>
                  </EuiTableHeader>
                  {nodeStats.map((node: any, idx: number) => (
                    <EuiTableRow key={idx}>
                      <EuiTableCell>{node.name || `node-${idx}`}</EuiTableCell>
                      <EuiTableCell>
                        {((node.os?.cpu || {}).percent || 0).toFixed(1)}%
                      </EuiTableCell>
                      <EuiTableCell>
                        {((node.jvm?.mem_heap_used_in_bytes || 0) / (node.jvm?.mem_heap_max_in_bytes || 1) * 100).toFixed(1)}%
                      </EuiTableCell>
                      <EuiTableCell>{node.os?.load_average || 0}</EuiTableCell>
                    </EuiTableRow>
                  ))}
                </EuiTable>
              ) : (
                <EuiText>No node data available</EuiText>
              )}
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>
      </EuiFlexGroup>

      {/* Detailed Node Metrics (expandable cards) */}
      <EuiTitle size={"l"}>Node Details</EuiTitle>
      <EuiText>
        Detailed metrics for each node in the cluster.
      </EuiText>
      <EuiSpacer />

      {nodeStats.length === 0 ? (
        <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
          <EuiText>No node details available</EuiText>
        </EuiFlexGroup>
      ) : (
        <>
          {nodeStats.map((node: any, idx: number) => (
            <EuiFlexItem key={node.name || idx} grow={false} shrink={false} basis={100}>
              <EuiCard>
                <EuiCardBody>
                  <EuiTitle size={"s"}>{node.name}</EuiTitle>
                  <EuiText size="xs" color="textSecondary">
                    {node.host || 'unknown'} : {node.transport_port || 9300}
                  </EuiText>

                  <EuiHorizontalRule marginSize="xs" />

                  <EuiTitle size={"xxs"}>JVM</EuiTitle>
                  <EuiTable responsive={false}>
                    <EuiTableHeader>
                      <EuiTableHeaderContent>
                        <EuiTableCell>Metric</EuiTableCell>
                        <EuiTableCell>Value</EuiTableCell>
                      </EuiTableHeaderContent>
                    </EuiTableHeader>
                    <EuiTableRow>
                      <EuiTableCell>Heap Used</EuiTableCell>
                      <EuiTableCell>
                        {(node.jvm?.mem_heap_used_in_bytes || 0) / 1024 / 1024} MB
                      </EuiTableCell>
                    </EuiTableRow>
                    <EuiTableRow>
                      <EuiTableCell>Heap Max</EuiTableCell>
                      <EuiTableCell>
                        {(node.jvm?.mem_heap_max_in_bytes || 0) / 1024 / 1024} MB
                      </EuiTableCell>
                    </EuiTableRow>
                    <EuiTableRow>
                      <EuiTableCell>Heap Used %</EuiTableCell>
                      <EuiTableCell>
                        {((node.jvm?.mem_heap_used_in_bytes || 0) / (node.jvm?.mem_heap_max_in_bytes || 1) * 100).toFixed(1)}%
                      </EuiTableCell>
                    </EuiTableRow>
                    </EuiTable>
                  </EuiCardBody>
                </EuiCard>
              </EuiFlexItem>
            ))}
          </>
      )}

      {/* Refresh button and last updated */}
      <EuiFlexGroup justifyContent="flexEnd" verticalSize="s">
        <EuiText>
          Last updated: {new Date().toLocaleString()}
        </EuiText>
        <EuiSpacer size="s" />
        <EuiButtonEmpty onClick={() => window.location.reload()}>
          Refresh Live Data
        </EuiButtonEmpty>
      </EuiFlexGroup>
    </>
  );
};
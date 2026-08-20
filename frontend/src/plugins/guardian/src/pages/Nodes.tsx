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
  EuiTableCell
} from '@elastic/eui';
import { guardianApi } from '../services/apiService';

export const NodesPage: React.FC = () => {
  const [nodes, setNodes] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNodes = async () => {
      try {
        setLoading(true);
        const response = await guardianApi.getNodesStats();
        setNodes(response.nodes || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };
    fetchNodes();
  }, []);

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Nodes</EuiTitle>
        <EuiText>Loading node statistics...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Nodes</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Nodes</EuiTitle>
      <EuiText>Detailed statistics for each node in your OpenSearch cluster.</EuiText>
      <EuiSpacer />
      
      {nodes.length === 0 && (
        <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
          <EuiText>No nodes found</EuiText>
        </EuiFlexGroup>
      )}
      
      {nodes.length > 0 && (
        <EuiFlexGroup justifyContent="spaceBetween" wrap>
          {nodes.map((node, index) => (
            <EuiFlexItem key={node.name || index} grow={false} shrink={false} basis={300}>
              <EuiCard>
                <EuiCardBody>
                  <EuiTitle size={"s"}>{node.name || `Node ${index + 1}`}</EuiTitle>
                  {node.jvm && (
                    <>
                      <EuiText>
                        <strong>JVM Heap:</strong>{' '}
                        {((node.jvm.mem_heap_used_in_bytes || 0) / (node.jvm.mem_heap_max_in_bytes || 1) * 100).toFixed(1)}%
                        {' ('}{(node.jvm.mem_heap_used_in_bytes || 0) / (1024**3).toFixed(1)} GB / {(node.jvm.mem_heap_max_in_bytes || 0) / (1024**3).toFixed(1)} GB)
                      </EuiText>
                      <EuiText color={((node.jvm.mem_heap_used_in_bytes || 0) / (node.jvm.mem_heap_max_in_bytes || 1) > 0.9 ? 'danger' : ((node.jvm.mem_heap_used_in_bytes || 0) / (node.jvm.mem_heap_max_in_bytes || 1) > 0.75 ? 'warning' : 'success'))}>
                        {((node.jvm.mem_heap_used_in_bytes || 0) / (node.jvm.mem_heap_max_in_bytes || 1) > 0.9 ? 'CRITICAL' : ((node.jvm.mem_heap_used_in_bytes || 0) / (node.jvm.mem_heap_max_in_bytes || 1) > 0.75 ? 'WARNING' : 'OK'))}
                      </EuiText>
                    </>
                  )}
                  {node.os && (
                    <>
                      <EuiText><strong>CPU Usage:</strong> {node.os.cpu || 0}%</EuiText>
                      <EuiText color={node.os.cpu && node.os.cpu > 85 ? 'danger' : 'success'}>
                        {node.os.cpu && node.os.cpu > 85 ? 'HIGH' : 'NORMAL'}
                      </EuiText>
                      <EuiText><strong>Load Average (1m):</strong> {node.os.load_average?.['1m'] || 0}</EuiText>
                    </>
                  )}
                  {node.fs && node.fs.length > 0 && (
                    <>
                      <EuiText>
                        <strong>Disk Usage:</strong>{' '}
                        {((node.fs[0].total_in_bytes - node.fs[0].available_in_bytes) / node.fs[0].total_in_bytes * 100).toFixed(1)}%
                        {' ('}{((node.fs[0].total_in_bytes - node.fs[0].available_in_bytes) / (1024**3)).toFixed(1)} GB / {(node.fs[0].total_in_bytes / (1024**3)).toFixed(1)} GB)
                      </EuiText>
                      <EuiText color={((node.fs[0].total_in_bytes - node.fs[0].available_in_bytes) / node.fs[0].total_in_bytes) > 0.95 ? 'danger' : (((node.fs[0].total_in_bytes - node.fs[0].available_in_bytes) / node.fs[0].total_in_bytes) > 0.9 ? 'warning' : 'success')}>
                        {((node.fs[0].total_in_bytes - node.fs[0].available_in_bytes) / node.fs[0].total_in_bytes) > 0.95 ? 'FLOOD' : (((node.fs[0].total_in_bytes - node.fs[0].available_in_bytes) / node.fs[0].total_in_bytes) > 0.9 ? 'HIGH' : 'NORMAL')}
                      </EuiText>
                    </>
                  )}
                  {node.transport && (
                    <EuiText><strong>Transport:</strong> {node.transport.tx_count || 0} TX / {node.transport.rx_count || 0} RX</EuiText>
                  )}
                </EuiCardBody>
              </EuiCard>
            </EuiFlexItem>
          ))}
        </EuiFlexGroup>
      )}
      
      <EuiFlexGroup justifyContent="flexEnd">
        <EuiButtonEmpty onClick={() => window.location.reload()}>Refresh</EuiButtonEmpty>
      </EuiFlexGroup>
    </>
  );
};

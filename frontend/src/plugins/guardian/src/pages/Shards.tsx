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

export const ShardsPage: React.FC = () => {
  const [shards, setShards] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchShards = async () => {
      try {
        setLoading(true);
        const response = await guardianApi.getShardsStats();
        setShards(response.shards || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };
    fetchShards();
  }, []);

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Shards</EuiTitle>
        <EuiText>Loading shards statistics...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Shards</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Shards</EuiTitle>
      <EuiText>Detailed shard allocation and status information.</EuiText>
      <EuiSpacer />
      
      {shards.length === 0 && (
        <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
          <EuiText>No shards found</EuiText>
        </EuiFlexGroup>
      )}
      
      {shards.length > 0 && (
        <EuiFlexGroup justifyContent="spaceBetween" wrap>
          {shards.map((shard, idx) => (
            <EuiFlexItem key={shard.shard_id || idx} grow={false} shrink={false} basis={250}>
              <EuiCard>
                <EuiCardBody>
                  <EuiTitle size={"xxs"}>{shard.index || 'unknown'} #{shard.shard}</EuiTitle>
                  {shard.routing && (
                    <>
                      <EuiText>
                        <strong>State:</strong>{' '}
                        <EuiBadge color={shard.routing.state === 'STARTED' ? 'success' : shard.routing.state === 'RELOCATING' ? 'warning' : shard.routing.state === 'INITIALIZING' ? 'accent' : shard.routing.state === 'UNASSIGNED' ? 'danger' : 'ghost'}>
                          {shard.routing.state}
                        </EuiBadge>
                      </EuiText>
                      <EuiText size="xs">{shard.routing.primary ? 'PRIMARY' : 'REPLICA'}</EuiText>
                    </>
                  )}
                  {shard.nodes && (
                    <EuiText><strong>Node:</strong> {shard.nodes[0] || 'unassigned'}</EuiText>
                  )}
                  {shard.routing && shard.routing.state === 'UNASSIGNED' && shard.routing.unassigned_info && (
                    <EuiText size="xs" color="warning" title={shard.routing.unassigned_info.detail}>
                      {(shard.routing.unassigned_info.reason || 'unknown').substring(0, 15)}
                    </EuiText>
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

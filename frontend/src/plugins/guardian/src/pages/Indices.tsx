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
  EuiTitleSize
} from '@elastic/eui';
import { guardianApi } from '../services/apiService';

export const IndicesPage: React.FC = () => {
  const [indices, setIndices] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIndices = async () => {
      try {
        setLoading(true);
        const response = await guardianApi.getIndicesStats();
        setIndices(response.indices || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };
    fetchIndices();
  }, []);

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Indices</EuiTitle>
        <EuiText>Loading indices statistics...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Indices</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Indices</EuiTitle>
      <EuiText>Statistics and health information for all indices in your cluster.</EuiText>
      <EuiSpacer />
      
      {indices.length === 0 && (
        <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
          <EuiText>No indices found</EuiText>
        </EuiFlexGroup>
      )}
      
      {indices.length > 0 && (
        <EuiFlexGroup justifyContent="spaceBetween" wrap>
          {indices.map((index, idx) => (
            <EuiFlexItem key={index.index || idx} grow={false} shrink={false} basis={300}>
              <EuiCard>
                <EuiCardBody>
                  <EuiTitle size={"s"}>{index.index || `Index ${idx + 1}`}</EuiTitle>
                  {index.health && (
                    <EuiText>
                      <strong>Health:</strong>{' '}
                      <EuiBadge color={index.health === 'green' ? 'success' : index.health === 'yellow' ? 'warning' : 'danger'}>
                        {index.health.toUpperCase()}
                      </EuiBadge>
                    </EuiText>
                  )}
                  <EuiText><strong>Docs Count:</strong> {(index.docs_count || 0).toLocaleString()}</EuiText>
                  <EuiText><strong>Deleted Docs:</strong> {(index.deleted_docs || 0).toLocaleString()}</EuiText>
                  <EuiText><strong>Store Size:</strong> {(index.store_size_in_bytes || 0) / (1024**3).toFixed(1)} GB</EuiText>
                  <EuiText><strong>Pri. Store Size:</strong> {(index.pri_store_size_in_bytes || 0) / (1024**3).toFixed(1)} GB</EuiText>
                  {index.primaries !== undefined && index.replicas !== undefined && (
                    <EuiText><strong>Shards:</strong> {index.primaries} primaries, {index.replicas} replicas</EuiText>
                  )}
                  {index.blocks && index.blocks.read_only && (
                    <EuiText color="warning"><strong>Read-only:</strong> Yes</EuiText>
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

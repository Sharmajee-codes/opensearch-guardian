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
  EuiHorizontalRule,
  EuiAccordion,
  EuiSelect,
  EuiButton
} from '@elastic/eui';
import { guardianApi } from '../services/apiService';

export const DoctorPage: React.FC = () => {
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<{
    severity: 'all' | 'critical' | 'high' | 'medium' | 'low';
    status: 'all' | 'active' | 'acknowledged' | 'resolved';
    type: 'all' | 'health' | 'performance' | 'storage' | 'capacity';
  }>({
    severity: 'all',
    status: 'all',
    type: 'all'
  });

  useEffect(() => {
    const fetchFindings = async () => {
      try {
        setLoading(true);
        const data = await guardianApi.getDiagnosisFindings();
        setFindings(data.findings || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };

    fetchFindings();
  }, []);

  // Filter findings based on current filters
  const filteredFindings = findings.filter(finding => {
    if (filters.severity !== 'all' && finding.severity !== filters.severity) return false;
    if (filters.status !== 'all' && finding.status !== filters.status) return false;
    if (filters.type !== 'all' && finding.type !== filters.type) return false;
    return true;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'danger';
      case 'high': return 'warning';
      case 'medium': return 'accent';
      case 'low': return 'primary';
      default: return 'secondary';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'danger';
      case 'acknowledged': return 'warning';
      case 'resolved': return 'success';
      default: return 'secondary';
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Doctor - Diagnostic Findings</EuiTitle>
        <EuiText>Loading diagnostic findings...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Doctor - Diagnostic Findings</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Doctor - Diagnostic Findings</EuiTitle>
      <EuiText>
        Evidence-based diagnostic findings with confidence levels and remediation guidance.
      </EuiText>
      <EuiSpacer />

      {/* Filter controls */}
      <EuiFlexGroup justifyContent="spaceBetween" alignItems="center" verticalSize="s">
        <EuiFlexItem basis={400}>
          <EuiTitle size={"m"}>Filters</EuiTitle>
          <EuiSpacer size="xs" />
          <EuiFlexGroup wrap>
            <EuiFlexItem>
              <EuiText size="s">Severity:</EuiText>
              <EuiSelect
                value={filters.severity}
                onChange={(e) => handleFilterChange('severity', e.target.value)}
                options={[
                  { value: 'all', text: 'All' },
                  { value: 'critical', text: 'Critical' },
                  { value: 'high', text: 'High' },
                  { value: 'medium', text: 'Medium' },
                  { value: 'low', text: 'Low' }
                ]}
              />
            </EuiFlexItem>
            <EuiFlexItem>
              <EuiText size="s">Status:</EuiText>
              <EuiSelect
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                options={[
                  { value: 'all', text: 'All' },
                  { value: 'active', text: 'Active' },
                  { value: 'acknowledged', text: 'Acknowledged' },
                  { value: 'resolved', text: 'Resolved' }
                ]}
              />
            </EuiFlexItem>
            <EuiFlexItem>
              <EuiText size="s">Type:</EuiText>
              <EuiSelect
                value={filters.type}
                onChange={(e) => handleFilterChange('type', e.target.value)}
                options={[
                  { value: 'all', text: 'All' },
                  { value: 'health', text: 'Health' },
                  { value: 'performance', text: 'Performance' },
                  { value: 'storage', text: 'Storage' },
                  { value: 'capacity', text: 'Capacity' }
                ]}
              />
            </EuiFlexItem>
          </EuiFlexGroup>
        </EuiFlexItem>
        <EuiFlexItem>
          <EuiButtonEmpty onClick={() => window.location.reload()}>
            Refresh Findings
          </EuiButtonEmpty>
        </EuiFlexItem>
      </EuiFlexGroup>

      <EuiSpacer />

      {filteredFindings.length === 0 ? (
        <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
          <EuiText>No findings match your filters</EuiText>
        </EuiFlexGroup>
      ) : (
        <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="m">
          {filteredFindings.map((finding: any, idx: number) => (
            <EuiFlexItem key={finding.id || idx} grow={false} shrink={false} basis={350}>
              <EuiCard>
                <EuiCardBody>
                  <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="xs">
                    <EuiFlexItem>
                      <EuiTitle size={"s"}>{finding.title || 'Finding'}</EuiTitle>
                    </EuiFlexItem>
                    <EuiFlexItem>
                      <EuiFlexGroup wrap justifyContent="flexEnd">
                        <EuiBadge color={getSeverityColor(finding.severity)}>{finding.severity}</EuiBadge>
                        <EuiBadge color={getStatusColor(finding.status)}>{finding.status}</EuiBadge>
                      </EuiFlexGroup>
                    </EuiFlexItem>
                  </EuiFlexGroup>

                  <EuiHorizontalRule marginSize="xs" />

                  <EuiText size="s">
                    {finding.description || 'No description available'}
                  </EuiText>

                  <EuiHorizontalRule marginSize="xs" />

                  <EuiTitle size={"xxs"}>Evidence</EuiTitle>
                  <EuiTable responsive={false}>
                    <EuiTableHeader>
                      <EuiTableHeaderContent>
                        <EuiTableCell>Metric</EuiTableCell>
                        <EuiTableCell>Value</EuiTableCell>
                      </EuiTableHeaderContent>
                    </EuiTableHeader>
                    {(finding.evidence || []).map((ev: any, evIdx: number) => (
                      <EuiTableRow key={evIdx}>
                        <EuiTableCell>{ev.metric || ev.key || 'unknown'}</EuiTableCell>
                        <EuiTableCell>{ev.value || 'unknown'}</EuiTableCell>
                      </EuiTableRow>
                    ))}
                  </EuiTable>

                  <EuiHorizontalRule marginSize="xs" />

                  <EuiTitle size={"xxs"}>Remediation</EuiTitle>
                  <EuiText size="s" color="text">
                    {finding.remediation || 'No remediation guidance available'}
                  </EuiText>

                  <EuiHorizontalRule marginSize="xs" />

                  <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="xs">
                    <EuiFlexItem basis={50}>
                      <EuiText size="xs">Confidence: {finding.confidence?.toFixed(1) || 'N/A'}%</EuiText>
                    </EuiFlexItem>
                    <EuiFlexItem basis={50}>
                      <EuiText size="xs">Root Cause: {finding.root_cause || 'unknown'}</EuiText>
                    </EuiFlexItem>
                  </EuiFlexGroup>

                  <EuiSpacer size="s" />

                  <EuiFlexGroup justifyContent="flexEnd" wrap>
                    <EuiButtonEmpty size="s">
                      Acknowledge
                    </EuiButtonEmpty>
                    <EuiButtonEmpty size="s">
                      Resolve
                    </EuiButtonEmpty>
                  </EuiFlexGroup>
                </EuiCardBody>
              </EuiCard>
            </EuiFlexItem>
          ))}
        </EuiFlexGroup>
      )}

      {/* Summary */}
      <EuiSpacer />
      <EuiFlexGroup justifyContent="flexEnd" verticalSize="s">
        <EuiText>
          Showing {filteredFindings.length} of {findings.length} findings
        </EuiText>
      </EuiFlexGroup>
    </>
  );
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'danger';
    case 'high': return 'warning';
    case 'medium': return 'accent';
    case 'low': return 'primary';
    default: return 'secondary';
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'danger';
    case 'acknowledged': return 'warning';
    case 'resolved': return 'success';
    default: return 'secondary';
  }
};

const handleFilterChange = (key: string, value: string) => {
  // This is a placeholder - in a real component this would use useState setter
  console.log(`Filter ${key} changed to ${value}`);
};

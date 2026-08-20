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
  EuiAccordion
} from '@elastic/eui';

export const OptimizerPage: React.FC = () => {
  const [optimizations, setOptimizations] = useState<any[]>([]);
  const [totalSavings, setTotalSavings] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<{
    category: 'all' | 'storage' | 'shard' | 'capacity' | 'retention';
    priority: 'all' | 'high' | 'medium' | 'low';
    status: 'all' | 'pending' | 'applied' | 'deferred';
  }>({
    category: 'all',
    priority: 'all',
    status: 'all'
  });

  useEffect(() => {
    const fetchOptimizations = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/guardian/optimizer/suggestions');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setOptimizations(data.optimizations || []);
        setTotalSavings(data.total_savings || 0);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };

    fetchOptimizations();
  }, []);

  // Filter optimizations based on current filters
  const filteredOptimizations = optimizations.filter(opt => {
    if (filters.category !== 'all' && opt.category !== filters.category) return false;
    if (filters.priority !== 'all' && opt.priority !== filters.priority) return false;
    if (filters.status !== 'all' && opt.status !== filters.status) return false;
    return true;
  });

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'storage': return 'primary';
      case 'shard': return 'accent';
      case 'capacity': return 'warning';
      case 'retention': return 'success';
      default: return 'secondary';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'danger';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'secondary';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'applied': return 'success';
      case 'deferred': return 'ghost';
      default: return 'secondary';
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Optimizer</EuiTitle>
        <EuiText>Loading optimization suggestions...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Optimizer</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Optimizer</EuiTitle>
      <EuiText>
        Observability cost optimization recommendations with transparent assumptions.
      </EuiText>
      <EuiSpacer />

      {/* Summary card */}
      <EuiCard>
        <EuiCardBody>
          <EuiFlexGroup justifyContent="spaceBetween" alignItems="center">
            <EuiFlexItem>
              <EuiTitle size={"m"}>Total Estimated Savings</EuiTitle>
              <EuiText color="success" size="xl">
                ${totalSavings.toLocaleString()}/month
              </EuiText>
              <EuiText size="s" color="textSecondary">
                Based on {filteredOptimizations.length} active optimization suggestions
              </EuiText>
            </EuiFlexItem>
            <EuiFlexItem>
              <EuiButtonEmpty>Export Report</EuiButtonEmpty>
              <EuiButtonEmpty>Apply All</EuiButtonEmpty>
            </EuiFlexItem>
          </EuiFlexGroup>
        </EuiCardBody>
      </EuiCard>

      <EuiSpacer />

      {/* Filter controls */}
      <EuiFlexGroup justifyContent="spaceBetween" alignItems="center" verticalSize="s">
        <EuiFlexItem basis={600}>
          <EuiTitle size={"m"}>Filters</EuiTitle>
          <EuiSpacer size="xs" />
          <EuiFlexGroup wrap>
            <EuiFlexItem>
              <EuiText size="s">Category:</EuiText>
              <EuiSelect
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                options={[
                  { value: 'all', text: 'All' },
                  { value: 'storage', text: 'Storage' },
                  { value: 'shard', text: 'Shard' },
                  { value: 'capacity', text: 'Capacity' },
                  { value: 'retention', text: 'Retention' }
                ]}
              />
            </EuiFlexItem>
            <EuiFlexItem>
              <EuiText size="s">Priority:</EuiText>
              <EuiSelect
                value={filters.priority}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
                options={[
                  { value: 'all', text: 'All' },
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
                  { value: 'pending', text: 'Pending' },
                  { value: 'applied', text: 'Applied' },
                  { value: 'deferred', text: 'Deferred' }
                ]}
              />
            </EuiFlexItem>
          </EuiFlexGroup>
        </EuiFlexItem>
        <EuiFlexItem>
          <EuiButtonEmpty onClick={() => window.location.reload()}>
            Refresh
          </EuiButtonEmpty>
        </EuiFlexItem>
      </EuiFlexGroup>

      <EuiSpacer />

      {filteredOptimizations.length === 0 ? (
        <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
          <EuiText>No optimization suggestions match your filters</EuiText>
        </EuiFlexGroup>
      ) : (
        <EuiAccordion>
          {filteredOptimizations.map((opt: any, idx: number) => (
            <EuiAccordion
              key={opt.id || idx}
              isActive={idx === 0}
              text={`${opt.title || 'Optimization'} - ${opt.category}`}
            >
              <EuiAccordion items={null}>
                <EuiCard>
                  <EuiCardBody>
                    <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="xs">
                      <EuiFlexItem>
                        <EuiTitle size={"s"}>{opt.title || 'Optimization'}</EuiTitle>
                        <EuiText size="s" color="textSecondary">{opt.description || 'No description'}</EuiText>
                      </EuiFlexItem>
                      <EuiFlexItem>
                        <EuiFlexGroup wrap justifyContent="flexEnd">
                          <EuiBadge color={getCategoryColor(opt.category)}>{opt.category}</EuiBadge>
                          <EuiBadge color={getPriorityColor(opt.priority)}>{opt.priority}</EuiBadge>
                          <EuiBadge color={getStatusColor(opt.status)}>{opt.status}</EuiBadge>
                        </EuiFlexGroup>
                      </EuiFlexItem>
                    </EuiFlexGroup>

                    <EuiHorizontalRule marginSize="xs" />

                    <EuiTitle size={"xxs"}>Estimated Savings</EuiTitle>
                    <EuiTable responsive={false}>
                      <EuiTableHeader>
                        <EuiTableHeaderContent>
                          <EuiTableCell>Metric</EuiTableCell>
                          <EuiTableCell>Value</EuiTableCell>
                        </EuiTableHeaderContent>
                      </EuiTableHeader>
                      <EuiTableRow>
                        <EuiTableCell>Monthly Savings</EuiTableCell>
                        <EuiTableCell color="success">${opt.monthly_savings?.toLocaleString() || 0}</EuiTableCell>
                      </EuiTableRow>
                      <EuiTableRow>
                        <EuiTableCell>Annual Savings</EuiTableCell>
                        <EuiTableCell color="success">${(opt.monthly_savings * 12)?.toLocaleString() || 0}</EuiTableCell>
                      </EuiTableRow>
                      <EuiTableRow>
                        <EuiTableCell>Confidence</EuiTableCell>
                        <EuiTableCell>{opt.confidence?.toFixed(1) || 'N/A'}%</EuiTableCell>
                      </EuiTableRow>
                    </EuiTable>

                    <EuiHorizontalRule marginSize="xs" />

                    <EuiTitle size={"xxs"}>Assumptions</EuiTitle>
                    <EuiText size="s" color="text">
                      {opt.assumptions || 'No assumptions documented'}
                    </EuiText>

                    <EuiHorizontalRule marginSize="xs" />

                    <EuiTitle size={"xxs"}>Evidence</EuiTitle>
                    <EuiTable responsive={false}>
                      <EuiTableHeader>
                        <EuiTableHeaderContent>
                          <EuiTableCell>Metric</EuiTableCell>
                          <EuiTableCell>Current</EuiTableCell>
                          <EuiTableCell>Projected</EuiTableCell>
                          <EuiTableCell>Change</EuiTableCell>
                        </EuiTableHeaderContent>
                      </EuiTableHeader>
                      {(opt.evidence || []).map((ev: any, evIdx: number) => (
                        <EuiTableRow key={evIdx}>
                          <EuiTableCell>{ev.metric || ev.key || 'unknown'}</EuiTableCell>
                          <EuiTableCell>{ev.current || 'N/A'}</EuiTableCell>
                          <EuiTableCell>{ev.projected || 'N/A'}</EuiTableCell>
                          <EuiTableCell color={ev.change?.includes('-') ? 'danger' : 'success'}>
                            {ev.change || 'N/A'}
                          </EuiTableCell>
                        </EuiTableRow>
                      ))}
                    </EuiTable>

                    <EuiHorizontalRule marginSize="xs" />

                    <EuiTitle size={"xxs"}>Implementation</EuiTitle>
                    <EuiText size="s" color="text">
                      {opt.implementation_steps || 'No implementation steps provided'}
                    </EuiText>

                    <EuiSpacer size="s" />

                    <EuiFlexGroup justifyContent="flexEnd" wrap>
                      <EuiButtonEmpty size="s">View Details</EuiButtonEmpty>
                      <EuiButtonEmpty size="s">Apply</EuiButtonEmpty>
                      <EuiButtonEmpty size="s">Defer</EuiButtonEmpty>
                    </EuiFlexGroup>
                  </EuiCardBody>
                </EuiCard>
              </EuiAccordion>
            </EuiAccordion>
          ))}
        </EuiAccordion>
      )}

      {/* Summary */}
      <EuiSpacer />
      <EuiFlexGroup justifyContent="flexEnd" verticalSize="s">
        <EuiText>
          Showing {filteredOptimizations.length} of {optimizations.length} suggestions
        </EuiText>
      </EuiFlexGroup>
    </>
  );
};
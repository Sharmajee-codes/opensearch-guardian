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
  EuiFilterButton
} from '@elastic/eui';

export const RecommendationsPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<{
    category: 'all' | 'performance' | 'cost' | 'security' | 'capacity' | 'health';
    priority: 'all' | 'high' | 'medium' | 'low';
    status: 'all' | 'pending' | 'applied' | 'deferred' | 'dismissed';
  }>({
    category: 'all',
    priority: 'all',
    status: 'all'
  });

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/guardian/recommendations/list');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setRecommendations(data.recommendations || []);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, []);

  // Filter recommendations based on current filters
  const filteredRecommendations = recommendations.filter(rec => {
    if (filters.category !== 'all' && rec.category !== filters.category) return false;
    if (filters.priority !== 'all' && rec.priority !== filters.priority) return false;
    if (filters.status !== 'all' && rec.status !== filters.status) return false;
    return true;
  });

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'performance': return 'primary';
      case 'cost': return 'success';
      case 'security': return 'danger';
      case 'capacity': return 'warning';
      case 'health': return 'accent';
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
      case 'deferred': return 'secondary';
      case 'dismissed': return 'ghost';
      default: return 'secondary';
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Recommendations</EuiTitle>
        <EuiText>Loading recommendations data...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Recommendations</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Recommendations</EuiTitle>
      <EuiText>
        Actionable recommendations based on Guardian diagnostic findings.
      </EuiText>
      <EuiSpacer />

      {/* Summary cards */}
      <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="m">
        <EuiFlexItem grow={false} shrink={false} basis={200}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"xxs"}>Total</EuiTitle>
              <EuiText size="xl">{recommendations.length}</EuiText>
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>

        <EuiFlexItem grow={false} shrink={false} basis={200}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"xxs"}>Pending</EuiTitle>
              <EuiText size="xl" color="warning">
                {recommendations.filter(r => r.status === 'pending').length}
              </EuiText>
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>

        <EuiFlexItem grow={false} shrink={false} basis={200}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"xxs"}>High Priority</EuiTitle>
              <EuiText size="xl" color="danger">
                {recommendations.filter(r => r.priority === 'high' && r.status === 'pending').length}
              </EuiText>
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>

        <EuiFlexItem grow={false} shrink={false} basis={200}>
          <EuiCard>
            <EuiCardBody>
              <EuiTitle size={"xxs"}>Applied</EuiTitle>
              <EuiText size="xl" color="success">
                {recommendations.filter(r => r.status === 'applied').length}
              </EuiText>
            </EuiCardBody>
          </EuiCard>
        </EuiFlexItem>
      </EuiFlexGroup>

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
                  { value: 'performance', text: 'Performance' },
                  { value: 'cost', text: 'Cost' },
                  { value: 'security', text: 'Security' },
                  { value: 'capacity', text: 'Capacity' },
                  { value: 'health', text: 'Health' }
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
                  { value: 'deferred', text: 'Deferred' },
                  { value: 'dismissed', text: 'Dismissed' }
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

      {filteredRecommendations.length === 0 ? (
        <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
          <EuiText>No recommendations match your filters</EuiText>
        </EuiFlexGroup>
      ) : (
        <EuiAccordion>
          {filteredRecommendations.map((rec: any, idx: number) => (
            <EuiAccordion
              key={rec.id || idx}
              isActive={idx === 0}
              text={`${rec.title || 'Recommendation'} - ${rec.category}`}
            >
              <EuiAccordion items={null}>
                <EuiCard>
                  <EuiCardBody>
                    <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="xs">
                      <EuiFlexItem>
                        <EuiTitle size={"s"}>{rec.title || 'Recommendation'}</EuiTitle>
                        <EuiText size="s" color="textSecondary">{rec.description || 'No description'}</EuiText>
                      </EuiFlexItem>
                      <EuiFlexItem>
                        <EuiFlexGroup wrap justifyContent="flexEnd">
                          <EuiBadge color={getCategoryColor(rec.category)}>{rec.category}</EuiBadge>
                          <EuiBadge color={getPriorityColor(rec.priority)}>{rec.priority}</EuiBadge>
                          <EuiBadge color={getStatusColor(rec.status)}>{rec.status}</EuiBadge>
                        </EuiFlexGroup>
                      </EuiFlexItem>
                    </EuiFlexGroup>

                    <EuiHorizontalRule marginSize="xs" />

                    <EuiTitle size={"xxs"}>Impact Analysis</EuiTitle>
                    <EuiTable responsive={false}>
                      <EuiTableHeader>
                        <EuiTableHeaderContent>
                          <EuiTableCell>Metric</EuiTableCell>
                          <EuiTableCell>Current</EuiTableCell>
                          <EuiTableCell>Projected</EuiTableCell>
                          <EuiTableCell>Improvement</EuiTableCell>
                        </EuiTableHeaderContent>
                      </EuiTableHeader>
                      {(rec.impact || []).map((impact: any, impactIdx: number) => (
                        <EuiTableRow key={impactIdx}>
                          <EuiTableCell>{impact.metric || impact.key || 'unknown'}</EuiTableCell>
                          <EuiTableCell>{impact.current || 'N/A'}</EuiTableCell>
                          <EuiTableCell>{impact.projected || 'N/A'}</EuiTableCell>
                          <EuiTableCell color={impact.improvement?.includes('+') || impact.improvement?.includes('-') ? 'success' : undefined}>
                            {impact.improvement || 'N/A'}
                          </EuiTableCell>
                        </EuiTableRow>
                      ))}
                    </EuiTable>

                    <EuiHorizontalRule marginSize="xs" />

                    <EuiTitle size={"xxs"}>Implementation</EuiTitle>
                    <EuiText size="s" color="text">
                      {rec.implementation_steps || 'No implementation steps provided'}
                    </EuiText>

                    <EuiHorizontalRule marginSize="xs" />

                    <EuiFlexGroup justifyContent="spaceBetween" wrap verticalSize="xs">
                      <EuiFlexItem basis={50}>
                        <EuiText size="xs">Confidence: {rec.confidence?.toFixed(1) || 'N/A'}%</EuiText>
                      </EuiFlexItem>
                      <EuiFlexItem basis={50}>
                        <EuiText size="xs">Risk Level: {rec.risk_level || 'unknown'}</EuiText>
                      </EuiFlexItem>
                    </EuiFlexGroup>

                    <EuiSpacer size="s" />

                    <EuiFlexGroup justifyContent="flexEnd" wrap>
                      <EuiButtonEmpty size="s">Apply Now</EuiButtonEmpty>
                      <EuiButtonEmpty size="s">Defer</EuiButtonEmpty>
                      <EuiButtonEmpty size="s">Dismiss</EuiButtonEmpty>
                      <EuiButtonEmpty size="s">View Details</EuiButtonEmpty>
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
          Showing {filteredRecommendations.length} of {recommendations.length} recommendations
        </EuiText>
      </EuiFlexGroup>
    </>
  );
};
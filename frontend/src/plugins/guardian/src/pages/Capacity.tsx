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
  EuiButton,
  EuiNumberInput
} from '@elastic/eui';
import { guardianApi } from '../services/apiService';

export const CapacityPage: React.FC = () => {
  const [capacityData, setCapacityData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [forecastDays, setForecastDays] = useState<number>(30);

  useEffect(() => {
    const fetchCapacity = async () => {
      try {
        setLoading(true);
        const response = await guardianApi.getCapacityPlanning(forecastDays);
        setCapacityData(response);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };
    fetchCapacity();
  }, [forecastDays]);

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Capacity Planning</EuiTitle>
        <EuiText>Loading capacity planning data...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Capacity Planning</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiFlexGroup justifyContent="spaceBetween" alignItems="center">
        <EuiTitle size={"l"}>Capacity Planning</EuiTitle>
        <EuiFlexGroup justifyContent="flexStart" alignItems="center">
          <EuiText>Forecast period: </EuiText>
          <EuiNumberInput
            min={7}
            max={365}
            value={forecastDays}
            onChange={(value) => setForecastDays(value)}
            inputLabel="Days"
            unitLabel="days"
          />
          <EuiButton onClick={() => {
            guardianApi.getCapacityPlanning(forecastDays).then(data => setCapacityData(data));
          }} disabled={loading}>
            Update Forecast
          </EuiButton>
        </EuiFlexGroup>
      </EuiFlexGroup>
      <EuiText>Projected resource utilization, growth trends, and scaling recommendations.</EuiText>
      <EuiSpacer />
      
      {error && (
        <EuiCard>
          <EuiCardBody>
            <EuiText color="danger">Error: {error}</EuiText>
          </EuiCardBody>
        </EuiCard>
      )}
      
      {capacityData && (
        <>
          <EuiFlexGroup justifyContent="spaceBetween" wrap>
            <EuiFlexItem grow={false} shrink={false} basis={400}>
              <EuiCard>
                <EuiCardBody>
                  <EuiTitle size={"m"}>Resource Utilization</EuiTitle>
                  {capacityData.utilization && (
                    <EuiTable responsive={false}>
                      <EuiTableHeader>
                        <EuiTableHeaderContent>
                          <EuiTableCell>Resource</EuiTableCell>
                          <EuiTableCell>Current</EuiTableCell>
                          <EuiTableCell>Projected</EuiTableCell>
                          <EuiTableCell>Growth</EuiTableCell>
                        </EuiTableHeaderContent>
                      </EuiTableHeader>
                      {Object.entries(capacityData.utilization).map(([resource, data]: [string, any], idx: number) => (
                        <EuiTableRow key={idx}>
                          <EuiTableCell>{resource}</EuiTableCell>
                          <EuiTableCell>{(data.current || 0).toFixed(1)}%</EuiTableCell>
                          <EuiTableCell>{(data.projected || 0).toFixed(1)}%</EuiTableCell>
                          <EuiTableCell color={((data.projected || 0) - (data.current || 0)) > 5 ? 'warning' : 'success'}>
                            {(((data.projected || 0) - (data.current || 0)).toFixed(1))}/day
                          </EuiTableCell>
                        </EuiTableRow>
                      ))}
                    </EuiTable>
                  )}
                </EuiCardBody>
              </EuiCard>
            </EuiFlexItem>
            
            <EuiFlexItem grow={false} shrink={false} basis={400}>
              <EuiCard>
                <EuiCardBody>
                  <EuiTitle size={"m"}>Scaling Recommendations</EuiTitle>
                  {capacityData.recommendations && capacityData.recommendations.length > 0 ? (
                    <EuiTable responsive={false}>
                      <EuiTableHeader>
                        <EuiTableHeaderContent>
                          <EuiTableCell>Recommendation</EuiTableCell>
                          <EuiTableCell>Type</EuiTableCell>
                          <EuiTableCell>Urgency</EuiTableCell>
                          <EuiTableCell>Action</EuiTableCell>
                        </EuiTableHeaderContent>
                      </EuiTableHeader>
                      {capacityData.recommendations.map((rec: any, idx: number) => (
                        <EuiTableRow key={idx}>
                          <EuiTableCell title={rec.description}>
                            {rec.title || `Recommendation ${idx + 1}`}
                          </EuiTableCell>
                          <EuiTableCell>
                            <EuiBadge color={rec.type === 'scale_up' ? 'danger' : rec.type === 'scale_down' ? 'warning' : rec.type === 'optimize' ? 'accent' : 'primary'}>
                              {rec.type?.replace('_', ' ').toUpperCase()}
                            </EuiBadge>
                          </EuiTableCell>
                          <EuiTableCell>
                            <EuiBadge color={rec.urgency === 'high' ? 'danger' : rec.urgency === 'medium' ? 'warning' : 'success'}>
                              {rec.urgency?.toUpperCase()}
                            </EuiBadge>
                          </EuiTableCell>
                          <EuiTableCell>
                            <EuiButton size="xs" onClick={() => {
                              alert(`Would execute: ${rec.action}
Requires approval for safety level: ${rec.safety_level || 'unknown'}`);
                            }}>
                              Execute
                            </EuiButton>
                          </EuiTableCell>
                        </EuiTableRow>
                      ))}
                    </EuiTable>
                  ) : (
                    <EuiText>No scaling recommendations at this time</EuiText>
                  )}
                </EuiCardBody>
              </EuiCard>
            </EuiFlexItem>
          </EuiFlexGroup>
        </>
      )}
      
      <EuiFlexGroup justifyContent="flexEnd">
        <EuiButtonEmpty onClick={() => window.location.reload()}>Refresh</EuiButtonEmpty>
      </EuiFlexGroup>
    </>
  );
};

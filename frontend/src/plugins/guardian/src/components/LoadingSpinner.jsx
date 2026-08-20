import React from 'react';
import {
  EuiFlexGroup,
  EuiFlexItem,
  EuiText,
  EuiSpinner
} from '@elastic/eui';

export const LoadingSpinner = ({ message = 'Loading...' }) => {
  return (
    <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
      <EuiFlexItem>
        <EuiSpinner size="xl" />
      </EuiFlexItem>
      <EuiFlexItem>
        <EuiText size="m">{message}</EuiText>
      </EuiFlexItem>
    </EuiFlexGroup>
  );
};

export default LoadingSpinner;

import React from 'react';
import {
  EuiAlert,
  EuiFlexGroup,
  EuiFlexItem,
  EuiText,
  EuiIcon
} from '@elastic/eui';

export const AlertBox = ({ type = 'info', title, children, onClose }) => {
  const colorMap = {
    success: 'success',
    warning: 'warning',
    danger: 'danger',
    info: 'primary',
    error: 'danger'
  };

  const iconMap = {
    success: 'check',
    warning: 'warning',
    danger: 'alert',
    info: 'iInCircle',
    error: 'alert'
  };

  return (
    <EuiAlert
      color={colorMap[type] || colorMap.info}
      iconType={iconMap[type] || iconMap.info}
      title={title}
    >
      {children}
      {onClose && (
        <EuiFlexGroup justifyContent="flexEnd">
          <EuiFlexItem grow={false}>
            <EuiIcon type={iconMap[type] || iconMap.info} size="m" />
          </EuiFlexItem>
        </EuiFlexGroup>
      )}
    </EuiAlert>
  );
};

export default AlertBox;

import React from 'react';
import {
  EuiEmptyPrompt,
  EuiText,
  EuiButton
} from '@elastic/eui';

export const NotFoundPage = ({ onGoHome }) => {
  return (
    <EuiEmptyPrompt
      title={<EuiText>Page not found</EuiText>}
      body={
        <EuiText>
          The page you're looking for doesn't exist or has been moved.
        </EuiText>
      }
      actions={
        <EuiButton onClick={onGoHome} color="primary">
          Go to overview
        </EuiButton>
      }
    />
  );
};

export default NotFoundPage;

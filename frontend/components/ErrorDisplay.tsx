// components/ErrorDisplay.tsx
import React from 'react';
import { 
  ERROR_STYLES, 
  ErrorIcon, 
  RetryButton 
} from '@/lib/utils';

interface ErrorDisplayProps {
  message?: string;
  retry?: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  message = 'Something went wrong. Please try again.',
  retry
}) => {
  return (
    <div className={ERROR_STYLES.CONTAINER}>
      <ErrorIcon />
      <h3 className={ERROR_STYLES.TITLE}>Error</h3>
      <p className={ERROR_STYLES.MESSAGE}>{message}</p>
      {retry && <RetryButton onClick={retry} />}
    </div>
  );
};
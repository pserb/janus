// components/ErrorDisplay.tsx
import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorDisplayProps {
  message?: string;
  retry?: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  message = 'Something went wrong. Please try again.',
  retry
}) => {
  return (
    <div className="flex flex-col items-center justify-center w-full py-12 px-4 text-center">
      <div className="bg-red-100 text-red-800 rounded-full p-3 mb-4">
        <AlertTriangle className="h-8 w-8" />
      </div>
      <h3 className="text-lg font-medium mb-2">Error</h3>
      <p className="text-muted-foreground mb-6 max-w-md">{message}</p>
      {retry && (
        <Button onClick={retry} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      )}
    </div>
  );
};
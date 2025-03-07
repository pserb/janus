// components/LoadingSkeleton.tsx
import React from 'react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';

export const JobCardSkeleton: React.FC = () => {
  return (
    <Card className="w-full h-full">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="h-6 w-3/4 bg-gray-200 rounded animate-pulse-gentle"></div>
            <div className="h-4 w-1/2 bg-gray-200 rounded mt-2 animate-pulse-gentle"></div>
          </div>
          <div className="h-5 w-20 bg-gray-200 rounded animate-pulse-gentle"></div>
        </div>
      </CardHeader>
      
      <CardContent className="pb-2">
        <div className="text-sm mt-1">
          <div className="h-4 w-1/3 bg-gray-200 rounded animate-pulse-gentle"></div>
          <div className="h-4 w-full bg-gray-200 rounded mt-3 animate-pulse-gentle"></div>
          <div className="h-4 w-full bg-gray-200 rounded mt-1 animate-pulse-gentle"></div>
        </div>
      </CardContent>
      
      <CardFooter className="pt-0 flex gap-2 justify-between">
        <div className="h-9 w-28 bg-gray-200 rounded animate-pulse-gentle"></div>
        <div className="h-9 w-28 bg-gray-200 rounded animate-pulse-gentle"></div>
      </CardFooter>
    </Card>
  );
};

export const JobListSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <JobCardSkeleton key={index} />
      ))}
    </div>
  );
};
// components/LoadingSkeleton.tsx
import React from 'react';
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card';
import { LOADING_STYLES } from '@/lib/utils';

export const JobCardSkeleton: React.FC = () => {
  return (
    <Card className="w-full h-full">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className={`h-6 w-3/4 ${LOADING_STYLES.SKELETON_BG} rounded`}></div>
            <div className={`h-4 w-1/2 ${LOADING_STYLES.SKELETON_BG} rounded mt-2`}></div>
          </div>
          <div className={`h-5 w-20 ${LOADING_STYLES.SKELETON_BG} rounded`}></div>
        </div>
      </CardHeader>
      
      <CardContent className="pb-2">
        <div className="text-sm mt-1">
          <div className={`h-4 w-1/3 ${LOADING_STYLES.SKELETON_BG} rounded`}></div>
          <div className={`h-4 w-full ${LOADING_STYLES.SKELETON_BG} rounded mt-3`}></div>
          <div className={`h-4 w-full ${LOADING_STYLES.SKELETON_BG} rounded mt-1`}></div>
        </div>
      </CardContent>
      
      <CardFooter className="pt-0 flex gap-2 justify-between">
        <div className={`h-9 w-28 ${LOADING_STYLES.SKELETON_BG} rounded`}></div>
        <div className={`h-9 w-28 ${LOADING_STYLES.SKELETON_BG} rounded`}></div>
      </CardFooter>
    </Card>
  );
};

export const JobListSkeleton: React.FC = () => {
  return (
    <div className={LOADING_STYLES.CONTAINER_CLASSES}>
      {Array.from({ length: 6 }).map((_, index) => (
        <JobCardSkeleton key={index} />
      ))}
    </div>
  );
};
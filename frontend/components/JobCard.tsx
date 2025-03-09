// components/JobCard.tsx
import React, { useState } from 'react';
import { ExternalLink, Building, Ellipsis } from 'lucide-react';
import { Job } from '@/types';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  formatDate,
  getRelativeTime,
  truncateText,
  getCompanyTicker,
  getJobCategoryBadgeProps,
  getJobStatusBadgeProps,
} from '@/lib/utils';
import Image from 'next/image';

interface JobCardProps {
  job: Job;
  onViewDetails?: (job: Job) => void;
}

export const JobCard: React.FC<JobCardProps> = ({ job, onViewDetails }) => {
  // Always define state at the top level, not conditionally
  const [logoError, setLogoError] = useState(false);

  // Get company ticker for logo
  const ticker = getCompanyTicker(job.company_name);

  // Get badge styling from centralized utility
  const categoryBadgeProps = getJobCategoryBadgeProps(job.category);
  const statusBadgeProps = getJobStatusBadgeProps(job.is_new);

  return (
    <Card className="w-full h-full flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex flex-col space-y-2">
          {/* Company & Badge Row */}
          <div className="flex justify-between items-center">
            {/* Company Logo & Name (Left) */}
            <div className="flex items-center text-sm text-muted-foreground">
              {ticker && !logoError ? (
                <div className="h-7 w-7 mr-2 relative">
                  <Image
                    src={`/logos/company_logos/${ticker}.svg`}
                    alt={`${job.company_name} logo`}
                    className="object-contain rounded"
                    fill
                    sizes="28px"
                    onError={() => setLogoError(true)}
                  />
                </div>
              ) : (
                <Building className="h-4 w-4 mr-1" />
              )}
              <span className="font-medium">{job.company_name}</span>
            </div>

            {/* Badges (Right) */}
            <div className="flex gap-2 ml-auto">
              {statusBadgeProps && (
                <Badge variant={statusBadgeProps.variant} icon={statusBadgeProps.icon}>
                  {statusBadgeProps.label}
                </Badge>
              )}
              <Badge
                variant={categoryBadgeProps.variant}
                icon={categoryBadgeProps.icon}
              >
                {categoryBadgeProps.label}
              </Badge>
            </div>
          </div>

          {/* Job Title - Fixed height with ellipsis for overflow */}
          <div className="h-[3rem]"> {/* Fixed height container */}
            <CardTitle className="text-lg font-bold line-clamp-2">
              {job.title}
            </CardTitle>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-2 flex-grow flex flex-col -mt-4">
        <div className="text-sm flex flex-col h-full">
          {/* Posted Date - Fixed height */}
          <div className="text-muted-foreground mb-3">
            <span className="font-medium">Posted:</span> {formatDate(job.posting_date)} ({getRelativeTime(job.posting_date)})
          </div>

          {/* Description - Takes remaining space with fixed height */}
          <div className="flex-grow">
            <p className="line-clamp-2 text-sm">
              {truncateText(job.requirements_summary || job.description || 'No specific requirements extracted.')}
            </p>
          </div>
        </div>
      </CardContent>

      {/* Footer always at the bottom */}
      <CardFooter className="pt-2 mt-auto">
        <div className="w-full flex justify-between items-center">
          <Button
            className='cursor-pointer'
            variant="outline"
            size="sm"
            onClick={() => onViewDetails && onViewDetails(job)}
          >
            <Ellipsis className="h-4 w-4 mr-2" />
            View Details
          </Button>

          <Button
            className='cursor-pointer'
            variant="secondary"
            size="sm"
            onClick={() => window.open(job.link, '_blank')}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Apply Now
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};
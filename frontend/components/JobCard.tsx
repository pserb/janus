// components/JobCard.tsx
import React, { useState } from 'react';
import { ExternalLink, Briefcase, Building } from 'lucide-react';
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
    <Card className="w-full h-full transition-all hover:shadow-md">
      <CardHeader className="pb-2">
        <div className="flex flex-col space-y-2">
          <div className="flex-1">
            <CardTitle className="text-lg font-bold line-clamp-2">{job.title}</CardTitle>
            <div className="flex flex-wrap gap-2 sm:flex-nowrap sm:items-start mt-2">
              {statusBadgeProps && (
                <Badge variant={statusBadgeProps.variant}>
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
            <div className="flex items-center text-sm text-muted-foreground mt-4 ml-[0.1rem]">
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
          </div>

        </div>
      </CardHeader>

      <CardContent className="pb-2 -mt-2">
        <div className="text-sm">
          <div className="text-muted-foreground">
            <span className="font-medium">Posted:</span> {formatDate(job.posting_date)} ({getRelativeTime(job.posting_date)})
          </div>
          <div className="mt-3">
            <p className="line-clamp-2 text-sm mt-1">{truncateText(job.requirements_summary || job.description || '')}</p>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-0 flex gap-2 justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onViewDetails && onViewDetails(job)}
        >
          <Briefcase className="h-4 w-4 mr-2" />
          View Details
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => window.open(job.link, '_blank')}
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          Apply Now
        </Button>
      </CardFooter>
    </Card>
  );
};
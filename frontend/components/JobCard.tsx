// components/JobCard.tsx
import React from 'react';
import { ExternalLink, Briefcase, Building } from 'lucide-react';
import { Job } from '@/types';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate, getRelativeTime, truncateText } from '@/lib/utils';

interface JobCardProps {
  job: Job;
  onViewDetails?: (job: Job) => void;
}

export const JobCard: React.FC<JobCardProps> = ({ job, onViewDetails }) => {
  return (
    <Card className="w-full h-full transition-all hover:shadow-md">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-bold line-clamp-2">{job.title}</CardTitle>
            <div className="flex items-center text-sm text-muted-foreground mt-1">
              <Building className="h-4 w-4 mr-1" />
              <span className="font-medium">{job.company_name}</span>
            </div>
          </div>
          <div className="flex gap-2">
            {job.is_new && <Badge variant="default">New</Badge>}
            <Badge variant="default">{job.category === 'software' ? 'Software' : 'Hardware'}</Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pb-2">
        <div className="text-sm mt-1">
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
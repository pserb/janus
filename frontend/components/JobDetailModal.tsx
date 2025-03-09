// components/JobDetailModal.tsx
import React, { useState } from 'react';
import { ExternalLink, X, Building } from 'lucide-react';
import { Job } from '@/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  formatDate, 
  getCompanyTicker,
  getJobCategoryBadgeProps,
  getJobStatusBadgeProps,
  MODAL_STYLES,
  StatusIcons,
  JOB_DESCRIPTION_STYLES,
  LAYOUT
} from '@/lib/utils';
import * as Dialog from '@radix-ui/react-dialog';
import Image from 'next/image';

interface JobDetailModalProps {
  job: Job | null;
  isOpen: boolean;
  onClose: () => void;
}

export const JobDetailModal: React.FC<JobDetailModalProps> = ({ job, isOpen, onClose }) => {
  // Always declare hooks at the top level
  const [logoError, setLogoError] = useState(false);
  
  if (!job) return null;

  // Get company ticker for logo - after hooks but before return
  const ticker = getCompanyTicker(job.company_name);
  
  // Get badge styling from centralized utility
  const categoryBadgeProps = getJobCategoryBadgeProps(job.category);
  const statusBadgeProps = getJobStatusBadgeProps(job.is_new);

  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className={MODAL_STYLES.OVERLAY} />
        <Dialog.Content className={MODAL_STYLES.CONTENT}>
          <div className="flex justify-between items-start mb-4">
            <Dialog.Title className="text-xl font-bold">
              {job.title}
            </Dialog.Title>
            <Dialog.Close asChild>
              <Button variant="ghost" size="icon" className="h-6 w-6 rounded-full" aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            </Dialog.Close>
          </div>
          
          <div className={LAYOUT.SECTION_SPACING}>
            <div className={`flex flex-wrap ${LAYOUT.GAP_SMALL} items-center`}>
              <div className="flex items-center gap-1">
                {ticker && !logoError ? (
                  <div className="h-6 w-6 mr-1 relative">
                    <Image 
                      src={`/logos/company_logos/${ticker}.svg`}
                      alt={`${job.company_name} logo`}
                      className="object-contain rounded"
                      fill
                      sizes="24px"
                      onError={() => setLogoError(true)}
                    />
                  </div>
                ) : (
                  <Building className="h-4 w-4 text-muted-foreground" />
                )}
                <span className="font-medium">{job.company_name}</span>
              </div>
              
              <div className="flex items-center gap-1">
                {StatusIcons.CALENDAR}
                <span>{formatDate(job.posting_date)}</span>
              </div>
              
              <Badge 
                variant={categoryBadgeProps.variant}
                icon={categoryBadgeProps.icon}
              >
                {categoryBadgeProps.label}
              </Badge>
              
              {statusBadgeProps && (
                <Badge variant={statusBadgeProps.variant} icon={statusBadgeProps.icon}>
                  {statusBadgeProps.label}
                </Badge>
              )}
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-2">Requirements Summary</h3>
              <p className="whitespace-pre-line">
                {job.requirements_summary || "No summary available."}
              </p>
            </div>
            
            <div className="mt-6">
              <h3 className="text-lg font-medium mb-2">Job Description</h3>
              <div className={JOB_DESCRIPTION_STYLES.CONTAINER}>
                {job.description || "No description available."}
              </div>
            </div>
            
            <div className="pt-4 flex justify-end">
              <Button onClick={() => window.open(job.link, '_blank')}>
                <ExternalLink className="h-4 w-4 mr-2" />
                Apply on Company Website
              </Button>
            </div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
};
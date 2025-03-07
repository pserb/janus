// components/JobDetailModal.tsx
import React from 'react';
import { ExternalLink, X, Calendar, Building, Tag } from 'lucide-react';
import { Job } from '@/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import * as Dialog from '@radix-ui/react-dialog';

interface JobDetailModalProps {
  job: Job | null;
  isOpen: boolean;
  onClose: () => void;
}

export const JobDetailModal: React.FC<JobDetailModalProps> = ({ job, isOpen, onClose }) => {
  if (!job) return null;

  return (
    <Dialog.Root open={isOpen} onOpenChange={onClose}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content className="fixed left-[50%] top-[50%] max-h-[85vh] w-[90vw] max-w-[700px] translate-x-[-50%] translate-y-[-50%] rounded-[6px] bg-white p-[25px] shadow-[hsl(206_22%_7%_/_35%)_0px_10px_38px_-10px,_hsl(206_22%_7%_/_20%)_0px_10px_20px_-15px] focus:outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] dark:bg-slate-900 overflow-y-auto">
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
          
          <div className="space-y-6">
            <div className="flex flex-wrap gap-2 items-center">
              <div className="flex items-center gap-1">
                <Building className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{job.company_name}</span>
              </div>
              
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <span>{formatDate(job.posting_date)}</span>
              </div>
              
              <div className="flex items-center gap-1">
                <Tag className="h-4 w-4 text-muted-foreground" />
                <Badge variant="default">{job.category === 'software' ? 'Software' : 'Hardware'}</Badge>
              </div>
              
              {job.is_new == 1 ? <Badge variant="default">New</Badge> : null}
            </div>
            
            <div>
              <h3 className="text-lg font-medium mb-2">Requirements Summary</h3>
              <p className="whitespace-pre-line">
                {job.requirements_summary || "No summary available."}
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-medium mb-2">Job Description</h3>
              <div className="whitespace-pre-line max-h-[300px] overflow-y-auto border rounded-md p-4 bg-gray-50 dark:bg-slate-800">
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
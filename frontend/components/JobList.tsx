// components/JobList.tsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
import { Job, JobFilters } from '@/types';
import { JobCard } from '@/components/JobCard';
import { JobDetailModal } from '@/components/JobDetailModal';
import { JobFiltersComponent } from '@/components/JobFilters';
import { Button } from '@/components/ui/button';
import { getJobsWithFilters } from '@/lib/db';
import { syncJobs } from '@/lib/api';
import { toast } from 'sonner';
import { JobListSkeleton } from '@/components/LoadingSkeleton';
import { ErrorDisplay } from '@/components/ErrorDisplay';

export const JobList: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(true);
  const [filters, setFilters] = useState<JobFilters>({
    category: 'all',
    showOnlyNew: false,
    search: '',
  });
  // Track if initial load has been done
  const hasInitiallyLoaded = useRef(false);

  // Load jobs function - define with useCallback to use in dependency arrays
  const loadJobs = useCallback(async () => {
    setError(null);
    
    try {
      const filteredJobs = await getJobsWithFilters({
        category: filters.category,
        showOnlyNew: filters.showOnlyNew,
        search: filters.search,
      });
      setJobs(filteredJobs);
    } catch (err) {
      console.error('Error loading jobs:', err);
      setError('There was a problem loading job listings.');
      toast.error('Error loading jobs', {
        description: 'There was a problem loading job listings.'
      });
    }
  }, [filters]);

  // Handle sync with server
  const handleSync = useCallback(async () => {
    if (!isOnline) {
      toast.info('Offline Mode', {
        description: 'You are currently offline. Job listings will update when you reconnect.'
      });
      return;
    }

    setIsSyncing(true);

    try {
      const { newJobsCount, timestamp, isOnline: syncIsOnline } = await syncJobs();
      setLastSyncTime(timestamp);
      setIsOnline(syncIsOnline);

      // Reload jobs to reflect any changes
      await loadJobs();

      if (newJobsCount > 0) {
        toast.success('Sync Completed', {
          description: `Found ${newJobsCount} new job ${newJobsCount === 1 ? 'listing' : 'listings'}.`
        });
      } else {
        toast.success('Sync Completed', {
          description: 'You are up to date with the latest job listings.'
        });
      }
    } catch (error) {
      console.error('Error syncing jobs:', error);
      toast.error('Sync Failed', {
        description: 'There was a problem syncing job listings.'
      });
    } finally {
      setIsSyncing(false);
    }
  }, [isOnline, loadJobs]);

  // Initial load and sync
  const handleInitialLoad = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // First load data from local DB
      await loadJobs();
      
      // Then sync with server
      await handleSync();
    } catch (err) {
      console.error('Error during initial load:', err);
      setError('Failed to initialize the application. Please try refreshing the page.');
    } finally {
      setIsLoading(false);
    }
  }, [loadJobs, handleSync]);

  // Load jobs when filters change
  useEffect(() => {
    // Only reload jobs, don't sync with server when filters change
    loadJobs();
  }, [filters, loadJobs]);

  // Check online status and handle initial load
  useEffect(() => {
    const handleOnlineStatusChange = () => {
      setIsOnline(navigator.onLine);
    };

    window.addEventListener('online', handleOnlineStatusChange);
    window.addEventListener('offline', handleOnlineStatusChange);

    // Initial check
    setIsOnline(navigator.onLine);

    // Auto-sync when app opens but ONLY ONCE
    if (!hasInitiallyLoaded.current) {
      hasInitiallyLoaded.current = true;
      handleInitialLoad();
    }

    return () => {
      window.removeEventListener('online', handleOnlineStatusChange);
      window.removeEventListener('offline', handleOnlineStatusChange);
    };
  }, [handleInitialLoad]);

  // Handle filter changes
  const handleFiltersChange = (newFilters: JobFilters) => {
    setFilters(newFilters);
  };

  // Handle opening job detail modal
  const handleViewJobDetails = (job: Job) => {
    setSelectedJob(job);
    setIsModalOpen(true);
  };

  // Handle closing job detail modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedJob(null);
  };

  return (
    <div>
      {/* Sync status and button */}
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-muted-foreground">
          {!isOnline && (
            <div className="flex items-center text-amber-600">
              <AlertCircle className="h-4 w-4 mr-1" />
              <span>Offline Mode</span>
            </div>
          )}
          {lastSyncTime && (
            <div>Last updated: {new Date(lastSyncTime).toLocaleString()}</div>
          )}
        </div>
        <Button 
          onClick={handleSync} 
          disabled={isSyncing || isLoading || !isOnline}
          size="sm"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isSyncing ? 'animate-spin' : ''}`} />
          {isSyncing ? 'Syncing...' : 'Refresh'}
        </Button>
      </div>

      {/* Filters */}
      <JobFiltersComponent 
        filters={filters} 
        onFiltersChange={handleFiltersChange} 
        totalJobs={jobs.length} 
      />

      {/* Content area */}
      {isLoading ? (
        <JobListSkeleton />
      ) : error ? (
        <ErrorDisplay message={error} retry={handleInitialLoad} />
      ) : jobs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-lg font-medium">No jobs found</p>
          <p className="text-muted-foreground mt-1">
            Try adjusting your filters or sync to look for new jobs
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onViewDetails={handleViewJobDetails}
            />
          ))}
        </div>
      )}

      {/* Job detail modal */}
      <JobDetailModal 
        job={selectedJob} 
        isOpen={isModalOpen} 
        onClose={handleCloseModal} 
      />
    </div>
  );
};
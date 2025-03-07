// ib/api.ts
import axios from 'axios';
import { Job, PaginatedResponse, JobListingStats } from '@/types';
import { getSyncInfo, saveJobs, updateSyncTimestamp } from '@/lib/db';

// Base URL for API - would be environment variable in production
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create an axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Fetch jobs from the API
export async function fetchJobs({
  page = 1,
  pageSize = 50,
  category = 'all',
  since = undefined
}: {
  page?: number;
  pageSize?: number;
  category?: string;
  since?: string;
}): Promise<PaginatedResponse<Job>> {
  try {
    const params: Record<string, string | number> = {
      page,
      page_size: pageSize,
      category
    };

    if (since) {
      params.since = since;
    }

    const response = await api.get<PaginatedResponse<Job>>('/jobs', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching jobs:', error);
    throw new Error('Failed to fetch jobs');
  }
}

// Fetch stats from the API
export async function fetchStats(): Promise<JobListingStats> {
  try {
    const response = await api.get<JobListingStats>('/stats');
    return response.data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw new Error('Failed to fetch stats');
  }
}

// Sync jobs with the local database
export async function syncJobs(): Promise<{
  newJobsCount: number;
  timestamp: string;
  isOnline: boolean;
}> {
  try {
    // Check if online
    if (!navigator.onLine) {
      return {
        newJobsCount: 0,
        timestamp: new Date().toISOString(),
        isOnline: false
      };
    }

    // Get the last sync timestamp
    const syncInfo = await getSyncInfo();
    const { last_sync_timestamp } = syncInfo;

    // Fetch new jobs since last sync
    const response = await fetchJobs({
      since: last_sync_timestamp,
      pageSize: 100 // Fetch more jobs when syncing (max allowed by API)
    });

    // Return early if no new jobs
    if (response.items.length === 0) {
      // Still update the timestamp
      const newTimestamp = new Date().toISOString();
      await updateSyncTimestamp(newTimestamp);
      
      return {
        newJobsCount: 0,
        timestamp: newTimestamp,
        isOnline: true
      };
    }

    // Mark newly fetched jobs as "new"
    const newJobs = response.items.map(job => ({
      ...job,
      is_new: 1  // Changed from boolean to number (1) for IndexedDB compatibility
    }));

    // Save jobs to local database
    await saveJobs(newJobs);

    // Update the sync timestamp
    const newTimestamp = new Date().toISOString();
    await updateSyncTimestamp(newTimestamp);

    return {
      newJobsCount: newJobs.length,
      timestamp: newTimestamp,
      isOnline: true
    };
  } catch (error) {
    console.error('Error syncing jobs:', error);
    throw new Error('Failed to sync jobs');
  }
}
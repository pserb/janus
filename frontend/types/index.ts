// types/index.ts
export interface Job {
  id: number;
  company_id: number;
  company_name: string;
  title: string;
  link: string;
  posting_date: string;
  discovery_date: string;
  category: 'software' | 'hardware';
  description: string;
  requirements_summary: string;
  is_active: boolean;
  is_new: number;
}

export interface Company {
  id: number;
  name: string;
  career_page_url: string;
}

export interface SyncInfo {
  id?: number;
  last_sync_timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface JobFilters {
  category?: string; 
  search?: string;
  showOnlyNew?: boolean;
}

export interface JobListingStats {
  total_jobs: number;
  software_jobs: number;
  hardware_jobs: number;
  new_jobs: number;
  last_update_time: string;
}
// src/lib/db.ts
import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { Job, SyncInfo } from '@/types';

interface JanusDB extends DBSchema {
  jobs: {
    key: number;
    value: Job;
    indexes: {
      'by-company': number;
      'by-category': string;
      'by-posting-date': string;
      'by-is-new': boolean;
    };
  };
  sync_info: {
    key: number;
    value: SyncInfo;
  };
}

let dbPromise: Promise<IDBPDatabase<JanusDB>> | null = null;

const DB_NAME = 'janus-db';
const DB_VERSION = 1;

export async function getDb() {
  if (!dbPromise) {
    dbPromise = openDB<JanusDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        // Create jobs store
        const jobStore = db.createObjectStore('jobs', { keyPath: 'id' });
        jobStore.createIndex('by-company', 'company_id');
        jobStore.createIndex('by-category', 'category');
        jobStore.createIndex('by-posting-date', 'posting_date');
        jobStore.createIndex('by-is-new', 'is_new');

        // Create sync info store
        db.createObjectStore('sync_info', { keyPath: 'id' });

        // Initialize sync_info with default value
        const syncStore = db.transaction('sync_info', 'readwrite').objectStore('sync_info');
        syncStore.put({
          id: 1,
          last_sync_timestamp: new Date(0).toISOString()
        });
      },
    });
  }
  return dbPromise;
}

// Job CRUD operations
export async function getAllJobs(): Promise<Job[]> {
  const db = await getDb();
  return db.getAll('jobs');
}

export async function getJobById(id: number): Promise<Job | undefined> {
  const db = await getDb();
  return db.get('jobs', id);
}

export async function saveJob(job: Job): Promise<number> {
  const db = await getDb();
  return db.put('jobs', job);
}

export async function saveJobs(jobs: Job[]): Promise<void> {
  const db = await getDb();
  const tx = db.transaction('jobs', 'readwrite');
  await Promise.all([
    ...jobs.map(job => tx.store.put(job)),
    tx.done
  ]);
}

export async function deleteJob(id: number): Promise<void> {
  const db = await getDb();
  await db.delete('jobs', id);
}

export async function clearJobs(): Promise<void> {
  const db = await getDb();
  await db.clear('jobs');
}

// Sync info operations
export async function getSyncInfo(): Promise<SyncInfo> {
  const db = await getDb();
  const syncInfo = await db.get('sync_info', 1);
  return syncInfo || { last_sync_timestamp: new Date(0).toISOString() };
}

export async function updateSyncTimestamp(timestamp: string): Promise<void> {
  const db = await getDb();
  await db.put('sync_info', {
    id: 1,
    last_sync_timestamp: timestamp
  });
}

// Query operations
export async function getJobsByCategory(category: string): Promise<Job[]> {
  const db = await getDb();
  return db.getAllFromIndex('jobs', 'by-category', category);
}

export async function getNewJobs(): Promise<Job[]> {
  const db = await getDb();
  return db.getAllFromIndex('jobs', 'by-is-new', true);
}

export async function getJobsWithFilters({
  category = 'all',
  showOnlyNew = false,
  search = ''
}: {
  category?: string;
  showOnlyNew?: boolean;
  search?: string;
}): Promise<Job[]> {
  const db = await getDb();
  let jobs: Job[] = [];
  
  if (category !== 'all') {
    jobs = await db.getAllFromIndex('jobs', 'by-category', category);
  } else {
    jobs = await db.getAll('jobs');
  }
  
  if (showOnlyNew) {
    jobs = jobs.filter(job => job.is_new);
  }
  
  if (search && search.trim() !== '') {
    const searchLower = search.toLowerCase();
    jobs = jobs.filter(job => 
      job.title.toLowerCase().includes(searchLower) ||
      job.company_name.toLowerCase().includes(searchLower) ||
      job.description?.toLowerCase().includes(searchLower) ||
      job.requirements_summary?.toLowerCase().includes(searchLower)
    );
  }
  
  // Sort by posting date (newest first)
  jobs.sort((a, b) => new Date(b.posting_date).getTime() - new Date(a.posting_date).getTime());
  
  return jobs;
}
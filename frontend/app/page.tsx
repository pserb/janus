// app/page.tsx
'use client';

import React from 'react';
import { Header } from '@/components/Header';
import { JobList } from '@/components/JobList';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      <Header />
      
      <div className="container mx-auto py-8 px-4 flex-1">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold mb-6">Latest Internships & Entry-Level Positions</h2>
          
          <JobList />
        </div>
      </div>
      
      <footer className="border-t py-6 mt-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} Janus - Internship Tracker</p>
        </div>
      </footer>
    </main>
  );
}
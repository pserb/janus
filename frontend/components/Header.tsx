// components/Header.tsx
import React from 'react';
import { Briefcase } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="bg-primary text-primary-foreground py-4 px-6 shadow-md">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Briefcase className="h-6 w-6" />
          <h1 className="text-xl font-bold">Janus</h1>
          <span className="text-sm bg-primary-foreground text-primary px-1.5 py-0.5 rounded-md ml-2 opacity-80">Internship Tracker</span>
        </div>
        <div className="text-sm">
          <span className="opacity-80">Helping students find opportunities</span>
        </div>
      </div>
    </header>
  );
};
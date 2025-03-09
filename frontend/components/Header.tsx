import React from 'react';
import { Briefcase } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Badge } from '@/components/ui/badge';

export const Header: React.FC = () => {
  return (
    <header className="bg-background border-b py-4 px-6">
      <div className="container mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Briefcase className="h-6 w-6" />
          <h1 className="text-xl font-bold">Janus</h1>
          <Badge variant="sky-subtle" size="lg" className="ml-1">Internship Tracker</Badge>
          <Badge variant="sky" size="lg" className="ml-1">Internship Tracker</Badge>
        </div>
        <div className="flex items-center gap-4">
          <Badge variant="secondary">Helping students find opportunities</Badge>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
};
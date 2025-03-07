// components/JobFilters.tsx
import React from 'react';
import { Search, Filter, SlidersHorizontal } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { JobFilters } from '@/types';
import * as Label from '@radix-ui/react-label';
import * as Select from '@radix-ui/react-select';

interface JobFiltersProps {
  filters: JobFilters;
  onFiltersChange: (filters: JobFilters) => void;
  totalJobs: number;
}

export const JobFiltersComponent: React.FC<JobFiltersProps> = ({
  filters,
  onFiltersChange,
  totalJobs,
}) => {
  // Handle category change
  const handleCategoryChange = (value: string) => {
    onFiltersChange({
      ...filters,
      category: value as 'software' | 'hardware' | 'all',
    });
  };

  // Handle search input change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      search: e.target.value,
    });
  };

  // Handle show only new toggle
  const handleShowOnlyNewChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      showOnlyNew: e.target.checked,
    });
  };

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search input */}
          <div className="flex-1">
            <Label.Root className="text-sm font-medium mb-1.5 block">
              Search Jobs
            </Label.Root>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by title, company, or keywords..."
                className="w-full pl-9 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                value={filters.search || ''}
                onChange={handleSearchChange}
              />
            </div>
          </div>

          {/* Category filter */}
          <div className="w-full md:w-48">
            <Label.Root className="text-sm font-medium mb-1.5 block">
              Category
            </Label.Root>
            <Select.Root
              value={filters.category || 'all'}
              onValueChange={handleCategoryChange}
            >
              <Select.Trigger
                className="inline-flex items-center justify-between w-full rounded-md border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary data-[placeholder]:text-muted-foreground"
                aria-label="Category"
              >
                <div className="flex items-center">
                  <Filter className="mr-2 h-4 w-4" />
                  <Select.Value placeholder="Select category" />
                </div>
                <Select.Icon>
                  <SlidersHorizontal className="h-4 w-4 opacity-50" />
                </Select.Icon>
              </Select.Trigger>
              <Select.Portal>
                <Select.Content className="overflow-hidden bg-popover rounded-md border shadow-md">
                  <Select.Viewport className="p-1">
                    <Select.Item
                      value="all"
                      className="relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                    >
                      <Select.ItemText>All Categories</Select.ItemText>
                    </Select.Item>
                    <Select.Item
                      value="software"
                      className="relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                    >
                      <Select.ItemText>Software</Select.ItemText>
                    </Select.Item>
                    <Select.Item
                      value="hardware"
                      className="relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                    >
                      <Select.ItemText>Hardware</Select.ItemText>
                    </Select.Item>
                  </Select.Viewport>
                </Select.Content>
              </Select.Portal>
            </Select.Root>
          </div>

          {/* Show only new checkbox */}
          <div className="w-full md:w-48">
            <div className="flex items-center h-full pt-6">
              <input
                type="checkbox"
                id="showOnlyNew"
                className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                checked={filters.showOnlyNew || false}
                onChange={handleShowOnlyNewChange}
              />
              <label
                htmlFor="showOnlyNew"
                className="ml-2 block text-sm font-medium"
              >
                Show only new jobs
              </label>
            </div>
          </div>
        </div>

        {/* Results count */}
        <div className="mt-4 text-sm text-muted-foreground">
          Showing {totalJobs} {totalJobs === 1 ? 'result' : 'results'}
        </div>
      </CardContent>
    </Card>
  );
};
// components/JobFilters.tsx
import React from 'react';
import { Search, Filter } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { JobFilters } from '@/types';
import * as Label from '@radix-ui/react-label';
import { Badge } from '@/components/ui/badge';
import {
  getAllJobCategories,
  getJobCategoryBadgeProps,
  getJobStatusBadgeProps,
  type JobCategory
} from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

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
  // Get all available job categories
  const jobCategories: JobCategory[] = getAllJobCategories();

  // Handle category change
  const handleCategoryChange = (value: string) => {
    onFiltersChange({
      ...filters,
      category: value,
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

  const newBadgeProps = getJobStatusBadgeProps(true);

  // Get the current category selection for display
  const currentCategory: JobCategory | null = filters.category === 'all'
    ? null
    : getJobCategoryBadgeProps(filters.category || '');

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

          {/* Category filter - Using shadcn/ui Select component */}
          <div className="w-full md:w-48">
            <Label.Root className="text-sm font-medium mb-1.5 block">
              Category
            </Label.Root>
            <Select
              value={filters.category || 'all'}
              onValueChange={handleCategoryChange}
            >
              <SelectTrigger
                className="w-full h-[38px] py-2 px-3"
              >
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 flex-shrink-0" />
                  <SelectValue placeholder="Select category">
                    {currentCategory ? (
                      <div className="flex items-center"> {/* Add flex container for alignment */}
                        <Badge
                          variant={currentCategory.variant}
                          icon={currentCategory.icon}
                          size="md"
                          className="inline-flex items-center" /* Ensure badge content is aligned */
                        >
                          {currentCategory.label}
                        </Badge>
                      </div>
                    ) : (
                      <span className="flex items-center h-5">All Categories</span> /* Match height for consistent alignment */
                    )}
                  </SelectValue>
                </div>
              </SelectTrigger>
              <SelectContent>
                {/* All Categories option */}
                <SelectItem value="all">
                  <span className="flex items-center h-5">All Categories</span> {/* Match height */}
                </SelectItem>

                {/* Dynamically generate category options */}
                {jobCategories.map(category => (
                  <SelectItem key={category.id} value={category.id}>
                    <div className="flex items-center"> {/* Add flex container for alignment */}
                      <Badge
                        variant={category.variant}
                        icon={category.icon}
                        size="md"
                        className="inline-flex items-center" /* Ensure badge content is aligned */
                      >
                        {category.label}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
                className="ml-2 flex flex-row text-sm font-medium gap-x-1"
              >
                Show only
                {newBadgeProps && <Badge variant={newBadgeProps.variant} icon={newBadgeProps.icon} className="ml-1">
                  {newBadgeProps.label}
                </Badge>}
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
'use client';

import React, { useState } from 'react';
import { Job, JobFilters } from '@/types';
import { Header } from '@/components/Header';
import { JobCard } from '@/components/JobCard';
import { JobDetailModal } from '@/components/JobDetailModal';
import { JobFiltersComponent } from '@/components/JobFilters';
import { JobListSkeleton } from '@/components/LoadingSkeleton';
import { ErrorDisplay } from '@/components/ErrorDisplay';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ExternalLink, Star, Clock, Calendar } from 'lucide-react';
import { BADGE_VARIANTS, getJobCategoryBadgeProps } from '@/lib/utils';

// Mock data for demo purposes
const mockJobs: Job[] = [
  {
    id: 1,
    company_id: 1,
    company_name: 'Google',
    title: 'Software Engineering Intern - Summer 2026',
    link: 'https://careers.google.com/jobs/123',
    posting_date: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(), // 2 days ago
    discovery_date: new Date().toISOString(),
    category: 'software',
    description: 'Google is looking for Software Engineering Interns to join our team for Summer 2026. As an intern, you will work on real projects and have mentorship from experienced engineers. You will have the opportunity to apply your skills in areas such as frontend, backend, mobile, or machine learning.\n\nRequirements:\n• Currently pursuing a BS, MS, or PhD in Computer Science or related field\n• Strong knowledge of data structures and algorithms\n• Experience with one or more programming languages (e.g. Java, Python, C++, JavaScript)\n• Good problem-solving skills\n• Ability to work in a team environment',
    requirements_summary: '• Currently pursuing a BS, MS, or PhD in Computer Science\n• Strong knowledge of data structures and algorithms\n• Experience with Java, Python, C++, or JavaScript',
    is_active: true,
    is_new: 1
  },
  {
    id: 2,
    company_id: 2,
    company_name: 'Apple',
    title: 'Hardware Engineering Intern',
    link: 'https://jobs.apple.com/en-us/details/456',
    posting_date: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(), // 7 days ago
    discovery_date: new Date().toISOString(),
    category: 'hardware',
    description: 'Apple is seeking a Hardware Engineering Intern to join our hardware engineering team. In this role, you will help design and test next-generation hardware components for Apple products.\n\nResponsibilities:\n• Support the design and testing of hardware components\n• Analyze test data and document results\n• Collaborate with cross-functional teams\n• Contribute to innovative solutions for complex problems\n\nRequirements:\n• Currently pursuing a degree in Electrical Engineering, Computer Engineering, or related field\n• Familiarity with circuit design and analysis\n• Understanding of digital/analog electronics principles\n• Knowledge of hardware description languages (e.g., VHDL, Verilog) is a plus\n• Strong problem-solving skills and attention to detail',
    requirements_summary: '• Pursuing a degree in Electrical Engineering or Computer Engineering\n• Familiarity with circuit design and analysis\n• Understanding of digital/analog electronics principles',
    is_active: true,
    is_new: 0
  },
  {
    id: 3,
    company_id: 3,
    company_name: 'Microsoft',
    title: 'Software Development Engineer Intern',
    link: 'https://careers.microsoft.com/students/jobs/789',
    posting_date: new Date(Date.now() - 1000 * 60 * 60 * 24 * 1).toISOString(), // 1 day ago
    discovery_date: new Date().toISOString(),
    category: 'software',
    description: 'Microsoft is looking for Software Development Engineer Interns to work on challenging projects with experienced mentors.\n\nAs an intern, you will:\n• Design and develop features for Microsoft products\n• Work with experienced engineers on real-world projects\n• Learn about software development processes at scale\n• Participate in code reviews and design discussions\n\nRequirements:\n• Currently pursuing a degree in Computer Science, Software Engineering, or related field\n• Strong coding skills in at least one programming language\n• Knowledge of data structures and algorithms\n• Passion for technology and innovation',
    requirements_summary: '• Pursuing a degree in Computer Science or Software Engineering\n• Strong coding skills in at least one programming language\n• Knowledge of data structures and algorithms',
    is_active: true,
    is_new: 1
  },
  {
    id: 4,
    company_id: 4,
    company_name: 'Nvidia',
    title: 'Hardware Design Engineer Intern',
    link: 'https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/123',
    posting_date: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(), // 5 days ago
    discovery_date: new Date().toISOString(),
    category: 'hardware',
    description: 'Nvidia is seeking a Hardware Design Engineer Intern to join our growing team. In this role, you will work on cutting-edge hardware designs for next-generation GPUs and AI accelerators.\n\nResponsibilities:\n• Assist in the design and validation of hardware components\n• Develop test cases and analyze test results\n• Document design specifications and test procedures\n• Collaborate with cross-functional teams\n\nRequirements:\n• Currently pursuing a degree in Electrical Engineering, Computer Engineering, or related field\n• Understanding of digital logic design and computer architecture\n• Experience with hardware description languages (Verilog/VHDL)\n• Familiarity with circuit simulation tools\n• Strong problem-solving skills',
    requirements_summary: '• Pursuing a degree in Electrical Engineering or Computer Engineering\n• Understanding of digital logic design and computer architecture\n• Experience with hardware description languages (Verilog/VHDL)',
    is_active: true,
    is_new: 0
  }
];

export default function DemoPage() {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filters, setFilters] = useState<JobFilters>({
    category: 'all',
    showOnlyNew: false,
    search: '',
  });

  const handleViewJobDetails = (job: Job) => {
    setSelectedJob(job);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedJob(null);
  };

  const handleFiltersChange = (newFilters: JobFilters) => {
    setFilters(newFilters);
  };

  // Get badge props for categories from our centralized utility
  const softwareBadgeProps = getJobCategoryBadgeProps('software');
  const hardwareBadgeProps = getJobCategoryBadgeProps('hardware');

  return (
    <main className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-3xl font-bold mb-8">Janus Component Demo</h1>
        
        {/* Header Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Header Component</h2>
          <p className="text-muted-foreground mb-4">The main application header with app name and theme toggle.</p>
          <div className="border rounded-lg p-4 bg-muted/10">
            <Header />
          </div>
        </section>

        {/* Filters Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Job Filters</h2>
          <p className="text-muted-foreground mb-4">Filter controls for job listings with search, category selection, and new job toggle.</p>
          <div className="border rounded-lg p-4 bg-muted/10">
            <JobFiltersComponent 
              filters={filters} 
              onFiltersChange={handleFiltersChange} 
              totalJobs={mockJobs.length} 
            />
          </div>
        </section>

        {/* Job Cards Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Job Cards</h2>
          <p className="text-muted-foreground mb-4">Cards displaying job information with category badges and action buttons.</p>
          
          <h3 className="text-xl font-medium mb-3">Software Jobs</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {mockJobs
              .filter(job => job.category === 'software')
              .map(job => (
                <div key={job.id} className="h-full">
                  <JobCard job={job} onViewDetails={handleViewJobDetails} />
                </div>
              ))
            }
          </div>
          
          <h3 className="text-xl font-medium mb-3">Hardware Jobs</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {mockJobs
              .filter(job => job.category === 'hardware')
              .map(job => (
                <div key={job.id} className="h-full">
                  <JobCard job={job} onViewDetails={handleViewJobDetails} />
                </div>
              ))
            }
          </div>
        </section>
        
        {/* Loading States Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Loading States</h2>
          <p className="text-muted-foreground mb-4">Skeleton loaders shown while content is loading.</p>
          <JobListSkeleton />
        </section>
        
        {/* Error States Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Error States</h2>
          <p className="text-muted-foreground mb-4">Error messages displayed when something goes wrong.</p>
          <ErrorDisplay 
            message="We couldn't load the job listings. Please try again later." 
            retry={() => alert('Retry action triggered')}
          />
        </section>
        
        {/* Badge Variants Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Badge Variants</h2>
          <p className="text-muted-foreground mb-4">Different badge styles used throughout the application with centralized configuration.</p>
          
          <Card>
            <CardHeader>
              <CardTitle>Job Category Badges</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                <Badge 
                  variant={softwareBadgeProps.variant}
                  icon={softwareBadgeProps.icon}
                >
                  {softwareBadgeProps.label}
                </Badge>
                <Badge 
                  variant={hardwareBadgeProps.variant}
                  icon={hardwareBadgeProps.icon}
                >
                  {hardwareBadgeProps.label}
                </Badge>
                <Badge variant={BADGE_VARIANTS.NEW}>
                  New
                </Badge>
                <Badge variant="secondary">
                  Default
                </Badge>
                <Badge variant="outline">
                  Outline
                </Badge>
              </div>
            </CardContent>
          </Card>
          
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Other Badge Examples Using Centralized Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                <Badge variant={BADGE_VARIANTS.SOFTWARE} icon={<Star className="h-3 w-3" />}>
                  Featured
                </Badge>
                <Badge variant={BADGE_VARIANTS.HARDWARE} icon={<Clock className="h-3 w-3" />}>
                  Urgent
                </Badge>
                <Badge variant={BADGE_VARIANTS.NEW} icon={<Calendar className="h-3 w-3" />}>
                  Upcoming
                </Badge>
              </div>
            </CardContent>
          </Card>
        </section>
        
        {/* Button Variants Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 pb-2 border-b">Button Variants</h2>
          <p className="text-muted-foreground mb-4">Different button styles used throughout the application.</p>
          
          <Card>
            <CardHeader>
              <CardTitle>Action Buttons</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-4">
                <Button>
                  Default Button
                </Button>
                <Button variant="outline">
                  Outline Button
                </Button>
                <Button variant="ghost">
                  Ghost Button
                </Button>
                <Button variant="secondary">
                  Secondary Button
                </Button>
                <Button variant="destructive">
                  Destructive Button
                </Button>
                <Button>
                  <ExternalLink className="h-4 w-4 mr-2" />
                  With Icon
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
      
      {/* Job Detail Modal */}
      <JobDetailModal 
        job={selectedJob} 
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
      
      {/* Demo Modal Trigger */}
      <div className="fixed bottom-4 right-4">
        <Button 
          onClick={() => handleViewJobDetails(mockJobs[0])}
          size="lg"
        >
          Show Job Detail Modal
        </Button>
      </div>
    </main>
  );
}
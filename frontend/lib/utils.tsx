// lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, formatDistance } from 'date-fns'
import { AlertTriangle, Code, Cpu, RefreshCw, Calendar, Clock, Zap } from 'lucide-react';
import React from 'react'
import { badgeVariants } from "@/components/ui/badge"

/**
 * Combines class names using clsx and tailwind-merge
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Formats a date in a human-readable format
 */
export function formatDate(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return format(dateObj, 'MMM d, yyyy')
}

/**
 * Returns a relative time string (e.g. "2 days ago")
 */
export function getRelativeTime(date: Date | string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return formatDistance(dateObj, new Date(), { addSuffix: true })
}

/**
 * Truncates text to a specified length
 */
export function truncateText(text: string, maxLength: number = 150): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Creates a unique ID for use with lists, etc.
 */
export function createUniqueId(): string {
  return Math.random().toString(36).substring(2, 9)
}

/**
 * Maps company names to their ticker symbols
 */
export function getCompanyTicker(companyName: string): string | null {
  if (!companyName) return null;

  // Normalize the company name (lowercase, remove Inc., Corp., etc.)
  const normalizedName = companyName.toLowerCase()
    .replace(/\binc\.?\b|\bcorp\.?\b|\bco\.?\b|\bcompany\b|\bcorporation\b|\blimited\b|\bltd\.?\b/g, '')
    .trim();

  // Common company name to ticker mappings
  const companyMap: Record<string, string> = {
    'adobe': 'ADBE',
    'advanced micro devices': 'AMD',
    'airbnb': 'ABNB',
    'alibaba': 'BABA',
    'alphabet': 'GOOGL',
    'amazon': 'AMZN',
    'amd': 'AMD',
    'analog devices': 'ADI',
    'apple': 'AAPL',
    'applied materials': 'AMAT',
    'atlassian': 'TEAM',
    'autodesk': 'ADSK',
    'baidu': 'BIDU',
    'block': 'SQ',
    'booking holdings': 'BKNG',
    'broadcom': 'AVGO',
    'c3.ai': 'AI',
    'cadence design systems': 'CDNS',
    'cisco': 'CSCO',
    'cloudflare': 'NET',
    'coinbase': 'COIN',
    'crowdstrike': 'CRWD',
    'datadog': 'DDOG',
    'dell': 'DELL',
    'digital ocean': 'DOCN',
    'docusign': 'DOCU',
    'doordash': 'DASH',
    'ebay': 'EBAY',
    'expedia': 'EXPE',
    'facebook': 'META',
    'fortinet': 'FTNT',
    'github': 'MSFT',
    'google': 'GOOGL',
    'hewlett packard enterprise': 'HPE',
    'hp': 'HPQ',
    'ibm': 'IBM',
    'intel': 'INTC',
    'intuit': 'INTU',
    'jd.com': 'JD',
    'lam research': 'LRCX',
    'linkedin': 'MSFT',
    'lyft': 'LYFT',
    'match group': 'MTCH',
    'meta': 'META',
    'micron technology': 'MU',
    'microsoft': 'MSFT',
    'mongodb': 'MDB',
    'netflix': 'NFLX',
    'nvidia': 'NVDA',
    'okta': 'OKTA',
    'oracle': 'ORCL',
    'palo alto networks': 'PANW',
    'palantir': 'PLTR',
    'paypal': 'PYPL',
    'pinterest': 'PINS',
    'qualcomm': 'QCOM',
    'roblox': 'RBLX',
    'roku': 'ROKU',
    'salesforce': 'CRM',
    'seagate technology': 'STX',
    'servicenow': 'NOW',
    'shopify': 'SHOP',
    'snap': 'SNAP',
    'snowflake': 'SNOW',
    'splunk': 'SPLK',
    'spotify': 'SPOT',
    'square': 'SQ',
    'synopsys': 'SNPS',
    'tencent': 'TCEHY',
    'tesla': 'TSLA',
    'texas instruments': 'TXN',
    'twilio': 'TWLO',
    'twitter': 'TWTR',
    'uber': 'UBER',
    'unity': 'U',
    'vmware': 'VMW',
    'western digital': 'WDC',
    'workday': 'WDAY',
    'zoom': 'ZM',
    'zscaler': 'ZS'
  };

  // Check for matches
  for (const [name, ticker] of Object.entries(companyMap)) {
    if (normalizedName.includes(name)) {
      return ticker;
    }
  }

  // If no match found
  return null;
}

type BadgeVariantType = NonNullable<Parameters<typeof badgeVariants>[0]>['variant'];


/**
 * Configuration for badge design elements
 */
export const BADGE_VARIANTS: Record<string, BadgeVariantType> = {
  // Status badges
  NEW: 'green',

  // Job categories
  SOFTWARE: 'indigo-subtle',
  HARDWARE: 'amber-subtle',

  // Default fallback
  DEFAULT: 'secondary'
} as const;

/**
 * Gets badge styling information for job status (new, etc.)
 */
export function getJobStatusBadgeProps(isNew: boolean | number) {
  if (isNew) {
    return {
      variant: BADGE_VARIANTS.NEW,
      icon: StatusIcons.NEW,
      label: 'New',
    };
  }
  return null;
}

// Interface for job category configuration
export interface JobCategory {
  id: string;
  label: string;
  variant: BadgeVariantType;
  icon: React.ReactNode;
}

export type JobCategoriesConfig = {
  [key: string]: JobCategory;
};

// Job Category Configuration
export const JOB_CATEGORIES: JobCategoriesConfig = {
  software: {
    id: 'software',
    label: 'Software',
    variant: BADGE_VARIANTS.SOFTWARE,
    icon: <Code className="h-3 w-3 text-current" />
  },
  hardware: {
    id: 'hardware',
    label: 'Hardware',
    variant: BADGE_VARIANTS.HARDWARE,
    icon: <Cpu className="h-3 w-3 text-current" />
  },
  // Additional categories can be added here in the future
  // e.g. design: { id: 'design', label: 'Design', variant: 'purple-subtle', icon: <Paintbrush className="h-3 w-3" /> }
};

// Helper to get all categories as an array
export function getAllJobCategories() {
  return Object.values(JOB_CATEGORIES);
}

// Updated function to use the centralized configuration
export function getJobCategoryBadgeProps(categoryId: string) {
  return JOB_CATEGORIES[categoryId] || {
    id: categoryId,
    label: categoryId,
    variant: BADGE_VARIANTS.DEFAULT,
    icon: null
  };
}

// Existing code continues...

/**
 * Common animation classes
 */
export const ANIMATIONS = {
  FADE_IN: "animate-in fade-in-0",
  FADE_OUT: "animate-out fade-out-0",
  ZOOM_IN: "animate-in zoom-in-95",
  ZOOM_OUT: "animate-out zoom-out-95",
  SLIDE_IN_FROM_TOP: "animate-in slide-in-from-top-[48%]",
  SLIDE_OUT_TO_TOP: "animate-out slide-out-to-top-[48%]",
  SLIDE_IN_FROM_LEFT: "animate-in slide-in-from-left-1/2",
  SLIDE_OUT_TO_LEFT: "animate-out slide-out-to-left-1/2",
  PULSE_GENTLE: "animate-pulse-gentle"
} as const;

/**
 * Modal styling
 */
export const MODAL_STYLES = {
  OVERLAY: `fixed inset-0 bg-black/50 data-[state=open]:${ANIMATIONS.FADE_IN} data-[state=closed]:${ANIMATIONS.FADE_OUT}`,
  CONTENT: `fixed left-[50%] top-[50%] max-h-[85vh] w-[90vw] max-w-[700px] translate-x-[-50%] translate-y-[-50%] 
    rounded-[6px] p-[25px] shadow-[hsl(206_22%_7%_/_35%)_0px_10px_38px_-10px,_hsl(206_22%_7%_/_20%)_0px_10px_20px_-15px] 
    focus:outline-none data-[state=open]:${ANIMATIONS.FADE_IN} data-[state=closed]:${ANIMATIONS.FADE_OUT} 
    data-[state=closed]:${ANIMATIONS.ZOOM_OUT} data-[state=open]:${ANIMATIONS.ZOOM_IN} 
    data-[state=closed]:${ANIMATIONS.SLIDE_OUT_TO_LEFT} data-[state=closed]:${ANIMATIONS.SLIDE_OUT_TO_TOP} 
    data-[state=open]:${ANIMATIONS.SLIDE_IN_FROM_LEFT} data-[state=open]:${ANIMATIONS.SLIDE_IN_FROM_TOP} 
    overflow-y-auto bg-slate-100 dark:bg-slate-900 border`
} as const;

/**
 * Loading state styling
 */
export const LOADING_STYLES = {
  SKELETON_BG: "bg-gray-200 animate-pulse",
  CONTAINER_CLASSES: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
} as const;

/**
 * Error state styling and components
 */
export const ERROR_STYLES = {
  CONTAINER: "flex flex-col items-center justify-center w-full py-12 px-4 text-center",
  ICON_CONTAINER: "bg-red-100 text-red-800 rounded-full p-3 mb-4",
  TITLE: "text-lg font-medium mb-2",
  MESSAGE: "text-muted-foreground mb-6 max-w-md"
} as const;

export const ErrorIcon = () => (
  <div className={ERROR_STYLES.ICON_CONTAINER}>
    <AlertTriangle className="h-8 w-8" />
  </div>
);

export const RetryButton = ({ onClick }: { onClick: () => void }) => (
  <button
    onClick={onClick}
    className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-[color,box-shadow] h-9 px-4 py-2 has-[>svg]:px-3 bg-secondary text-secondary-foreground shadow-xs hover:bg-secondary/80"
  >
    <RefreshCw className="h-4 w-4 mr-2" />
    Try Again
  </button>
);

/**
 * Layout and spacing constants
 */
export const LAYOUT = {
  CONTAINER: "container mx-auto px-4",
  CONTENT_MAX_WIDTH: "max-w-6xl",
  SECTION_SPACING: "mb-12",
  CARD_SPACING: "p-4",
  GAP_SMALL: "gap-2",
  GAP_MEDIUM: "gap-4",
  GAP_LARGE: "gap-6"
} as const;

/**
 * Job description styling
 */
export const JOB_DESCRIPTION_STYLES = {
  CONTAINER: "whitespace-pre-line max-h-[300px] overflow-y-auto border rounded-md p-4 bg-gray-50 bg-slate-200 dark:bg-slate-950"
} as const;

/**
 * Common icon components for use throughout the app
 */
export const StatusIcons = {
  NEW: <Zap className="h-3 w-3" />,
  CALENDAR: <Calendar className="h-4 w-4 text-muted-foreground" />,
  CLOCK: <Clock className="h-4 w-4 text-muted-foreground" />
};
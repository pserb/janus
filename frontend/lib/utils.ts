// lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { format, formatDistance } from 'date-fns'

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

// lib/utils.ts (append to existing file)

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
    'apple': 'AAPL',
    'microsoft': 'MSFT',
    'google': 'GOOGL',
    'alphabet': 'GOOGL',
    'amazon': 'AMZN',
    'meta': 'META',
    'facebook': 'META',
    'tesla': 'TSLA',
    'nvidia': 'NVDA',
    'netflix': 'NFLX',
    'adobe': 'ADBE',
    'salesforce': 'CRM',
    'oracle': 'ORCL',
    'ibm': 'IBM',
    'intel': 'INTC',
    'amd': 'AMD',
    'cisco': 'CSCO',
    'paypal': 'PYPL',
    'uber': 'UBER',
    'lyft': 'LYFT',
    'snap': 'SNAP',
    'square': 'SQ',
    'block': 'SQ',
    'shopify': 'SHOP',
    'zoom': 'ZM',
    'pinterest': 'PINS',
    'spotify': 'SPOT',
    'coinbase': 'COIN',
    'snowflake': 'SNOW',
    'palantir': 'PLTR',
    'roblox': 'RBLX',
    'unity': 'U',
    'c3.ai': 'AI',
    'atlassian': 'TEAM',
    'doordash': 'DASH',
    'roku': 'ROKU',
    'alibaba': 'BABA',
    'jd.com': 'JD',
    'baidu': 'BIDU',
    'tencent': 'TCEHY',
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
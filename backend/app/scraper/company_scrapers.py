# scraper/company_scrapers.py
import logging
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx
import subprocess
import tempfile
import os
from bs4 import BeautifulSoup

from app.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

class AppleScraper(BaseScraper):
    """
    Scraper for Apple's internship listings using a combination of
    httpx and BS4 with fallbacks to handle dynamic content
    """
    
    def __init__(self):
        super().__init__(
            company_name="Apple",
            career_page_url="https://jobs.apple.com/en-us/search?location=united-states-USA&team=internships-STDNT-INTRN"
        )
        self.base_url = "https://jobs.apple.com"
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape internship listings using multiple strategies"""
        self.logger.info(f"Starting scrape for {self.company_name}")
        
        jobs = []
        
        try:
            # First approach: Direct HTTP request
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(self.career_page_url)
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch {self.career_page_url}, status: {response.status_code}")
                    return jobs
                
                # Parse the HTML
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Try to extract job listings
                job_listings = self._extract_job_listings_from_html(soup)
                
                # If we found job listings, process them
                if job_listings:
                    self.logger.info(f"Found {len(job_listings)} job listings via HTML parsing")
                    
                    # Process each job listing
                    for listing in job_listings:
                        try:
                            # Get job details
                            job_response = await client.get(listing['link'])
                            if job_response.status_code == 200:
                                job_soup = BeautifulSoup(job_response.text, 'html.parser')
                                description = self._extract_job_description(job_soup)
                                
                                # Create job data
                                category = self.classify_job_category(listing['title'], description)
                                
                                job = {
                                    "title": listing['title'],
                                    "link": listing['link'],
                                    "posting_date": listing['date'],
                                    "description": description,
                                    "category": category
                                }
                                
                                jobs.append(job)
                            
                            # Small delay between requests
                            await asyncio.sleep(0.5)
                        
                        except Exception as e:
                            self.logger.error(f"Error processing job listing: {str(e)}")
                
                # If we didn't find any jobs, try the fallback method
                if not jobs:
                    self.logger.info("No jobs found via direct HTTP request, trying Chrome fallback")
                    fallback_jobs = await self._chrome_screenshot_fallback()
                    if fallback_jobs:
                        jobs.extend(fallback_jobs)
            
            self.logger.info(f"Successfully scraped {len(jobs)} internship listings from {self.company_name}")
            
        except Exception as e:
            self.logger.error(f"Error in {self.company_name} scraper: {str(e)}")
        
        return jobs
    
    def _extract_job_listings_from_html(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract job listings from HTML using BeautifulSoup"""
        job_listings = []
        
        # Try various common selectors for job listings
        job_elements = []
        
        # Try to find job listings
        selectors = [
            '.table-row',
            '.job-result',
            '.job-card',
            '[data-testid="job-card"]',
            'article',
            'div.list-container > div',  # Generic list container pattern
            '.searchResults-section > *',  # Apple's search results section
            'ul.job-list > li'  # Common job list pattern
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                job_elements.extend(elements)
                self.logger.info(f"Found {len(elements)} elements with selector: {selector}")
                break
        
        # If we didn't find any elements with those selectors, try links to job details
        if not job_elements:
            self.logger.info("No job elements found with standard selectors, trying links")
            job_links = soup.select('a[href*="/details/"]')
            
            for link in job_links:
                href = link.get('href')
                if href:
                    # Find the surrounding card/container (go up a few levels)
                    container = link
                    for _ in range(3):  # Look up to 3 levels
                        if container.parent:
                            container = container.parent
                    
                    job_elements.append(container)
        
        # Used for de-duplication
        seen_links = set()
        
        # Process each element
        for element in job_elements:
            try:
                # Find title
                title_element = element.select_one('h2, h3, h4, .job-title, .title, [class*="title"]')
                title = title_element.get_text().strip() if title_element else None
                
                # If no title found, try to get it from the link text
                if not title:
                    link_element = element.select_one('a[href*="/details/"]')
                    if link_element:
                        title = link_element.get_text().strip()
                
                # If we still don't have a title, skip this element
                if not title:
                    continue
                
                # Skip "Share this role" entries which are not actual jobs
                if title.lower() == "share this role." or title.lower() == "share this role":
                    continue
                    
                # Skip other non-job titles like "Removed from favorites"
                non_job_indicators = ["share", "favorite", "login", "sign in", "apply", "submit"]
                if any(indicator in title.lower() for indicator in non_job_indicators) and len(title) < 30:
                    continue
                
                # Find link
                link_element = element.select_one('a[href*="/details/"]')
                if not link_element:
                    continue
                
                href = link_element.get('href')
                
                # Make sure the link is absolute
                if href.startswith('/'):
                    href = f"{self.base_url}{href}"
                elif not href.startswith('http'):
                    href = f"{self.base_url}/{href}"
                
                # Skip if we've already seen this link (de-duplication)
                if href in seen_links:
                    continue
                seen_links.add(href)
                
                # Find date
                date_element = element.select_one('time, .date, [class*="date"], [class*="posted"]')
                date_text = date_element.get_text().strip() if date_element else ''
                posting_date = self._parse_date(date_text)
                
                job_listings.append({
                    'title': title,
                    'link': href,
                    'date': posting_date
                })
            
            except Exception as e:
                self.logger.warning(f"Error processing job element: {str(e)}")
        
        return job_listings
    
    def _extract_job_description(self, soup: BeautifulSoup) -> str:
        """Extract job description from job detail page"""
        # Try various selectors for the job description
        selectors = [
            '.job-description',
            '#job-details-section',
            '[data-testid="job-description"]',
            '.job-details',
            'main article',
            'main .content',
            'article',
            'main'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text()) > 100:
                # Remove any navigation elements
                for nav in element.select('nav, header, footer, .navigation'):
                    nav.decompose()
                
                return element.get_text().strip()
        
        # If no description found, try to get all paragraphs
        paragraphs = [p.get_text().strip() for p in soup.select('p') if len(p.get_text().strip()) > 30]
        if paragraphs:
            return '\n\n'.join(paragraphs)
        
        # Last resort: get the main content
        main = soup.select_one('main, #content, article')
        if main:
            return main.get_text().strip()
        
        # If all else fails, return an empty string
        return ""
    
    async def _chrome_screenshot_fallback(self) -> List[Dict[str, Any]]:
        """
        Fallback method using Chrome to render the page and take screenshots
        This is a last resort for heavily JavaScript-dependent pages
        """
        jobs = []
        
        try:
            # Create temporary directory for screenshots
            with tempfile.TemporaryDirectory() as temp_dir:
                # Use Chrome to take screenshots
                self.logger.info("Using Chrome to render and capture the page")
                
                # Generate screenshot filename
                screenshot_path = os.path.join(temp_dir, "apple_jobs.png")
                
                # Use Chrome headless to take a screenshot
                cmd = [
                    "google-chrome",
                    "--headless",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    f"--screenshot={screenshot_path}",
                    "--window-size=1920,5000",  # Taller to capture more content
                    self.career_page_url
                ]
                
                try:
                    # Run Chrome headless
                    self.logger.info(f"Running Chrome headless: {' '.join(cmd)}")
                    process = subprocess.run(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        timeout=60
                    )
                    
                    # Check if the screenshot was created
                    if os.path.exists(screenshot_path):
                        self.logger.info(f"Screenshot created at {screenshot_path}")
                        
                        # Now, use Chrome to dump the HTML after JavaScript execution
                        html_path = os.path.join(temp_dir, "apple_jobs.html")
                        
                        cmd = [
                            "google-chrome",
                            "--headless",
                            "--disable-gpu",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--dump-dom",
                            self.career_page_url
                        ]
                        
                        process = subprocess.run(
                            cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            timeout=60
                        )
                        
                        # Save the HTML output
                        with open(html_path, 'wb') as f:
                            f.write(process.stdout)
                        
                        self.logger.info(f"HTML dumped to {html_path}")
                        
                        # Parse the HTML
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Extract job listings
                        job_listings = self._extract_job_listings_from_html(soup)
                        
                        self.logger.info(f"Found {len(job_listings)} job listings from Chrome dump")
                        
                        # We'll just create basic job entries without fetching details
                        for listing in job_listings:
                            job = {
                                "title": listing['title'],
                                "link": listing['link'],
                                "posting_date": listing['date'],
                                "description": f"Job posting for {listing['title']} at Apple. Visit the link for full details.",
                                "category": self.classify_job_category(listing['title'])
                            }
                            
                            jobs.append(job)
                
                except subprocess.TimeoutExpired:
                    self.logger.error("Chrome process timed out")
                except subprocess.SubprocessError as e:
                    self.logger.error(f"Error running Chrome: {str(e)}")
                except Exception as e:
                    self.logger.error(f"Error in Chrome fallback: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error in Chrome screenshot fallback: {str(e)}")
        
        return jobs
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse date from various formats"""
        try:
            if not date_text:
                return datetime.utcnow()
            
            # Format "Dec 3, 2024" or "December 3, 2024"
            date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', date_text)
            if date_match:
                month_str, day_str, year_str = date_match.groups()
                # Map month names to numbers
                month_map = {
                    'Jan': 1, 'January': 1, 
                    'Feb': 2, 'February': 2, 
                    'Mar': 3, 'March': 3, 
                    'Apr': 4, 'April': 4, 
                    'May': 5, 
                    'Jun': 6, 'June': 6, 
                    'Jul': 7, 'July': 7, 
                    'Aug': 8, 'August': 8, 
                    'Sep': 9, 'September': 9, 
                    'Oct': 10, 'October': 10, 
                    'Nov': 11, 'November': 11, 
                    'Dec': 12, 'December': 12
                }
                month = month_map.get(month_str, 1)
                day = int(day_str)
                year = int(year_str)
                return datetime(year, month, day)
            
            # Format "YYYY-MM-DD"
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_text)
            if date_match:
                year_str, month_str, day_str = date_match.groups()
                return datetime(int(year_str), int(month_str), int(day_str))
            
            # Relative dates like "Posted 3 days ago"
            days_ago_match = re.search(r'(\d+)\s+days?\s+ago', date_text, re.IGNORECASE)
            if days_ago_match:
                days = int(days_ago_match.group(1))
                return datetime.utcnow() - timedelta(days=days)
            
            # If it just says "Today" or "Yesterday"
            if re.search(r'today', date_text, re.IGNORECASE):
                return datetime.utcnow()
            elif re.search(r'yesterday', date_text, re.IGNORECASE):
                return datetime.utcnow() - timedelta(days=1)
            
        except Exception as e:
            self.logger.warning(f"Failed to parse date '{date_text}': {e}")
        
        # Default to current time if parsing fails
        return datetime.utcnow()
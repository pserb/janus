import logging
import aiohttp
import asyncio
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
import time
import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

from .. import crud, models, models  # Add models import here
from ..database import SessionLocal

logger = logging.getLogger("logo-fetcher")

# Directory to store company logos
LOGO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logos", "company_logos"))

class LogoFetcher:
    """
    Fetcher for company logos using TradingView and other sources.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Create logo directory if it doesn't exist
        os.makedirs(LOGO_DIR, exist_ok=True)
        
        # Headers to mimic a browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
    
    async def fetch_logos(self, limit: int = 50) -> int:
        """
        Fetch logos for companies without logos.
        
        Args:
            limit: Maximum number of companies to process at once
            
        Returns:
            int: Number of logos fetched
        """
        # Get companies without logos
        companies = self.db.query(models.Company).filter(
            models.Company.logo_path.is_(None)
        ).limit(limit).all()
        
        if not companies:
            logger.info("No companies need logos")
            return 0
        
        logger.info(f"Fetching logos for {len(companies)} companies")
        
        count = 0
        async with aiohttp.ClientSession() as session:
            for company in companies:
                try:
                    # Get ticker symbol from the database
                    ticker = company.ticker
                    
                    # If no ticker in database, try to lookup based on company name
                    if not ticker:
                        ticker = await self._lookup_ticker(session, company.name)
                    
                    logo_path = None
                    
                    # Try to fetch logo from TradingView if we have a ticker
                    if ticker:
                        logo_path = await self._fetch_tradingview_logo(session, ticker, company.name)
                    
                    # If TradingView logo fetch failed, generate a placeholder
                    if not logo_path:
                        logo_path = self._generate_placeholder_logo(company.name)
                    
                    # Update company with logo path
                    if logo_path:
                        company.logo_path = logo_path
                        company.ticker = ticker  # Update ticker if we looked it up
                        count += 1
                        
                        logger.info(f"Fetched logo for {company.name}")
                    
                except Exception as e:
                    logger.error(f"Error fetching logo for {company.name}: {str(e)}")
            
            # Commit changes
            self.db.commit()
        
        logger.info(f"Fetched {count} logos")
        return count
    
    async def _lookup_ticker(self, session: aiohttp.ClientSession, company_name: str) -> Optional[str]:
        """
        Lookup ticker symbol for a company name.
        
        Args:
            session: aiohttp ClientSession
            company_name: Company name to lookup
            
        Returns:
            Optional[str]: Ticker symbol if found, None otherwise
        """
        # Common mapping of company names to ticker symbols
        common_tickers = {
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "microsoft": "MSFT",
            "apple": "AAPL",
            "amazon": "AMZN",
            "facebook": "META",
            "meta": "META",
            "netflix": "NFLX",
            "nvidia": "NVDA",
            "intel": "INTC",
            "amd": "AMD",
            "ibm": "IBM",
            "oracle": "ORCL",
            "salesforce": "CRM",
            "adobe": "ADBE",
            "cisco": "CSCO",
            "qualcomm": "QCOM",
            "broadcom": "AVGO",
            "texas instruments": "TXN",
            "tesla": "TSLA",
            "twitter": "TWTR",
            "uber": "UBER",
            "lyft": "LYFT",
            "airbnb": "ABNB",
            "snap": "SNAP",
            "spotify": "SPOT",
            "square": "SQ",
            "paypal": "PYPL",
            "shopify": "SHOP",
            "zoom": "ZM",
            "dropbox": "DBX",
            "slack": "WORK",
            "dell": "DELL",
            "hp": "HPQ",
            "ibm": "IBM",
            "accenture": "ACN",
            "vmware": "VMW",
            "workday": "WDAY",
            "autodesk": "ADSK",
            "intuit": "INTU",
            "activision": "ATVI",
            "electronic arts": "EA",
            "take-two": "TTWO",
            "zynga": "ZNGA",
            "roblox": "RBLX",
            "pinterest": "PINS",
            "zillow": "ZG",
            "twilio": "TWLO",
            "databricks": "DBX",
            "palantir": "PLTR",
            "snowflake": "SNOW",
            "coinbase": "COIN",
            "robinhood": "HOOD",
            "docusign": "DOCU",
            "zendesk": "ZEN",
            "splunk": "SPLK",
            "datadog": "DDOG",
            "mongodb": "MDB",
            "atlassian": "TEAM",
            "elastic": "ESTC",
            "cloudflare": "NET",
            "okta": "OKTA",
            "fortinet": "FTNT",
            "crowdstrike": "CRWD",
            "zscaler": "ZS",
            "palo alto networks": "PANW",
            "symantec": "SYMC",
            "mcafee": "MCFE",
            "fireeye": "FEYE",
            "citrix": "CTXS",
            "micron": "MU",
            "western digital": "WDC",
            "seagate": "STX",
            "cadence design systems": "CDNS",
            "synopsys": "SNPS",
            "unity": "U",
            "c3.ai": "AI",
            "doordash": "DASH",
            "roku": "ROKU",
            "alibaba": "BABA",
            "jd.com": "JD",
            "baidu": "BIDU",
            "tencent": "TCEHY",
        }
        
        # Check if company name is in common tickers
        company_lower = company_name.lower()
        for name, ticker in common_tickers.items():
            if name in company_lower or company_lower in name:
                return ticker
        
        # If not found in common tickers, we could implement a more sophisticated lookup
        # For now, return None
        return None
    
    async def _fetch_tradingview_logo(
        self, 
        session: aiohttp.ClientSession, 
        ticker: str, 
        company_name: str
    ) -> Optional[str]:
        """
        Fetch logo from TradingView using improved scraping approach.
        
        Args:
            session: aiohttp ClientSession
            ticker: Company ticker symbol
            company_name: Company name
            
        Returns:
            Optional[str]: Path to saved logo or None
        """
        try:
            # Normalize ticker symbol
            ticker = ticker.upper()
            
            # First, navigate to the TradingView page for this ticker
            tradingview_url = f"https://www.tradingview.com/symbols/{ticker.lower()}/"
            
            # Add a random delay (1-3 seconds) to avoid rate limiting
            await asyncio.sleep(random.uniform(1, 3))
            
            # Fetch the TradingView page
            async with session.get(tradingview_url, headers=self.headers) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch TradingView page for {ticker} (HTTP {response.status})")
                    return None
                
                html_content = await response.text()
                
                # Parse HTML to find the logo URL
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all image tags
                img_tags = soup.find_all('img')
                
                # Look for the SVG image URL with the pattern observed in company logos
                svg_url = None
                for img in img_tags:
                    src = img.get('src', '')
                    if 's3-symbol-logo.tradingview.com' in src and ('--big.svg' in src or '.svg' in src):
                        svg_url = src
                        break
                
                if not svg_url:
                    logger.warning(f"Could not find SVG URL for {ticker} on TradingView page")
                    return None
                
                # Now download the SVG
                async with session.get(svg_url, headers=self.headers) as svg_response:
                    if svg_response.status != 200:
                        logger.warning(f"Failed to download SVG for {ticker} (HTTP {svg_response.status})")
                        return None
                    
                    svg_data = await svg_response.text()
                    
                    # Save SVG to file
                    logo_filename = f"{ticker}.svg"
                    logo_path = os.path.join(LOGO_DIR, logo_filename)
                    
                    with open(logo_path, "w") as f:
                        f.write(svg_data)
                    
                    # Return the path relative to the logo directory
                    return logo_filename
        
        except Exception as e:
            logger.error(f"Error fetching TradingView logo for {ticker}: {str(e)}")
            return None
    
    def _generate_placeholder_logo(self, company_name: str) -> str:
        """
        Generate a placeholder logo for companies without a logo.
        
        Args:
            company_name: Company name
            
        Returns:
            str: Path to saved placeholder logo
        """
        try:
            # Get company initials (1-2 letters)
            initials = self._get_initials(company_name)
            
            # Create SVG for placeholder
            svg_data = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
                <rect width="100" height="100" rx="10" fill="#f0f0f0"/>
                <text x="50" y="50" font-family="Arial, sans-serif" font-size="40" font-weight="bold" 
                    text-anchor="middle" dominant-baseline="middle" fill="#555555">{initials}</text>
            </svg>
            """
            
            # Generate a filename based on the company name
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', company_name.lower())
            logo_filename = f"{safe_name}_placeholder.svg"
            logo_path = os.path.join(LOGO_DIR, logo_filename)
            
            # Save SVG to file
            with open(logo_path, "w") as f:
                f.write(svg_data)
            
            # Return the path relative to the logo directory
            return logo_filename
        
        except Exception as e:
            logger.error(f"Error generating placeholder logo for {company_name}: {str(e)}")
            return None
    
    def _get_initials(self, company_name: str) -> str:
        """
        Get initials from company name.
        
        Args:
            company_name: Company name
            
        Returns:
            str: Company initials (1-2 characters)
        """
        # Remove common company suffixes
        suffixes = [
            "Inc", "Corp", "Corporation", "Company", "Co", "Ltd", "LLC", "LLP",
            "Limited", "Group", "Holdings", "Holding", "Technologies", "Technology"
        ]
        
        name = company_name
        for suffix in suffixes:
            pattern = rf"\s+{suffix}\.?$"
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)
        
        # Split into words
        words = name.split()
        
        if not words:
            return "?"
        
        if len(words) == 1:
            # Single word company name, use first letter
            return words[0][0].upper()
        else:
            # Multi-word company name, use first letter of first and last words
            # (or first two words if more recognizable)
            if len(words) > 2 and len(words[0]) <= 2:  # If first word is short (like "A", "An", "The")
                return (words[0][0] + words[1][0]).upper()
            else:
                return (words[0][0] + words[-1][0]).upper()


async def fetch_logos_batch(limit: int = 50) -> int:
    """
    Fetch logos for a batch of companies.
    
    Args:
        limit: Maximum number of companies to process
        
    Returns:
        int: Number of logos fetched
    """
    db = SessionLocal()
    try:
        fetcher = LogoFetcher(db)
        return await fetcher.fetch_logos(limit)
    finally:
        db.close()


async def fetch_all_logos() -> int:
    """
    Fetch logos for all companies without logos.
    
    Returns:
        int: Total number of logos fetched
    """
    total_fetched = 0
    batch_size = 10  # Smaller batch size to avoid rate limiting
    
    while True:
        fetched = await fetch_logos_batch(batch_size)
        total_fetched += fetched
        
        if fetched < batch_size:
            # No more companies need logos
            break
        
        # Add a longer delay between batches to be extra safe with TradingView
        await asyncio.sleep(10)
    
    return total_fetched


if __name__ == "__main__":
    asyncio.run(fetch_all_logos())
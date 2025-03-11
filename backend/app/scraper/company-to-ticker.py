#!/usr/bin/env python
# company_to_ticker.py

import os
import sys
import logging
import csv
import json
from pathlib import Path
from typing import Dict, Optional

# Add the project root to the Python path if needed
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import from the app package
from app.database import get_db, Base, engine
from app.models import Company, Job
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ticker_mapper")

# Create ticker mapping table model
class CompanyTicker(Base):
    __tablename__ = "company_tickers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), unique=True)
    ticker = Column(String, nullable=False)
    exchange = Column(String, nullable=True)

def get_connection_string():
    """Get database connection string based on environment"""
    # Check for environment variable
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        return db_url
    
    # If running directly (not in Docker), use localhost
    if os.path.exists('/etc/hosts'):
        with open('/etc/hosts', 'r') as f:
            if 'db' in f.read():
                # We're in Docker
                return "postgresql://postgres:postgres@db:5432/janus"
    
    # Default to localhost
    return "postgresql://postgres:postgres@localhost:5432/janus"

def load_ticker_mapping() -> Dict[str, str]:
    """Load company name to ticker mapping from the included CSV data"""
    # This is a basic mapping of common tech companies to their tickers
    ticker_map = {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Google": "GOOGL",
        "Alphabet": "GOOGL",
        "Amazon": "AMZN",
        "Meta": "META",
        "Facebook": "META",
        "Netflix": "NFLX",
        "NVIDIA": "NVDA",
        "Tesla": "TSLA",
        "Oracle": "ORCL",
        "IBM": "IBM",
        "Intel": "INTC",
        "AMD": "AMD",
        "Cisco": "CSCO",
        "Adobe": "ADBE",
        "Salesforce": "CRM",
        "PayPal": "PYPL",
        "Uber": "UBER",
        "Lyft": "LYFT",
        "Snap": "SNAP",
        "Block": "SQ",
        "Square": "SQ",
        "Shopify": "SHOP",
        "Zoom": "ZM",
        "Pinterest": "PINS",
        "Spotify": "SPOT",
        "Coinbase": "COIN",
        "Snowflake": "SNOW",
        "Palantir": "PLTR",
        "Roblox": "RBLX",
        "Unity": "U",
        "C3.ai": "AI",
        "Atlassian": "TEAM",
        "DoorDash": "DASH",
        "Roku": "ROKU",
        "Alibaba": "BABA",
        "JD.com": "JD",
        "Baidu": "BIDU",
        "Tencent": "TCEHY",
        "Dell": "DELL",
        "HP": "HPQ",
        "Hewlett Packard Enterprise": "HPE",
        "Texas Instruments": "TXN",
        "Qualcomm": "QCOM",
        "Advanced Micro Devices": "AMD",
        "Broadcom": "AVGO",
        "Micron Technology": "MU",
        "Western Digital": "WDC",
        "Seagate Technology": "STX",
        "Autodesk": "ADSK",
        "Workday": "WDAY",
        "ServiceNow": "NOW",
        "Digital Ocean": "DOCN",
        "Cloudflare": "NET",
        "Datadog": "DDOG",
        "MongoDB": "MDB",
        "Twilio": "TWLO",
        "Okta": "OKTA",
        "DocuSign": "DOCU",
        "Fortinet": "FTNT",
        "Palo Alto Networks": "PANW",
        "CrowdStrike": "CRWD",
        "Zscaler": "ZS",
        "Splunk": "SPLK",
        "VMware": "VMW",
        "Intuit": "INTU",
        "Cadence Design Systems": "CDNS",
        "Synopsys": "SNPS",
        "Analog Devices": "ADI",
        "Applied Materials": "AMAT",
        "Lam Research": "LRCX",
        "Airbnb": "ABNB",
        "Match Group": "MTCH",
        "eBay": "EBAY",
        "Expedia": "EXPE",
        "Booking Holdings": "BKNG",
        "Twitter": "TWTR",
        "LinkedIn": "MSFT",  # Now owned by Microsoft
        "GitHub": "MSFT",    # Now owned by Microsoft
    }
    
    # Load the expanded ticker data if available
    try:
        with open('ticker_data.csv', 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    company_name, ticker = row[0], row[1]
                    ticker_map[company_name] = ticker
    except (FileNotFoundError, IOError):
        logger.info("No expanded ticker data found. Using default mappings.")
    
    return ticker_map

def normalize_company_name(name: str) -> str:
    """Normalize company name for better matching"""
    # Convert to lowercase
    name = name.lower()
    
    # Remove common suffixes
    suffixes = [" inc", " inc.", " llc", " llc.", " corporation", " corp", " corp.", 
                " co", " co.", " limited", " ltd", " ltd.", " group", " holdings",
                " technologies", " technology", " tech", " systems", " labs"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    
    return name.strip()

def find_ticker_for_company(company_name: str, ticker_map: Dict[str, str]) -> Optional[str]:
    """Find ticker for a company using normalized name matching"""
    # Try direct match
    if company_name in ticker_map:
        return ticker_map[company_name]
    
    # Normalize and try again
    normalized_name = normalize_company_name(company_name)
    
    # Try direct match with normalized name
    for map_name, ticker in ticker_map.items():
        if normalize_company_name(map_name) == normalized_name:
            return ticker
    
    # Try partial match (starts with)
    for map_name, ticker in ticker_map.items():
        norm_map_name = normalize_company_name(map_name)
        if normalized_name.startswith(norm_map_name) or norm_map_name.startswith(normalized_name):
            return ticker
    
    return None

def map_companies_to_tickers():
    """Map companies in the database to their stock tickers"""
    # Get database connection
    connection_string = get_connection_string()
    logger.info(f"Connecting to database with: {connection_string}")
    
    # Create a new engine
    db_engine = create_engine(connection_string)
    
    # Create ticker table if it doesn't exist
    # Use the existing Base from app.database
    Base.metadata.create_all(bind=db_engine)
    
    # Create a session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = SessionLocal()
    
    try:
        # Load ticker mapping
        ticker_map = load_ticker_mapping()
        logger.info(f"Loaded {len(ticker_map)} ticker mappings")
        
        # Get all companies
        companies = db.query(Company).all()
        logger.info(f"Found {len(companies)} companies in the database")
        
        # Stats
        mapped_count = 0
        existing_count = 0
        
        # Process each company
        for company in companies:
            # Skip if already mapped
            existing_ticker = db.query(CompanyTicker).filter(CompanyTicker.company_id == company.id).first()
            if existing_ticker:
                logger.debug(f"Company {company.name} already mapped to {existing_ticker.ticker}")
                existing_count += 1
                continue
            
            # Try to find ticker
            ticker = find_ticker_for_company(company.name, ticker_map)
            
            if ticker:
                # Create mapping
                company_ticker = CompanyTicker(
                    company_id=company.id,
                    ticker=ticker,
                    exchange="NASDAQ/NYSE"  # Default exchange for simplicity
                )
                db.add(company_ticker)
                mapped_count += 1
                logger.info(f"Mapped {company.name} to ticker {ticker}")
            else:
                logger.debug(f"No ticker found for {company.name}")
        
        # Commit changes
        db.commit()
        
        # Report results
        logger.info(f"Mapping complete! Mapped {mapped_count} companies to tickers.")
        logger.info(f"Found {existing_count} companies with existing ticker mappings.")
        logger.info(f"Total companies with tickers: {mapped_count + existing_count}/{len(companies)}")
        
        # Create a JSON file with all ticker mappings for use with other scripts
        output_mappings = {}
        all_mappings = db.query(CompanyTicker).join(Company).all()
        for mapping in all_mappings:
            output_mappings[mapping.company.name] = mapping.ticker
        
        with open('company_tickers.json', 'w') as f:
            json.dump(output_mappings, f, indent=2)
        
        logger.info(f"Saved all ticker mappings to company_tickers.json")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error mapping companies to tickers: {str(e)}")
    finally:
        db.close()

def export_tickers_for_logo_download():
    """Export a list of tickers for use with the logo download script"""
    connection_string = get_connection_string()
    db_engine = create_engine(connection_string)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    db = SessionLocal()
    
    try:
        # Get all mapped tickers
        tickers = db.query(CompanyTicker.ticker).distinct().all()
        ticker_list = [t[0] for t in tickers]
        
        # Save to file
        with open('download_tickers.py', 'w') as f:
            f.write("#!/usr/bin/env python\n\n")
            f.write("# Auto-generated list of tickers for logo download\n\n")
            f.write("companies = [\n")
            for ticker in sorted(ticker_list):
                f.write(f'    "{ticker}",  # {get_company_name_for_ticker(db, ticker)}\n')
            f.write("]\n")
        
        logger.info(f"Created download_tickers.py with {len(ticker_list)} tickers")
    except Exception as e:
        logger.error(f"Error exporting tickers: {str(e)}")
    finally:
        db.close()

def get_company_name_for_ticker(db, ticker):
    """Get a company name for a ticker for comments in the output file"""
    mapping = db.query(CompanyTicker).filter(CompanyTicker.ticker == ticker).first()
    if mapping:
        company = db.query(Company).filter(Company.id == mapping.company_id).first()
        if company:
            return company.name
    return "Unknown"

if __name__ == "__main__":
    logger.info("Starting company to ticker mapping")
    map_companies_to_tickers()
    export_tickers_for_logo_download()
    logger.info("Mapping complete")
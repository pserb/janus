import os
import requests
from bs4 import BeautifulSoup
import time

# List of major tech companies (FAANGMULA and others)
companies = [
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "GOOGL", # Alphabet (Google) - Class A
    "GOOG",  # Alphabet (Google) - Class C
    "AMZN",  # Amazon
    "META",  # Meta (formerly Facebook)
    "NFLX",  # Netflix
    "NVDA",  # NVIDIA
    "TSLA",  # Tesla
    "ORCL",  # Oracle
    "IBM",   # IBM
    "INTC",  # Intel
    "AMD",   # AMD
    "CSCO",  # Cisco
    "ADBE",  # Adobe
    "CRM",   # Salesforce
    "PYPL",  # PayPal
    "UBER",  # Uber
    "LYFT",  # Lyft
    "SNAP",  # Snap
    "SQ",    # Block (formerly Square)
    "SHOP",  # Shopify
    "ZM",    # Zoom
    "PINS",  # Pinterest
    "SPOT",  # Spotify
    "COIN",  # Coinbase
    "SNOW",  # Snowflake
    "PLTR",  # Palantir
    "RBLX",  # Roblox
    "U",     # Unity
    "AI",    # C3.ai
    "TEAM",  # Atlassian
    "DASH",  # DoorDash
    "ROKU",  # Roku
    "BABA",  # Alibaba
    "JD",    # JD.com
    "BIDU",  # Baidu
    "TCEHY", # Tencent
    "AAPL",  # Apple
    "AMD",  # AMD
    "AMZN",  # Amazon
    "CDNS",  # Cadence Design Systems
    "GOOGL",  # Google
    "MSFT",  # Microsoft
    "SNAP",  # Snap-on
    "TSLA",  # Tesla
    "WDC",  # Western Digital
]

# Create directory for saved SVGs
output_dir = "company_logos"
os.makedirs(output_dir, exist_ok=True)

# Headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Download SVGs for each company
success_count = 0
failed_tickers = []

total_companies = len(companies)
print(f"Starting to download {total_companies} company logos...\n")

for i, ticker in enumerate(companies, 1):
    print(f"[{i}/{total_companies}] Processing {ticker}...")
    
    try:
        # Construct TradingView URL
        tradingview_url = f"https://www.tradingview.com/symbols/{ticker.lower()}/"
        
        # Make request to TradingView
        response = requests.get(tradingview_url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all image tags
        img_tags = soup.find_all('img')
        
        # Look for the SVG image URL with the pattern observed in the examples
        svg_url = None
        for img in img_tags:
            src = img.get('src', '')
            if 's3-symbol-logo.tradingview.com' in src and src.endswith('--big.svg'):
                svg_url = src
                break
        
        if svg_url:
            # Download SVG
            svg_response = requests.get(svg_url, headers=headers)
            svg_response.raise_for_status()
            
            # Save to file
            filename = os.path.join(output_dir, f"{ticker}.svg")
            with open(filename, 'wb') as f:
                f.write(svg_response.content)
            
            print(f"✓ Downloaded {ticker}.svg")
            success_count += 1
            
        else:
            print(f"✗ Could not find SVG for {ticker}")
            failed_tickers.append(ticker)
            
    except Exception as e:
        print(f"✗ Error processing {ticker}: {e}")
        failed_tickers.append(ticker)
    
    # Add delay to avoid rate limiting
    if i < total_companies:  # Don't delay after the last company
        time.sleep(1)

print(f"\nDownload complete! Successfully downloaded {success_count}/{total_companies} SVGs")

if failed_tickers:
    print("\nFailed to download SVGs for the following tickers:")
    for ticker in failed_tickers:
        print(f"- {ticker}")

print(f"\nSVGs are saved in the '{output_dir}' directory")
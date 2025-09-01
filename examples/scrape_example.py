import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient(api_token="your-api-key") #can also be taken from .env file

URL = (["https://www.amazon.com/dp/B079QHML21",
        "https://www.ebay.com/itm/365771796300",
        "https://www.walmart.com/ip/Apple-MacBook-Air-13-3-inch-Laptop-Space-Gray-M1-Chip-8GB-RAM-256GB-storage/609040889"])

results = client.scrape(url=URL, max_workers=5)

result = client.parse_content(results, extract_text=True) # Choose what to extract

print(result)
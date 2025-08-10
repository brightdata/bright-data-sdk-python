import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient(auto_create_zones=False) #can also be taken from .env file

URL = (["https://www.amazon.com/dp/B079QHML21",
        "https://www.ebay.com/itm/365771796300",
        "https://www.walmart.com/ip/Apple-MacBook-Air-13-3-inch-Laptop-Space-Gray-M1-Chip-8GB-RAM-256GB-storage/609040889"])

results = client.scrape(url=URL, max_workers=5)

client.download_content(results)
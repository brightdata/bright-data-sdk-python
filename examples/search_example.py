import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient(api_token="your-api-token") #can also be taken from .env file

query = ["iphone 16", "coffee maker", "portable projector", "sony headphones",
        "laptop stand", "power bank", "running shoes", "android tablet",
        "hiking backpack", "dash cam"]

results = client.search(query, search_engine="bing", max_workers=10)

print(results)

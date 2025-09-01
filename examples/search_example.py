import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient(api_token="your-api-token", auto_create_zones=False, serp_zone="your-custom-serp-zone") # zone and API token can also be defined in .env file

query = ["iphone 16", "coffee maker", "portable projector", "sony headphones",
        "laptop stand", "power bank", "running shoes", "android tablet",
        "hiking backpack", "dash cam"]

results = client.search(query, max_workers=10,
response_format="json", parse=True)

client.download_content(results, parse=True) # parse=True to save as JSON, otherwise saves as raw HTML
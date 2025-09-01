import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient
client = bdclient(api_token="your-api-key") # can also be taken from .env file

result = client.crawl(
    url="https://example.com/", depth=1, filter="/product/", 
    exclude_filter="/ads/", custom_output_fields=["markdown", "url", "page_title"]
)
print(f"Snapshot ID: {result['snapshot_id']}")
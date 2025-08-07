from brightdata import bdclient

client = bdclient(api_token="your-api-token") # The API can also be taken from .env file

urls = ["https://example1.com", "https://example2.com", "https://example3.com"] # Replace with real URLs

results = client.scrape(url=urls) # Try to hover over the "scrape" function to see what available parameters you can add

bd.download_content(results, filename="scrape_results.json")

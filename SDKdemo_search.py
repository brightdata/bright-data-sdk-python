from brightdata import bdclient

client = bdclient(api_token="your-api-token") #can also be taken from .env file

query = ["iphone 16", "coffee maker", "portable projector", "sony headphones",
        "laptop stand", "power bank", "running shoes", "android tablet",
        "hiking backpack", "dash cam"]

results = client.search(query=query, search_engine="google", format="json") # Try to hover over the "search" function to see what available parameters you can add

bd.download_content(results, filename="search_results.json", format="json")

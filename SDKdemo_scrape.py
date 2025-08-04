from brightdata import bdclient

bd = bdclient(api_token="73fa4ac2-4487-4509-9250-d902e58985fd")

query = ["iphone 16", "coffee maker", "portable projector", "sony headphones",
        "laptop stand", "power bank", "running shoes", "android tablet",
        "hiking backpack", "dash cam"]

results = bd.search(query=query, search_engine="google", format="json")

bd.download_content(results, filename="search_results.json", format="json")
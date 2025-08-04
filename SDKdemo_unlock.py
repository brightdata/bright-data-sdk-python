from brightdata import bdclient

bd = bdclient(api_token="73fa4ac2-4487-4509-9250-d902e58985fd")

URL = (["https://www.amazon.com/dp/B079QHML21",
        "https://www.ebay.com/itm/365771796300",
        "https://www.walmart.com/ip/Apple-MacBook-Air-13-3-inch-Laptop-Space-Gray-M1-Chip-8GB-RAM-256GB-storage/609040889"])

results = bd.scrape(url=URL, )
bd.download_content(results, filename="scrape_results.json")
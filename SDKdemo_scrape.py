from brightdata import bdclient

bd = bdclient(api_token="your-api-token") #can also be taken from .env file

URL = (["https://www.amazon.com/dp/B079QHML21",
        "https://www.ebay.com/itm/365771796300",
        "https://www.walmart.com/ip/Apple-MacBook-Air-13-3-inch-Laptop-Space-Gray-M1-Chip-8GB-RAM-256GB-storage/609040889"])

results = bd.scrape(url=URL, )
bd.download_content(results, filename="scrape_results.json")

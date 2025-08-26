import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brightdata import bdclient

client = bdclient(api_token="your-api-token")
client.scrape_chatGPT(
    prompt=["What are the top 3 programming languages in 2024?", "Best hotels in New York", "Explain quantum computing"],
    additional_prompt=["Can you explain why?", "Are you sure?", ""]  
)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brightdata import bdclient

client = bdclient(api_token="e15dcf475e7b0cac6f7c9ae332d59816dd01c75fedb25a0c34b83faff4a58bb8")
client.scrape_chatGPT(
    prompt=["What are the top 3 programming languages in 2024?", "Best hotels in New York", "Explain quantum computing"],
    additional_prompt=["Can you explain why?", "Are you sure?", ""]  
)
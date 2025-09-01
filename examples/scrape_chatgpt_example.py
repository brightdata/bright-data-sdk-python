import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient("your-api-key") # can also be taken from .env file

result = client.search_chatGPT(
    prompt="what day is it today?"
    # prompt=["What are the top 3 programming languages in 2024?", "Best hotels in New York", "Explain quantum computing"],
    # additional_prompt=["Can you explain why?", "Are you sure?", ""]  
)

client.download_content(result)
# In case of timeout error, your snapshot is still created and can be downloaded using the snapshot ID example file

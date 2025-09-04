import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient()

result = client.extract("Extract most watched news from CNN.com") # BRIGHTDATA_API_KEY and OPENAI_API_KEY API key can be set in .env

print(result)
print(f"Tokens used: {result.token_usage['total_tokens']}")
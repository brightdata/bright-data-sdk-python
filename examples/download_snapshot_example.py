import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brightdata import bdclient

client = bdclient(api_token="your-api-key") # can also be taken from .env file

snapshot_id = "" # replace with your snapshot ID

client.download_snapshot(snapshot_id)
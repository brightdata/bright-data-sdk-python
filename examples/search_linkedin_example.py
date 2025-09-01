import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient(api_token="your-api-key") # can also be taken from .env file

# Search LinkedIn profiles by name
first_names = ["James", "Idan"]
last_names = ["Smith", "Vilenski"]
result = client.search_linkedin.profiles(first_names, last_names)

# Search jobs by URL
job_urls = [
    "https://www.linkedin.com/jobs/search?keywords=Software&location=Tel%20Aviv-Yafo",
    "https://www.linkedin.com/jobs/reddit-inc.-jobs-worldwide?f_C=150573"
]
result = client.search_linkedin.jobs(url=job_urls)

# Search jobs by keyword and location
result = client.search_linkedin.jobs(
    location="Paris", 
    keyword="product manager",
    country="FR",
    time_range="Past month",
    job_type="Full-time"
)

# Search posts by profile URL with date range
result = client.search_linkedin.posts(
    profile_url="https://www.linkedin.com/in/bettywliu",
    start_date="2018-04-25T00:00:00.000Z",
    end_date="2021-05-25T00:00:00.000Z"
)
# Search posts by company URL
result = client.search_linkedin.posts(
    company_url="https://www.linkedin.com/company/bright-data"
)

# Returns snapshot ID that can be used to download the content later using download_snapshot function
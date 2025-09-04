import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brightdata import bdclient

client = bdclient() # can also be taken from .env file
    
# LinkedIn Profile URLs
profile_url = "https://www.linkedin.com/in/elad-moshe-05a90413/"

# LinkedIn Company URLs
company_urls = [
    "https://il.linkedin.com/company/ibm",
    "https://www.linkedin.com/company/bright-data",
    "https://www.linkedin.com/company/stalkit"
]

# LinkedIn Job URLs
job_urls = [
    "https://www.linkedin.com/jobs/view/remote-typist-%E2%80%93-data-entry-specialist-work-from-home-at-cwa-group-4181034038?trk=public_jobs_topcard-title",
    "https://www.linkedin.com/jobs/view/arrt-r-at-shared-imaging-llc-4180989163?trk=public_jobs_topcard-title"
]

# LinkedIn Post URLs
post_urls = [
    "https://www.linkedin.com/posts/orlenchner_scrapecon-activity-7180537307521769472-oSYN?trk=public_profile",
    "https://www.linkedin.com/pulse/getting-value-out-sunburst-guillaume-de-b%C3%A9naz%C3%A9?trk=public_profile_article_view"
]

results = client.scrape_linkedin.posts(post_urls) # can also be changed to async

client.download_content(results)
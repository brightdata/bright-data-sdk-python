import json
import re
import requests
from typing import Union, Dict, Any, List

from ..utils import get_logger
from ..exceptions import ValidationError, APIError, AuthenticationError

logger = get_logger('api.linkedin')


class LinkedInAPI:
    """Handles LinkedIn data collection using Bright Data's collect API"""
    
    DATASET_IDS = {
        'profile': 'gd_l1viktl72bvl7bjuj0',
        'company': 'gd_l1vikfnt1wgvvqz95w', 
        'job': 'gd_lpfll7v5hcqtkxl6l',
        'post': 'gd_lyy3tktm25m4avu764'
    }
    
    URL_PATTERNS = {
        'profile': re.compile(r'linkedin\.com/in/[^/?]+/?(\?.*)?$'),
        'company': re.compile(r'linkedin\.com/(company|organization-guest/company)/[^/?]+/?(\?.*)?$'),
        'job': re.compile(r'linkedin\.com/jobs/view/[^/?]+/?(\?.*)?$'),
        'post': re.compile(r'linkedin\.com/(posts|pulse)/[^/?]+/?(\?.*)?$')
    }
    
    def __init__(self, session, api_token, default_timeout=30, max_retries=3, retry_backoff=1.5):
        self.session = session
        self.api_token = api_token
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
    
    def _identify_dataset_type(self, url: str) -> str:
        """
        Identify LinkedIn dataset type based on URL pattern
        
        Args:
            url: LinkedIn URL to analyze
            
        Returns:
            Dataset type ('profile', 'company', 'job', 'post')
            
        Raises:
            ValidationError: If URL doesn't match any known LinkedIn pattern
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string")
        
        url = url.strip().lower()
        for dataset_type, pattern in self.URL_PATTERNS.items():
            if pattern.search(url):
                logger.debug(f"URL '{url}' identified as LinkedIn {dataset_type}")
                return dataset_type
        
        raise ValidationError(f"URL '{url}' does not match any supported LinkedIn data type")
    
    def _scrape_linkedin_dataset(
        self,
        urls: Union[str, List[str]],
        dataset_id: str,
        dataset_type: str,
        sync: bool = True,
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        Internal method to scrape LinkedIn data using Bright Data's collect API
        
        Args:
            urls: Single LinkedIn URL or list of LinkedIn URLs
            dataset_id: Bright Data dataset ID for the specific LinkedIn data type
            dataset_type: Type of LinkedIn data (for logging purposes)
            sync: If True (default), uses synchronous API for immediate results
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing response with snapshot_id or direct data (if sync=True)
            
        Raises:
            ValidationError: Invalid URL format
            AuthenticationError: Invalid API token or insufficient permissions
            APIError: Request failed or server error
        """
        if isinstance(urls, str):
            url_list = [urls]
        else:
            url_list = urls
            
        if not url_list or len(url_list) == 0:
            raise ValidationError("At least one URL is required")
        for url in url_list:
            if not url or not isinstance(url, str):
                raise ValidationError("All URLs must be non-empty strings")
        
        logger.info(f"Processing {len(url_list)} LinkedIn {dataset_type} URL(s) {'synchronously' if sync else 'asynchronously'}")
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": dataset_id,
            "include_errors": "true"
        }
        
        data = [{"url": url} for url in url_list]
        
        try:
            response = self.session.post(
                api_url,
                headers=headers,
                params=params,
                json=data,
                timeout=timeout or (65 if sync else self.default_timeout)
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API token or insufficient permissions")
            elif response.status_code != 200:
                raise APIError(f"LinkedIn data collection request failed with status {response.status_code}: {response.text}")
            
            if sync:
                response_text = response.text
                if '\n{' in response_text and response_text.strip().startswith('{'):
                    json_objects = []
                    for line in response_text.strip().split('\n'):
                        if line.strip():
                            try:
                                json_objects.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                    result = json_objects
                else:
                    try:
                        result = response.json()
                    except json.JSONDecodeError:
                        result = response_text
                
                logger.info(f"LinkedIn {dataset_type} data retrieved synchronously for {len(url_list)} URL(s)")
                print(f"Retrieved {len(result) if isinstance(result, list) else 1} LinkedIn {dataset_type} record(s)")
            else:
                result = response.json()
                snapshot_id = result.get('snapshot_id')
                if snapshot_id:
                    logger.info(f"LinkedIn {dataset_type} data collection job initiated successfully for {len(url_list)} URL(s)")
                    print("")
                    print("Snapshot ID:")
                    print(snapshot_id)
                    print("")
            
            return result
            
        except requests.exceptions.Timeout:
            raise APIError("Timeout while initiating LinkedIn data collection")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during LinkedIn data collection: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Failed to parse LinkedIn data collection response: {str(e)}")
        except Exception as e:
            if isinstance(e, (ValidationError, AuthenticationError, APIError)):
                raise
            raise APIError(f"Unexpected error during LinkedIn data collection: {str(e)}")


class LinkedInScraper:
    """LinkedIn data scraping interface with specialized methods for different data types"""
    
    def __init__(self, linkedin_api):
        self.linkedin_api = linkedin_api
    
    def profiles(self, url: Union[str, List[str]], sync: bool = True, timeout: int = None) -> Dict[str, Any]:
        """
        ## Scrape LinkedIn Profile Data
        
        Scrapes structured data from LinkedIn profiles using the profiles dataset.
        
        ### Parameters:
        - `url` (str | List[str]): Single LinkedIn profile URL or list of profile URLs
        - `sync` (bool, optional): If True (default), returns data immediately. If False, returns snapshot_id for async processing
        - `timeout` (int, optional): Request timeout in seconds (default: 65 for sync, 30 for async)
        
        ### Returns:
        - `Dict[str, Any]`: If sync=True, returns scraped profile data directly. If sync=False, returns response with snapshot_id for async processing
        
        ### Example URLs:
        - `https://www.linkedin.com/in/username/`
        - `https://linkedin.com/in/first-last-123456/`
        
        ### Example Usage:
        ```python
        # Single profile (synchronous - returns data immediately)
        result = client.scrape_linkedin.profiles("https://www.linkedin.com/in/elad-moshe-05a90413/")
        
        # Multiple profiles (synchronous - returns data immediately)
        profiles = [
            "https://www.linkedin.com/in/user1/", 
            "https://www.linkedin.com/in/user2/"
        ]
        result = client.scrape_linkedin.profiles(profiles)
        
        # Asynchronous processing (returns snapshot_id)
        result = client.scrape_linkedin.profiles(profiles, sync=False)
        ```
        """
        return self.linkedin_api._scrape_linkedin_dataset(
            url, 
            self.linkedin_api.DATASET_IDS['profile'], 
            'profile', 
            sync,
            timeout
        )
    
    def companies(self, url: Union[str, List[str]], sync: bool = True, timeout: int = None) -> Dict[str, Any]:
        """
        ## Scrape LinkedIn Company Data
        
        Scrapes structured data from LinkedIn company pages using the companies dataset.
        
        ### Parameters:
        - `url` (str | List[str]): Single LinkedIn company URL or list of company URLs
        - `sync` (bool, optional): If True (default), returns data immediately. If False, returns snapshot_id for async processing
        - `timeout` (int, optional): Request timeout in seconds (default: 65 for sync, 30 for async)
        
        ### Returns:
        - `Dict[str, Any]`: If sync=True, returns scraped company data directly. If sync=False, returns response with snapshot_id for async processing
        
        ### Example URLs:
        - `https://www.linkedin.com/company/company-name/`
        - `https://linkedin.com/company/bright-data/`
        
        ### Example Usage:
        ```python
        # Single company (synchronous)
        result = client.scrape_linkedin.companies("https://www.linkedin.com/company/bright-data/")
        
        # Multiple companies (synchronous)
        companies = [
            "https://www.linkedin.com/company/ibm/",
            "https://www.linkedin.com/company/microsoft/"
        ]
        result = client.scrape_linkedin.companies(companies)
        
        # Asynchronous processing
        result = client.scrape_linkedin.companies(companies, sync=False)
        ```
        """
        return self.linkedin_api._scrape_linkedin_dataset(
            url, 
            self.linkedin_api.DATASET_IDS['company'], 
            'company', 
            sync,
            timeout
        )
    
    def jobs(self, url: Union[str, List[str]], sync: bool = True, timeout: int = None) -> Dict[str, Any]:
        """
        ## Scrape LinkedIn Job Data
        
        Scrapes structured data from LinkedIn job listings using the jobs dataset.
        
        ### Parameters:
        - `url` (str | List[str]): Single LinkedIn job URL or list of job URLs
        - `sync` (bool, optional): If True (default), returns data immediately. If False, returns snapshot_id for async processing
        - `timeout` (int, optional): Request timeout in seconds (default: 65 for sync, 30 for async)
        
        ### Returns:
        - `Dict[str, Any]`: If sync=True, returns scraped job data directly. If sync=False, returns response with snapshot_id for async processing
        
        ### Example URLs:
        - `https://www.linkedin.com/jobs/view/1234567890/`
        - `https://linkedin.com/jobs/view/job-id/`
        
        ### Example Usage:
        ```python
        # Single job listing (synchronous)
        result = client.scrape_linkedin.jobs("https://www.linkedin.com/jobs/view/1234567890/")
        
        # Multiple job listings (synchronous)
        jobs = [
            "https://www.linkedin.com/jobs/view/1111111/",
            "https://www.linkedin.com/jobs/view/2222222/"
        ]
        result = client.scrape_linkedin.jobs(jobs)
        
        # Asynchronous processing
        result = client.scrape_linkedin.jobs(jobs, sync=False)
        ```
        """
        return self.linkedin_api._scrape_linkedin_dataset(
            url, 
            self.linkedin_api.DATASET_IDS['job'], 
            'job', 
            sync,
            timeout
        )
    
    def posts(self, url: Union[str, List[str]], sync: bool = True, timeout: int = None) -> Dict[str, Any]:
        """
        ## Scrape LinkedIn Post Data
        
        Scrapes structured data from LinkedIn posts and articles using the posts dataset.
        
        ### Parameters:
        - `url` (str | List[str]): Single LinkedIn post URL or list of post URLs
        - `sync` (bool, optional): If True (default), returns data immediately. If False, returns snapshot_id for async processing
        - `timeout` (int, optional): Request timeout in seconds (default: 65 for sync, 30 for async)
        
        ### Returns:
        - `Dict[str, Any]`: If sync=True, returns scraped post data directly. If sync=False, returns response with snapshot_id for async processing
        
        ### Example URLs:
        - `https://www.linkedin.com/posts/username-activity-123456/`
        - `https://www.linkedin.com/pulse/article-title-author/`
        
        ### Example Usage:
        ```python
        # Single post (synchronous)
        result = client.scrape_linkedin.posts("https://www.linkedin.com/posts/user-activity-123/")
        
        # Multiple posts (synchronous)
        posts = [
            "https://www.linkedin.com/posts/user1-activity-111/",
            "https://www.linkedin.com/pulse/article-author/"
        ]
        result = client.scrape_linkedin.posts(posts)
        
        # Asynchronous processing
        result = client.scrape_linkedin.posts(posts, sync=False)
        ```
        """
        return self.linkedin_api._scrape_linkedin_dataset(
            url, 
            self.linkedin_api.DATASET_IDS['post'], 
            'post', 
            sync,
            timeout
        )


class LinkedInSearcher:
    """LinkedIn search interface for discovering new LinkedIn data by various criteria"""
    
    def __init__(self, linkedin_api):
        self.linkedin_api = linkedin_api
    
    def profiles(
        self, 
        first_name: Union[str, List[str]], 
        last_name: Union[str, List[str]], 
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        ## Search LinkedIn Profiles by Name
        
        Discovers LinkedIn profiles by searching for first and last names.
        
        ### Parameters:
        - `first_name` (str | List[str]): Single first name or list of first names to search for
        - `last_name` (str | List[str]): Single last name or list of last names to search for  
        - `timeout` (int, optional): Request timeout in seconds (default: 30)
        
        ### Returns:
        - `Dict[str, Any]`: Response containing snapshot_id for async processing
        
        ### Example Usage:
        ```python
        # Single name search (returns snapshot_id)
        result = client.search_linkedin.profiles("James", "Smith")
        
        # Multiple names search (returns snapshot_id)
        first_names = ["James", "Idan"]
        last_names = ["Smith", "Vilenski"]
        result = client.search_linkedin.profiles(first_names, last_names)
        ```
        """
        if isinstance(first_name, str):
            first_names = [first_name]
        else:
            first_names = first_name
            
        if isinstance(last_name, str):
            last_names = [last_name]
        else:
            last_names = last_name
        
        if len(first_names) != len(last_names):
            raise ValidationError("first_name and last_name must have the same length")
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
            
        headers = {
            "Authorization": f"Bearer {self.linkedin_api.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": self.linkedin_api.DATASET_IDS['profile'],
            "include_errors": "true",
            "type": "discover_new",
            "discover_by": "name"
        }
        
        data = [
            {
                "first_name": first_names[i],
                "last_name": last_names[i]
            }
            for i in range(len(first_names))
        ]
        
        return self._make_request(api_url, headers, params, data, 'profile search', len(data), timeout)
    
    def jobs(
        self,
        url: Union[str, List[str]] = None,
        location: Union[str, List[str]] = None,
        keyword: Union[str, List[str]] = "",
        country: Union[str, List[str]] = "",
        time_range: Union[str, List[str]] = "",
        job_type: Union[str, List[str]] = "",
        experience_level: Union[str, List[str]] = "",
        remote: Union[str, List[str]] = "",
        company: Union[str, List[str]] = "",
        location_radius: Union[str, List[str]] = "",
        selective_search: Union[bool, List[bool]] = False,
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        ## Search LinkedIn Jobs by URL or Keywords
        
        Discovers LinkedIn jobs either by searching specific job search URLs or by keyword criteria.
        
        ### Parameters:
        - `url` (str | List[str], optional): LinkedIn job search URLs to scrape
        - `location` (str | List[str], optional): Job location(s) - required when searching by keyword
        - `keyword` (str | List[str], optional): Job keyword(s) to search for (default: "")
        - `country` (str | List[str], optional): Country code(s) (default: "")
        - `time_range` (str | List[str], optional): Time range filter (default: "")
        - `job_type` (str | List[str], optional): Job type filter (default: "")
        - `experience_level` (str | List[str], optional): Experience level filter (default: "")
        - `remote` (str | List[str], optional): Remote work filter (default: "")
        - `company` (str | List[str], optional): Company name filter (default: "")
        - `location_radius` (str | List[str], optional): Location radius filter (default: "")
        - `selective_search` (bool | List[bool], optional): Enable selective search (default: False)
        - `timeout` (int, optional): Request timeout in seconds (default: 30)
        
        ### Returns:
        - `Dict[str, Any]`: Response containing snapshot_id for async processing
        
        ### Example Usage:
        ```python
        # Search by job URLs (returns snapshot_id)
        job_urls = [
            "https://www.linkedin.com/jobs/search?keywords=Software&location=Tel%20Aviv-Yafo",
            "https://www.linkedin.com/jobs/reddit-inc.-jobs-worldwide?f_C=150573"
        ]
        result = client.search_linkedin.jobs(url=job_urls)
        
        # Search by keyword (returns snapshot_id)
        result = client.search_linkedin.jobs(
            location="Paris", 
            keyword="product manager",
            country="FR",
            time_range="Past month",
            job_type="Full-time"
        )
        ```
        """
        if url is not None:
            return self._search_jobs_by_url(url, timeout)
        elif location is not None:
            return self._search_jobs_by_keyword(
                location, keyword, country, time_range, job_type, 
                experience_level, remote, company, location_radius, 
                selective_search, timeout
            )
        else:
            raise ValidationError("Either 'url' or 'location' parameter must be provided")
    
    def posts(
        self,
        profile_url: Union[str, List[str]] = None,
        company_url: Union[str, List[str]] = None,
        url: Union[str, List[str]] = None,
        start_date: Union[str, List[str]] = "",
        end_date: Union[str, List[str]] = "",
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        ## Search LinkedIn Posts by Profile, Company, or General URL
        
        Discovers LinkedIn posts using various search methods.
        
        ### Parameters:
        - `profile_url` (str | List[str], optional): LinkedIn profile URL(s) to get posts from
        - `company_url` (str | List[str], optional): LinkedIn company URL(s) to get posts from
        - `url` (str | List[str], optional): General LinkedIn URL(s) for posts
        - `start_date` (str | List[str], optional): Start date filter (ISO format, default: "")
        - `end_date` (str | List[str], optional): End date filter (ISO format, default: "")
        - `timeout` (int, optional): Request timeout in seconds (default: 30)
        
        ### Returns:
        - `Dict[str, Any]`: Response containing snapshot_id for async processing
        
        ### Example Usage:
        ```python
        # Search posts by profile URL with date range (returns snapshot_id)
        result = client.search_linkedin.posts(
            profile_url="https://www.linkedin.com/in/bettywliu",
            start_date="2018-04-25T00:00:00.000Z",
            end_date="2021-05-25T00:00:00.000Z"
        )
        
        # Search posts by company URL (returns snapshot_id)
        result = client.search_linkedin.posts(
            company_url="https://www.linkedin.com/company/bright-data"
        )
        
        # Search posts by general URL (returns snapshot_id)
        result = client.search_linkedin.posts(
            url="https://www.linkedin.com/posts/activity-123456"
        )
        ```
        """
        if profile_url is not None:
            return self._search_posts_by_profile(profile_url, start_date, end_date, timeout)
        elif company_url is not None:
            return self._search_posts_by_company(company_url, timeout)
        elif url is not None:
            return self._search_posts_by_url(url, timeout)
        else:
            raise ValidationError("One of 'profile_url', 'company_url', or 'url' parameter must be provided")
    
    def _search_jobs_by_url(self, urls, timeout):
        """Search jobs by LinkedIn job search URLs"""
        if isinstance(urls, str):
            url_list = [urls]
        else:
            url_list = urls
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
            
        headers = {
            "Authorization": f"Bearer {self.linkedin_api.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": self.linkedin_api.DATASET_IDS['job'],
            "include_errors": "true",
            "type": "discover_new",
            "discover_by": "url"
        }
        
        data = [{"url": url} for url in url_list]
        return self._make_request(api_url, headers, params, data, 'job search by URL', len(data), timeout)
    
    def _search_jobs_by_keyword(self, location, keyword, country, time_range, job_type, experience_level, remote, company, location_radius, selective_search, timeout):
        """Search jobs by keyword criteria"""
        params_dict = {
            'location': location, 'keyword': keyword, 'country': country,
            'time_range': time_range, 'job_type': job_type, 'experience_level': experience_level,
            'remote': remote, 'company': company, 'location_radius': location_radius,
            'selective_search': selective_search
        }
        
        max_length = 1
        for key, value in params_dict.items():
            if isinstance(value, list):
                max_length = max(max_length, len(value))
        normalized_params = {}
        for key, value in params_dict.items():
            if isinstance(value, list):
                if len(value) != max_length and len(value) != 1:
                    raise ValidationError(f"Parameter '{key}' list length must be 1 or {max_length}")
                normalized_params[key] = value * max_length if len(value) == 1 else value
            else:
                normalized_params[key] = [value] * max_length
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
            
        headers = {
            "Authorization": f"Bearer {self.linkedin_api.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": self.linkedin_api.DATASET_IDS['job'],
            "include_errors": "true",
            "type": "discover_new",
            "discover_by": "keyword"
        }
        
        data = []
        for i in range(max_length):
            data.append({
                "location": normalized_params['location'][i],
                "keyword": normalized_params['keyword'][i],
                "country": normalized_params['country'][i],
                "time_range": normalized_params['time_range'][i],
                "job_type": normalized_params['job_type'][i],
                "experience_level": normalized_params['experience_level'][i],
                "remote": normalized_params['remote'][i],
                "company": normalized_params['company'][i],
                "location_radius": normalized_params['location_radius'][i],
                "selective_search": normalized_params['selective_search'][i]
            })
        
        return self._make_request(api_url, headers, params, data, 'job search by keyword', len(data), timeout)
    
    def _search_posts_by_profile(self, profile_urls, start_dates, end_dates, timeout):
        """Search posts by profile URL with optional date filtering"""
        if isinstance(profile_urls, str):
            url_list = [profile_urls]
        else:
            url_list = profile_urls
            
        if isinstance(start_dates, str):
            start_list = [start_dates] * len(url_list)
        else:
            start_list = start_dates if len(start_dates) == len(url_list) else [start_dates[0]] * len(url_list)
            
        if isinstance(end_dates, str):
            end_list = [end_dates] * len(url_list)
        else:
            end_list = end_dates if len(end_dates) == len(url_list) else [end_dates[0]] * len(url_list)
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
            
        headers = {
            "Authorization": f"Bearer {self.linkedin_api.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": self.linkedin_api.DATASET_IDS['post'],
            "include_errors": "true",
            "type": "discover_new",
            "discover_by": "profile_url"
        }
        
        data = []
        for i in range(len(url_list)):
            item = {"url": url_list[i]}
            if start_list[i]:
                item["start_date"] = start_list[i]
            if end_list[i]:
                item["end_date"] = end_list[i]
            data.append(item)
        
        return self._make_request(api_url, headers, params, data, 'post search by profile', len(data), timeout)
    
    def _search_posts_by_company(self, company_urls, timeout):
        """Search posts by company URL"""
        if isinstance(company_urls, str):
            url_list = [company_urls]
        else:
            url_list = company_urls
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
            
        headers = {
            "Authorization": f"Bearer {self.linkedin_api.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": self.linkedin_api.DATASET_IDS['post'],
            "include_errors": "true",
            "type": "discover_new",
            "discover_by": "company_url"
        }
        
        data = [{"url": url} for url in url_list]
        return self._make_request(api_url, headers, params, data, 'post search by company', len(data), timeout)
    
    def _search_posts_by_url(self, urls, timeout):
        """Search posts by general URL"""
        if isinstance(urls, str):
            url_list = [urls]
        else:
            url_list = urls
        
        api_url = "https://api.brightdata.com/datasets/v3/trigger"
            
        headers = {
            "Authorization": f"Bearer {self.linkedin_api.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": self.linkedin_api.DATASET_IDS['post'],
            "include_errors": "true",
            "type": "discover_new",
            "discover_by": "url"
        }
        
        data = [{"url": url} for url in url_list]
        return self._make_request(api_url, headers, params, data, 'post search by URL', len(data), timeout)
    
    def _make_request(self, api_url, headers, params, data, operation_type, count, timeout):
        """Common method to make API requests (async only for search operations)"""
        try:
            response = self.linkedin_api.session.post(
                api_url,
                headers=headers,
                params=params,
                json=data,
                timeout=timeout or self.linkedin_api.default_timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API token or insufficient permissions")
            elif response.status_code != 200:
                raise APIError(f"LinkedIn {operation_type} request failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            snapshot_id = result.get('snapshot_id')
            if snapshot_id:
                logger.info(f"LinkedIn {operation_type} job initiated successfully for {count} item(s)")
                print("")
                print("Snapshot ID:")
                print(snapshot_id)
                print("")
            
            return result
            
        except requests.exceptions.Timeout:
            raise APIError(f"Timeout while initiating LinkedIn {operation_type}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during LinkedIn {operation_type}: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Failed to parse LinkedIn {operation_type} response: {str(e)}")
        except Exception as e:
            if isinstance(e, (ValidationError, AuthenticationError, APIError)):
                raise
            raise APIError(f"Unexpected error during LinkedIn {operation_type}: {str(e)}")
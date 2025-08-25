import json
import requests
from typing import Union, Dict, Any, List

from ..utils import get_logger
from ..exceptions import ValidationError, APIError, AuthenticationError

logger = get_logger('api.chatgpt')


class ChatGPTAPI:
    """Handles ChatGPT scraping operations using Bright Data's ChatGPT dataset API"""
    
    def __init__(self, session, api_token, default_timeout=30, max_retries=3, retry_backoff=1.5):
        self.session = session
        self.api_token = api_token
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
    
    def scrape_chatgpt(
        self,
        prompts: List[str],
        countries: List[str],
        additional_prompts: List[str],
        web_searches: List[bool],
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        Internal method to handle ChatGPT scraping API requests
        
        Parameters:
        - prompts: List of prompts to send to ChatGPT
        - countries: List of country codes matching prompts
        - additional_prompts: List of follow-up prompts matching prompts
        - web_searches: List of web_search flags matching prompts
        - timeout: Request timeout in seconds
        
        Returns:
        - Dict containing response with snapshot_id
        """
        url = "https://api.brightdata.com/datasets/v3/trigger"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        params = {
            "dataset_id": "gd_m7aof0k82r803d5bjm",
            "include_errors": "true"
        }
        
        data = []
        for i in range(len(prompts)):
            data.append({
                "url": "https://chatgpt.com/",
                "prompt": prompts[i],
                "country": countries[i],
                "additional_prompt": additional_prompts[i],
                "web_search": web_searches[i]
            })
        
        try:
            response = self.session.post(
                url, 
                headers=headers, 
                params=params, 
                json=data, 
                timeout=timeout or self.default_timeout
            )
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API token or insufficient permissions")
            elif response.status_code != 200:
                raise APIError(f"ChatGPT scraping request failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            snapshot_id = result.get('snapshot_id')
            if snapshot_id:
                logger.info(f"ChatGPT scraping job initiated successfully for {len(prompts)} prompt(s)")
                print("")
                print("Snapshot ID:")
                print(snapshot_id)
                print("")
            
            return result
            
        except requests.exceptions.Timeout:
            raise APIError("Timeout while initiating ChatGPT scraping")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during ChatGPT scraping: {str(e)}")
        except json.JSONDecodeError as e:
            raise APIError(f"Failed to parse ChatGPT scraping response: {str(e)}")
        except Exception as e:
            if isinstance(e, (ValidationError, AuthenticationError, APIError)):
                raise
            raise APIError(f"Unexpected error during ChatGPT scraping: {str(e)}")
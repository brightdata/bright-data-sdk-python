import requests
import json
import logging
import time
from ..exceptions import ZoneError, NetworkError, APIError
from .retry import retry_request

logger = logging.getLogger(__name__)


class ZoneManager:
    """Manages Bright Data zones - creation and validation"""
    
    def __init__(self, session: requests.Session):
        self.session = session
    
    def ensure_required_zones(self, web_unlocker_zone: str, serp_zone: str):
        """
        Check if required zones exist and create them if they don't.
        Raises exceptions on failure instead of silently continuing.
        """
        try:
            logger.info("Checking existing zones...")
            zones = self._get_zones_with_retry()
            zone_names = {zone.get('name') for zone in zones}
            logger.info(f"Found {len(zones)} existing zones")
            
            zones_to_create = []
            if web_unlocker_zone not in zone_names:
                zones_to_create.append((web_unlocker_zone, 'unblocker'))
                logger.info(f"Need to create web unlocker zone: {web_unlocker_zone}")
            
            if serp_zone not in zone_names:
                zones_to_create.append((serp_zone, 'serp'))
                logger.info(f"Need to create SERP zone: {serp_zone}")
            
            if not zones_to_create:
                logger.info("All required zones already exist")
                return
                
            for zone_name, zone_type in zones_to_create:
                logger.info(f"Creating zone: {zone_name} (type: {zone_type})")
                self._create_zone_with_retry(zone_name, zone_type)
                logger.info(f"Successfully created zone: {zone_name}")
            
            self._verify_zones_created([zone[0] for zone in zones_to_create])
                
        except (ZoneError, NetworkError, APIError):
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while ensuring zones exist: {e}")
            raise NetworkError(f"Failed to ensure zones due to network error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response while checking zones: {e}")
            raise ZoneError(f"Invalid response format from zones API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while ensuring zones exist: {e}")
            raise ZoneError(f"Unexpected error during zone creation: {str(e)}")
    
    @retry_request(max_retries=3, backoff_factor=1.5, retry_statuses={429, 500, 502, 503, 504})
    def _get_zones_with_retry(self):
        """Get zones list with retry logic for network issues"""
        response = self.session.get('https://api.brightdata.com/zone/get_active_zones')
        
        if response.status_code == 200:
            try:
                return response.json() or []
            except json.JSONDecodeError as e:
                raise ZoneError(f"Invalid JSON response from zones API: {str(e)}")
        elif response.status_code == 401:
            raise ZoneError("Unauthorized (401): Check your API token and ensure it has proper permissions")
        elif response.status_code == 403:
            raise ZoneError("Forbidden (403): API token lacks sufficient permissions for zone operations")
        else:
            raise ZoneError(f"Failed to list zones ({response.status_code}): {response.text}")
    
    @retry_request(max_retries=3, backoff_factor=1.5, retry_statuses={429, 500, 502, 503, 504})
    def _create_zone_with_retry(self, zone_name: str, zone_type: str):
        """
        Create a new zone in Bright Data with retry logic
        
        Args:
            zone_name: Name for the new zone
            zone_type: Type of zone ('unblocker' or 'serp')
        """
        if zone_type == "serp":
            plan_config = {
                "type": "unblocker",
                "serp": True
            }
        else:
            plan_config = {
                "type": zone_type
            }
            
        payload = {
            "plan": plan_config,
            "zone": {
                "name": zone_name,
                "type": zone_type
            }
        }
        
        response = self.session.post(
            'https://api.brightdata.com/zone',
            json=payload
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"Zone creation successful: {zone_name}")
            return response
        elif response.status_code == 409 or "Duplicate zone name" in response.text or "already exists" in response.text.lower():
            logger.info(f"Zone {zone_name} already exists - this is expected")
            return response
        elif response.status_code == 401:
            raise ZoneError(f"Unauthorized (401): API token invalid or lacks permissions to create zone '{zone_name}'")
        elif response.status_code == 403:
            raise ZoneError(f"Forbidden (403): API token lacks permissions to create zone '{zone_name}'. Note: sdk_unlocker and sdk_serp zones should be allowed for all permissions.")
        elif response.status_code == 400:
            raise ZoneError(f"Bad request (400) creating zone '{zone_name}': {response.text}")
        else:
            raise ZoneError(f"Failed to create zone '{zone_name}' ({response.status_code}): {response.text}")
    
    def _verify_zones_created(self, zone_names: list):
        """
        Verify that zones were successfully created by checking the zones list
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                logger.info(f"Verifying zone creation (attempt {attempt + 1}/{max_attempts})")
                time.sleep(1)
                
                zones = self._get_zones_with_retry()
                existing_zone_names = {zone.get('name') for zone in zones}
                
                missing_zones = [name for name in zone_names if name not in existing_zone_names]
                
                if not missing_zones:
                    logger.info("All zones verified successfully")
                    return
                    
                if attempt == max_attempts - 1:
                    raise ZoneError(f"Zone verification failed: zones {missing_zones} not found after creation")
                    
                logger.warning(f"Zones not yet visible: {missing_zones}. Retrying verification...")
                
            except (ZoneError, NetworkError):
                if attempt == max_attempts - 1:
                    raise
                logger.warning(f"Zone verification attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)
    
    def _create_zone(self, zone_name: str, zone_type: str):
        """
        Legacy method - kept for backward compatibility
        Use _create_zone_with_retry instead for new code
        """
        return self._create_zone_with_retry(zone_name, zone_type)
    
    def list_zones(self):
        """
        List all active zones in your Bright Data account
        
        Returns:
            List of zone dictionaries with their configurations
        """
        try:
            return self._get_zones_with_retry()
        except (ZoneError, NetworkError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing zones: {e}")
            raise ZoneError(f"Unexpected error while listing zones: {str(e)}")
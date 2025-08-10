import requests
import json
import logging
from ..exceptions import ZoneError, NetworkError

logger = logging.getLogger(__name__)


class ZoneManager:
    """Manages Bright Data zones - creation and validation"""
    
    def __init__(self, session: requests.Session):
        self.session = session
    
    def ensure_required_zones(self, web_unlocker_zone: str, serp_zone: str):
        """
        Check if required zones exist and create them if they don't.
        """
        try:
            response = self.session.get('https://api.brightdata.com/zone/get_active_zones')
            
            if response.status_code != 200:
                return
            
            zones = response.json() or []
            zone_names = {zone.get('name') for zone in zones}
            
            if web_unlocker_zone not in zone_names:
                self._create_zone(web_unlocker_zone, 'unblocker')
            if serp_zone not in zone_names:
                self._create_zone(serp_zone, 'serp')
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error while ensuring zones exist: {e}")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON response while checking zones: {e}")
        except KeyError as e:
            logger.warning(f"Unexpected response format while checking zones: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error while ensuring zones exist: {e}")
    
    def _create_zone(self, zone_name: str, zone_type: str):
        """
        Create a new zone in Bright Data
        
        Args:
            zone_name: Name for the new zone
            zone_type: Type of zone ('unblocker' or 'serp')
        """
        payload = {
            "zone": {
                "name": zone_name,
                "type": zone_type
            },
            "plan": {
                "type": "static",
                "ips_type": "shared",
                "bandwidth": "1",
                "ip_alloc_preset": "shared_block",
                "ips": 0,
                "country": "any",
                "country_city": "any",
                "mobile": "false",
                "serp": "false",
                "city": "false",
                "asn": "false",
                "vip": "false",
                "vips_type": "shared",
                "vips": "0",
                "vip_country": "any",
                "vip_country_city": "any",
                "ub_premium": False,
                "solve_captcha_disable": True,
                "custom_headers": False
            }
        }
        
        response = self.session.post(
            'https://api.brightdata.com/zone',
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            if "Duplicate zone name" in response.text or "already exists" in response.text.lower():
                return
            else:
                raise ZoneError(f"Failed to create zone: {response.text}")
    
    def list_zones(self):
        """
        List all active zones in your Bright Data account
        
        Returns:
            List of zone dictionaries with their configurations
        """
        try:
            response = self.session.get('https://api.brightdata.com/zone/get_active_zones')
            if response.status_code == 200:
                try:
                    return response.json() or []
                except json.JSONDecodeError as e:
                    raise ZoneError(f"Invalid JSON response from zones API: {str(e)}")
            elif response.status_code == 401:
                raise ZoneError(f"Unauthorized (401): Check your API token")
            else:
                raise ZoneError(f"Failed to list zones ({response.status_code}): {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error listing zones: {e}")
            raise NetworkError(f"Network error while listing zones: {str(e)}")
        except Exception as e:
            logger.error(f"Error listing zones: {e}")
            raise
"""
Comprehensive tests for the Bright Data SDK client.

This test suite covers:
- Client initialization with API tokens (from parameter and environment)
- API token validation and error handling for missing tokens
- Zone configuration (default and custom zone names)
- URL validation in scrape method (scheme requirement)
- Search query validation (empty query handling)
- Search engine validation (unsupported engine handling)

All tests are designed to run without requiring real API tokens by:
- Using sufficiently long test tokens to pass validation
- Mocking zone management to avoid network calls
- Testing validation logic and error messages
"""

import pytest
import os
from unittest.mock import patch

from brightdata import bdclient
from brightdata.exceptions import ValidationError


class TestBdClient:
    """Test cases for the main bdclient class"""
    
    @patch('brightdata.utils.zone_manager.ZoneManager.ensure_required_zones')
    def test_client_init_with_token(self, mock_zones):
        """Test client initialization with API token"""
        with patch.dict(os.environ, {}, clear=True):
            client = bdclient(api_token="valid_test_token_12345678", auto_create_zones=False)
            assert client.api_token == "valid_test_token_12345678"
    
    @patch('brightdata.utils.zone_manager.ZoneManager.ensure_required_zones')
    def test_client_init_from_env(self, mock_zones):
        """Test client initialization from environment variable"""
        with patch.dict(os.environ, {"BRIGHTDATA_API_TOKEN": "valid_env_token_12345678"}):
            client = bdclient(auto_create_zones=False)
            assert client.api_token == "valid_env_token_12345678"
    
    def test_client_init_no_token_raises_error(self):
        """Test that missing API token raises ValidationError"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('dotenv.load_dotenv'):
                with pytest.raises(ValidationError, match="API token is required"):
                    bdclient()
    
    @patch('brightdata.utils.zone_manager.ZoneManager.ensure_required_zones')
    def test_client_zone_defaults(self, mock_zones):
        """Test default zone configurations"""
        with patch.dict(os.environ, {}, clear=True):
            client = bdclient(api_token="valid_test_token_12345678", auto_create_zones=False)
            assert client.web_unlocker_zone == "sdk_unlocker"
            assert client.serp_zone == "sdk_serp"
    
    @patch('brightdata.utils.zone_manager.ZoneManager.ensure_required_zones')
    def test_client_custom_zones(self, mock_zones):
        """Test custom zone configuration"""
        with patch.dict(os.environ, {}, clear=True):
            client = bdclient(
                api_token="valid_test_token_12345678",
                web_unlocker_zone="custom_unlocker",
                serp_zone="custom_serp",
                auto_create_zones=False
            )
            assert client.web_unlocker_zone == "custom_unlocker"
            assert client.serp_zone == "custom_serp"


class TestClientMethods:
    """Test cases for client methods with mocked responses"""
    
    @pytest.fixture
    @patch('brightdata.utils.zone_manager.ZoneManager.ensure_required_zones')
    def client(self, mock_zones):
        """Create a test client with mocked validation"""
        with patch.dict(os.environ, {}, clear=True):
            client = bdclient(api_token="valid_test_token_12345678", auto_create_zones=False)
            return client
    
    def test_scrape_single_url_validation(self, client):
        """Test URL validation in scrape method"""
        with pytest.raises(ValidationError, match="URL must include a scheme"):
            client.scrape("not_a_url")
    
    def test_search_empty_query_validation(self, client):
        """Test query validation in search method"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            client.search("")
    
    def test_search_unsupported_engine(self, client):
        """Test unsupported search engine validation"""
        with pytest.raises(ValidationError, match="Invalid search engine"):
            client.search("test query", search_engine="invalid_engine")
    
    def test_search_with_parse_parameter(self, client, monkeypatch):
        """Test search with parse parameter adds brd_json=1 to URL"""
        # Mock the session.post method to capture the request
        captured_request = {}
        
        def mock_post(*args, **kwargs):
            captured_request.update(kwargs)
            from unittest.mock import Mock
            response = Mock()
            response.status_code = 200
            response.text = "mocked html response"
            return response
        
        monkeypatch.setattr(client.search_api.session, 'post', mock_post)
        
        result = client.search("test query", parse=True)
        
        # Verify the request was made with correct URL containing &brd_json=1
        request_data = captured_request.get('json', {})
        assert "&brd_json=1" in request_data["url"]


if __name__ == "__main__":
    pytest.main([__file__])
import json
import requests
from datetime import datetime
from typing import Union, Dict, Any, List

from ..utils import get_logger
from ..exceptions import ValidationError, APIError, AuthenticationError

logger = get_logger('api.download')


class DownloadAPI:
    """Handles snapshot and content download operations using Bright Data's download API"""
    
    def __init__(self, session, api_token, default_timeout=30):
        self.session = session
        self.api_token = api_token
        self.default_timeout = default_timeout
    
    def download_content(self, content: Union[Dict, str], filename: str = None, format: str = "json", parse: bool = False) -> str:
        """
        ## Download content to a file based on its format
        
        ### Args:
            content: The content to download (dict for JSON, string for other formats)
            filename: Optional filename. If not provided, generates one with timestamp
            format: Format of the content ("json", "csv", "ndjson", "jsonl", "txt")
            parse: If True, automatically parse JSON strings in 'body' fields to objects (default: False)
        
        ### Returns:
            Path to the downloaded file
        """
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"brightdata_results_{timestamp}.{format}"
        
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
        
        if parse and isinstance(content, (list, dict)):
            content = self._parse_body_json(content)
        
        try:
            if format == "json":
                with open(filename, 'w', encoding='utf-8') as f:
                    if isinstance(content, dict) or isinstance(content, list):
                        json.dump(content, f, indent=2, ensure_ascii=False)
                    else:
                        f.write(str(content))
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(str(content))
            
            logger.info(f"Content downloaded to: {filename}")
            return filename
            
        except IOError as e:
            raise APIError(f"Failed to write file {filename}: {str(e)}")
        except Exception as e:
            raise APIError(f"Failed to download content: {str(e)}")
    
    def download_snapshot(
        self,
        snapshot_id: str,
        format: str = "json",
        compress: bool = False,
        batch_size: int = None,
        part: int = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
        """
        ## Download snapshot content from Bright Data dataset API
        
        Downloads the snapshot content using the snapshot ID returned from scrape_chatGPT() 
        or other dataset collection triggers.
        
        ### Parameters:
        - `snapshot_id` (str): The snapshot ID returned when collection was triggered (required)
        - `format` (str, optional): Format of the data - "json", "ndjson", "jsonl", or "csv" (default: "json")
        - `compress` (bool, optional): Whether the result should be compressed (default: False)
        - `batch_size` (int, optional): Divide into batches of X records (minimum: 1000)
        - `part` (int, optional): If batch_size provided, specify which part to download
        
        ### Returns:
        - `Union[Dict, List, str]`: Snapshot data in the requested format
        
        ### Example Usage:
        ```python
        # Download complete snapshot
        data = client.download_snapshot("s_m4x7enmven8djfqak")
        
        # Download as CSV format
        csv_data = client.download_snapshot("s_m4x7enmven8djfqak", format="csv")
        
        # Download in batches
        batch_data = client.download_snapshot(
            "s_m4x7enmven8djfqak", 
            batch_size=1000, 
            part=1
        )
        ```
        
        ### Raises:
        - `ValidationError`: Invalid parameters or snapshot_id format
        - `AuthenticationError`: Invalid API token or insufficient permissions
        - `APIError`: Request failed, snapshot not found, or server error
        """
        if not snapshot_id or not isinstance(snapshot_id, str):
            raise ValidationError("Snapshot ID is required and must be a non-empty string")
        
        if format not in ["json", "ndjson", "jsonl", "csv"]:
            raise ValidationError("Format must be one of: json, ndjson, jsonl, csv")
        
        if not isinstance(compress, bool):
            raise ValidationError("Compress must be a boolean")
        
        if batch_size is not None:
            if not isinstance(batch_size, int) or batch_size < 1000:
                raise ValidationError("Batch size must be an integer >= 1000")
        
        if part is not None:
            if not isinstance(part, int) or part < 1:
                raise ValidationError("Part must be a positive integer")
            if batch_size is None:
                raise ValidationError("Part parameter requires batch_size to be specified")
        
        url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json"
        }
        params = {
            "format": format
        }
        
        if compress:
            params["compress"] = "true"
        
        if batch_size is not None:
            params["batch_size"] = batch_size
            
        if part is not None:
            params["part"] = part
        
        try:
            logger.info(f"Downloading snapshot {snapshot_id} in {format} format")
            
            response = self.session.get(
                url, 
                headers=headers, 
                params=params, 
                timeout=self.default_timeout
            )
            
            if response.status_code == 200:
                pass
            elif response.status_code == 202:
                try:
                    response_data = response.json()
                    message = response_data.get('message', 'Snapshot is not ready yet')
                    print("Snapshot is not ready yet, try again soon")
                    return {"status": "not_ready", "message": message, "snapshot_id": snapshot_id}
                except json.JSONDecodeError:
                    print("Snapshot is not ready yet, try again soon")
                    return {"status": "not_ready", "message": "Snapshot is not ready yet, check again soon", "snapshot_id": snapshot_id}
            elif response.status_code == 401:
                raise AuthenticationError("Invalid API token or insufficient permissions")
            elif response.status_code == 404:
                raise APIError(f"Snapshot '{snapshot_id}' not found")
            else:
                raise APIError(f"Download request failed with status {response.status_code}: {response.text}")
            
            if format == "csv":
                data = response.text
                save_data = data
            else:
                response_text = response.text
                if '\n{' in response_text and response_text.strip().startswith('{'):
                    json_objects = []
                    for line in response_text.strip().split('\n'):
                        if line.strip():
                            try:
                                json_objects.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                    data = json_objects
                    save_data = json_objects
                else:
                    try:
                        data = response.json()
                        save_data = data
                    except json.JSONDecodeError:
                        data = response_text
                        save_data = response_text
            
            try:
                output_file = f"snapshot_{snapshot_id}.{format}"
                if format == "csv" or isinstance(save_data, str):
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(str(save_data))
                else:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(save_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Data saved to: {output_file}")
            except Exception:
                pass
            
            logger.info(f"Successfully downloaded snapshot {snapshot_id}")
            return data
            
        except requests.exceptions.Timeout:
            raise APIError("Timeout while downloading snapshot")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error during snapshot download: {str(e)}")
        except Exception as e:
            if isinstance(e, (ValidationError, AuthenticationError, APIError)):
                raise
            raise APIError(f"Unexpected error during snapshot download: {str(e)}")
    
    def _parse_body_json(self, content: Union[Dict, List]) -> Union[Dict, List]:
        """
        Parse JSON strings in 'body' fields to objects
        
        Args:
            content: The content to process
            
        Returns:
            Content with parsed body fields
        """
        if content is None:
            return content
            
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and 'body' in item:
                    body = item['body']
                    if isinstance(body, str):
                        try:
                            item['body'] = json.loads(body)
                        except (json.JSONDecodeError, TypeError):
                            pass
                elif isinstance(item, (dict, list)):
                    self._parse_body_json(item)
                    
        elif isinstance(content, dict):
            if 'body' in content:
                body = content['body']
                if isinstance(body, str):
                    try:
                        content['body'] = json.loads(body)
                    except (json.JSONDecodeError, TypeError):
                        pass
            
            for key, value in content.items():
                if isinstance(value, (dict, list)):
                    content[key] = self._parse_body_json(value)
                    
        return content
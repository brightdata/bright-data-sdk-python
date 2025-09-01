"""
Content parsing utilities for Bright Data SDK responses

Provides functions to extract and parse content from scraping and search results.
"""
import json
import re
from typing import Any, Dict, List, Union, Optional

from bs4 import BeautifulSoup


def parse_content(data: Union[str, Dict, List], extract_text: bool = True, extract_links: bool = False, extract_images: bool = False) -> Dict[str, Any]:
    """
    Parse content from Bright Data API responses
    
    Can be used as a standalone function or called from the client.
    Handles both JSON and raw HTML responses from scrape/search operations.
    
    Args:
        data: Response data from scrape() or search() - can be JSON dict/list or HTML string
        extract_text: Extract clean text content (default: True)
        extract_links: Extract all links from content (default: False)  
        extract_images: Extract image URLs from content (default: False)
        
    Returns:
        Dict containing parsed content with keys:
        - 'type': 'json' or 'html'
        - 'text': Cleaned text content (if extract_text=True)
        - 'links': List of extracted links (if extract_links=True)
        - 'images': List of image URLs (if extract_images=True)
        - 'title': Page title (if available)
        - 'raw_length': Length of original content
        - 'structured_data': Original JSON data (if type='json')
    """
    result = {
        'type': None,
        'raw_length': 0,
        'title': None
    }
    
    if data is None:
        return result
    
    if isinstance(data, (dict, list)):
        result['type'] = 'json'
        result['structured_data'] = data
        result['raw_length'] = len(str(data))
        
        html_content = _extract_html_from_json(data)
        if html_content and (extract_text or extract_links or extract_images):
            _parse_html_content(html_content, result, extract_text, extract_links, extract_images)
        
        result['title'] = _extract_title_from_json(data)
    
    elif isinstance(data, str):
        result['type'] = 'html'
        result['raw_length'] = len(data)
        
        if extract_text or extract_links or extract_images:
            _parse_html_content(data, result, extract_text, extract_links, extract_images)
    
    return result


def parse_multiple(data_list: List[Union[str, Dict]], **kwargs) -> List[Dict[str, Any]]:
    """
    Parse multiple content items (useful for batch scraping results)
    
    Args:
        data_list: List of response data items
        **kwargs: Arguments passed to parse_content()
        
    Returns:
        List of parsed content dictionaries
    """
    return [parse_content(item, **kwargs) for item in data_list]


def extract_structured_data(data: Union[str, Dict, List]) -> Optional[Dict]:
    """
    Extract structured data (JSON-LD, microdata) from content
    
    Args:
        data: Response data
        
    Returns:
        Structured data if found, None otherwise
    """
    html_content = None
    
    if isinstance(data, str):
        html_content = data
    elif isinstance(data, (dict, list)):
        html_content = _extract_html_from_json(data)
    
    if not html_content:
        return None
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        scripts = soup.find_all('script', type='application/ld+json')
        if scripts:
            structured_data = []
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    structured_data.append(data)
                except json.JSONDecodeError:
                    continue
            if structured_data:
                return {'json_ld': structured_data}
                
    except Exception:
        pass
    
    return None


def _extract_html_from_json(data: Union[Dict, List]) -> Optional[str]:
    """Extract HTML content from JSON response structure"""
    if isinstance(data, dict):
        html_keys = ['html', 'body', 'content', 'page_html', 'raw_html']
        for key in html_keys:
            if key in data and isinstance(data[key], str):
                return data[key]
        
        for value in data.values():
            if isinstance(value, (dict, list)):
                html = _extract_html_from_json(value)
                if html:
                    return html
                    
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                html = _extract_html_from_json(item)
                if html:
                    return html
    
    return None


def _extract_title_from_json(data: Union[Dict, List]) -> Optional[str]:
    """Extract title from JSON response structure"""
    if isinstance(data, dict):
        title_keys = ['title', 'page_title', 'name']
        for key in title_keys:
            if key in data and isinstance(data[key], str):
                return data[key].strip()
                
        for value in data.values():
            if isinstance(value, (dict, list)):
                title = _extract_title_from_json(value)
                if title:
                    return title
                    
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                title = _extract_title_from_json(item)
                if title:
                    return title
    
    return None


def _parse_html_content(html: str, result: Dict, extract_text: bool, extract_links: bool, extract_images: bool):
    """Parse HTML content and update result dictionary"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        if not result.get('title'):
            title_tag = soup.find('title')
            if title_tag:
                result['title'] = title_tag.get_text().strip()
        
        if extract_text:
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            result['text'] = '\n'.join(chunk for chunk in chunks if chunk)
        
        if extract_links:
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                text = a_tag.get_text().strip()
                links.append({'url': href, 'text': text})
            result['links'] = links
        
        if extract_images:
            images = []
            for img_tag in soup.find_all('img', src=True):
                src = img_tag['src']
                alt = img_tag.get('alt', '').strip()
                images.append({'url': src, 'alt': alt})
            result['images'] = images
            
    except Exception as e:
        if extract_text:
            result['text'] = f"HTML parsing failed: {str(e)}"
        if extract_links:
            result['links'] = []
        if extract_images:
            result['images'] = []
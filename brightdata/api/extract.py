import os
import re
import openai
from typing import Dict, Any, Tuple
from urllib.parse import urlparse

from ..utils import get_logger
from ..exceptions import ValidationError, APIError

logger = get_logger('api.extract')


class ExtractResult(str):
    """
    Custom result class that behaves like a string (extracted content) 
    but also provides access to metadata attributes
    """
    def __new__(cls, extracted_content, metadata):
        obj = str.__new__(cls, extracted_content)
        obj._metadata = metadata
        return obj
    
    def __getattr__(self, name):
        if name in self._metadata:
            return self._metadata[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def __getitem__(self, key):
        return self._metadata[key]
    
    def get(self, key, default=None):
        return self._metadata.get(key, default)
    
    def keys(self):
        return self._metadata.keys()
    
    def values(self):
        return self._metadata.values()
    
    def items(self):
        return self._metadata.items()
    
    @property
    def metadata(self):
        """Access full metadata dictionary"""
        return self._metadata


class ExtractAPI:
    """Handles content extraction using web scraping + LLM processing"""
    
    def __init__(self, client):
        self.client = client
    
    def extract(self, query: str, llm_key: str = None) -> Dict[str, Any]:
        """
        ## Extract specific information from websites using AI
        
        Combines web scraping with OpenAI's language models to extract targeted information
        from web pages based on natural language queries.
        
        ### Parameters:
        - `query` (str): Natural language query containing what to extract and from which URL
                        (e.g. "extract the most recent news from cnn.com")
        - `llm_key` (str, optional): OpenAI API key. If not provided, uses OPENAI_API_KEY env variable
        
        ### Returns:
        - `Dict[str, Any]`: Extracted information in structured format
        
        ### Example Usage:
        ```python
        result = client.extract(
            query="extract the most recent news from cnn.com",
            llm_key="your-openai-api-key"
        )
        print(result['extracted_content'])
        ```
        
        ### Raises:
        - `ValidationError`: Invalid query format or missing LLM key
        - `APIError`: Scraping failed or LLM processing error
        """
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        
        if not llm_key:
            llm_key = os.getenv('OPENAI_API_KEY')
        
        if not llm_key or not isinstance(llm_key, str):
            raise ValidationError("OpenAI API key is required. Provide it as parameter or set OPENAI_API_KEY environment variable")
        
        logger.info(f"Processing extract query: {query[:50]}...")
        
        try:
            parsed_query, url = self._parse_query_and_url(query)
            logger.info(f"Parsed - Query: '{parsed_query}', URL: '{url}'")
            
            scraped_content = self.client.scrape(url, response_format="raw")
            logger.info(f"Scraped content from {url}")
            
            parsed_content = self.client.parse_content(
                scraped_content, 
                extract_text=True, 
                extract_links=False, 
                extract_images=False
            )
            logger.info(f"Parsed content - text length: {len(parsed_content.get('text', ''))}")
            
            extracted_info, token_usage = self._process_with_llm(
                parsed_query, 
                parsed_content.get('text', ''), 
                llm_key,
                url
            )
            
            metadata = {
                'query': parsed_query,
                'url': url,
                'extracted_content': extracted_info,
                'source_title': parsed_content.get('title', 'Unknown'),
                'content_length': len(parsed_content.get('text', '')),
                'token_usage': token_usage,
                'success': True
            }
            
            return ExtractResult(extracted_info, metadata)
            
        except Exception as e:
            if isinstance(e, (ValidationError, APIError)):
                raise
            logger.error(f"Unexpected error during extraction: {e}")
            raise APIError(f"Extraction failed: {str(e)}")
    
    def _parse_query_and_url(self, query: str) -> Tuple[str, str]:
        """
        Parse natural language query to extract the task and URL
        
        Args:
            query: Natural language query like "extract news from cnn.com"
            
        Returns:
            Tuple of (parsed_query, full_url)
        """
        query = query.strip()
        
        url_patterns = [
            r'from\s+((?:https?://)?(?:www\.)?[\w\.-]+(?:\.[\w]{2,})+(?:/[\w\.-]*)*)',
            r'on\s+((?:https?://)?(?:www\.)?[\w\.-]+(?:\.[\w]{2,})+(?:/[\w\.-]*)*)',
            r'at\s+((?:https?://)?(?:www\.)?[\w\.-]+(?:\.[\w]{2,})+(?:/[\w\.-]*)*)',
            r'((?:https?://)?(?:www\.)?[\w\.-]+(?:\.[\w]{2,})+(?:/[\w\.-]*)*)'
        ]
        
        url = None
        for pattern in url_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                url = match.group(1)
                break
        
        if not url:
            raise ValidationError("Could not extract URL from query. Please include a website URL.")
        
        full_url = self._build_full_url(url)
        
        extract_query = re.sub(r'\b(?:from|on|at)\s+(?:https?://)?(?:www\.)?[\w\.-]+(?:\.[\w]{2,})+(?:/[\w\.-]*)*', '', query, flags=re.IGNORECASE)
        extract_query = re.sub(r'\b(?:https?://)?(?:www\.)?[\w\.-]+(?:\.[\w]{2,})+(?:/[\w\.-]*)*', '', extract_query, flags=re.IGNORECASE)
        extract_query = re.sub(r'\s+', ' ', extract_query).strip()
        
        if not extract_query:
            extract_query = "extract the main content"
        
        return extract_query, full_url
    
    def _build_full_url(self, url: str) -> str:
        """
        Build a complete URL from potentially partial URL
        
        Args:
            url: Potentially partial URL like "cnn.com" or "https://example.com"
            
        Returns:
            Complete URL with https:// and www if needed
        """
        url = url.strip()
        
        if not url.startswith(('http://', 'https://')):
            if not url.startswith('www.'):
                url = f'www.{url}'
            url = f'https://{url}'
        
        parsed = urlparse(url)
        if not parsed.netloc:
            raise ValidationError(f"Invalid URL format: {url}")
        
        return url
    
    def _process_with_llm(self, query: str, content: str, llm_key: str, source_url: str) -> Tuple[str, Dict[str, int]]:
        """
        Process scraped content with OpenAI to extract requested information
        
        Args:
            query: What to extract from the content
            content: Scraped and parsed text content
            llm_key: OpenAI API key
            source_url: Source URL for context
            
        Returns:
            Tuple of (extracted information, token usage dict)
        """
        if len(content) > 15000:
            beginning = content[:8000]
            end = content[-4000:]
            content = f"{beginning}\n\n... [middle content truncated for token efficiency] ...\n\n{end}"
        elif len(content) > 12000:
            content = content[:12000] + "\n\n... [content truncated to optimize tokens]"
        
        client = openai.OpenAI(api_key=llm_key)
        
        system_prompt = f"""You are a precise web content extraction specialist. Your task: {query}

SOURCE: {source_url}

INSTRUCTIONS:
1. Extract ONLY the specific information requested
2. Format output clearly with headings/bullet points when appropriate  
3. Include relevant details (dates, numbers, names) when available
4. If requested info isn't found, briefly state what content IS available
5. Keep response concise but complete
6. Use structured formatting for readability

OUTPUT FORMAT: Present extracted information in an organized, easy-to-scan format."""

        user_prompt = f"CONTENT TO ANALYZE:\n\n{content}\n\nEXTRACT: {query}"
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            extracted_content = response.choices[0].message.content.strip()
            
            token_usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            logger.info(f"OpenAI token usage: {token_usage['total_tokens']} total ({token_usage['prompt_tokens']} prompt + {token_usage['completion_tokens']} completion)")
            
            return extracted_content, token_usage
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise APIError(f"Failed to process content with LLM: {str(e)}")
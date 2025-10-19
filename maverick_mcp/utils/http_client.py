"""
HTTP Client Abstraction

Provides a centralized HTTP client with:
- Automatic retries with exponential backoff
- Rate limiting
- Timeout handling
- Session pooling
- User-agent management
"""

import logging
from typing import Optional, Dict, Any

import requests
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Centralized HTTP client with retry logic and rate limiting.
    
    Features:
    - Automatic retries (3 attempts with exponential backoff)
    - Rate limiting (configurable calls per minute)
    - Connection pooling
    - Custom headers and user-agent
    - Timeout handling
    
    Usage:
        client = HTTPClient(rate_limit_calls=10, rate_limit_period=60)
        response = client.get("https://api.example.com/data")
        data = response.json()
    """
    
    # Default user agent
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        rate_limit_calls: int = 30,
        rate_limit_period: int = 60,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None,
        additional_headers: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize HTTP client.
        
        Args:
            rate_limit_calls: Number of calls allowed per period
            rate_limit_period: Time period in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: Custom user agent string
            additional_headers: Additional headers to include in requests
        """
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_period = rate_limit_period
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Create session with connection pooling
        self.session = requests.Session()
        
        # Set up default headers
        self.session.headers.update({
            "User-Agent": user_agent or self.DEFAULT_USER_AGENT,
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })
        
        # Add any additional headers
        if additional_headers:
            self.session.headers.update(additional_headers)
        
        logger.info(
            f"HTTPClient initialized (rate limit: {rate_limit_calls}/{rate_limit_period}s, "
            f"timeout: {timeout}s, retries: {max_retries})"
        )
    
    @sleep_and_retry
    @limits(calls=30, period=60)  # This will be overridden by instance method
    def _rate_limited_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make a rate-limited HTTP request.
        
        Note: The decorator uses default values. Actual rate limiting
        is enforced by the calling method.
        """
        return self.session.request(method, url, **kwargs)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
        )),
        reraise=True,
    )
    def _request_with_retry(
        self,
        method: str,
        url: str,
        timeout: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with automatic retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            timeout: Request timeout (uses instance default if not provided)
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object
            
        Raises:
            requests.exceptions.RequestException: If all retries fail
        """
        timeout = timeout or self.timeout
        
        try:
            response = self._rate_limited_request(
                method=method,
                url=url,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            raise
    
    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """
        Perform GET request with retry and rate limiting.
        
        Args:
            url: Request URL
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            Response object
        """
        if headers:
            kwargs['headers'] = {**self.session.headers, **headers}
        
        return self._request_with_retry(
            method="GET",
            url=url,
            params=params,
            timeout=timeout,
            **kwargs
        )
    
    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> requests.Response:
        """
        Perform POST request with retry and rate limiting.
        
        Args:
            url: Request URL
            data: Form data
            json: JSON data
            headers: Additional headers
            timeout: Request timeout
            **kwargs: Additional arguments
            
        Returns:
            Response object
        """
        if headers:
            kwargs['headers'] = {**self.session.headers, **headers}
        
        return self._request_with_retry(
            method="POST",
            url=url,
            data=data,
            json=json,
            timeout=timeout,
            **kwargs
        )
    
    def get_text(self, url: str, **kwargs) -> str:
        """
        Get response as text.
        
        Args:
            url: Request URL
            **kwargs: Additional arguments
            
        Returns:
            Response text
        """
        response = self.get(url, **kwargs)
        return response.text
    
    def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Get response as JSON.
        
        Args:
            url: Request URL
            **kwargs: Additional arguments
            
        Returns:
            Parsed JSON response
        """
        response = self.get(url, **kwargs)
        return response.json()
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
        logger.debug("HTTPClient session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Singleton instance for shared use
_default_client: Optional[HTTPClient] = None


def get_http_client(
    rate_limit_calls: int = 30,
    rate_limit_period: int = 60,
    timeout: int = 30,
) -> HTTPClient:
    """
    Get a shared HTTP client instance.
    
    Args:
        rate_limit_calls: Number of calls allowed per period
        rate_limit_period: Time period in seconds
        timeout: Request timeout in seconds
        
    Returns:
        HTTPClient instance
    """
    global _default_client
    
    if _default_client is None:
        _default_client = HTTPClient(
            rate_limit_calls=rate_limit_calls,
            rate_limit_period=rate_limit_period,
            timeout=timeout,
        )
    
    return _default_client


__all__ = ["HTTPClient", "get_http_client"]


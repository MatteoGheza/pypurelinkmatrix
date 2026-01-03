"""HTTP client helper for PureLink device communication.

Handles HTTP requests with automatic timestamp appending to endpoints.
"""

import logging
import time

import requests

logger = logging.getLogger(__name__)


def get_timestamped_endpoint(endpoint: str) -> str:
    """Get endpoint with appended Unix timestamp in milliseconds.

    Args:
        endpoint: Base endpoint name (e.g., 'video_set', 'audio_set')

    Returns:
        Endpoint with timestamp appended (e.g., 'video_set1234567890123')

    Example:
        >>> get_timestamped_endpoint('video_set')
        'video_set1704283200000'
    """
    timestamp = int(time.time() * 1000)
    return f"{endpoint}{timestamp}"


def post_request(
    session: requests.Session,
    base_url: str,
    endpoint: str,
    data: str,
    timeout: int = 30,
    verify_ssl: bool = False,
) -> requests.Response:
    """Send POST request to device with timestamped endpoint.

    Args:
        session: Requests session object
        base_url: Device base URL (e.g., 'http://192.168.1.100')
        endpoint: Endpoint name (timestamp will be appended automatically)
        data: Command data to send
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Response object from requests library

    Raises:
        Exception: If request fails

    Example:
        >>> session = requests.Session()
        >>> response = post_request(
        ...     session,
        ...     'http://192.168.1.100',
        ...     'video_set',
        ...     '#video_d out1 matrix=2'
        ... )
    """
    timestamped_endpoint = get_timestamped_endpoint(endpoint)
    url = f"{base_url}/{timestamped_endpoint}"

    logger.debug(f"POST request to {url} with data: {data}")

    return session.post(
        url,
        data=data,
        timeout=timeout,
        verify=verify_ssl,
    )


def get_request(
    session: requests.Session,
    base_url: str,
    endpoint: str,
    timeout: int = 30,
    verify_ssl: bool = False,
) -> requests.Response:
    """Send GET request to device with timestamped endpoint.

    Args:
        session: Requests session object
        base_url: Device base URL (e.g., 'http://192.168.1.100')
        endpoint: Endpoint name (timestamp will be appended automatically)
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Response object from requests library

    Raises:
        Exception: If request fails

    Example:
        >>> session = requests.Session()
        >>> response = get_request(
        ...     session,
        ...     'http://192.168.1.100',
        ...     'status'
        ... )
    """
    timestamped_endpoint = get_timestamped_endpoint(endpoint)
    url = f"{base_url}/{timestamped_endpoint}"

    logger.debug(f"GET request to {url}")

    return session.get(
        url,
        timeout=timeout,
        verify=verify_ssl,
    )

"""Base HTTP client for microservice communication.

This module provides a base client class that all RoboMage service clients
inherit from. It handles common HTTP operations, health checks, retry logic,
and error handling.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests

from robomage.service_registry.models import ServiceMetadata

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Base exception for service errors."""

    def __init__(
        self,
        error_type: str,
        message: str,
        details: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        """Initialize service error.

        Args:
            error_type: Error category (e.g., 'ConnectionError', 'ValidationError')
            message: Human-readable error message
            details: Additional error details (optional)
            status_code: HTTP status code if applicable
        """
        self.error_type = error_type
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(f"{error_type}: {message}")


class BaseServiceClient:
    """Base HTTP client for microservice communication.

    This class provides common functionality for all service clients including
    connection management, health checks, retry logic, and error handling.

    Example:
        >>> from robomage.service_registry import ServiceRegistry
        >>> registry = ServiceRegistry()
        >>> metadata = registry.get_service("peak_analysis")
        >>> client = BaseServiceClient(metadata)
        >>> if client.ping():
        ...     print("Service is running")
    """

    def __init__(
        self,
        service_metadata: Optional[ServiceMetadata] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """Initialize the base service client.

        Args:
            service_metadata: Service metadata from registry (preferred)
            base_url: Base URL of the service (if metadata not provided)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        if service_metadata is None and base_url is None:
            raise ValueError("Either service_metadata or base_url must be provided")

        self.metadata = service_metadata
        self.base_url = (
            service_metadata.get_base_url() if service_metadata else base_url
        ).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

        logger.debug(f"Initialized client for {self.base_url}")

    def __enter__(self) -> "BaseServiceClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()
        logger.debug(f"Closed client for {self.base_url}")

    def get_client_url(self) -> str:
        """Get the base URL for the service.

        Returns:
            Base URL string
        """
        return self.base_url

    def health_check(self) -> Dict[str, Any]:
        """Check service health status.

        Returns:
            Service health information dictionary

        Raises:
            ServiceError: If service is unhealthy or unreachable
        """
        health_endpoint = (
            self.metadata.endpoints.health if self.metadata else "/health"
        )

        try:
            response = self.session.get(
                f"{self.base_url}{health_endpoint}", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise ServiceError(
                "ConnectionError",
                f"Failed to connect to service at {self.base_url}",
                str(e),
            ) from e

    def ping(self) -> bool:
        """Quick health check to see if service is running.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            result = self.health_check()
            return result.get("status") == "healthy"
        except ServiceError:
            return False

    def wait_for_service(
        self, max_wait: float = 30.0, check_interval: float = 1.0
    ) -> bool:
        """Wait for service to become available.

        Args:
            max_wait: Maximum time to wait in seconds
            check_interval: Time between checks in seconds

        Returns:
            True if service became available, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.ping():
                logger.info(
                    f"Service at {self.base_url} became available after "
                    f"{time.time() - start_time:.1f}s"
                )
                return True
            time.sleep(check_interval)

        logger.warning(
            f"Service at {self.base_url} did not become available within {max_wait}s"
        )
        return False

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/analyze')
            data: Request body data (for POST/PUT)
            params: Query parameters
            retry: Whether to retry on failure

        Returns:
            Response JSON data

        Raises:
            ServiceError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        retries = 0

        while retries <= (self.max_retries if retry else 0):
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        url, params=params, timeout=self.timeout
                    )
                elif method.upper() == "POST":
                    response = self.session.post(
                        url, json=data, params=params, timeout=self.timeout
                    )
                elif method.upper() == "PUT":
                    response = self.session.put(
                        url, json=data, params=params, timeout=self.timeout
                    )
                elif method.upper() == "DELETE":
                    response = self.session.delete(
                        url, params=params, timeout=self.timeout
                    )
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json() if response.content else {}

            except requests.exceptions.Timeout as e:
                if retries >= self.max_retries:
                    raise ServiceError(
                        "TimeoutError",
                        f"Request to {url} timed out after {self.timeout}s",
                        str(e),
                    ) from e
                retries += 1
                time.sleep(self.retry_delay * retries)

            except requests.exceptions.ConnectionError as e:
                if retries >= self.max_retries:
                    raise ServiceError(
                        "ConnectionError",
                        f"Failed to connect to service at {url}",
                        str(e),
                    ) from e
                retries += 1
                time.sleep(self.retry_delay * retries)

            except requests.exceptions.HTTPError as e:
                # Extract error details from response if available
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("detail", str(e))
                except Exception:
                    error_msg = str(e)

                raise ServiceError(
                    "HTTPError",
                    f"Service returned error: {error_msg}",
                    str(e),
                    status_code=e.response.status_code,
                ) from e

            except requests.exceptions.RequestException as e:
                raise ServiceError(
                    "RequestError", f"Request failed: {str(e)}", str(e)
                ) from e

        # Should never reach here, but just in case
        raise ServiceError("RetryExhausted", f"Failed after {retries} retries")

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make GET request to service.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON data
        """
        return self._make_request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make POST request to service.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON data
        """
        return self._make_request("POST", endpoint, data=data, params=params)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make PUT request to service.

        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters

        Returns:
            Response JSON data
        """
        return self._make_request("PUT", endpoint, data=data, params=params)

    def delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make DELETE request to service.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON data
        """
        return self._make_request("DELETE", endpoint, params=params)

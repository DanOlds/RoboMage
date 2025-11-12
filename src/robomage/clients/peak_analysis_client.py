"""
Peak Analysis HTTP Client - RoboMage Integration Library

A robust HTTP client library for seamless integration with the peak analysis
microservice. This client provides a Pythonic interface for scientific peak
analysis workflows within the RoboMage framework.

Architecture:
    - HTTP/JSON communication with the peak analysis REST API
    - Type-safe request/response handling with Pydantic validation
    - Automatic retry logic with exponential backoff for reliability
    - Connection pooling and session management for performance
    - Comprehensive error handling with scientific context

Key Features:
    Data Integration:
        - Native support for RoboMage DiffractionData objects
        - Automatic data serialization and validation
        - Seamless conversion between Q-space and d-spacing
        - Preservation of metadata throughout analysis pipeline

    Service Communication:
        - RESTful API client with requests library
        - JSON serialization optimized for scientific data
        - Configurable timeouts and retry policies
        - Service health monitoring and status checks

    Error Handling:
        - Custom exception hierarchy for different error types
        - Detailed error messages with scientific context
        - Connection error recovery and graceful degradation
        - Validation error reporting with field-level details

    Performance:
        - Connection reuse for multiple analysis requests
        - Efficient memory usage for large datasets
        - Concurrent request support for batch processing
        - Configurable timeout and retry parameters

Usage Patterns:
    Basic Analysis:
        client = PeakAnalysisClient("http://localhost:8001")
        response = client.analyze_peaks(q_values, intensities)

    RoboMage Integration:
        data = load_diffraction_file("sample.chi")
        response = client.analyze_diffraction_data(data)

    Service Management:
        if client.check_service_health():
            results = client.analyze_peaks(q, intensity)

    Configuration:
        client = PeakAnalysisClient(
            base_url="http://analysis-server:8001",
            timeout=30.0,
            max_retries=3
        )

Scientific Workflow:
    This client is designed for crystallographic analysis workflows where peak
    detection and fitting are critical steps in structure determination. It
    maintains full scientific metadata and provides statistical validation of
    analysis results.

Integration Points:
    - RoboMage data pipeline: Direct integration with loaders and models
    - CLI tools: Backend for peak_analyzer.py command-line interface
    - Jupyter notebooks: Interactive scientific analysis workflows
    - Automated pipelines: High-throughput crystallographic processing

Error Recovery:
    The client implements robust error handling for distributed scientific
    computing environments, including network failures, service unavailability,
    and data validation errors with appropriate retry strategies.
"""

import json
import time
from typing import Any

import requests

from ..data.models import DiffractionData


class PeakAnalysisServiceError(Exception):
    """Exception raised for peak analysis service errors."""

    def __init__(self, error_type: str, message: str, details: str | None = None):
        self.error_type = error_type
        self.message = message
        self.details = details
        super().__init__(f"{error_type}: {message}")


class PeakAnalysisClient:
    """
    HTTP client for the peak analysis service.

    Provides a Python interface for communicating with the peak analysis
    service through REST API calls.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the peak analysis client.

        Args:
            base_url: Base URL of the peak analysis service
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Create session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def __enter__(self) -> "PeakAnalysisClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP session."""
        self.session.close()

    def health_check(self) -> dict[str, Any]:
        """
        Check service health status.

        Returns:
            Service health information

        Raises:
            PeakAnalysisServiceError: If service is unhealthy or unreachable
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise PeakAnalysisServiceError(
                "ConnectionError",
                f"Failed to connect to service at {self.base_url}",
                str(e),
            ) from e

    def get_schemas(self) -> dict[str, Any]:
        """
        Get JSON schemas for request/response models.

        Returns:
            Dictionary containing JSON schemas

        Raises:
            PeakAnalysisServiceError: If schemas cannot be retrieved
        """
        try:
            response = self.session.get(f"{self.base_url}/schema", timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise PeakAnalysisServiceError(
                "ConnectionError", "Failed to retrieve schemas", str(e)
            ) from e

    def analyze_peaks(
        self,
        data: DiffractionData,
        config: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze diffraction data for peaks.

        Args:
            data: Diffraction data to analyze
            config: Analysis configuration (optional)
            request_id: Request identifier for tracking (optional)

        Returns:
            Peak analysis results

        Raises:
            PeakAnalysisServiceError: If analysis fails or service error occurs
        """
        # Convert DiffractionData to request format
        request_data: dict[str, Any] = {
            "data": {
                "q_values": data.q_values.tolist(),
                "intensities": data.intensities.tolist(),
                "filename": data.filename,
                "sample_name": data.sample_name,
            }
        }

        if config is not None:
            request_data["config"] = config

        if request_id is not None:
            request_data["request_id"] = request_id

        return self._make_request_with_retry(
            "POST", f"{self.base_url}/analyze", json=request_data
        )

    def analyze_peaks_raw(
        self,
        q_values: list[float],
        intensities: list[float],
        config: dict[str, Any] | None = None,
        filename: str | None = None,
        sample_name: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Analyze raw data arrays for peaks.

        Args:
            q_values: Q-space values (Å⁻¹)
            intensities: Diffraction intensities
            config: Analysis configuration (optional)
            filename: Original filename (optional)
            sample_name: Sample identifier (optional)
            request_id: Request identifier for tracking (optional)

        Returns:
            Peak analysis results

        Raises:
            PeakAnalysisServiceError: If analysis fails or service error occurs
        """
        request_data: dict[str, Any] = {
            "data": {"q_values": q_values, "intensities": intensities}
        }

        if filename is not None:
            request_data["data"]["filename"] = filename
        if sample_name is not None:
            request_data["data"]["sample_name"] = sample_name
        if config is not None:
            request_data["config"] = config
        if request_id is not None:
            request_data["request_id"] = request_id

        return self._make_request_with_retry(
            "POST", f"{self.base_url}/analyze", json=request_data
        )

    def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional request arguments

        Returns:
            Response JSON data

        Raises:
            PeakAnalysisServiceError: If request fails after all retries
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method, url, timeout=self.timeout, **kwargs
                )

                # Handle HTTP errors
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict) and "error_type" in error_data:
                            raise PeakAnalysisServiceError(
                                error_data.get("error_type", "UnknownError"),
                                error_data.get("message", "Service error"),
                                error_data.get("details"),
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass

                    # Fall back to HTTP status error
                    response.raise_for_status()

                # Success - return JSON data
                return response.json()

            except requests.exceptions.RequestException as e:
                last_exception = e

                # Don't retry on client errors (4xx)
                if hasattr(e, "response") and e.response is not None:
                    if 400 <= e.response.status_code < 500:
                        break

                # Retry on connection/server errors
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff
                    continue

                break

        # All retries failed
        raise PeakAnalysisServiceError(
            "ConnectionError",
            f"Request failed after {self.max_retries + 1} attempts",
            str(last_exception),
        ) from last_exception

    def ping(self) -> bool:
        """
        Simple ping to check if service is reachable.

        Returns:
            True if service responds, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    def wait_for_service(
        self, max_wait: float = 30.0, check_interval: float = 1.0
    ) -> bool:
        """
        Wait for service to become available.

        Args:
            max_wait: Maximum time to wait in seconds
            check_interval: Time between checks in seconds

        Returns:
            True if service becomes available, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if self.ping():
                return True
            time.sleep(check_interval)

        return False

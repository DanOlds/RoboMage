"""Tests for base service client."""

import pytest
import requests
from unittest.mock import Mock, patch

from robomage.clients.base_service_client import BaseServiceClient, ServiceError
from robomage.service_registry.models import ServiceMetadata


class TestBaseServiceClient:
    """Tests for BaseServiceClient class."""

    @pytest.fixture
    def mock_service_metadata(self):
        """Create mock service metadata."""
        return ServiceMetadata(
            name="test_service",
            display_name="Test Service",
            description="A test service",
            port=8000,
            host="127.0.0.1",
            startup_command="python main.py",
        )

    def test_init_with_metadata(self, mock_service_metadata):
        """Test initialization with service metadata."""
        client = BaseServiceClient(service_metadata=mock_service_metadata)

        assert client.base_url == "http://127.0.0.1:8000"
        assert client.metadata == mock_service_metadata
        assert client.timeout == 30.0
        assert client.max_retries == 3

    def test_init_with_base_url(self):
        """Test initialization with base URL."""
        client = BaseServiceClient(base_url="http://localhost:8001")

        assert client.base_url == "http://localhost:8001"
        assert client.metadata is None

    def test_init_without_params_raises_error(self):
        """Test initialization without metadata or URL raises error."""
        with pytest.raises(ValueError, match="Either service_metadata or base_url"):
            BaseServiceClient()

    def test_get_client_url(self, mock_service_metadata):
        """Test getting client URL."""
        client = BaseServiceClient(service_metadata=mock_service_metadata)
        assert client.get_client_url() == "http://127.0.0.1:8000"

    def test_context_manager(self, mock_service_metadata):
        """Test context manager protocol."""
        with BaseServiceClient(service_metadata=mock_service_metadata) as client:
            assert isinstance(client, BaseServiceClient)
            assert client.session is not None

    @patch("requests.Session.get")
    def test_health_check_success(self, mock_get, mock_service_metadata):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.health_check()

        assert result == {"status": "healthy"}
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_health_check_connection_error(self, mock_get, mock_service_metadata):
        """Test health check with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        client = BaseServiceClient(service_metadata=mock_service_metadata)

        with pytest.raises(ServiceError, match="ConnectionError"):
            client.health_check()

    @patch("requests.Session.get")
    def test_ping_success(self, mock_get, mock_service_metadata):
        """Test successful ping."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        assert client.ping() is True

    @patch("requests.Session.get")
    def test_ping_failure(self, mock_get, mock_service_metadata):
        """Test failed ping."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        assert client.ping() is False

    @patch("requests.Session.get")
    def test_wait_for_service_success(self, mock_get, mock_service_metadata):
        """Test waiting for service to become available."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.wait_for_service(max_wait=5.0, check_interval=0.1)

        assert result is True

    @patch("requests.Session.get")
    def test_wait_for_service_timeout(self, mock_get, mock_service_metadata):
        """Test waiting for service times out."""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.wait_for_service(max_wait=0.5, check_interval=0.1)

        assert result is False

    @patch("requests.Session.get")
    def test_get_request(self, mock_get, mock_service_metadata):
        """Test GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = Mock()
        mock_response.content = b'{"data": "test"}'
        mock_get.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.get("/test", params={"key": "value"})

        assert result == {"data": "test"}
        mock_get.assert_called_once()

    @patch("requests.Session.post")
    def test_post_request(self, mock_post, mock_service_metadata):
        """Test POST request."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.raise_for_status = Mock()
        mock_response.content = b'{"result": "success"}'
        mock_post.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.post("/analyze", data={"input": "data"})

        assert result == {"result": "success"}
        mock_post.assert_called_once()

    @patch("requests.Session.put")
    def test_put_request(self, mock_put, mock_service_metadata):
        """Test PUT request."""
        mock_response = Mock()
        mock_response.json.return_value = {"updated": True}
        mock_response.raise_for_status = Mock()
        mock_response.content = b'{"updated": true}'
        mock_put.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.put("/update", data={"field": "value"})

        assert result == {"updated": True}
        mock_put.assert_called_once()

    @patch("requests.Session.delete")
    def test_delete_request(self, mock_delete, mock_service_metadata):
        """Test DELETE request."""
        mock_response = Mock()
        mock_response.json.return_value = {"deleted": True}
        mock_response.raise_for_status = Mock()
        mock_response.content = b'{"deleted": true}'
        mock_delete.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.delete("/resource/123")

        assert result == {"deleted": True}
        mock_delete.assert_called_once()

    @patch("requests.Session.get")
    def test_timeout_error(self, mock_get, mock_service_metadata):
        """Test handling of timeout errors."""
        mock_get.side_effect = requests.exceptions.Timeout()

        client = BaseServiceClient(service_metadata=mock_service_metadata, max_retries=0)

        with pytest.raises(ServiceError, match="TimeoutError"):
            client.get("/test")

    @patch("requests.Session.get")
    def test_http_error(self, mock_get, mock_service_metadata):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        http_error = requests.exceptions.HTTPError()
        http_error.response = mock_response
        mock_get.side_effect = http_error

        client = BaseServiceClient(service_metadata=mock_service_metadata)

        with pytest.raises(ServiceError, match="HTTPError") as exc_info:
            client.get("/test")

        assert exc_info.value.status_code == 404

    @patch("requests.Session.get")
    def test_retry_on_connection_error(self, mock_get, mock_service_metadata):
        """Test retry logic on connection errors."""
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        mock_response.content = b'{"status": "ok"}'

        mock_get.side_effect = [
            requests.exceptions.ConnectionError(),
            requests.exceptions.ConnectionError(),
            mock_response,
        ]

        client = BaseServiceClient(
            service_metadata=mock_service_metadata,
            max_retries=3,
            retry_delay=0.01,
        )
        result = client.get("/test")

        assert result == {"status": "ok"}
        assert mock_get.call_count == 3

    def test_unsupported_http_method(self, mock_service_metadata):
        """Test error on unsupported HTTP method."""
        client = BaseServiceClient(service_metadata=mock_service_metadata)

        with pytest.raises(ValueError, match="Unsupported HTTP method"):
            client._make_request("PATCH", "/test")

    @patch("requests.Session.get")
    def test_empty_response(self, mock_get, mock_service_metadata):
        """Test handling of empty responses."""
        mock_response = Mock()
        mock_response.content = b""
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = BaseServiceClient(service_metadata=mock_service_metadata)
        result = client.get("/test")

        assert result == {}

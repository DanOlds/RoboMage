"""Tests for service registry functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from robomage.service_registry import ServiceRegistry
from robomage.service_registry.models import (
    DashboardIntegration,
    EndpointConfig,
    ServiceDependencies,
    ServiceMetadata,
    ServiceRegistryConfig,
    ServiceRegistryEntry,
    WorkflowIntegration,
)
from robomage.service_registry.registry import (
    ServiceNotFoundError,
    ServiceRegistryError,
    ServiceValidationError,
)


class TestServiceMetadata:
    """Tests for ServiceMetadata model."""

    def test_service_metadata_minimal(self):
        """Test creating minimal service metadata."""
        metadata = ServiceMetadata(
            name="test_service",
            display_name="Test Service",
            description="A test service",
            port=8000,
            startup_command="python main.py --port {port}",
        )

        assert metadata.name == "test_service"
        assert metadata.port == 8000
        assert metadata.host == "127.0.0.1"
        assert metadata.version == "1.0.0"

    def test_service_metadata_get_base_url(self):
        """Test base URL generation."""
        metadata = ServiceMetadata(
            name="test",
            display_name="Test",
            description="Test",
            port=8001,
            host="localhost",
            startup_command="test",
        )

        assert metadata.get_base_url() == "http://localhost:8001"

    def test_service_metadata_get_health_url(self):
        """Test health URL generation."""
        metadata = ServiceMetadata(
            name="test",
            display_name="Test",
            description="Test",
            port=8001,
            startup_command="test",
        )

        assert metadata.get_health_url() == "http://127.0.0.1:8001/health"

    def test_service_metadata_format_startup_command(self):
        """Test startup command formatting."""
        metadata = ServiceMetadata(
            name="test",
            display_name="Test",
            description="Test",
            port=8001,
            host="0.0.0.0",
            startup_command="python main.py --port {port} --host {host}",
        )

        command = metadata.format_startup_command()
        assert command == "python main.py --port 8001 --host 0.0.0.0"

    def test_service_name_validation(self):
        """Test service name validation."""
        # Valid name
        metadata = ServiceMetadata(
            name="valid_name",
            display_name="Valid",
            description="Test",
            port=8000,
            startup_command="test",
        )
        assert metadata.name == "valid_name"

        # Invalid: uppercase
        with pytest.raises(ValueError, match="lowercase"):
            ServiceMetadata(
                name="InvalidName",
                display_name="Invalid",
                description="Test",
                port=8000,
                startup_command="test",
            )

        # Invalid: spaces
        with pytest.raises(ValueError, match="lowercase"):
            ServiceMetadata(
                name="invalid name",
                display_name="Invalid",
                description="Test",
                port=8000,
                startup_command="test",
            )

    def test_port_validation(self):
        """Test port validation."""
        # Valid port
        metadata = ServiceMetadata(
            name="test",
            display_name="Test",
            description="Test",
            port=8000,
            startup_command="test",
        )
        assert metadata.port == 8000

        # Invalid: too low
        with pytest.raises(ValueError):
            ServiceMetadata(
                name="test",
                display_name="Test",
                description="Test",
                port=1023,
                startup_command="test",
            )

        # Invalid: too high
        with pytest.raises(ValueError):
            ServiceMetadata(
                name="test",
                display_name="Test",
                description="Test",
                port=65536,
                startup_command="test",
            )


class TestServiceRegistryConfig:
    """Tests for ServiceRegistryConfig model."""

    def test_get_enabled_services(self):
        """Test filtering enabled services."""
        config = ServiceRegistryConfig(
            services=[
                ServiceRegistryEntry(id="service1", path="path1", enabled=True),
                ServiceRegistryEntry(id="service2", path="path2", enabled=False),
                ServiceRegistryEntry(id="service3", path="path3", enabled=True),
            ]
        )

        enabled = config.get_enabled_services()
        assert len(enabled) == 2
        assert enabled[0].id == "service1"
        assert enabled[1].id == "service3"

    def test_get_auto_start_services(self):
        """Test filtering auto-start services."""
        config = ServiceRegistryConfig(
            services=[
                ServiceRegistryEntry(
                    id="service1", path="path1", enabled=True, auto_start=True
                ),
                ServiceRegistryEntry(
                    id="service2", path="path2", enabled=True, auto_start=False
                ),
                ServiceRegistryEntry(
                    id="service3", path="path3", enabled=False, auto_start=True
                ),
            ]
        )

        auto_start = config.get_auto_start_services()
        assert len(auto_start) == 1
        assert auto_start[0].id == "service1"


class TestServiceRegistry:
    """Tests for ServiceRegistry class."""

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Create temporary workspace with service structure."""
        # Create directory structure
        services_dir = tmp_path / "services"
        services_dir.mkdir()

        # Create test service 1
        service1_dir = services_dir / "test_service_1"
        service1_dir.mkdir()

        service1_metadata = {
            "name": "test_service_1",
            "display_name": "Test Service 1",
            "description": "First test service",
            "port": 8001,
            "startup_command": "python main.py",
        }
        (service1_dir / "service.json").write_text(json.dumps(service1_metadata))

        # Create test service 2
        service2_dir = services_dir / "test_service_2"
        service2_dir.mkdir()

        service2_metadata = {
            "name": "test_service_2",
            "display_name": "Test Service 2",
            "description": "Second test service",
            "port": 8002,
            "startup_command": "python main.py",
        }
        (service2_dir / "service.json").write_text(json.dumps(service2_metadata))

        # Create registry.json
        registry_config = {
            "version": "1.0",
            "services": [
                {"id": "test_service_1", "path": "services/test_service_1", "enabled": True},
            ],
            "discovery": {"auto_discover": True, "scan_directories": ["services/"]},
        }
        (services_dir / "registry.json").write_text(json.dumps(registry_config))

        return tmp_path

    def test_registry_load(self, temp_workspace):
        """Test loading service registry."""
        registry = ServiceRegistry(
            registry_path=temp_workspace / "services" / "registry.json",
            workspace_root=temp_workspace,
        )
        registry.load_registry()

        assert len(registry._services) == 2  # 1 registered + 1 auto-discovered
        assert "test_service_1" in registry._services
        assert "test_service_2" in registry._services

    def test_get_service(self, temp_workspace):
        """Test getting service by ID."""
        registry = ServiceRegistry(
            registry_path=temp_workspace / "services" / "registry.json",
            workspace_root=temp_workspace,
        )
        registry.load_registry()

        service = registry.get_service("test_service_1")
        assert service.name == "test_service_1"
        assert service.port == 8001

    def test_get_service_not_found(self, temp_workspace):
        """Test error when service not found."""
        registry = ServiceRegistry(
            registry_path=temp_workspace / "services" / "registry.json",
            workspace_root=temp_workspace,
        )
        registry.load_registry()

        with pytest.raises(ServiceNotFoundError, match="nonexistent"):
            registry.get_service("nonexistent")

    def test_get_all_services(self, temp_workspace):
        """Test getting all services."""
        registry = ServiceRegistry(
            registry_path=temp_workspace / "services" / "registry.json",
            workspace_root=temp_workspace,
        )
        registry.load_registry()

        services = registry.get_all_services()
        assert len(services) == 2

    def test_get_services_by_type(self, temp_workspace):
        """Test filtering services by type."""
        # Modify service metadata to include types
        services_dir = temp_workspace / "services"

        service1_metadata = {
            "name": "test_service_1",
            "display_name": "Test Service 1",
            "description": "First test service",
            "service_type": "analysis",
            "port": 8001,
            "startup_command": "python main.py",
        }
        (services_dir / "test_service_1" / "service.json").write_text(
            json.dumps(service1_metadata)
        )

        service2_metadata = {
            "name": "test_service_2",
            "display_name": "Test Service 2",
            "description": "Second test service",
            "service_type": "orchestration",
            "port": 8002,
            "startup_command": "python main.py",
        }
        (services_dir / "test_service_2" / "service.json").write_text(
            json.dumps(service2_metadata)
        )

        registry = ServiceRegistry(
            registry_path=services_dir / "registry.json",
            workspace_root=temp_workspace,
        )
        registry.load_registry()

        analysis_services = registry.get_services_by_type("analysis")
        assert len(analysis_services) == 1
        assert analysis_services[0].name == "test_service_1"

    def test_port_conflict_detection(self, temp_workspace):
        """Test detection of port conflicts."""
        services_dir = temp_workspace / "services"

        # Create two services with same port
        service3_dir = services_dir / "test_service_3"
        service3_dir.mkdir()

        service3_metadata = {
            "name": "test_service_3",
            "display_name": "Test Service 3",
            "description": "Third test service",
            "port": 8001,  # Same as service 1
            "startup_command": "python main.py",
        }
        (service3_dir / "service.json").write_text(json.dumps(service3_metadata))

        registry = ServiceRegistry(
            registry_path=services_dir / "registry.json",
            workspace_root=temp_workspace,
        )

        with pytest.raises(ServiceRegistryError, match="Port conflicts"):
            registry.load_registry()

    def test_reload(self, temp_workspace):
        """Test reloading registry."""
        registry = ServiceRegistry(
            registry_path=temp_workspace / "services" / "registry.json",
            workspace_root=temp_workspace,
        )
        registry.load_registry()

        initial_count = len(registry._services)

        # Add a new service
        services_dir = temp_workspace / "services"
        service3_dir = services_dir / "test_service_3"
        service3_dir.mkdir()

        service3_metadata = {
            "name": "test_service_3",
            "display_name": "Test Service 3",
            "description": "Third test service",
            "port": 8003,
            "startup_command": "python main.py",
        }
        (service3_dir / "service.json").write_text(json.dumps(service3_metadata))

        # Reload and verify new service discovered
        registry.reload()
        assert len(registry._services) > initial_count
        assert "test_service_3" in registry._services

    def test_auto_discover_disabled(self, temp_workspace):
        """Test registry with auto-discovery disabled."""
        services_dir = temp_workspace / "services"

        # Update registry to disable auto-discover
        registry_config = {
            "version": "1.0",
            "services": [
                {"id": "test_service_1", "path": "services/test_service_1", "enabled": True},
            ],
            "discovery": {"auto_discover": False},
        }
        (services_dir / "registry.json").write_text(json.dumps(registry_config))

        registry = ServiceRegistry(
            registry_path=services_dir / "registry.json",
            workspace_root=temp_workspace,
        )
        registry.load_registry()

        # Should only have service 1 (not auto-discovered service 2)
        assert len(registry._services) == 1
        assert "test_service_1" in registry._services
        assert "test_service_2" not in registry._services

    def test_missing_registry_file(self, tmp_path):
        """Test handling missing registry file."""
        registry = ServiceRegistry(
            registry_path=tmp_path / "nonexistent" / "registry.json",
            workspace_root=tmp_path,
        )

        # Should not raise error, just use empty registry
        registry.load_registry()
        assert len(registry._services) == 0

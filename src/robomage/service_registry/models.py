"""Pydantic models for service registry metadata.

These models define the structure of service metadata files (service.json)
and the global service registry (registry.json).
"""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class EndpointConfig(BaseModel):
    """Service endpoint configuration."""

    health: str = Field(default="/health", description="Health check endpoint")
    root: str = Field(default="/", description="Root endpoint")
    docs: str = Field(default="/docs", description="API documentation endpoint")


class ServiceDependencies(BaseModel):
    """Service dependency requirements."""

    python: str = Field(default=">=3.10", description="Python version requirement")
    packages: List[str] = Field(
        default_factory=list, description="Required Python packages"
    )


class WorkflowIntegration(BaseModel):
    """Workflow integration configuration."""

    enabled: bool = Field(default=False, description="Enable workflow integration")
    node_types: List[str] = Field(
        default_factory=list, description="Workflow node types provided by service"
    )


class DashboardIntegration(BaseModel):
    """Dashboard integration configuration."""

    enabled: bool = Field(default=True, description="Enable dashboard integration")
    tab_name: Optional[str] = Field(
        default=None, description="Dashboard tab name (if dedicated tab)"
    )
    status_indicator: bool = Field(
        default=True, description="Show status indicator in dashboard"
    )
    icon: str = Field(default="fas fa-cog", description="Font Awesome icon class")


class ServiceMetadata(BaseModel):
    """Complete service metadata from service.json file.

    This model represents all the configuration and metadata for a
    microservice in the RoboMage framework.

    Example:
        >>> metadata = ServiceMetadata.model_validate_json(json_str)
        >>> print(f"{metadata.display_name} on port {metadata.port}")
    """

    name: str = Field(..., description="Service identifier (lowercase, no spaces)")
    display_name: str = Field(..., description="Human-readable service name")
    description: str = Field(..., description="Service description")
    version: str = Field(default="1.0.0", description="Service version (semver)")
    service_type: str = Field(
        default="analysis", description="Service type (analysis, utility, etc.)"
    )
    port: int = Field(..., ge=1024, le=65535, description="Service port")
    host: str = Field(default="127.0.0.1", description="Service host")
    endpoints: EndpointConfig = Field(
        default_factory=EndpointConfig, description="Endpoint configuration"
    )
    health_check_interval: int = Field(
        default=5000, description="Health check interval (ms)"
    )
    startup_timeout: int = Field(
        default=30, description="Service startup timeout (seconds)"
    )
    dependencies: ServiceDependencies = Field(
        default_factory=ServiceDependencies, description="Service dependencies"
    )
    workflow_integration: WorkflowIntegration = Field(
        default_factory=WorkflowIntegration, description="Workflow integration config"
    )
    dashboard_integration: DashboardIntegration = Field(
        default_factory=DashboardIntegration, description="Dashboard integration config"
    )
    client_class: Optional[str] = Field(
        default=None,
        description="Fully qualified client class name (e.g., 'robomage.clients.peak_analysis_client.PeakAnalysisClient')",
    )
    startup_command: str = Field(
        ...,
        description="Command to start service (supports {port} and {host} placeholders)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate service name is lowercase with no spaces."""
        if not v.islower() or " " in v:
            raise ValueError("Service name must be lowercase with no spaces")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is in valid range."""
        if v < 1024 or v > 65535:
            raise ValueError("Port must be between 1024 and 65535")
        return v

    def get_base_url(self) -> str:
        """Get the base URL for the service.

        Returns:
            Base URL string (e.g., 'http://127.0.0.1:8001')
        """
        return f"http://{self.host}:{self.port}"

    def get_health_url(self) -> str:
        """Get the health check URL for the service.

        Returns:
            Health check URL string
        """
        return f"{self.get_base_url()}{self.endpoints.health}"

    def format_startup_command(self) -> str:
        """Format the startup command with current host/port.

        Returns:
            Formatted command string
        """
        return self.startup_command.format(port=self.port, host=self.host)


class ServiceRegistryEntry(BaseModel):
    """Entry in the global service registry."""

    id: str = Field(..., description="Service identifier (matches service.name)")
    path: str = Field(..., description="Relative path to service directory")
    enabled: bool = Field(default=True, description="Service is enabled")
    auto_start: bool = Field(
        default=True, description="Auto-start service on dashboard launch"
    )

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Ensure path uses forward slashes."""
        return v.replace("\\", "/")


class ServiceRegistryConfig(BaseModel):
    """Global service registry configuration from registry.json."""

    version: str = Field(default="1.0", description="Registry format version")
    services: List[ServiceRegistryEntry] = Field(
        default_factory=list, description="Registered services"
    )
    discovery: Dict[str, bool | List[str]] = Field(
        default_factory=lambda: {
            "auto_discover": True,
            "scan_directories": ["services/"],
        },
        description="Service discovery settings",
    )

    def get_enabled_services(self) -> List[ServiceRegistryEntry]:
        """Get list of enabled services.

        Returns:
            List of enabled ServiceRegistryEntry objects
        """
        return [svc for svc in self.services if svc.enabled]

    def get_auto_start_services(self) -> List[ServiceRegistryEntry]:
        """Get list of services to auto-start.

        Returns:
            List of auto-start ServiceRegistryEntry objects
        """
        return [svc for svc in self.services if svc.enabled and svc.auto_start]

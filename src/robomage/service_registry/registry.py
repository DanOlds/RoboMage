"""Service registry for discovering and managing microservices.

The ServiceRegistry provides a centralized way to discover, load, and manage
microservices in the RoboMage framework. Services can be registered via the
global registry.json file or auto-discovered from the services/ directory.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from robomage.service_registry.models import (
    ServiceMetadata,
    ServiceRegistryConfig,
    ServiceRegistryEntry,
)

logger = logging.getLogger(__name__)


class ServiceRegistryError(Exception):
    """Base exception for service registry errors."""

    pass


class ServiceNotFoundError(ServiceRegistryError):
    """Service not found in registry."""

    pass


class ServiceValidationError(ServiceRegistryError):
    """Service metadata validation failed."""

    pass


class ServiceRegistry:
    """Central registry for microservices.

    The ServiceRegistry manages all microservices in the RoboMage framework,
    including loading metadata, discovering services, and providing lookup APIs.

    Example:
        >>> registry = ServiceRegistry()
        >>> registry.load_registry()
        >>> peak_service = registry.get_service("peak_analysis")
        >>> print(peak_service.get_base_url())
        http://127.0.0.1:8001
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        workspace_root: Optional[Path] = None,
    ):
        """Initialize the service registry.

        Args:
            registry_path: Path to registry.json. If None, uses default location.
            workspace_root: Path to workspace root. If None, auto-detects.
        """
        self._workspace_root = workspace_root or self._detect_workspace_root()
        self._registry_path = registry_path or self._workspace_root / "services" / "registry.json"
        self._config: Optional[ServiceRegistryConfig] = None
        self._services: Dict[str, ServiceMetadata] = {}
        self._loaded = False

    @staticmethod
    def _detect_workspace_root() -> Path:
        """Auto-detect workspace root from current file location.

        Returns:
            Path to workspace root directory
        """
        # Navigate from src/robomage/service_registry/ to root
        current = Path(__file__).resolve()
        # Go up: registry.py -> service_registry -> robomage -> src -> root
        return current.parent.parent.parent.parent

    def load_registry(self) -> None:
        """Load and parse the service registry.

        This method loads the global registry.json, discovers services based
        on configuration, and validates all service metadata.

        Raises:
            ServiceRegistryError: If registry cannot be loaded
            ServiceValidationError: If service metadata is invalid
        """
        try:
            # Load registry.json
            if not self._registry_path.exists():
                logger.warning(
                    f"Registry file not found at {self._registry_path}, using empty registry"
                )
                self._config = ServiceRegistryConfig()
            else:
                with open(self._registry_path) as f:
                    data = json.load(f)
                self._config = ServiceRegistryConfig.model_validate(data)
                logger.info(f"Loaded service registry from {self._registry_path}")

            # Discover services
            discovered_services = self._discover_services()
            logger.info(f"Discovered {len(discovered_services)} services")

            # Load enabled services from registry
            for entry in self._config.get_enabled_services():
                service_dir = self._workspace_root / entry.path
                if service_dir.exists():
                    try:
                        metadata = self._load_service_metadata(service_dir)
                        if metadata.name != entry.id:
                            logger.warning(
                                f"Service name mismatch: registry has '{entry.id}' "
                                f"but metadata has '{metadata.name}'"
                            )
                        self._services[entry.id] = metadata
                    except Exception as e:
                        logger.error(f"Failed to load service {entry.id}: {e}")
                else:
                    logger.warning(f"Service directory not found: {service_dir}")

            # Add auto-discovered services not in registry
            if self._config.discovery.get("auto_discover", True):
                for service_id, metadata in discovered_services.items():
                    if service_id not in self._services:
                        logger.info(f"Auto-discovered service: {service_id}")
                        self._services[service_id] = metadata

            # Validate no port conflicts
            self._validate_unique_ports()

            self._loaded = True
            logger.info(f"Service registry loaded with {len(self._services)} services")

        except Exception as e:
            raise ServiceRegistryError(f"Failed to load service registry: {e}") from e

    def _discover_services(self) -> Dict[str, ServiceMetadata]:
        """Auto-discover services in scan directories.

        Returns:
            Dictionary mapping service IDs to ServiceMetadata
        """
        discovered = {}

        if not self._config or not self._config.discovery.get("auto_discover", True):
            return discovered

        scan_dirs = self._config.discovery.get("scan_directories", ["services/"])
        if isinstance(scan_dirs, str):
            scan_dirs = [scan_dirs]

        for scan_dir_str in scan_dirs:
            scan_dir = self._workspace_root / scan_dir_str
            if not scan_dir.exists():
                logger.warning(f"Scan directory does not exist: {scan_dir}")
                continue

            # Look for service.json files in subdirectories
            for service_dir in scan_dir.iterdir():
                if not service_dir.is_dir():
                    continue

                service_json = service_dir / "service.json"
                if service_json.exists():
                    try:
                        metadata = self._load_service_metadata(service_dir)
                        discovered[metadata.name] = metadata
                        logger.debug(f"Discovered service: {metadata.name}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to load service metadata from {service_dir}: {e}"
                        )

        return discovered

    def _load_service_metadata(self, service_dir: Path) -> ServiceMetadata:
        """Load service metadata from service.json file.

        Args:
            service_dir: Path to service directory

        Returns:
            ServiceMetadata object

        Raises:
            ServiceValidationError: If metadata is invalid
        """
        service_json = service_dir / "service.json"
        if not service_json.exists():
            raise ServiceValidationError(
                f"service.json not found in {service_dir}"
            )

        try:
            with open(service_json) as f:
                data = json.load(f)
            metadata = ServiceMetadata.model_validate(data)
            return metadata
        except Exception as e:
            raise ServiceValidationError(
                f"Invalid service metadata in {service_json}: {e}"
            ) from e

    def _validate_unique_ports(self) -> None:
        """Validate that all services use unique ports.

        Raises:
            ServiceValidationError: If port conflicts detected
        """
        port_map: Dict[int, List[str]] = {}
        for service_id, metadata in self._services.items():
            if metadata.port not in port_map:
                port_map[metadata.port] = []
            port_map[metadata.port].append(service_id)

        conflicts = {port: services for port, services in port_map.items() if len(services) > 1}
        if conflicts:
            conflict_msg = "; ".join(
                f"port {port}: {', '.join(services)}"
                for port, services in conflicts.items()
            )
            raise ServiceValidationError(f"Port conflicts detected: {conflict_msg}")

    def get_service(self, service_id: str) -> ServiceMetadata:
        """Get service metadata by ID.

        Args:
            service_id: Service identifier

        Returns:
            ServiceMetadata object

        Raises:
            ServiceNotFoundError: If service not found
        """
        if not self._loaded:
            self.load_registry()

        if service_id not in self._services:
            raise ServiceNotFoundError(
                f"Service '{service_id}' not found in registry. "
                f"Available services: {', '.join(self._services.keys())}"
            )

        return self._services[service_id]

    def get_all_services(self) -> List[ServiceMetadata]:
        """Get all registered services.

        Returns:
            List of ServiceMetadata objects
        """
        if not self._loaded:
            self.load_registry()

        return list(self._services.values())

    def is_service_enabled(self, service_id: str) -> bool:
        """Check if a service is enabled in the registry.

        Args:
            service_id: Service identifier

        Returns:
            True if service is enabled, False otherwise
        """
        if not self._loaded:
            self.load_registry()

        return service_id in self._services

    def get_services_by_type(self, service_type: str) -> List[ServiceMetadata]:
        """Get all services of a specific type.

        Args:
            service_type: Service type filter (e.g., 'analysis')

        Returns:
            List of ServiceMetadata objects matching the type
        """
        if not self._loaded:
            self.load_registry()

        return [
            svc for svc in self._services.values()
            if svc.service_type == service_type
        ]

    def get_auto_start_services(self) -> List[ServiceMetadata]:
        """Get services that should auto-start.

        Returns:
            List of ServiceMetadata for auto-start services
        """
        if not self._loaded:
            self.load_registry()

        if not self._config:
            return []

        auto_start_ids = {
            entry.id for entry in self._config.get_auto_start_services()
        }

        return [
            metadata for service_id, metadata in self._services.items()
            if service_id in auto_start_ids
        ]

    def reload(self) -> None:
        """Reload the service registry from disk.

        This will clear all cached services and re-discover/load everything.
        """
        self._services.clear()
        self._config = None
        self._loaded = False
        self.load_registry()

    def save_registry(self, registry_path: Optional[Path] = None) -> None:
        """Save the current registry configuration to disk.

        Args:
            registry_path: Path to save registry.json. If None, uses default.
        """
        if not self._config:
            raise ServiceRegistryError("No registry configuration to save")

        save_path = registry_path or self._registry_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w") as f:
            json.dump(self._config.model_dump(), f, indent=2)

        logger.info(f"Saved service registry to {save_path}")

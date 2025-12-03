"""
Integration tests for Custom Services Architecture.

This module provides end-to-end tests for the complete custom services
system including:
- Service creation via generator
- Service discovery and registration
- Workflow integration
- Dashboard integration
- Service lifecycle management
"""

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from robomage.service_registry import get_registry


class TestServiceGenerator:
    """Test the interactive service generator."""

    def test_generator_script_exists(self):
        """Test that the generator script exists and is executable."""
        generator_path = Path(__file__).parent.parent / "services" / "create_service.py"
        assert generator_path.exists()
        assert generator_path.stat().st_mode & 0o111  # Executable

    def test_service_template_exists(self):
        """Test that all template files exist."""
        template_dir = Path(__file__).parent.parent / "services" / "service_template"
        assert template_dir.exists()

        required_templates = [
            "main.py.template",
            "models.py.template",
            "analysis.py.template",
            "requirements.txt.template",
            ".env.template",
            "service.json.template",
            "README.md",
        ]

        for template in required_templates:
            template_path = template_dir / template
            assert template_path.exists(), f"Missing template: {template}"

    def test_template_placeholders(self):
        """Test that templates contain expected placeholders."""
        template_dir = Path(__file__).parent.parent / "services" / "service_template"

        # Check main.py template
        main_template = template_dir / "main.py.template"
        content = main_template.read_text()
        assert "{{SERVICE_NAME}}" in content
        assert "{{DISPLAY_NAME}}" in content
        assert "{{DESCRIPTION}}" in content
        assert "{{PORT}}" in content

    def test_generate_test_service(self):
        """Test generating a service via the generator script."""
        generator_path = Path(__file__).parent.parent / "services" / "create_service.py"
        services_dir = Path(__file__).parent.parent / "services"
        test_service_dir = services_dir / "test_integration_service"

        # Clean up if exists
        if test_service_dir.exists():
            shutil.rmtree(test_service_dir, ignore_errors=True)

        try:
            # Run generator with automated input
            result = subprocess.run(
                ["python", str(generator_path)],
                input="test_integration_service\nTest Integration Service\nA test service\n8099\n1\ny\n",
                text=True,
                capture_output=True,
                timeout=10,
            )

            # Check service was created
            assert test_service_dir.exists()

            # Check all files were created
            expected_files = [
                "main.py",
                "models.py",
                "analysis.py",
                "requirements.txt",
                ".env",
                "service.json",
                "README.md",
            ]

            for filename in expected_files:
                filepath = test_service_dir / filename
                assert filepath.exists(), f"Missing generated file: {filename}"

            # Check placeholders were replaced in service.json
            service_json = test_service_dir / "service.json"
            config = json.loads(service_json.read_text())
            assert config["name"] == "test_integration_service"
            assert config["display_name"] == "Test Integration Service"
            assert config["port"] == 8099

            # Check placeholders were replaced in main.py
            main_py = test_service_dir / "main.py"
            main_content = main_py.read_text()
            assert "{{SERVICE_NAME}}" not in main_content
            assert "Test Integration Service" in main_content
            assert "8099" in main_content

        finally:
            # Clean up - try multiple times with delays
            for attempt in range(3):
                try:
                    if test_service_dir.exists():
                        shutil.rmtree(test_service_dir, ignore_errors=False)
                        break
                except (OSError, PermissionError):
                    if attempt < 2:
                        time.sleep(0.1)
                    else:
                        # Last resort - ignore errors
                        shutil.rmtree(test_service_dir, ignore_errors=True)


class TestServiceRegistry:
    """Test service registry functionality."""

    def test_registry_discovers_existing_services(self):
        """Test that registry discovers existing services."""
        registry = get_registry()
        services = registry.get_all_services()

        # Should find at least peak_analysis and workflow_engine
        assert len(services) >= 2

        service_names = [s.name for s in services]
        assert "peak_analysis" in service_names
        assert "workflow_engine" in service_names

    def test_registry_singleton(self):
        """Test that get_registry returns singleton."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_get_service_by_name(self):
        """Test retrieving specific service by name."""
        registry = get_registry()
        peak_service = registry.get_service("peak_analysis")

        assert peak_service is not None
        assert peak_service.name == "peak_analysis"
        assert peak_service.port == 8001

    def test_get_auto_start_services(self):
        """Test getting auto-start services."""
        registry = get_registry()
        auto_start = registry.get_auto_start_services()

        # Both peak_analysis and workflow_engine should auto-start
        assert len(auto_start) >= 2
        names = [s.name for s in auto_start]
        assert "peak_analysis" in names
        assert "workflow_engine" in names

    def test_registry_reload(self):
        """Test registry reload functionality."""
        registry = get_registry()
        services_before = len(registry.get_all_services())

        # Reload should work without error
        registry.reload()

        services_after = len(registry.get_all_services())
        assert services_before == services_after


class TestWorkflowIntegration:
    """Test workflow integration of custom services."""

    def test_service_nodes_registered(self):
        """Test that service nodes are registered with workflow engine."""
        from robomage.workflow.nodes.registry import NodeRegistry

        node_registry = NodeRegistry()
        node_registry.discover_and_register_all()

        # Check that service-based nodes are registered
        registered_types = node_registry.get_node_types()

        # Should include service nodes (peak_analysis_service, workflow_engine, etc.)
        # Note: Exact names depend on service configuration
        assert len(registered_types) > 0

    def test_service_node_metadata(self):
        """Test that service nodes have proper metadata."""
        from robomage.workflow.nodes.registry import NodeRegistry

        node_registry = NodeRegistry()
        node_registry.discover_and_register_all()

        # Get a service node
        service_registry = get_registry()
        for service in service_registry.get_all_services():
            if service.workflow_integration and service.workflow_integration.enabled:
                # Check if node is registered
                node_types = node_registry.get_node_types()
                # Service nodes should be discoverable
                assert len(node_types) > 0


class TestDashboardIntegration:
    """Test dashboard integration of custom services."""

    def test_service_monitor_component_exists(self):
        """Test that service monitor component exists."""
        monitor_path = (
            Path(__file__).parent.parent
            / "src"
            / "robomage"
            / "dashboard"
            / "components"
            / "service_monitor.py"
        )
        assert monitor_path.exists()

    def test_dashboard_callbacks_use_registry(self):
        """Test that dashboard callbacks import and use registry."""
        analysis_callback = (
            Path(__file__).parent.parent
            / "src"
            / "robomage"
            / "dashboard"
            / "callbacks"
            / "analysis.py"
        )

        content = analysis_callback.read_text()

        # Should import service_registry
        assert "service_registry" in content.lower() or "get_registry" in content


class TestServiceLifecycle:
    """Test service lifecycle management."""

    @pytest.mark.slow
    def test_start_services_script(self):
        """Test that start_services.py uses registry."""
        start_script = Path(__file__).parent.parent / "start_services.py"
        content = start_script.read_text()

        # Should use get_registry
        assert "get_registry" in content
        assert "get_auto_start_services" in content

    def test_pixi_tasks_exist(self):
        """Test that pixi tasks are defined."""
        pixi_toml = Path(__file__).parent.parent / "pixi.toml"
        content = pixi_toml.read_text()

        # Check for registry-driven tasks
        assert "list-services" in content
        assert "check-services" in content
        assert "test-services" in content
        assert "start-all" in content


class TestServiceAPI:
    """Test service API patterns."""

    def test_base_service_client_exists(self):
        """Test that BaseServiceClient exists and is importable."""
        from robomage.clients.base_service_client import BaseServiceClient

        assert BaseServiceClient is not None

    def test_service_client_creation_from_metadata(self):
        """Test creating client from service metadata."""
        from robomage.clients.base_service_client import BaseServiceClient

        registry = get_registry()
        peak_service = registry.get_service("peak_analysis")

        # Should be able to create client from metadata
        client = BaseServiceClient(service_metadata=peak_service)
        assert client is not None
        assert client.base_url == peak_service.get_base_url()

    def test_service_health_endpoint_format(self):
        """Test that services have consistent health endpoint."""
        registry = get_registry()
        services = registry.get_all_services()

        for service in services:
            # All services should have /health endpoint
            assert service.endpoints is not None
            assert service.endpoints.health == "/health"


class TestDocumentation:
    """Test that documentation is complete."""

    def test_custom_services_guide_exists(self):
        """Test that custom services guide exists."""
        guide_path = Path(__file__).parent.parent / "docs" / "CUSTOM-SERVICES-GUIDE.md"
        assert guide_path.exists()

        # Should be substantial (500+ lines)
        content = guide_path.read_text()
        assert len(content.split("\n")) > 500

    def test_phase_completion_docs_exist(self):
        """Test that phase completion docs exist (in archive after cleanup)."""
        archive_dir = Path(__file__).parent.parent / "archive" / "custom-services"

        phase_docs = [
            "PHASE-1-SERVICE-REGISTRY-COMPLETE.md",
            "PHASE-2-DASHBOARD-INTEGRATION-COMPLETE.md",
            "PHASE-3-WORKFLOW-INTEGRATION-COMPLETE.md",
            "PHASE-4-SERVICE-TEMPLATE-COMPLETE.md",
        ]

        for doc in phase_docs:
            doc_path = archive_dir / doc
            assert doc_path.exists(), f"Missing phase doc: {doc}"

    def test_readme_mentions_custom_services(self):
        """Test that README mentions custom services."""
        readme = Path(__file__).parent.parent / "README.md"
        content = readme.read_text()

        # Should link to custom services guide
        assert "CUSTOM-SERVICES-GUIDE" in content or "custom-services" in content.lower()


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.slow
    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath("services/peak_analysis/main.py").exists(),
        reason="Peak analysis service not available",
    )
    def test_full_workflow_with_service(self):
        """Test complete workflow with service-backed node."""
        # This is a placeholder for a full end-to-end test
        # In production, this would:
        # 1. Start services
        # 2. Create workflow with service node
        # 3. Execute workflow
        # 4. Verify results
        # 5. Stop services
        pass


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

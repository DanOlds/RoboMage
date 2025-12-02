#!/usr/bin/env python3
"""
RoboMage Custom Service Generator

Interactive script to generate a new microservice from the service template.
Creates all necessary files with proper naming and configuration.

Usage:
    python create_service.py

The script will prompt for:
    - Service name (e.g., background_subtraction)
    - Display name (e.g., Background Subtraction)
    - Description
    - Port number
    - Node type for workflow integration
"""

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_step(step: int, text: str) -> None:
    """Print a formatted step."""
    print(f"\n[Step {step}] {text}")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"✅ {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"❌ {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"⚠️  {text}")


def validate_service_name(name: str) -> bool:
    """
    Validate service name (lowercase, underscores only).
    
    Args:
        name: Service name to validate
        
    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(r'^[a-z][a-z0-9_]*$', name))


def validate_port(port: str) -> bool:
    """
    Validate port number (8000-9000 range).
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        port_num = int(port)
        return 8000 <= port_num <= 9000
    except ValueError:
        return False


def check_port_conflict(port: str, services_dir: Path) -> bool:
    """
    Check if port is already in use by another service.
    
    Args:
        port: Port number to check
        services_dir: Services directory path
        
    Returns:
        True if port is available, False if conflict
    """
    for service_json in services_dir.glob("*/service.json"):
        with open(service_json) as f:
            config = json.load(f)
            if config.get("port") == int(port):
                print_warning(f"Port {port} already used by {service_json.parent.name}")
                return False
    return True


def check_name_conflict(name: str, services_dir: Path) -> bool:
    """
    Check if service name already exists.
    
    Args:
        name: Service name to check
        services_dir: Services directory path
        
    Returns:
        True if name is available, False if conflict
    """
    service_path = services_dir / name
    if service_path.exists():
        print_warning(f"Service '{name}' already exists at {service_path}")
        return False
    return True


def get_user_input() -> Dict[str, str]:
    """
    Collect user input for service configuration.
    
    Returns:
        Dictionary with service configuration
    """
    print_header("RoboMage Custom Service Generator")
    
    print("This script will create a new microservice from the template.")
    print("You'll be prompted for configuration details.\n")
    
    # Get service name
    while True:
        service_name = input("Service name (lowercase_with_underscores): ").strip()
        if not service_name:
            print_error("Service name cannot be empty")
            continue
        if not validate_service_name(service_name):
            print_error("Invalid name. Use lowercase letters, numbers, and underscores only.")
            print_error("Must start with a letter (e.g., 'background_subtraction')")
            continue
        
        # Check for name conflicts
        services_dir = Path(__file__).parent
        if not check_name_conflict(service_name, services_dir):
            retry = input("Use a different name? (y/n): ").strip().lower()
            if retry != 'y':
                print("Aborting.")
                sys.exit(0)
            continue
        break
    
    # Get display name
    while True:
        display_name = input(f"Display name (e.g., 'Background Subtraction'): ").strip()
        if not display_name:
            # Auto-generate from service name
            display_name = ' '.join(word.capitalize() for word in service_name.split('_'))
            print(f"  Using auto-generated: {display_name}")
        break
    
    # Get description
    while True:
        description = input("Service description: ").strip()
        if not description:
            print_error("Description cannot be empty")
            continue
        break
    
    # Get port
    while True:
        port = input("Port number (8000-9000, default: 8003): ").strip()
        if not port:
            port = "8003"
            print(f"  Using default: {port}")
        if not validate_port(port):
            print_error("Invalid port. Must be between 8000 and 9000.")
            continue
        
        # Check for port conflicts
        services_dir = Path(__file__).parent
        if not check_port_conflict(port, services_dir):
            retry = input("Use a different port? (y/n): ").strip().lower()
            if retry != 'y':
                print("Aborting.")
                sys.exit(0)
            continue
        break
    
    # Get node type
    print("\nWorkflow node type options:")
    print("  1. analysis    - Analysis operation (default)")
    print("  2. transform   - Data transformation")
    print("  3. filter      - Data filtering")
    print("  4. export      - Data export")
    
    while True:
        choice = input("Select node type (1-4, default: 1): ").strip()
        if not choice:
            node_type = "analysis"
            break
        
        node_type_map = {
            "1": "analysis",
            "2": "transform",
            "3": "filter",
            "4": "export",
        }
        
        if choice in node_type_map:
            node_type = node_type_map[choice]
            break
        else:
            print_error("Invalid choice. Enter 1-4.")
    
    return {
        "service_name": service_name,
        "display_name": display_name,
        "description": description,
        "port": port,
        "node_type": node_type,
    }


def create_service_from_template(config: Dict[str, str]) -> Path:
    """
    Create service directory and files from template.
    
    Args:
        config: Service configuration
        
    Returns:
        Path to created service directory
    """
    template_dir = Path(__file__).parent / "service_template"
    services_dir = Path(__file__).parent
    service_dir = services_dir / config["service_name"]
    
    print_step(1, f"Creating service directory: {service_dir}")
    service_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Created {service_dir}")
    
    # Process each template file
    template_files = [
        "main.py.template",
        "models.py.template",
        "analysis.py.template",
        "requirements.txt.template",
        ".env.template",
        "service.json.template",
        "README.md",
    ]
    
    print_step(2, "Generating files from templates")
    
    for template_file in template_files:
        template_path = template_dir / template_file
        
        if not template_path.exists():
            print_warning(f"Template not found: {template_file}")
            continue
        
        # Determine output filename
        if template_file.endswith(".template"):
            output_filename = template_file[:-9]  # Remove .template
        else:
            output_filename = template_file
        
        output_path = service_dir / output_filename
        
        # Read template
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace placeholders
        content = content.replace("{{SERVICE_NAME}}", config["service_name"])
        content = content.replace("{{DISPLAY_NAME}}", config["display_name"])
        content = content.replace("{{DESCRIPTION}}", config["description"])
        content = content.replace("{{PORT}}", config["port"])
        content = content.replace("{{NODE_TYPE}}", config["node_type"])
        
        # Write output
        with open(output_path, 'w') as f:
            f.write(content)
        
        print_success(f"  {output_filename}")
    
    return service_dir


def print_next_steps(service_dir: Path, config: Dict[str, str]) -> None:
    """
    Print next steps for the user.
    
    Args:
        service_dir: Path to created service
        config: Service configuration
    """
    print_header("Service Created Successfully!")
    
    print(f"📁 Service location: {service_dir}\n")
    
    print("Next steps:\n")
    
    print("1️⃣  Implement your analysis logic:")
    print(f"    Edit: {service_dir}/analysis.py")
    print(f"          {service_dir}/models.py\n")
    
    print("2️⃣  Install dependencies:")
    print(f"    cd {service_dir}")
    print(f"    pip install -r requirements.txt\n")
    
    print("3️⃣  Test the service:")
    print(f"    python main.py --port {config['port']}")
    print(f"    # In another terminal:")
    print(f"    curl http://localhost:{config['port']}/health\n")
    
    print("4️⃣  The service is automatically registered!")
    print(f"    - Registry: services/registry.json")
    print(f"    - Config: {service_dir}/service.json")
    print(f"    - Restart dashboard to see it\n")
    
    print("5️⃣  Use in workflows:")
    print(f"    - Node type: '{config['node_type']}'")
    print(f"    - Node name: '{config['service_name']}'")
    print(f"    - Auto-discovered by workflow engine\n")
    
    print("📚 Documentation:")
    print(f"    - Service README: {service_dir}/README.md")
    print(f"    - Custom Services Guide: docs/CUSTOM-SERVICES-GUIDE.md")
    print(f"    - Node Development: docs/node-development-guide.md\n")


def main():
    """Main entry point."""
    try:
        # Get user input
        config = get_user_input()
        
        # Confirm before proceeding
        print("\n" + "=" * 70)
        print("Configuration Summary:")
        print("=" * 70)
        for key, value in config.items():
            print(f"  {key:20s}: {value}")
        print("=" * 70 + "\n")
        
        confirm = input("Create service with this configuration? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Aborting.")
            sys.exit(0)
        
        # Create service
        service_dir = create_service_from_template(config)
        
        # Print next steps
        print_next_steps(service_dir, config)
        
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error creating service: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

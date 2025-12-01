"""
Custom Workflow Nodes

This package is for user-created custom workflow nodes.

To add a custom node:
1. Create a .py file in this directory (e.g., my_analysis.py)
2. Use the @register_node decorator on your handler function
3. Restart the workflow service - your node will auto-discover

The node will automatically appear in the dashboard's workflow builder palette.

See README.md in this directory for detailed instructions and examples.
"""

# Auto-discover pattern: Any imports here will be loaded
# But typically nodes just need to exist in this directory
# and the registry will find them automatically

__all__ = []

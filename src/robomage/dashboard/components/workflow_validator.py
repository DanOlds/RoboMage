"""
Workflow validation logic.

Validates workflow structure before execution.
Framework-agnostic - pure Python logic.
"""

from collections import defaultdict
from typing import Any


class WorkflowValidator:
    """
    Validates workflow structure and configuration.

    Checks for:
    - Cycles (DAG requirement - workflows must be Directed Acyclic Graphs)
    - Disconnected nodes
    - Invalid edge connections
    - Missing required configuration
    - Empty workflows

    Example:
        ```python
        workflow = {
            "nodes": [
                {"id": "n1", "type": "load_files", "config": {...}},
                {"id": "n2", "type": "peak_analysis", "config": {...}},
            ],
            "edges": [{"id": "e1", "source": "n1", "target": "n2"}],
        }

        is_valid, errors = WorkflowValidator.validate(workflow)
        if not is_valid:
            print("Workflow errors:", errors)
        ```
    """

    @staticmethod
    def validate(
        workflow: dict[str, Any], valid_node_types: set[str] | None = None
    ) -> tuple[bool, list[str]]:
        """
        Validate a workflow definition.

        Args:
            workflow: Workflow definition dict with 'nodes' and 'edges' keys
            valid_node_types: Optional set of valid node types. If None, uses default set.

        Returns:
            Tuple of (is_valid, list_of_errors)

        Example:
            ```python
            is_valid, errors = WorkflowValidator.validate(workflow)
            if is_valid:
                # Execute workflow
                pass
            else:
                # Display errors to user
                for error in errors:
                    print(f"❌ {error}")
            ```
        """
        errors = []

        # Check for empty workflow
        if not workflow.get("nodes"):
            errors.append("Workflow has no nodes")
            return False, errors

        # Check for cycles (DAG requirement)
        if WorkflowValidator._has_cycles(workflow):
            errors.append("Workflow contains cycles (must be a Directed Acyclic Graph)")

        # Check for disconnected nodes (warning, not necessarily an error)
        disconnected = WorkflowValidator._find_disconnected_nodes(workflow)
        if disconnected:
            errors.append(f"Disconnected nodes: {', '.join(disconnected)}")

        # Check for invalid edges
        edge_errors = WorkflowValidator._check_edge_validity(workflow)
        errors.extend(edge_errors)

        # Check for missing/invalid node types
        type_errors = WorkflowValidator._check_node_types(workflow, valid_node_types)
        errors.extend(type_errors)

        # Check for missing required configuration
        config_errors = WorkflowValidator._check_required_config(workflow)
        errors.extend(config_errors)

        return len(errors) == 0, errors

    @staticmethod
    def _has_cycles(workflow: dict[str, Any]) -> bool:
        """
        Check if workflow has cycles using Depth-First Search (DFS).

        A cycle exists if during DFS traversal, we encounter a node
        that is already in the current recursion stack.

        Args:
            workflow: Workflow definition dict

        Returns:
            True if cycles detected, False if DAG is valid
        """
        nodes = {node["id"] for node in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])

        # Build adjacency list (node -> list of successor nodes)
        graph = defaultdict(list)
        for edge in edges:
            graph[edge["source"]].append(edge["target"])

        # DFS with recursion stack tracking
        visited = set()
        rec_stack = set()  # Nodes in current recursion path

        def has_cycle_dfs(node_id: str) -> bool:
            """DFS helper that returns True if cycle detected."""
            visited.add(node_id)
            rec_stack.add(node_id)

            # Visit all neighbors
            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Back edge detected - cycle found!
                    return True

            # Remove from recursion stack on backtrack
            rec_stack.remove(node_id)
            return False

        # Check all nodes (handles disconnected components)
        for node_id in nodes:
            if node_id not in visited:
                if has_cycle_dfs(node_id):
                    return True

        return False

    @staticmethod
    def _find_disconnected_nodes(workflow: dict[str, Any]) -> list[str]:
        """
        Find nodes not connected to any edges.

        A disconnected node has no incoming or outgoing edges.
        This might be intentional (e.g., independent computations)
        or an error (forgot to connect).

        Args:
            workflow: Workflow definition dict

        Returns:
            List of disconnected node IDs
        """
        nodes = {node["id"] for node in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])

        # Track which nodes are connected
        connected = set()
        for edge in edges:
            connected.add(edge["source"])
            connected.add(edge["target"])

        return sorted(list(nodes - connected))

    @staticmethod
    def _check_edge_validity(workflow: dict[str, Any]) -> list[str]:
        """
        Check that all edges reference valid nodes.

        Args:
            workflow: Workflow definition dict

        Returns:
            List of error messages for invalid edges
        """
        errors = []
        nodes = {node["id"] for node in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])

        for edge in edges:
            edge_id = edge.get("id", "unknown")
            source = edge.get("source")
            target = edge.get("target")

            if not source:
                errors.append(f"Edge '{edge_id}': missing source node")
            elif source not in nodes:
                errors.append(f"Edge '{edge_id}': source '{source}' not found")

            if not target:
                errors.append(f"Edge '{edge_id}': missing target node")
            elif target not in nodes:
                errors.append(f"Edge '{edge_id}': target '{target}' not found")

            if source == target:
                errors.append(f"Edge '{edge_id}': self-loop (source == target)")

        return errors

    @staticmethod
    def _check_node_types(
        workflow: dict[str, Any], valid_node_types: set[str] | None = None
    ) -> list[str]:
        """
        Check that all nodes have valid types.

        Args:
            workflow: Workflow definition dict
            valid_node_types: Optional set of valid node types. If None, uses default set.

        Returns:
            List of error messages for nodes with missing/invalid types
        """
        errors = []
        nodes = workflow.get("nodes", [])

        # Use provided valid types or fall back to default set
        if valid_node_types is None:
            valid_types = {
                "load_files",
                "load_session",
                "filter_q_range",
                "normalize",
                "peak_analysis",
                "statistics",
                "export_csv",
                "export_json",
                "plot_results",
                "save_to_session",
            }
        else:
            valid_types = valid_node_types

        for node in nodes:
            node_id = node.get("id", "unknown")
            node_type = node.get("type")

            if not node_type:
                errors.append(f"Node '{node_id}': missing type")
            elif node_type not in valid_types:
                # Warning rather than error - might be a new node type
                errors.append(
                    f"Node '{node_id}': unknown type '{node_type}' "
                    f"(known types: {', '.join(sorted(valid_types))})"
                )

        return errors

    @staticmethod
    def _check_required_config(workflow: dict[str, Any]) -> list[str]:
        """
        Check for nodes missing required configuration.

        Different node types have different required config fields.
        This is a basic check - full validation happens server-side.

        Args:
            workflow: Workflow definition dict

        Returns:
            List of error messages for missing config
        """
        errors = []

        # Define required config per node type
        # Note: This is a basic check. Full schema validation happens
        # in NodeConfigurator.validate_config() with complete schemas.
        required_config = {
            "load_files": ["directory", "pattern"],
            "filter_q_range": ["q_min", "q_max"],
            "peak_analysis": ["profile_type"],
            "export_csv": ["output_path"],
            "export_json": ["output_path"],
        }

        for node in workflow.get("nodes", []):
            node_id = node.get("id", "unknown")
            node_type = node.get("type")
            config = node.get("config", {})

            if node_type in required_config:
                for required_field in required_config[node_type]:
                    if required_field not in config or not config[required_field]:
                        errors.append(
                            f"Node '{node_id}' ({node_type}): "
                            f"missing required config '{required_field}'"
                        )

        return errors

    @staticmethod
    def get_execution_order(workflow: dict[str, Any]) -> list[str] | None:
        """
        Get topological sort order for workflow execution.

        Returns node IDs in order they should be executed.
        Returns None if workflow has cycles.

        Args:
            workflow: Workflow definition dict

        Returns:
            List of node IDs in execution order, or None if invalid

        Example:
            ```python
            order = WorkflowValidator.get_execution_order(workflow)
            if order:
                print("Execute nodes in order:", order)
            else:
                print("Cannot determine order - workflow has cycles")
            ```
        """
        if WorkflowValidator._has_cycles(workflow):
            return None

        nodes = {node["id"] for node in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])

        # Build adjacency list and in-degree count
        graph = defaultdict(list)
        in_degree = {node_id: 0 for node_id in nodes}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            graph[source].append(target)
            in_degree[target] += 1

        # Kahn's algorithm for topological sort
        queue = [node_id for node_id in nodes if in_degree[node_id] == 0]
        result = []

        while queue:
            # Process node with no dependencies
            node_id = queue.pop(0)
            result.append(node_id)

            # Reduce in-degree for neighbors
            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If result doesn't include all nodes, there's a cycle
        # (shouldn't happen since we check earlier, but be safe)
        if len(result) != len(nodes):
            return None

        return result

    @staticmethod
    def visualize_errors(errors: list[str]) -> str:
        """
        Format error list for user-friendly display.

        Args:
            errors: List of error messages

        Returns:
            Formatted error string with emojis and bullets

        Example:
            ```python
            is_valid, errors = WorkflowValidator.validate(workflow)
            if not is_valid:
                print(WorkflowValidator.visualize_errors(errors))
            ```
        """
        if not errors:
            return "✅ Workflow is valid!"

        lines = [f"❌ Found {len(errors)} validation error(s):"]
        for i, error in enumerate(errors, 1):
            lines.append(f"  {i}. {error}")

        return "\n".join(lines)

"""
Data Models for Node I/O Inspection

Pydantic models for capturing and storing workflow node input/output snapshots
during execution. These models enable detailed inspection of data transformations
and help debug workflow issues.

Key Features:
- Type-safe data capture with Pydantic validation
- Automatic summarization of complex data structures
- Timing information for performance profiling
- JSON serialization for storage and transmission
- Human-readable data shape descriptions

Models:
    NodeIOSnapshot: Complete snapshot of node execution with I/O data
    InspectionMetadata: Additional context about execution environment
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field, field_serializer


class InspectionMetadata(BaseModel):
    """
    Metadata about inspection context and execution environment.

    Captures contextual information about when and how the inspection
    was performed, including workflow context and execution parameters.

    Attributes:
        workflow_id: ID of workflow being executed
        workflow_name: Human-readable workflow name
        execution_id: Unique ID for this execution run
        captured_at: When inspection was captured
        environment: Optional environment info (e.g., "production", "test")
    """

    workflow_id: str | None = Field(None, description="Workflow identifier")
    workflow_name: str | None = Field(None, description="Workflow display name")
    execution_id: str | None = Field(None, description="Execution run identifier")
    captured_at: datetime = Field(
        default_factory=datetime.now, description="Capture timestamp"
    )
    environment: str | None = Field(
        None, description="Execution environment (production/test/dev)"
    )


class NodeIOSnapshot(BaseModel):
    """
    Snapshot of input and output data for a single node execution.

    Captures all data flowing into and out of a workflow node, along with
    timing information and data shape summaries. This enables detailed
    inspection and debugging of workflow data transformations.

    The snapshot stores both serialized data (for persistence) and generates
    human-readable summaries (for UI display).

    Example:
        snapshot = NodeIOSnapshot(
            node_id="normalize_1",
            node_type="normalize",
            input_data={"files": [diffraction_data_1, diffraction_data_2]},
            timestamp_in=datetime.now()
        )

        # Later, after execution
        snapshot.output_data = {"files": [normalized_1, normalized_2]}
        snapshot.timestamp_out = datetime.now()

        print(snapshot.input_summary)  # "dict with 'files' (list, 2 items)"
        print(snapshot.duration_ms)    # 125.5

    Attributes:
        node_id: Unique node identifier in workflow
        node_type: Type of node (e.g., 'load_files', 'peak_analysis')
        input_data: Serialized input data (JSON-compatible)
        output_data: Serialized output data (JSON-compatible)
        timestamp_in: When node execution started
        timestamp_out: When node execution completed
        duration_ms: Execution duration in milliseconds
        metadata: Optional additional execution context
    """

    # Node identification
    node_id: str = Field(..., description="Unique node identifier")
    node_type: str = Field(..., description="Node type (e.g., 'load_files')")

    # I/O data (JSON-serializable)
    input_data: dict[str, Any] | list | str | int | float | None = Field(
        None, description="Serialized input data"
    )
    output_data: dict[str, Any] | list | str | int | float | None = Field(
        None, description="Serialized output data"
    )

    # Timing information
    timestamp_in: datetime | None = Field(None, description="Start timestamp")
    timestamp_out: datetime | None = Field(None, description="End timestamp")
    duration_ms: float | None = Field(
        None, ge=0.0, description="Execution duration (ms)"
    )

    # Additional context
    # Can be InspectionMetadata object or dict (for flexibility during construction)
    metadata: InspectionMetadata | dict[str, Any] | None = Field(
        None, description="Execution context metadata"
    )

    @field_serializer("input_data", "output_data", when_used="json")
    def _serialize_data(self, value: Any) -> Any:
        """
        Custom serializer to ensure numpy arrays are converted to lists.
        
        This is called automatically by Pydantic when serializing to JSON.
        It recursively converts any numpy arrays to lists to ensure
        JSON compatibility.
        """
        return self._make_json_serializable(value)
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """
        Recursively convert numpy arrays and other non-JSON types to JSON-serializable format.
        
        Args:
            obj: Object to convert
            
        Returns:
            JSON-serializable version of the object
        """
        # Import numpy conditionally
        try:
            import numpy as np  # type: ignore[import]
        except ImportError:
            np = None  # type: ignore[assignment]
        
        # Handle None
        if obj is None:
            return None
        
        # Handle primitives
        if isinstance(obj, (str, int, float, bool)):
            return obj
        
        # Handle numpy arrays - convert to list
        if np and isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # Handle numpy scalar types
        if np and isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        
        # Handle dict recursively
        if isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        
        # Handle list recursively
        if isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # For other objects, return as-is and let Pydantic handle it
        return obj

    @computed_field  # type: ignore[misc]
    @property
    def input_summary(self) -> str:
        """
        Human-readable summary of input data.

        Generates a concise description of the input data structure
        without exposing full data contents. Useful for UI display.

        Returns:
            String summary (e.g., "list of 3 DiffractionData objects")
        """
        return self._summarize_data(self.input_data)

    @computed_field  # type: ignore[misc]
    @property
    def output_summary(self) -> str:
        """
        Human-readable summary of output data.

        Generates a concise description of the output data structure
        without exposing full data contents. Useful for UI display.

        Returns:
            String summary (e.g., "dict with 'peaks' (25 items)")
        """
        return self._summarize_data(self.output_data)

    def _summarize_data(self, data: Any) -> str:
        """
        Create human-readable summary of data structure.

        Analyzes data and returns a concise description suitable for
        display in UIs and logs. Handles common types like lists, dicts,
        and Pydantic models.

        Args:
            data: Data to summarize (any type)

        Returns:
            String summary describing data structure and size
        """
        if data is None:
            return "None"

        if isinstance(data, dict):
            if not data:
                return "empty dict"

            # Special handling for common patterns
            if "type" in data and "count" in data:
                # Pre-formatted summary from orchestrator
                return f"{data.get('type')} ({data.get('count')} items)"

            # Generic dict summary
            keys = list(data.keys())[:3]  # Show first 3 keys
            key_str = ", ".join(f"'{k}'" for k in keys)
            if len(data) > 3:
                key_str += ", ..."
            return f"dict with {len(data)} keys: {key_str}"

        if isinstance(data, list):
            if not data:
                return "empty list"

            item_type = type(data[0]).__name__ if data else "unknown"
            return f"list of {len(data)} {item_type} objects"

        if isinstance(data, str):
            max_len = 50
            if len(data) > max_len:
                return f"string ({len(data)} chars): {data[:max_len]}..."
            return f"string: {data}"

        if isinstance(data, (int, float)):
            return f"{type(data).__name__}: {data}"

        # Default: show type name
        return f"<{type(data).__name__}>"

    @computed_field  # type: ignore[misc]
    @property
    def input_shape(self) -> str:
        """
        Compact shape description for database storage.

        Similar to input_summary but more concise, suitable for database
        columns and compact display.

        Returns:
            String like "list[3]" or "dict[5]"
        """
        return self._shape_description(self.input_data)

    @computed_field  # type: ignore[misc]
    @property
    def output_shape(self) -> str:
        """
        Compact shape description for database storage.

        Similar to output_summary but more concise, suitable for database
        columns and compact display.

        Returns:
            String like "list[3]" or "dict[5]"
        """
        return self._shape_description(self.output_data)

    def _shape_description(self, data: Any) -> str:
        """
        Create compact shape description.

        Args:
            data: Data to describe

        Returns:
            Compact shape string (e.g., "list[3]", "dict[5]")
        """
        if data is None:
            return "None"

        if isinstance(data, dict):
            return f"dict[{len(data)}]"

        if isinstance(data, list):
            return f"list[{len(data)}]"

        if isinstance(data, str):
            return f"str[{len(data)}]"

        return type(data).__name__


# Convenience function for creating snapshots
def create_snapshot(
    node_id: str,
    node_type: str,
    input_data: Any = None,
    output_data: Any = None,
    metadata: InspectionMetadata | None = None,
) -> NodeIOSnapshot:
    """
    Create a new NodeIOSnapshot with current timestamp.

    Helper function for quickly creating snapshots during node execution.

    Args:
        node_id: Unique node identifier
        node_type: Node type identifier
        input_data: Optional input data
        output_data: Optional output data
        metadata: Optional execution context

    Returns:
        New NodeIOSnapshot instance

    Example:
        snapshot = create_snapshot(
            node_id="analyze_1",
            node_type="peak_analysis",
            input_data={"files": diffraction_files},
            metadata=InspectionMetadata(workflow_id="workflow_123")
        )
    """
    return NodeIOSnapshot(
        node_id=node_id,
        node_type=node_type,
        input_data=input_data,
        output_data=output_data,
        timestamp_in=datetime.now() if input_data is not None else None,
        timestamp_out=datetime.now() if output_data is not None else None,
        metadata=metadata,
    )

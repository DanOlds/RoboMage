"""
Dynamic node configuration form builder.

Creates forms for configuring workflow nodes based on their schema.
Framework-agnostic - uses Dash Bootstrap Components.
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html


class NodeConfigurator:
    """
    Builds dynamic configuration forms for workflow nodes.

    Uses node type metadata from workflow service to generate
    appropriate input fields (text, number, dropdown, checkbox, etc.).

    Example:
        ```python
        schema = {
            "properties": {
                "prominence": {
                    "type": "number",
                    "description": "Peak prominence threshold",
                    "default": 0.1,
                    "minimum": 0.01,
                    "maximum": 1.0,
                },
                "profile_type": {
                    "type": "string",
                    "enum": ["gaussian", "lorentzian", "voigt"],
                    "default": "gaussian",
                },
            }
        }

        form = NodeConfigurator.create_config_form(
            node_id="peak_node_1",
            node_type="peak_analysis",
            current_config={},
            schema=schema,
        )
        ```
    """

    @staticmethod
    def create_config_form(
        node_id: str,
        node_type: str,
        current_config: dict[str, Any],
        schema: dict[str, Any],
    ) -> html.Div:
        """
        Create configuration form for a node.

        Args:
            node_id: Unique node identifier
            node_type: Node type (e.g., "peak_analysis", "load_files")
            current_config: Current configuration values
            schema: JSON schema for configuration with 'properties' key

        Returns:
            Dash component with form fields

        Example schema:
            ```python
            {
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory containing data files",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "File pattern (e.g., *.chi)",
                        "default": "*.chi",
                    },
                }
            }
            ```
        """
        if not schema or "properties" not in schema:
            return html.Div(
                [html.P("No configuration needed", className="text-muted")],
                className="p-3",
            )

        form_fields = []

        for prop_name, prop_schema in schema["properties"].items():
            field = NodeConfigurator._create_field(
                node_id=node_id,
                prop_name=prop_name,
                prop_schema=prop_schema,
                current_value=current_config.get(prop_name),
            )
            form_fields.append(field)

        return html.Div(
            [
                html.H6(f"Configure {node_type}", className="mb-3"),
                *form_fields,
                html.Hr(),
                dbc.Button(
                    "Apply Changes",
                    id={"type": "apply-node-config", "node_id": node_id},
                    color="primary",
                    size="sm",
                    className="w-100",
                ),
            ],
            className="p-3",
        )

    @staticmethod
    def _create_field(
        node_id: str,
        prop_name: str,
        prop_schema: dict[str, Any],
        current_value: Any,
    ) -> dbc.FormGroup:
        """
        Create form field based on property schema.

        Args:
            node_id: Unique node identifier
            prop_name: Property name
            prop_schema: JSON schema for this property
            current_value: Current value (None if not set)

        Returns:
            FormGroup with label and input field
        """
        field_type = prop_schema.get("type", "string")
        description = prop_schema.get("description", "")
        default = prop_schema.get("default")
        enum_values = prop_schema.get("enum")

        # Use current value or default
        value = current_value if current_value is not None else default

        # Create label with description
        label_text = prop_name.replace("_", " ").title()
        label = dbc.Label(
            [
                label_text,
                (
                    html.Small(f" - {description}", className="text-muted ms-1")
                    if description
                    else None
                ),
            ]
        )

        # Choose input type based on schema
        input_field = NodeConfigurator._create_input_field(
            node_id=node_id,
            prop_name=prop_name,
            field_type=field_type,
            enum_values=enum_values,
            value=value,
            prop_schema=prop_schema,
        )

        return html.Div([label, input_field], className="mb-3")

    @staticmethod
    def _create_input_field(
        node_id: str,
        prop_name: str,
        field_type: str,
        enum_values: list[str] | None,
        value: Any,
        prop_schema: dict[str, Any],
    ) -> Any:
        """
        Create appropriate input field based on field type.

        Args:
            node_id: Unique node identifier
            prop_name: Property name
            field_type: JSON schema type (string, number, boolean, etc.)
            enum_values: List of allowed values (for enum fields)
            value: Current/default value
            prop_schema: Full property schema

        Returns:
            Dash input component
        """
        field_id = {"type": "node-config-input", "node_id": node_id, "prop": prop_name}

        # Dropdown for enum values
        if enum_values:
            return dcc.Dropdown(
                id=field_id,
                options=[{"label": v, "value": v} for v in enum_values],
                value=value,
                clearable=False,
                className="mb-0",
            )

        # Numeric input
        if field_type == "number" or field_type == "integer":
            step = prop_schema.get("multipleOf", "any")
            if field_type == "integer" and step == "any":
                step = 1

            return dbc.Input(
                id=field_id,
                type="number",
                value=value if value is not None else "",
                step=step,
                min=prop_schema.get("minimum"),
                max=prop_schema.get("maximum"),
                placeholder=prop_schema.get("placeholder", ""),
            )

        # Boolean/checkbox
        if field_type == "boolean":
            return dbc.Checkbox(
                id=field_id,
                value=value if value is not None else False,
            )

        # Array (simple text input for now - could be enhanced)
        if field_type == "array":
            # Convert array to comma-separated string for input
            str_value = ", ".join(map(str, value)) if value else ""
            return dbc.Input(
                id=field_id,
                type="text",
                value=str_value,
                placeholder="Comma-separated values",
            )

        # Default: text input
        return dbc.Input(
            id=field_id,
            type="text",
            value=value if value is not None else "",
            placeholder=prop_schema.get("placeholder", ""),
            pattern=prop_schema.get("pattern"),
        )

    @staticmethod
    def parse_form_data(form_values: dict[str, Any]) -> dict[str, Any]:
        """
        Parse form values into config dict.

        Cleans up form data by:
        - Removing None values
        - Removing empty strings
        - Converting types as needed

        Args:
            form_values: Dict of {prop_name: value} from form inputs

        Returns:
            Validated config dict ready for node configuration

        Example:
            ```python
            form_data = {
                "prominence": 0.15,
                "profile_type": "gaussian",
                "min_distance": "",  # Empty - will be removed
                "enabled": True,
            }

            config = NodeConfigurator.parse_form_data(form_data)
            # Result: {"prominence": 0.15, "profile_type": "gaussian", "enabled": True}
            ```
        """
        # Strip None values and empty strings
        return {k: v for k, v in form_values.items() if v is not None and v != ""}

    @staticmethod
    def validate_config(
        config: dict[str, Any], schema: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Validate configuration against schema.

        Checks:
        - Required fields are present
        - Values are within min/max bounds
        - Enum values are valid
        - Type compatibility

        Args:
            config: Configuration dictionary to validate
            schema: JSON schema with 'properties' and optional 'required'

        Returns:
            Tuple of (is_valid, list_of_errors)

        Example:
            ```python
            schema = {
                "properties": {"prominence": {"type": "number", "minimum": 0.01}},
                "required": ["prominence"],
            }

            is_valid, errors = NodeConfigurator.validate_config(
                {"prominence": 0.005},  # Below minimum
                schema,
            )
            # is_valid = False
            # errors = ["prominence: value 0.005 is below minimum 0.01"]
            ```
        """
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in config or config[field] is None:
                errors.append(f"{field}: required field is missing")

        # Validate each field
        properties = schema.get("properties", {})
        for field, value in config.items():
            if field not in properties:
                continue  # Skip unknown fields (could be extra data)

            prop_schema = properties[field]
            field_type = prop_schema.get("type", "string")

            # Type validation
            if field_type == "number" or field_type == "integer":
                if not isinstance(value, (int, float)):
                    type_name = type(value).__name__
                    errors.append(f"{field}: expected number, got {type_name}")
                    continue

                # Min/max validation
                minimum = prop_schema.get("minimum")
                if minimum is not None and value < minimum:
                    errors.append(f"{field}: value {value} is below minimum {minimum}")

                maximum = prop_schema.get("maximum")
                if maximum is not None and value > maximum:
                    errors.append(f"{field}: value {value} exceeds maximum {maximum}")

            elif field_type == "boolean":
                if not isinstance(value, bool):
                    type_name = type(value).__name__
                    errors.append(f"{field}: expected boolean, got {type_name}")

            elif field_type == "string":
                if not isinstance(value, str):
                    type_name = type(value).__name__
                    errors.append(f"{field}: expected string, got {type_name}")
                    continue

                # Enum validation
                enum_values = prop_schema.get("enum")
                if enum_values and value not in enum_values:
                    errors.append(
                        f"{field}: value '{value}' not in allowed values {enum_values}"
                    )

                # Pattern validation (basic regex check)
                pattern = prop_schema.get("pattern")
                if pattern:
                    import re

                    if not re.match(pattern, value):
                        errors.append(
                            f"{field}: value does not match pattern {pattern}"
                        )

        return len(errors) == 0, errors

    @staticmethod
    def get_field_help_text(prop_schema: dict[str, Any]) -> str:
        """
        Generate helpful hint text for a field based on its schema.

        Args:
            prop_schema: JSON schema for the property

        Returns:
            Help text string describing field constraints

        Example:
            ```python
            schema = {"type": "number", "minimum": 0.01, "maximum": 1.0, "default": 0.1}

            help_text = NodeConfigurator.get_field_help_text(schema)
            # "Number between 0.01 and 1.0. Default: 0.1"
            ```
        """
        parts = []
        field_type = prop_schema.get("type", "string")

        # Type info
        if field_type == "number" or field_type == "integer":
            type_name = "Integer" if field_type == "integer" else "Number"

            minimum = prop_schema.get("minimum")
            maximum = prop_schema.get("maximum")

            if minimum is not None and maximum is not None:
                parts.append(f"{type_name} between {minimum} and {maximum}")
            elif minimum is not None:
                parts.append(f"{type_name} >= {minimum}")
            elif maximum is not None:
                parts.append(f"{type_name} <= {maximum}")
            else:
                parts.append(type_name)

        elif field_type == "boolean":
            parts.append("True/False")

        elif field_type == "string":
            enum_values = prop_schema.get("enum")
            if enum_values:
                parts.append(f"One of: {', '.join(enum_values)}")
            else:
                parts.append("Text")

        # Default value
        default = prop_schema.get("default")
        if default is not None:
            parts.append(f"Default: {default}")

        return ". ".join(parts) if parts else ""

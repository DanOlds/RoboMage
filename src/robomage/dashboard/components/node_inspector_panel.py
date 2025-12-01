"""
Node Inspector Panel Components

Reusable UI components for displaying node I/O data, execution statistics,
and metadata in the inspector tab.
"""

import json
from typing import Any

import dash_bootstrap_components as dbc
from dash import html


class NodeInspectorPanel:
    """Factory for creating inspector UI components."""

    @staticmethod
    def create_data_display(
        data: dict[str, Any] | None,
        title: str = "Data",
        data_type: str = "input",
    ) -> html.Div:
        """
        Create a formatted display for node I/O data.

        Args:
            data: Data dictionary to display (from inspection record)
            title: Title for the panel
            data_type: Type of data ("input" or "output")

        Returns:
            Div containing formatted data display
        """
        if data is None or not data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    f"No {data_type} data available for this node",
                ],
                color="info",
            )

        # Extract data type and summary
        data_type_str = data.get("type", "unknown")
        count = data.get("count")
        sample = data.get("sample")

        return html.Div(
            [
                # Data summary card
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H6(
                                    [
                                        html.I(className="fas fa-info-circle me-2"),
                                        title,
                                    ]
                                )
                            ]
                        ),
                        dbc.CardBody(
                            [
                                # Type badge
                                html.Div(
                                    [
                                        html.Strong("Data Type: "),
                                        dbc.Badge(
                                            data_type_str,
                                            color="primary",
                                            className="ms-2",
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                # Count if available
                                html.Div(
                                    [
                                        html.Strong("Count: "),
                                        html.Span(str(count)),
                                    ],
                                    className="mb-2",
                                )
                                if count is not None
                                else None,
                                html.Hr(),
                                # Sample data preview
                                html.Div(
                                    [
                                        html.Strong("Sample Data:"),
                                        NodeInspectorPanel._create_json_viewer(
                                            sample if sample else data
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ],
                    className="mb-3",
                )
            ]
        )

    @staticmethod
    def create_stats_display(
        duration_ms: float | None,
        timestamp_in: str | None,
        timestamp_out: str | None,
        input_shape: str | None,
        output_shape: str | None,
    ) -> html.Div:
        """
        Create a display for node execution statistics.

        Args:
            duration_ms: Execution duration in milliseconds
            timestamp_in: Input timestamp (ISO format)
            timestamp_out: Output timestamp (ISO format)
            input_shape: Summary of input data shape
            output_shape: Summary of output data shape

        Returns:
            Div containing execution statistics
        """
        # Color-code duration
        if duration_ms is not None:
            if duration_ms < 100:
                duration_color = "success"
                duration_label = "Fast"
            elif duration_ms < 500:
                duration_color = "info"
                duration_label = "Normal"
            elif duration_ms < 1000:
                duration_color = "warning"
                duration_label = "Slow"
            else:
                duration_color = "danger"
                duration_label = "Very Slow"
        else:
            duration_color = "secondary"
            duration_label = "Unknown"

        return html.Div(
            [
                # Duration card
                dbc.Card(
                    [
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-clock fa-3x text-muted mb-3"
                                        ),
                                        html.H3(
                                            f"{duration_ms:.2f} ms"
                                            if duration_ms is not None
                                            else "N/A",
                                            className="mb-1",
                                        ),
                                        dbc.Badge(
                                            duration_label,
                                            color=duration_color,
                                            className="mb-2",
                                        ),
                                        html.P(
                                            "Execution Time",
                                            className="text-muted mb-0",
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ]
                        )
                    ],
                    className="mb-3",
                ),
                # Data shapes card
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H6(
                                    [
                                        html.I(className="fas fa-shapes me-2"),
                                        "Data Shapes",
                                    ]
                                )
                            ]
                        ),
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-sign-in-alt text-success fa-2x mb-2"
                                                        ),
                                                        html.P(
                                                            "Input",
                                                            className="fw-bold mb-1",
                                                        ),
                                                        html.Code(
                                                            input_shape
                                                            if input_shape
                                                            else "N/A"
                                                        ),
                                                    ],
                                                    className="text-center",
                                                )
                                            ],
                                            width=6,
                                        ),
                                        dbc.Col(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-sign-out-alt text-primary fa-2x mb-2"
                                                        ),
                                                        html.P(
                                                            "Output",
                                                            className="fw-bold mb-1",
                                                        ),
                                                        html.Code(
                                                            output_shape
                                                            if output_shape
                                                            else "N/A"
                                                        ),
                                                    ],
                                                    className="text-center",
                                                )
                                            ],
                                            width=6,
                                        ),
                                    ]
                                )
                            ]
                        ),
                    ],
                    className="mb-3",
                ),
                # Timestamps card
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H6(
                                    [
                                        html.I(className="fas fa-calendar-alt me-2"),
                                        "Execution Timestamps",
                                    ]
                                )
                            ]
                        ),
                        dbc.CardBody(
                            [
                                html.Div(
                                    [
                                        html.Strong("Started: "),
                                        html.Code(
                                            timestamp_in if timestamp_in else "N/A"
                                        ),
                                    ],
                                    className="mb-2",
                                ),
                                html.Div(
                                    [
                                        html.Strong("Completed: "),
                                        html.Code(
                                            timestamp_out if timestamp_out else "N/A"
                                        ),
                                    ],
                                ),
                            ]
                        ),
                    ]
                ),
            ]
        )

    @staticmethod
    def create_metadata_display(metadata: dict[str, Any] | None) -> html.Div:
        """
        Create a display for node execution metadata.

        Args:
            metadata: Metadata dictionary from inspection record

        Returns:
            Div containing formatted metadata
        """
        if metadata is None or not metadata:
            return dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "No metadata available for this node",
                ],
                color="info",
            )

        return html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [
                                html.H6(
                                    [
                                        html.I(className="fas fa-tag me-2"),
                                        "Execution Metadata",
                                    ]
                                )
                            ]
                        ),
                        dbc.CardBody(
                            [NodeInspectorPanel._create_json_viewer(metadata)]
                        ),
                    ]
                )
            ]
        )

    @staticmethod
    def _create_json_viewer(data: Any, max_height: str = "400px") -> html.Div:
        """
        Create a JSON viewer with syntax highlighting.

        Args:
            data: Data to display as JSON
            max_height: Maximum height for scrollable container

        Returns:
            Div containing formatted JSON
        """
        try:
            json_str = json.dumps(data, indent=2, default=str)
        except Exception as e:
            json_str = f"Error serializing data: {e}"

        return html.Div(
            [
                html.Pre(
                    json_str,
                    style={
                        "backgroundColor": "#f8f9fa",
                        "padding": "15px",
                        "borderRadius": "5px",
                        "fontSize": "0.85rem",
                        "maxHeight": max_height,
                        "overflowY": "auto",
                        "whiteSpace": "pre-wrap",
                        "wordBreak": "break-word",
                    },
                )
            ]
        )

    @staticmethod
    def create_timeline_visualization(
        inspections: list[dict[str, Any]],
    ) -> html.Div:
        """
        Create a timeline visualization of workflow execution.

        Args:
            inspections: List of inspection records with timing data

        Returns:
            Div containing timeline visualization
        """
        if not inspections:
            return dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "No execution timeline available",
                ],
                color="info",
            )

        # Sort by timestamp
        sorted_inspections = sorted(
            inspections, key=lambda x: x.get("timestamp_in", "")
        )

        # Create timeline bars
        timeline_items = []
        for i, insp in enumerate(sorted_inspections):
            node_id = insp.get("node_id", "unknown")
            node_type = insp.get("node_type", "unknown")
            duration_ms = insp.get("duration_ms", 0)

            # Color by duration
            if duration_ms < 100:
                color = "success"
            elif duration_ms < 500:
                color = "info"
            elif duration_ms < 1000:
                color = "warning"
            else:
                color = "danger"

            timeline_items.append(
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Small(
                                            f"{i+1}.",
                                            className="text-muted me-2",
                                        ),
                                        html.Strong(node_id),
                                        html.Br(),
                                        html.Small(
                                            node_type,
                                            className="text-muted",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Badge(
                                            f"{duration_ms:.1f}ms",
                                            color=color,
                                            className="float-end",
                                        )
                                    ],
                                    width=6,
                                ),
                            ],
                            className="mb-2",
                        ),
                        dbc.Progress(
                            value=min(duration_ms / 10, 100),  # Scale for display
                            color=color,
                            className="mb-3",
                            style={"height": "8px"},
                        ),
                    ],
                    className="mb-2",
                )
            )

        return html.Div(timeline_items)


def create_empty_state(message: str, icon: str = "fa-info-circle") -> dbc.Alert:
    """
    Create an empty state message.

    Args:
        message: Message to display
        icon: FontAwesome icon class

    Returns:
        Alert component with empty state message
    """
    return dbc.Alert(
        [html.I(className=f"fas {icon} me-2"), message],
        color="light",
        className="text-center",
    )

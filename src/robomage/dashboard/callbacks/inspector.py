"""
Inspector Tab Callbacks

Callbacks for the Node I/O Inspector tab, handling workflow selection,
node selection, and data display.
"""

import dash
import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, html
from dash.exceptions import PreventUpdate

from robomage.dashboard.components import NodeInspectorPanel
from robomage.dashboard.layouts.inspector_layout import create_node_card
from robomage.persistence.api import SessionManager


def register_callbacks(app: dash.Dash) -> None:
    """
    Register all inspector-related callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        [
            Output("inspector-workflow-selector", "options"),
            Output("inspector-workflow-selector", "value"),
        ],
        [
            Input("inspector-refresh-btn", "n_clicks"),
            Input("current-session-id", "data"),
            Input("main-tabs", "active_tab"),  # Trigger when tab changes
        ],
    )
    def update_workflow_options(
        n_clicks: int | None, session_id: int | None, active_tab: str | None
    ) -> tuple:
        """
        Update the workflow selector dropdown with available workflows.

        Queries the database for workflows that have inspection data.
        Triggered when:
        - Refresh button is clicked
        - Session ID changes
        - Inspector tab becomes active

        Args:
            n_clicks: Refresh button clicks
            session_id: Current session ID
            active_tab: Currently active tab ID

        Returns:
            Tuple of (options, value) for workflow dropdown
        """
        # Only query database if Inspector tab is active (optimization)
        # Note: The tab ID is "inspector", not "inspector-tab"
        if active_tab and active_tab != "inspector":
            raise PreventUpdate
        
        try:
            mgr = SessionManager()
            
            # Get all inspections and extract unique workflow IDs
            all_inspections = mgr.get_inspections()
            
            if not all_inspections:
                # No inspections found
                options = [
                    {
                        "label": (
                            "No workflow executions found "
                            "(run a workflow with inspection enabled)"
                        ),
                        "value": "none",
                        "disabled": True,
                    }
                ]
                return options, None
            
            # Group by workflow_id and get counts
            workflow_ids = {}
            for insp in all_inspections:
                wf_id = insp.workflow_id
                if wf_id not in workflow_ids:
                    workflow_ids[wf_id] = {
                        "count": 0,
                        "first_timestamp": insp.timestamp_in,
                    }
                workflow_ids[wf_id]["count"] += 1
            
            # Get workflow names from Workflow table
            workflow_names = {}
            try:
                from robomage.persistence.models import Workflow
                session = mgr.Session()
                workflows = session.query(Workflow).filter(
                    Workflow.id.in_(workflow_ids.keys())
                ).all()
                workflow_names = {wf.id: wf.name for wf in workflows}
                session.close()
            except Exception as e:
                print(f"Warning: Could not fetch workflow names: {e}")
            
            # Create options sorted by most recent first
            options = []
            for wf_id, info in sorted(
                workflow_ids.items(),
                key=lambda x: x[1]["first_timestamp"] or "",
                reverse=True,
            ):
                timestamp_str = ""
                if info["first_timestamp"]:
                    try:
                        from datetime import datetime
                        if isinstance(info["first_timestamp"], str):
                            dt = datetime.fromisoformat(info["first_timestamp"])
                        else:
                            dt = info["first_timestamp"]
                        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        timestamp_str = str(info["first_timestamp"])[:19]
                
                # Build label with workflow name (if available) and metadata
                workflow_name = workflow_names.get(wf_id)
                if workflow_name:
                    label = f"{workflow_name}"
                else:
                    # Fallback to truncated UUID if no name found
                    label = f"{wf_id[:8]}..."
                
                label += f" ({info['count']} nodes)"
                if timestamp_str:
                    label += f" - {timestamp_str}"
                
                options.append({"label": label, "value": wf_id})
            
            # Select the most recent workflow by default
            default_value = options[0]["value"] if options else None
            
            return options, default_value
            
        except Exception as e:
            print(f"Error loading workflow options: {e}")
            options = [
                {
                    "label": f"Error loading workflows: {str(e)}",
                    "value": "error",
                    "disabled": True,
                }
            ]
            return options, None

    @app.callback(
        Output("inspector-workflow-info", "children"),
        [Input("inspector-workflow-selector", "value")],
    )
    def display_workflow_info(workflow_id: str | None) -> html.Div:
        """
        Display information about the selected workflow.

        Args:
            workflow_id: Selected workflow ID

        Returns:
            Div containing workflow information
        """
        if not workflow_id or workflow_id == "none":
            return html.Div()

        # Placeholder - will fetch actual workflow info
        return dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                f"Workflow ID: {workflow_id}",
            ],
            color="info",
            className="mt-2",
        )

    @app.callback(
        [
            Output("inspector-timeline", "children"),
            Output("inspector-node-list", "children"),
            Output("inspector-workflow-data", "data"),
        ],
        [Input("inspector-workflow-selector", "value")],
        [State("current-session-id", "data")],
    )
    def load_workflow_inspections(
        workflow_id: str | None, session_id: int | None
    ) -> tuple:
        """
        Load inspection data for the selected workflow.

        Args:
            workflow_id: Selected workflow ID
            session_id: Current session ID

        Returns:
            Tuple of (timeline, node_list, workflow_data)
        """
        if not workflow_id or workflow_id == "none":
            empty_timeline = dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Select a workflow execution to view timeline",
                ],
                color="info",
            )
            empty_nodes = html.P(
                "No nodes to display", className="text-muted text-center"
            )
            return empty_timeline, empty_nodes, None

        try:
            # Query inspection data from database
            mgr = SessionManager()
            inspections = mgr.get_workflow_inspections(workflow_id)

            if not inspections:
                empty_timeline = dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        "No inspection data found for this workflow",
                    ],
                    color="warning",
                )
                empty_nodes = html.P(
                    "No inspection data available", className="text-muted text-center"
                )
                return empty_timeline, empty_nodes, None

            # Convert to dict for storage
            inspection_dicts = [
                {
                    "id": insp.id,
                    "workflow_id": insp.workflow_id,
                    "node_id": insp.node_id,
                    "node_type": insp.node_type,
                    "input_data": insp.input_data,
                    "output_data": insp.output_data,
                    "input_shape": insp.input_shape,
                    "output_shape": insp.output_shape,
                    "timestamp_in": (
                        insp.timestamp_in.isoformat() if insp.timestamp_in else None
                    ),
                    "timestamp_out": (
                        insp.timestamp_out.isoformat() if insp.timestamp_out else None
                    ),
                    "duration_ms": insp.duration_ms,
                    "execution_metadata": insp.execution_metadata,
                }
                for insp in inspections
            ]

            # Create timeline visualization
            timeline = NodeInspectorPanel.create_timeline_visualization(
                inspection_dicts
            )

            # Create node cards
            node_cards = []
            for insp_dict in inspection_dicts:
                card = create_node_card(
                    node_id=insp_dict["node_id"],
                    node_type=insp_dict["node_type"],
                    duration_ms=insp_dict["duration_ms"] or 0,
                    input_shape=insp_dict["input_shape"] or "N/A",
                    output_shape=insp_dict["output_shape"] or "N/A",
                    is_selected=False,
                )
                node_cards.append(card)

            node_list = html.Div(node_cards)

            return timeline, node_list, inspection_dicts

        except Exception as e:
            error_timeline = dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error loading inspections: {str(e)}",
                ],
                color="danger",
            )
            error_nodes = html.P(
                "Error loading data", className="text-danger text-center"
            )
            return error_timeline, error_nodes, None

    @app.callback(
        Output("inspector-selected-node", "data"),
        [Input({"type": "inspector-node-card", "node_id": ALL}, "n_clicks")],
        [State({"type": "inspector-node-card", "node_id": ALL}, "id")],
        prevent_initial_call=True,
    )
    def select_node(n_clicks_list: list, ids_list: list) -> str | None:
        """
        Handle node card clicks to select a node.

        Args:
            n_clicks_list: List of click counts for each node card
            ids_list: List of node card IDs

        Returns:
            Selected node ID
        """
        if not any(n_clicks_list):
            raise PreventUpdate

        # Find which card was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if not triggered_id:
            raise PreventUpdate

        # Extract node_id from the triggered component
        import json

        id_dict = json.loads(triggered_id)
        node_id = id_dict.get("node_id")

        return node_id

    @app.callback(
        Output("inspector-input-panel", "children"),
        [
            Input("inspector-selected-node", "data"),
            Input("inspector-compact-view", "value"),
        ],
        [State("inspector-workflow-data", "data")],
    )
    def display_input_data(
        node_id: str | None, compact_view: bool, workflow_data: list[dict] | None
    ) -> html.Div:
        """
        Display input data for the selected node.

        Args:
            node_id: Selected node ID
            compact_view: Whether to use compact display mode
            workflow_data: Workflow inspection data

        Returns:
            Div containing input data display
        """
        if not node_id or not workflow_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-hand-pointer me-2"),
                    "Select a node to view its input data",
                ],
                color="light",
            )

        # Find the node's inspection data
        node_data = next(
            (item for item in workflow_data if item["node_id"] == node_id), None
        )

        if not node_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "No data found for this node",
                ],
                color="warning",
            )

        input_data = node_data.get("input_data")
        return NodeInspectorPanel.create_data_display(
            input_data,
            title=f"Input Data - {node_id}",
            data_type="input",
            compact=compact_view,
        )

    @app.callback(
        Output("inspector-output-panel", "children"),
        [
            Input("inspector-selected-node", "data"),
            Input("inspector-compact-view", "value"),
        ],
        [State("inspector-workflow-data", "data")],
    )
    def display_output_data(
        node_id: str | None, compact_view: bool, workflow_data: list[dict] | None
    ) -> html.Div:
        """
        Display output data for the selected node.

        Args:
            node_id: Selected node ID
            compact_view: Whether to use compact display mode
            workflow_data: Workflow inspection data

        Returns:
            Div containing output data display
        """
        if not node_id or not workflow_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-hand-pointer me-2"),
                    "Select a node to view its output data",
                ],
                color="light",
            )

        # Find the node's inspection data
        node_data = next(
            (item for item in workflow_data if item["node_id"] == node_id), None
        )

        if not node_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "No data found for this node",
                ],
                color="warning",
            )

        output_data = node_data.get("output_data")
        return NodeInspectorPanel.create_data_display(
            output_data,
            title=f"Output Data - {node_id}",
            data_type="output",
            compact=compact_view,
        )

    @app.callback(
        Output("inspector-stats-panel", "children"),
        [Input("inspector-selected-node", "data")],
        [State("inspector-workflow-data", "data")],
    )
    def display_stats(
        node_id: str | None, workflow_data: list[dict] | None
    ) -> html.Div:
        """
        Display execution statistics for the selected node.

        Args:
            node_id: Selected node ID
            workflow_data: Workflow inspection data

        Returns:
            Div containing statistics display
        """
        if not node_id or not workflow_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-hand-pointer me-2"),
                    "Select a node to view execution statistics",
                ],
                color="light",
            )

        # Find the node's inspection data
        node_data = next(
            (item for item in workflow_data if item["node_id"] == node_id), None
        )

        if not node_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "No data found for this node",
                ],
                color="warning",
            )

        return NodeInspectorPanel.create_stats_display(
            duration_ms=node_data.get("duration_ms"),
            timestamp_in=node_data.get("timestamp_in"),
            timestamp_out=node_data.get("timestamp_out"),
            input_shape=node_data.get("input_shape"),
            output_shape=node_data.get("output_shape"),
        )

    @app.callback(
        Output("inspector-metadata-panel", "children"),
        [Input("inspector-selected-node", "data")],
        [State("inspector-workflow-data", "data")],
    )
    def display_metadata(
        node_id: str | None, workflow_data: list[dict] | None
    ) -> html.Div:
        """
        Display execution metadata for the selected node.

        Args:
            node_id: Selected node ID
            workflow_data: Workflow inspection data

        Returns:
            Div containing metadata display
        """
        if not node_id or not workflow_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-hand-pointer me-2"),
                    "Select a node to view execution metadata",
                ],
                color="light",
            )

        # Find the node's inspection data
        node_data = next(
            (item for item in workflow_data if item["node_id"] == node_id), None
        )

        if not node_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "No data found for this node",
                ],
                color="warning",
            )

        metadata = node_data.get("execution_metadata")
        return NodeInspectorPanel.create_metadata_display(metadata)

    @app.callback(
        Output("inspector-export-btn", "n_clicks"),
        [Input("inspector-export-btn", "n_clicks")],
        [State("inspector-workflow-data", "data")],
        prevent_initial_call=True,
    )
    def export_inspection_data(
        n_clicks: int | None, workflow_data: list[dict] | None
    ) -> int:
        """
        Export inspection data (placeholder for future implementation).

        Args:
            n_clicks: Export button clicks
            workflow_data: Workflow inspection data

        Returns:
            Reset button click count
        """
        if not n_clicks or not workflow_data:
            raise PreventUpdate

        # Placeholder - will implement JSON/CSV export
        # For now, just log the action
        print(f"Export requested for {len(workflow_data)} inspection records")

        return 0

    @app.callback(
        Output("inspector-clear-history-modal", "is_open"),
        [
            Input("inspector-clear-history-btn", "n_clicks"),
            Input("inspector-clear-cancel-btn", "n_clicks"),
            Input("inspector-clear-confirm-btn", "n_clicks"),
        ],
        [State("inspector-clear-history-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_clear_modal(
        clear_click: int | None,
        cancel_click: int | None,
        confirm_click: int | None,
        is_open: bool,
    ) -> bool:
        """
        Toggle the clear history confirmation modal.

        Args:
            clear_click: Clear History button clicks
            cancel_click: Cancel button clicks
            confirm_click: Confirm button clicks
            is_open: Current modal state

        Returns:
            New modal state (open/closed)
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            return is_open

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Open modal when Clear History is clicked
        if triggered_id == "inspector-clear-history-btn":
            return True
        # Close modal when Cancel or Confirm is clicked
        elif triggered_id in [
            "inspector-clear-cancel-btn",
            "inspector-clear-confirm-btn",
        ]:
            return False

        return is_open

    @app.callback(
        [
            Output("inspector-workflow-selector", "options", allow_duplicate=True),
            Output("inspector-workflow-selector", "value", allow_duplicate=True),
        ],
        [Input("inspector-clear-confirm-btn", "n_clicks")],
        prevent_initial_call=True,
    )
    def clear_inspection_history(confirm_click: int | None) -> tuple:
        """
        Clear all inspection records from the database.

        Args:
            confirm_click: Confirm button clicks

        Returns:
            Tuple of (empty options, None value) for workflow dropdown
        """
        if not confirm_click:
            raise PreventUpdate

        try:
            mgr = SessionManager()
            count = mgr.clear_all_inspections()
            print(f"Cleared {count} inspection records from database")

            # Return empty dropdown options
            options = [
                {
                    "label": "No workflow executions found (history cleared)",
                    "value": "none",
                    "disabled": True,
                }
            ]
            return options, None

        except Exception as e:
            print(f"Error clearing inspection history: {e}")
            # Return error message in dropdown
            options = [
                {
                    "label": f"Error clearing history: {str(e)}",
                    "value": "error",
                    "disabled": True,
                }
            ]
            return options, None

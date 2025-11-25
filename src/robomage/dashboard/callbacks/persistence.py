"""
Session persistence callbacks for dashboard.

Handles saving, loading, and managing analysis sessions.
"""

import json
from typing import Any

import dash
import dash_bootstrap_components as dbc
import numpy as np
from dash import html
from dash.dependencies import Input, Output, State

from robomage.data.models import DiffractionData
from robomage.persistence import SessionManager


def register_persistence_callbacks(app: dash.Dash) -> None:
    """
    Register all session persistence callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        Output("save-session-modal", "is_open"),
        [
            Input("save-session-button", "n_clicks"),
            Input("save-session-cancel", "n_clicks"),
            Input("save-session-confirm", "n_clicks"),
        ],
        [State("save-session-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_save_modal(
        open_clicks: int, cancel_clicks: int, confirm_clicks: int, is_open: bool
    ) -> bool:
        """Toggle save session modal."""
        return not is_open

    @app.callback(
        Output("load-session-modal", "is_open"),
        [
            Input("load-session-button", "n_clicks"),
            Input("load-session-cancel", "n_clicks"),
        ],
        [State("load-session-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_load_modal(open_clicks: int, cancel_clicks: int, is_open: bool) -> bool:
        """Toggle load session modal."""
        return not is_open

    @app.callback(
        Output("manage-sessions-modal", "is_open"),
        [
            Input("manage-sessions-button", "n_clicks"),
            Input("manage-sessions-close", "n_clicks"),
        ],
        [State("manage-sessions-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_manage_modal(open_clicks: int, close_clicks: int, is_open: bool) -> bool:
        """Toggle manage sessions modal."""
        return not is_open

    @app.callback(
        [
            Output("save-session-feedback", "children"),
            Output("current-session-id", "data"),
        ],
        [Input("save-session-confirm", "n_clicks")],
        [
            State("session-name-input", "value"),
            State("session-description-input", "value"),
            State("file-data-store", "data"),
            State("wavelength-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def save_session(
        n_clicks: int,
        session_name: str | None,
        description: str | None,
        file_data: dict[str, Any] | None,
        wavelength_data: dict[str, float] | None,
    ) -> tuple[Any, int | None]:
        """
        Save current dashboard state to a session.

        Args:
            n_clicks: Number of button clicks
            session_name: User-provided session name
            description: Optional session description
            file_data: Dict mapping filenames to file data
            wavelength_data: Wavelength settings per file

        Returns:
            Tuple of (feedback message, session ID)
        """
        if not session_name or not session_name.strip():
            return (
                dbc.Alert(
                    "Please enter a session name",
                    color="danger",
                    dismissable=True,
                ),
                None,
            )

        if not file_data:
            return (
                dbc.Alert(
                    "No files to save. Please upload files first.",
                    color="warning",
                    dismissable=True,
                ),
                None,
            )

        try:
            mgr = SessionManager()

            # Create session
            session_id = mgr.create_session(
                name=session_name.strip(), description=description or ""
            )

            # Add each file to the session
            for filename, file_info in file_data.items():
                # Get wavelength for this file (default to synchrotron 0.1665 Å)
                wavelength = (
                    wavelength_data.get(filename, 0.1665) if wavelength_data else 0.1665
                )

                # Reconstruct DiffractionData from file-data-store format
                # Schema from file_upload.py:
                # {
                #   "filename": str,
                #   "q": list[float],
                #   "intensity": list[float],
                #   "metadata": dict,
                #   "num_points": int,
                #   "q_range": [min, max],
                #   "intensity_range": [min, max]
                # }
                q_array = np.array(file_info["q"])
                intensity_array = np.array(file_info["intensity"])

                # Create DiffractionData object with proper validation
                diffraction = DiffractionData(
                    filename=filename,
                    q=q_array,
                    intensity=intensity_array,
                    wavelength=wavelength,
                    metadata=file_info.get("metadata", {}),
                )

                # Save to FileStore via SessionManager
                mgr.add_file(session_id, diffraction)

            num_files = len(file_data)
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        f"Session '{session_name}' saved successfully with "
                        f"{num_files} file{'s' if num_files != 1 else ''}!",
                    ],
                    color="success",
                    dismissable=True,
                ),
                session_id,
            )

        except ValueError as e:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"Error: {str(e)}",
                    ],
                    color="danger",
                    dismissable=True,
                ),
                None,
            )
        except Exception as e:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-times-circle me-2"),
                        f"Unexpected error: {str(e)}",
                    ],
                    color="danger",
                    dismissable=True,
                ),
                None,
            )

    @app.callback(
        Output("session-list-container", "children"),
        [
            Input("load-session-modal", "is_open"),
        ],
        prevent_initial_call=False,
    )
    def populate_session_list(is_open: bool) -> Any:
        """
        Populate the session list when load modal opens.

        Args:
            is_open: Whether modal is open

        Returns:
            Session list component
        """
        if not is_open:
            return html.Div()

        try:
            mgr = SessionManager()
            sessions = mgr.list_sessions()

            if not sessions:
                return dbc.Alert(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "No saved sessions found. Create a session by uploading "
                        "files and clicking 'Save Session'.",
                    ],
                    color="info",
                )

            # Create a table of sessions
            session_rows = []
            for session in sessions:
                session_rows.append(
                    html.Tr(
                        [
                            html.Td(session.name),
                            html.Td(session.description or "—"),
                            html.Td(len(session.files)),
                            html.Td(
                                session.created_at.strftime("%Y-%m-%d %H:%M"),
                            ),
                            html.Td(
                                dbc.Button(
                                    [html.I(className="fas fa-upload me-1"), "Load"],
                                    id={"type": "load-session", "index": session.id},
                                    color="primary",
                                    size="sm",
                                )
                            ),
                        ]
                    )
                )

            return dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("Name"),
                                html.Th("Description"),
                                html.Th("Files"),
                                html.Th("Created"),
                                html.Th("Action"),
                            ]
                        )
                    ),
                    html.Tbody(session_rows),
                ],
                bordered=True,
                hover=True,
                responsive=True,
                striped=True,
            )

        except Exception as e:
            return dbc.Alert(
                f"Error loading sessions: {str(e)}",
                color="danger",
            )

    @app.callback(
        [
            Output("file-data-store", "data", allow_duplicate=True),
            Output("wavelength-store", "data", allow_duplicate=True),
            Output("load-session-feedback", "children"),
            Output("current-session-id", "data", allow_duplicate=True),
        ],
        [Input({"type": "load-session", "index": dash.ALL}, "n_clicks")],
        [State({"type": "load-session", "index": dash.ALL}, "id")],
        prevent_initial_call=True,
    )
    def load_session_callback(
        n_clicks_list: list[int], button_ids: list[dict[str, Any]]
    ) -> tuple[dict[str, Any], dict[str, float], Any, int | None]:
        """
        Load a saved session and restore files and wavelengths.

        Args:
            n_clicks_list: List of click counts
            button_ids: List of button IDs

        Returns:
            Tuple of (file_data, wavelength_data, feedback, session_id)
        """
        # Find which button was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return {}, {}, html.Div(), None

        # Get the button that triggered the callback
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if triggered_id == "":
            return {}, {}, html.Div(), None

        button_id = json.loads(triggered_id)
        session_id = button_id["index"]

        try:
            mgr = SessionManager()
            session = mgr.get_session(session_id)

            if not session:
                return (
                    {},
                    {},
                    dbc.Alert(
                        "Session not found!",
                        color="danger",
                        dismissable=True,
                    ),
                    None,
                )

            # Get all files for this session
            session_files = mgr.get_session_files(session_id)

            if not session_files:
                return (
                    {},
                    {},
                    dbc.Alert(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"Session '{session.name}' has no files!",
                        ],
                        color="warning",
                        dismissable=True,
                    ),
                    session_id,
                )

            # Reconstruct file data from stored files
            file_data = {}
            wavelength_data = {}

            for session_file in session_files:
                # Read DiffractionData from FileStore
                diffraction = mgr.file_store.read_file(session_file.file_id)

                if diffraction is None:
                    continue

                # Convert to file-data-store format (matching file_upload.py schema)
                filename = diffraction.filename
                file_info = {
                    "filename": filename,
                    "q": diffraction.q.tolist(),
                    "intensity": diffraction.intensity.tolist(),
                    "metadata": diffraction.metadata or {},
                    "num_points": len(diffraction.q),
                    "q_range": [float(diffraction.q.min()), float(diffraction.q.max())],
                    "intensity_range": [
                        float(diffraction.intensity.min()),
                        float(diffraction.intensity.max()),
                    ],
                }

                file_data[filename] = file_info
                wavelength_data[filename] = diffraction.wavelength

            return (
                file_data,
                wavelength_data,
                dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        (
                            f"Session '{session.name}' loaded successfully! "
                            f"Restored {len(file_data)} "
                            f"file{'s' if len(file_data) != 1 else ''}."
                        ),
                    ],
                    color="success",
                    dismissable=True,
                    duration=4000,
                ),
                session_id,
            )

        except ValueError as e:
            return (
                {},
                {},
                dbc.Alert(
                    f"Error: {str(e)}",
                    color="danger",
                    dismissable=True,
                ),
                None,
            )
        except Exception as e:
            return (
                {},
                {},
                dbc.Alert(
                    f"Unexpected error: {str(e)}",
                    color="danger",
                    dismissable=True,
                ),
                None,
            )

    @app.callback(
        Output("manage-sessions-container", "children"),
        [
            Input("manage-sessions-modal", "is_open"),
            Input("refresh-sessions-button", "n_clicks"),
        ],
        prevent_initial_call=False,
    )
    def populate_manage_sessions(is_open: bool, refresh_clicks: int) -> Any:
        """
        Populate the manage sessions list.

        Args:
            is_open: Whether modal is open
            refresh_clicks: Refresh button clicks

        Returns:
            Sessions management component
        """
        if not is_open:
            return html.Div()

        try:
            mgr = SessionManager()
            sessions = mgr.list_sessions()

            if not sessions:
                return dbc.Alert(
                    "No saved sessions found.",
                    color="info",
                )

            # Create detailed session cards
            session_cards = []
            for session in sessions:
                session_cards.append(
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            html.H5(session.name, className="mb-0"),
                                            width=8,
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                [
                                                    html.I(
                                                        className="fas fa-trash me-1"
                                                    ),
                                                    "Delete",
                                                ],
                                                id={
                                                    "type": "delete-session",
                                                    "index": session.id,
                                                },
                                                color="danger",
                                                size="sm",
                                            ),
                                            width=4,
                                            className="text-end",
                                        ),
                                    ]
                                )
                            ),
                            dbc.CardBody(
                                [
                                    html.P(
                                        session.description or "No description",
                                        className="text-muted",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Small(
                                                        [
                                                            html.I(
                                                                className=(
                                                                    "fas fa-file me-1"
                                                                )
                                                            ),
                                                            (
                                                                f"{len(session.files)} "
                                                                f"files"
                                                            ),
                                                        ]
                                                    ),
                                                ],
                                                width=4,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.Small(
                                                        [
                                                            html.I(
                                                                className=(
                                                                    "fas "
                                                                    "fa-calendar "
                                                                    "me-1"
                                                                )
                                                            ),
                                                            (
                                                                f"Created: "
                                                                f"{session.created_at.strftime('%Y-%m-%d')}"
                                                            ),
                                                        ]
                                                    ),
                                                ],
                                                width=8,
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        className="mb-3",
                    )
                )

            return html.Div(session_cards)

        except Exception as e:
            return dbc.Alert(
                f"Error loading sessions: {str(e)}",
                color="danger",
            )

    @app.callback(
        Output("manage-sessions-feedback", "children"),
        [Input({"type": "delete-session", "index": dash.ALL}, "n_clicks")],
        [State({"type": "delete-session", "index": dash.ALL}, "id")],
        prevent_initial_call=True,
    )
    def delete_session_callback(
        n_clicks_list: list[int], button_ids: list[dict[str, Any]]
    ) -> Any:
        """
        Handle session deletion.

        Args:
            n_clicks_list: List of click counts
            button_ids: List of button IDs

        Returns:
            Feedback message
        """
        # Find which button was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return html.Div()

        # Get the button that triggered the callback
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if triggered_id == "":
            return html.Div()

        button_id = json.loads(triggered_id)
        session_id = button_id["index"]

        try:
            mgr = SessionManager()
            session = mgr.get_session(session_id)
            session_name = session.name if session else f"Session {session_id}"

            mgr.delete_session(session_id)

            return dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Session '{session_name}' deleted successfully!",
                ],
                color="success",
                dismissable=True,
                duration=4000,
            )

        except ValueError as e:
            return dbc.Alert(
                f"Error: {str(e)}",
                color="danger",
                dismissable=True,
            )
        except Exception as e:
            return dbc.Alert(
                f"Unexpected error: {str(e)}",
                color="danger",
                dismissable=True,
            )

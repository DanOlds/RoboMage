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


def _load_session_files(
    mgr: SessionManager, session_id: int
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """
    Helper function to load files and analysis results from a session into UI store format.

    Args:
        mgr: SessionManager instance
        session_id: ID of session to load files from

    Returns:
        Tuple of (file_data, wavelength_data, analysis_results) dicts in UI store format
    """
    session_files = mgr.get_session_files(session_id)

    if not session_files:
        return {}, {"current_wavelength": 0.1665, "source_type": "standard"}, {}

    # Reconstruct file data from stored files
    file_data = {}
    analysis_results = {}
    loaded_wavelength = 0.1665  # Default

    for session_file in session_files:
        # Read DiffractionData from FileStore using stored path
        try:
            diffraction = mgr.file_store.load_file(session_file.stored_path)
        except FileNotFoundError:
            # File was deleted or moved - skip it
            print(f"⚠️ WARNING: Skipping missing file: {session_file.filename}")
            continue

        if diffraction is None:
            continue

        # Get wavelength from database (first file)
        if not file_data:  # First file
            loaded_wavelength = session_file.wavelength or 0.1665

        # Convert to file-data-store format (matching file_upload.py schema)
        filename = diffraction.filename or "unknown.chi"
        file_info = {
            "filename": filename,
            "q": diffraction.q_values.tolist(),
            "intensity": diffraction.intensities.tolist(),
            "metadata": {},  # DiffractionData doesn't store generic metadata
            "num_points": len(diffraction.q_values),
            "q_range": [
                float(diffraction.q_values.min()),
                float(diffraction.q_values.max()),
            ],
            "intensity_range": [
                float(diffraction.intensities.min()),
                float(diffraction.intensities.max()),
            ],
        }

        file_data[filename] = file_info

        # Load analysis results for this file (Sprint 7)
        latest_peak_analysis = mgr.get_latest_analysis(
            file_id=session_file.id, analysis_type="peak_detection"
        )

        if latest_peak_analysis:
            # Store analysis result in same format as analysis tab expects
            analysis_results[filename] = latest_peak_analysis.result_data

    # Restore global wavelength (matching wavelength-store schema)
    wavelength_data = {
        "current_wavelength": loaded_wavelength,
        "source_type": "standard",  # Could be enhanced to detect custom values
    }

    return file_data, wavelength_data, analysis_results


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
        Output("delete-all-sessions-modal", "is_open"),
        [
            Input("delete-all-sessions-button", "n_clicks"),
            Input("delete-all-cancel", "n_clicks"),
            Input("delete-all-confirm", "n_clicks"),
        ],
        [State("delete-all-sessions-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_delete_all_modal(
        open_clicks: int, cancel_clicks: int, confirm_clicks: int, is_open: bool
    ) -> bool:
        """Toggle delete all sessions confirmation modal."""
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
        wavelength_data: dict[str, Any] | None,
    ) -> tuple[Any, int | None]:
        """
        Save current dashboard state to a session.

        Args:
            n_clicks: Number of button clicks
            session_name: User-provided session name
            description: Optional session description
            file_data: Dict mapping filenames to file data
            wavelength_data: Global wavelength settings with schema:
                {"current_wavelength": float, "source_type": str}

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

        # Note: Removed file_data requirement to allow creating empty sessions
        # This supports workflow-first usage where data comes from workflow execution

        try:
            mgr = SessionManager()

            # Create session
            session_id = mgr.create_session(
                name=session_name.strip(), description=description or ""
            )

            # Get global wavelength
            # (current dashboard uses single wavelength for all files)
            # wavelength_data schema:
            # {"current_wavelength": float, "source_type": str}
            global_wavelength = 0.1665  # Default synchrotron wavelength
            if wavelength_data and "current_wavelength" in wavelength_data:
                global_wavelength = wavelength_data["current_wavelength"]

            # Add each file to the session (if any files are present)
            num_files = 0
            if file_data:
                for filename, file_info in file_data.items():
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
                        q_values=q_array,
                        intensities=intensity_array,
                        wavelength=global_wavelength,
                    )

                    # Save to FileStore via SessionManager
                    mgr.add_file_to_session(
                        session_id=session_id,
                        filename=filename,
                        wavelength=global_wavelength,
                        data=diffraction,
                    )
                    num_files += 1

            # Build success message
            if num_files > 0:
                message = f"Session '{session_name}' saved successfully with {num_files} file{'s' if num_files != 1 else ''}!"
            else:
                message = f"Empty session '{session_name}' created successfully. You can add files via upload or workflow execution."

            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        message,
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
            Output("analysis-results-store", "data", allow_duplicate=True),
            Output("load-session-feedback", "children"),
            Output("current-session-id", "data", allow_duplicate=True),
        ],
        [Input({"type": "load-session", "index": dash.ALL}, "n_clicks")],
        [State({"type": "load-session", "index": dash.ALL}, "id")],
        prevent_initial_call=True,
    )
    def load_session_callback(
        n_clicks_list: list[int | None], button_ids: list[dict[str, Any]]
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Any, int | None]:
        """
        Load a saved session and restore files and wavelengths.

        Args:
            n_clicks_list: List of click counts
            button_ids: List of button IDs

        Returns:
            Tuple of (file_data, wavelength_data, analysis_results, feedback, session_id)
            where wavelength_data has schema:
            {"current_wavelength": float, "source_type": str}
        """
        # Find which button was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, dash.no_update, html.Div(), dash.no_update

        # Get the button that triggered the callback
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if triggered_id == "":
            return dash.no_update, dash.no_update, html.Div(), dash.no_update

        # Check if this is actually a button click (not just a re-render)
        triggered_value = ctx.triggered[0]["value"]
        if triggered_value is None or triggered_value == 0:
            return (
                dash.no_update,
                dash.no_update,
                dash.no_update,
                html.Div(),
                dash.no_update,
            )

        button_id = json.loads(triggered_id)
        session_id = button_id["index"]

        try:
            mgr = SessionManager()
            session = mgr.get_session(session_id)

            if not session:
                return (
                    {},
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

            # Use helper function to load session files and analysis results
            file_data, wavelength_data, analysis_results = _load_session_files(
                mgr, session_id
            )

            # Analysis results now loaded from database (Sprint 7)
            return (
                file_data,
                wavelength_data,
                analysis_results,  # Restored from database
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
        [
            Output("manage-sessions-feedback", "children"),
            Output("manage-sessions-container", "children", allow_duplicate=True),
        ],
        [Input({"type": "delete-session", "index": dash.ALL}, "n_clicks")],
        [State({"type": "delete-session", "index": dash.ALL}, "id")],
        prevent_initial_call=True,
    )
    def delete_session_callback(
        n_clicks_list: list[int | None], button_ids: list[dict[str, Any]]
    ) -> tuple[Any, Any]:
        """
        Handle session deletion.

        Args:
            n_clicks_list: List of click counts
            button_ids: List of button IDs

        Returns:
            Tuple of (feedback message, updated session list)
        """
        # Find which button was clicked
        ctx = dash.callback_context
        if not ctx.triggered:
            return html.Div(), dash.no_update

        # Get the button that triggered the callback
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if triggered_id == "":
            return html.Div(), dash.no_update

        # Check if this is actually a button click (not just a re-render)
        triggered_value = ctx.triggered[0]["value"]
        if triggered_value is None or triggered_value == 0:
            return html.Div(), dash.no_update

        button_id = json.loads(triggered_id)
        session_id = button_id["index"]

        try:
            mgr = SessionManager()
            session = mgr.get_session(session_id)
            session_name = session.name if session else f"Session {session_id}"

            mgr.delete_session(session_id)

            # Refresh the session list after deletion
            sessions = mgr.list_sessions()

            if not sessions:
                session_list = dbc.Alert(
                    "No saved sessions found.",
                    color="info",
                )
            else:
                # Recreate session cards without the deleted session
                session_cards = []
                for s in sessions:
                    session_cards.append(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                html.H5(s.name, className="mb-0"),
                                                width=8,
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    [
                                                        html.I(
                                                            className=(
                                                                "fas fa-trash me-1"
                                                            )
                                                        ),
                                                        "Delete",
                                                    ],
                                                    id={
                                                        "type": "delete-session",
                                                        "index": s.id,
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
                                            s.description or "No description",
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
                                                                        "fas "
                                                                        "fa-file "
                                                                        "me-1"
                                                                    )
                                                                ),
                                                                (
                                                                    f"{len(s.files)} "
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
                                                                    f"{s.created_at.strftime('%Y-%m-%d')}"
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
                session_list = html.Div(session_cards)

            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        f"Session '{session_name}' deleted successfully!",
                    ],
                    color="success",
                    dismissable=True,
                    duration=4000,
                ),
                session_list,
            )

        except ValueError as e:
            return (
                dbc.Alert(
                    f"Error: {str(e)}",
                    color="danger",
                    dismissable=True,
                ),
                dash.no_update,
            )
        except Exception as e:
            return dbc.Alert(
                f"Unexpected error: {str(e)}",
                color="danger",
                dismissable=True,
            )

    @app.callback(
        [
            Output("delete-all-feedback", "children"),
            Output("manage-sessions-container", "children", allow_duplicate=True),
            Output("manage-sessions-feedback", "children", allow_duplicate=True),
        ],
        [Input("delete-all-confirm", "n_clicks")],
        prevent_initial_call=True,
    )
    def delete_all_sessions_callback(
        n_clicks: int | None,
    ) -> tuple[Any, Any, Any]:
        """
        Handle deletion of all sessions.

        Args:
            n_clicks: Number of confirm button clicks

        Returns:
            Tuple of (modal feedback, updated session list, manage modal feedback)
        """
        if n_clicks is None or n_clicks == 0:
            return html.Div(), dash.no_update, html.Div()

        try:
            mgr = SessionManager()
            sessions = mgr.list_sessions()
            num_sessions = len(sessions)

            # Delete all sessions
            for session in sessions:
                mgr.delete_session(session.id)

            # Success message
            success_msg = dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Successfully deleted {num_sessions} session{'s' if num_sessions != 1 else ''}!",
                ],
                color="success",
                dismissable=True,
                duration=4000,
            )

            # Empty session list
            empty_list = dbc.Alert(
                "No saved sessions found.",
                color="info",
            )

            return success_msg, empty_list, success_msg

        except Exception as e:
            error_msg = dbc.Alert(
                f"Error deleting sessions: {str(e)}",
                color="danger",
                dismissable=True,
            )
            return error_msg, dash.no_update, error_msg

    @app.callback(
        [
            Output("file-list", "children", allow_duplicate=True),
            Output("file-info", "children", allow_duplicate=True),
            Output("status-text", "children", allow_duplicate=True),
            Output("load-session-modal", "is_open", allow_duplicate=True),
        ],
        [
            Input("file-data-store", "data"),
        ],
        [
            State("load-session-modal", "is_open"),
        ],
        prevent_initial_call=True,
    )
    def sync_ui_with_store(
        file_data: dict[str, Any] | None, load_modal_open: bool
    ) -> tuple[Any, Any, str, bool]:
        """
        Sync file list UI with file-data-store when it changes.

        This ensures that when sessions are loaded, the UI updates to show
        the loaded files.

        Args:
            file_data: Current file data from store
            load_modal_open: Whether load session modal is open

        Returns:
            Tuple of (file_list, file_info, status_text, close_modal)
        """
        from .file_upload import create_file_info, create_file_list

        if not file_data:
            file_data = {}

        # Create updated UI components (same logic as file_upload.py)
        file_list = create_file_list(file_data)
        file_info = create_file_info(file_data)

        num_files = len(file_data)
        if num_files == 0:
            status = "No files loaded"
        elif num_files == 1:
            status = "Loaded 1 file"
        else:
            status = f"Loaded {num_files} files"

        # Close the load modal if it was open (session was just loaded)
        close_modal = False if load_modal_open else dash.no_update

        return file_list, file_info, status, close_modal

    # ===== Storage Configuration Callbacks =====

    @app.callback(
        Output("configure-storage-modal", "is_open"),
        [
            Input("configure-storage-button", "n_clicks"),
            Input("configure-storage-cancel", "n_clicks"),
            Input("configure-storage-apply", "n_clicks"),
        ],
        [State("configure-storage-modal", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_configure_storage_modal(
        open_clicks: int,
        cancel_clicks: int,
        apply_clicks: int,
        is_open: bool,
    ) -> bool:
        """Toggle configure storage modal."""
        return not is_open

    @app.callback(
        Output("storage-location-display", "children"),
        [
            Input("storage-location-store", "data"),
            Input("manage-sessions-modal", "is_open"),
        ],
    )
    def update_storage_location_display(
        custom_path: str | None, modal_open: bool
    ) -> str:
        """
        Update storage location display.

        Shows custom path if set, otherwise default location.
        """

        if custom_path:
            return custom_path
        else:
            # Show default location
            from robomage.persistence.database import DEFAULT_DB_PATH

            return str(DEFAULT_DB_PATH.parent)

    @app.callback(
        Output("current-storage-path", "children"),
        [Input("configure-storage-modal", "is_open")],
        [State("storage-location-store", "data")],
    )
    def update_current_storage_path(is_open: bool, custom_path: str | None) -> str:
        """Update current storage path in configuration modal."""

        if custom_path:
            return custom_path
        else:
            from robomage.persistence.database import DEFAULT_DB_PATH

            return str(DEFAULT_DB_PATH.parent)

    @app.callback(
        [
            Output("storage-location-store", "data", allow_duplicate=True),
            Output("configure-storage-feedback", "children"),
            Output("new-storage-path-input", "value"),
        ],
        [
            Input("configure-storage-apply", "n_clicks"),
            Input("reset-storage-button", "n_clicks"),
        ],
        [State("new-storage-path-input", "value")],
        prevent_initial_call=True,
    )
    def handle_storage_configuration(
        apply_clicks: int | None,
        reset_clicks: int | None,
        new_path: str | None,
    ) -> tuple[str | None, Any, str]:
        """
        Handle storage location configuration.

        Validates and applies new storage location.
        """
        from pathlib import Path

        ctx = dash.callback_context
        if not ctx.triggered:
            return dash.no_update, html.Div(), ""

        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Handle reset to default
        if triggered_id == "reset-storage-button":
            return (
                None,
                dbc.Alert(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        "Storage location reset to default (~/.robomage/)",
                    ],
                    color="success",
                    dismissable=True,
                    duration=3000,
                ),
                "",
            )

        # Handle apply new path
        if triggered_id == "configure-storage-apply":
            if not new_path or not new_path.strip():
                return (
                    dash.no_update,
                    dbc.Alert(
                        "Please enter a storage path",
                        color="danger",
                        dismissable=True,
                    ),
                    dash.no_update,
                )

            # Expand user path (~/)
            try:
                expanded_path = Path(new_path).expanduser()

                # Create directory if it doesn't exist
                expanded_path.mkdir(parents=True, exist_ok=True)

                # Verify it's writable
                test_file = expanded_path / ".robomage_test"
                test_file.touch()
                test_file.unlink()

                return (
                    str(expanded_path),
                    dbc.Alert(
                        [
                            html.I(className="fas fa-check-circle me-2"),
                            f"Storage location changed to: {expanded_path}",
                        ],
                        color="success",
                        dismissable=True,
                        duration=3000,
                    ),
                    "",
                )

            except Exception as e:
                return (
                    dash.no_update,
                    dbc.Alert(
                        f"Error: {str(e)}. Path must be writable.",
                        color="danger",
                        dismissable=True,
                    ),
                    dash.no_update,
                )

        return dash.no_update, html.Div(), ""

    # ===== Debug Panel Callbacks =====

    @app.callback(
        Output("debug-panel-collapse", "is_open"),
        [Input("toggle-debug-panel-button", "n_clicks")],
        [State("debug-panel-collapse", "is_open")],
        prevent_initial_call=True,
    )
    def toggle_debug_panel(n_clicks: int | None, is_open: bool) -> bool:
        """Toggle debug panel visibility."""
        return not is_open

    @app.callback(
        Output("debug-info-display", "children"),
        [
            Input("debug-panel-collapse", "is_open"),
            Input("refresh-sessions-button", "n_clicks"),
        ],
        [State("storage-location-store", "data")],
    )
    def update_debug_info(
        is_open: bool, refresh_clicks: int | None, custom_path: str | None
    ) -> Any:
        """
        Generate debug information display.

        Shows detailed information about storage, sessions, and configuration.
        """
        if not is_open:
            return html.Div()

        from pathlib import Path

        try:
            # Determine database path
            if custom_path:
                db_path = Path(custom_path) / "robomage.db"
                file_store_path = Path(custom_path) / "files"
            else:
                from robomage.persistence.database import DEFAULT_DB_PATH
                from robomage.persistence.file_store import DEFAULT_STORE_PATH

                db_path = DEFAULT_DB_PATH
                file_store_path = DEFAULT_STORE_PATH

            # Create session manager
            mgr = SessionManager(db_path=db_path) if custom_path else SessionManager()

            # Get all sessions
            sessions = mgr.list_sessions()

            # Collect debug information
            debug_sections = []

            # 1. Storage Configuration
            debug_sections.append(
                html.Div(
                    [
                        html.H6("Storage Configuration", className="fw-bold mb-2"),
                        html.Pre(
                            f"Database: {db_path}\n"
                            f"Files: {file_store_path}\n"
                            f"Database exists: {db_path.exists()}\n"
                            f"File store exists: {file_store_path.exists()}",
                            className="bg-light p-2 rounded",
                        ),
                    ],
                    className="mb-3",
                )
            )

            # 2. Session Summary
            total_files = sum(len(s.files) for s in sessions)
            debug_sections.append(
                html.Div(
                    [
                        html.H6("Session Summary", className="fw-bold mb-2"),
                        html.Pre(
                            f"Total sessions: {len(sessions)}\n"
                            f"Total files: {total_files}",
                            className="bg-light p-2 rounded",
                        ),
                    ],
                    className="mb-3",
                )
            )

            # 3. Detailed Session Info
            if sessions:
                session_details = []
                for s in sessions:
                    files_info = []
                    for f in s.files:
                        files_info.append(
                            f"    • {f.filename} "
                            f"({f.num_points} pts, {f.wavelength} Å)\n"
                            f"      Path: {f.stored_path}\n"
                            f"      Q range: [{f.q_min:.3f}, {f.q_max:.3f}]"
                        )

                    last_accessed_str = s.last_accessed.strftime("%Y-%m-%d %H:%M:%S")
                    session_details.append(
                        f"Session ID {s.id}: {s.name}\n"
                        f"  Description: {s.description or 'None'}\n"
                        f"  Created: {s.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"  Last accessed: {last_accessed_str}\n"
                        f"  Files ({len(s.files)}):\n" + "\n".join(files_info)
                    )

                debug_sections.append(
                    html.Div(
                        [
                            html.H6(
                                "Detailed Session Information",
                                className="fw-bold mb-2",
                            ),
                            html.Pre(
                                "\n\n".join(session_details),
                                className="bg-light p-2 rounded",
                                style={"maxHeight": "300px", "overflow": "auto"},
                            ),
                        ],
                        className="mb-3",
                    )
                )

            return html.Div(debug_sections)

        except Exception as e:
            return dbc.Alert(
                f"Error generating debug info: {str(e)}",
                color="danger",
            )

    @app.callback(
        Output("current-session-id", "data", allow_duplicate=True),
        Output("session-status", "children", allow_duplicate=True),
        Output("session-status", "className", allow_duplicate=True),
        Output("file-data-store", "data", allow_duplicate=True),
        Output("wavelength-store", "data", allow_duplicate=True),
        Output("analysis-results-store", "data", allow_duplicate=True),
        Input("init-interval", "n_intervals"),
        prevent_initial_call="initial_duplicate",  # Special mode for allow_duplicate on initial load
    )
    def auto_create_default_session(
        n_intervals: int | None,
    ) -> tuple[int | None, str, str, dict, dict, dict]:
        """
        Auto-create a default session when the dashboard loads and update status display.

        This ensures users always have an active session for workflow execution
        without needing to manually create one first.

        Also loads any existing files from the session into the UI stores.

        Triggered by init-interval which fires once on page load.

        Returns:
            Tuple of (session_id, status_text, css_class, file_data, wavelength_data, analysis_results)
        """
        print(
            f"🔍 DEBUG: auto_create_default_session called with n_intervals={n_intervals}"
        )
        try:
            mgr = SessionManager()

            # Check if a default session already exists
            all_sessions = mgr.list_sessions()
            print(f"🔍 DEBUG: Found {len(all_sessions)} total sessions")
            default_sessions = [
                s for s in all_sessions if s.name.startswith("Default Session")
            ]
            print(f"🔍 DEBUG: Found {len(default_sessions)} default sessions")

            if default_sessions:
                # Use the most recent default session
                default_session = max(default_sessions, key=lambda s: s.created_at)
                session_id = default_session.id
                file_count = len(default_session.files)
                status_text = f"{default_session.name} ({file_count} file{'s' if file_count != 1 else ''})"
                print(
                    f"🔍 DEBUG: Using existing session: {status_text}, ID={session_id}"
                )

                # Load files and analysis results from existing session (Sprint 7)
                file_data, wavelength_data, analysis_results = _load_session_files(
                    mgr, session_id
                )
                print(f"🔍 DEBUG: Loaded {len(file_data)} files from session")
                print(
                    f"🔍 DEBUG: Loaded {len(analysis_results)} analysis results from session"
                )

                return (
                    session_id,
                    status_text,
                    "text-success",
                    file_data,
                    wavelength_data,
                    analysis_results,
                )

            # Create a new default session
            from datetime import datetime

            session_name = f"Default Session {datetime.now().strftime('%Y-%m-%d')}"

            session_id = mgr.create_session(
                name=session_name,
                description="Auto-created default session for dashboard workflows",
            )

            # New session has 0 files
            status_text = f"{session_name} (0 files)"
            print(f"🔍 DEBUG: Created new session: {status_text}, ID={session_id}")

            # Empty session - no files to load
            return (
                session_id,
                status_text,
                "text-success",
                {},
                {"current_wavelength": 0.1665, "source_type": "standard"},
                {},
            )

        except Exception as e:
            # Log error but don't crash - user can still create manual sessions
            print(f"❌ ERROR in auto_create_default_session: {e}")
            import traceback

            traceback.print_exc()
            return (
                None,
                "No active session",
                "text-warning",
                {},
                {"current_wavelength": 0.1665, "source_type": "standard"},
                {},
            )

    @app.callback(
        Output("session-status", "children"),
        Output("session-status", "className"),
        Input("current-session-id", "data"),
        prevent_initial_call=True,  # Don't run on initial load (auto-create handles that)
    )
    def update_session_status_display(session_id: int | None) -> tuple[str, str]:
        """
        Update the session status display when session changes.

        This handles updates after save/load operations.
        The initial display is handled by auto_create_default_session.

        Args:
            session_id: Current active session ID

        Returns:
            Tuple of (status_text, css_class)
        """
        if session_id is None:
            return "No active session", "text-warning"

        try:
            mgr = SessionManager()
            session = mgr.get_session(session_id)

            if session:
                file_count = len(session.files)
                status_text = f"{session.name} ({file_count} file{'s' if file_count != 1 else ''})"
                return status_text, "text-success"
            else:
                return "Session not found", "text-danger"

        except Exception as e:
            return f"Error: {str(e)}", "text-danger"

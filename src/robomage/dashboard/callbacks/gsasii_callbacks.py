"""
GSAS-II Refinement Tab Callbacks

Interactive callbacks for the GSAS-II refinement interface.
Handles file upload, service communication, and results display.

CRITICAL: GSAS-II Data Format Requirements
===========================================
Synchrotron CHI files are in Q-space (Å⁻¹), but GSAS-II requires them to be
labeled as "two_theta" in the API. The instrument parameter file (e.g., PDF_1m.instprm)
handles the coordinate system conversion internally.

RULES:
1. Read Q values from CHI file (first column, typically 0.5-16 Å⁻¹)
2. Send Q values directly as "two_theta" in diffraction_data
3. DO NOT perform manual Q→2θ conversion before sending to service
4. GSAS-II will use the instrument file to interpret the coordinate system

Example:
  ✅ CORRECT:
    diffraction_data = {
        "two_theta": [0.647, 0.651, ...],  # Q values from CHI file
        "intensity": [30.6, 29.8, ...]
    }

  ❌ WRONG:
    two_theta = 2 * np.degrees(np.arcsin(q * λ / (4π)))  # Manual conversion
    diffraction_data = {
        "two_theta": two_theta.tolist(),  # This causes refinement failure!
        "intensity": [...]
    }

Failure symptoms when data is incorrectly converted:
  - "Invalid cell metric tensor" error
  - Negative cell values (e.g., -22248 Å)
  - Rwp = 0.0% (no actual refinement, calculation-only mode)
  - GSAS-II cycles fail immediately on Cycle 0

Successful refinement indicators:
  - Multiple cycles complete (Cycle 0, 1, 2, ...)
  - Rwp ≈ 7-8% for LaB6 standard
  - Cell parameter a ≈ 4.157 Å with non-zero ESDs
  - Chi² and GoF values are non-null
"""

import base64
import json
import traceback
from datetime import datetime
from typing import Any

import dash_bootstrap_components as dbc
import numpy as np
import requests
from dash import Input, Output, State, callback, html
from dash.exceptions import PreventUpdate

from robomage.clients.gsasii_client import GSASIIClient, GSASIIServiceError


def register_callbacks(app):
    """Register all GSAS-II tab callbacks."""

    @callback(
        Output("gsasii-service-status-badge", "children"),
        Output("gsasii-service-status-badge", "color"),
        Output("gsasii-service-status-text", "children"),
        Output("gsasii-service-alert", "color"),
        Input("gsasii-health-interval", "n_intervals"),
        Input("gsasii-health-check-btn", "n_clicks"),
    )
    def update_service_status(n_intervals, n_clicks):
        """Check GSAS-II service health and update status indicators."""
        try:
            client = GSASIIClient("http://localhost:8003")
            health = client.health_check()

            if health.get("status") == "healthy":
                badge_children = [
                    html.I(className="fas fa-check-circle me-1"),
                    "Connected",
                ]
                badge_color = "success"
                status_text = f"Service running on port 8003 • GSAS-II {health.get('gsas_ii_version', 'available')}"
                alert_color = "success"
            else:
                badge_children = [
                    html.I(className="fas fa-exclamation-triangle me-1"),
                    "Degraded",
                ]
                badge_color = "warning"
                status_text = "Service responding but may have issues"
                alert_color = "warning"

        except Exception:
            badge_children = [
                html.I(className="fas fa-times-circle me-1"),
                "Not Connected",
            ]
            badge_color = "danger"
            status_text = "Service unavailable • Start with: pixi run start-all"
            alert_color = "danger"

        return badge_children, badge_color, status_text, alert_color

    @callback(
        Output("gsasii-chi-upload-status", "children"),
        Output("gsasii-chi-data-store", "data"),
        Input("gsasii-chi-upload", "contents"),
        State("gsasii-chi-upload", "filename"),
    )
    def handle_chi_upload(contents, filename):
        """Handle CHI/XY file upload and parse data."""
        if contents is None:
            raise PreventUpdate

        try:
            # Decode file contents
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            text_data = decoded.decode("utf-8")

            # Parse data (simple two-column format)
            lines = [line.strip() for line in text_data.split("\n") if line.strip()]
            data_lines = [line for line in lines if not line.startswith("#")]

            q_values = []
            intensities = []
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        q_values.append(float(parts[0]))
                        intensities.append(float(parts[1]))
                    except ValueError:
                        continue

            if len(q_values) == 0:
                return (
                    dbc.Alert(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Failed to parse file - no valid data found",
                        ],
                        color="danger",
                    ),
                    None,
                )

            # Store data
            data = {
                "filename": filename,
                "q_values": q_values,
                "intensities": intensities,
            }

            status = dbc.Alert(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    f"Loaded {filename}: {len(q_values)} data points",
                ],
                color="success",
            )

            return status, data

        except Exception as e:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"Error loading file: {str(e)}",
                    ],
                    color="danger",
                ),
                None,
            )

    @callback(
        Output("gsasii-results-container", "children"),
        Output("gsasii-refinement-result-store", "data"),
        Output("gsasii-send-to-viz-button", "disabled"),
        Output("gsasii-download-gpx-btn", "disabled"),
        Output("gsasii-download-plot-btn", "disabled"),
        Output("gsasii-progress", "children"),
        Output("gsasii-debug-request-store", "data"),
        Output("gsasii-debug-response-store", "data"),
        Input("gsasii-run-btn", "n_clicks"),
        State("gsasii-chi-data-store", "data"),
        State("gsasii-cif-select", "value"),
        State("gsasii-inst-select", "value"),
        State("gsasii-phase-name", "value"),
        State("gsasii-cycles-slider", "value"),
        State("gsasii-refine-flags", "value"),
        State("gsasii-q-min", "value"),
        State("gsasii-q-max", "value"),
        prevent_initial_call=True,
    )
    def run_refinement(
        n_clicks,
        chi_data,
        cif_file,
        inst_file,
        phase_name,
        cycles,
        refine_flags,
        q_min,
        q_max,
    ):
        """Run GSAS-II refinement and display results."""
        if not n_clicks:
            raise PreventUpdate

        # Initialize debug data
        request_payload = None
        response_data = None

        # Validate inputs
        if chi_data is None:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Please upload a diffraction data file first",
                    ],
                    color="warning",
                ),
                None,
                True,
                True,
                True,
                "",
                None,
                None,
            )

        try:
            # Build recipe
            refine_flags = refine_flags or []
            recipe = {
                "instrument_file": inst_file,
                "cif_file": cif_file,
                "phase_name": phase_name or "Phase1",
                "refinement_dict": {
                    "set": {
                        "Limits": [q_min or 0.5, q_max or 16.0],
                        "Background": {
                            "no. coeffs": 6,
                            "refine": "background" in refine_flags,
                        },
                        "Cell": "cell" in refine_flags,
                    },
                    "do": "refine",
                },
            }

            # Add size/strain if requested
            if "size_strain" in refine_flags:
                recipe["refinement_dict"]["set"]["Size"] = True
                recipe["refinement_dict"]["set"]["Mustrain"] = {
                    "type": "isotropic",
                    "refine": True,
                }

            # Call service
            client = GSASIIClient("http://localhost:8003")

            # IMPORTANT: CHI files are in Q-space, but we send them as "two_theta" to GSAS-II
            # The instrument parameter file handles the coordinate system conversion internally
            # Do NOT convert Q to 2θ here - GSAS-II expects Q values labeled as "two_theta"
            q_array = np.array(chi_data["q_values"])

            # Build request matching service API schema
            request_payload = {
                "diffraction_data": {
                    "two_theta": q_array.tolist(),  # Send Q values as "two_theta" - GSAS-II converts internally
                    "intensity": chi_data["intensities"],
                },
                "recipe": recipe,
                "sample_name": phase_name or "Sample",
                "cycles": cycles or 5,
            }

            # Make direct API call
            response = client.session.post(
                f"{client.base_url}/refine",
                json=request_payload,
                timeout=client.timeout,
            )
            response.raise_for_status()
            result = response.json()
            response_data = result

            # Parse and display results
            results_display = create_results_display(result)

            return (
                results_display,
                result,
                False,
                False,
                False,
                "",
                request_payload,
                response_data,
            )

        except GSASIIServiceError as e:
            error_display = dbc.Alert(
                [
                    html.H5(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Refinement Failed",
                        ],
                        className="alert-heading",
                    ),
                    html.Hr(),
                    html.P(f"Error Type: {e.error_type}"),
                    html.P(f"Message: {e.message}"),
                    html.Details(
                        [
                            html.Summary("Technical Details", className="fw-bold"),
                            html.Pre(e.details or "No additional details"),
                        ],
                        className="mt-2",
                    ),
                ],
                color="danger",
            )
            return (
                error_display,
                None,
                True,
                True,
                True,
                "",
                request_payload,
                {"error": str(e)},
            )

        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors with response body
            error_msg = str(e)
            details = "No additional details"
            error_response = None
            try:
                if e.response is not None:
                    error_data = e.response.json()
                    error_response = error_data
                    if "detail" in error_data:
                        details = json.dumps(error_data["detail"], indent=2)
                    else:
                        details = json.dumps(error_data, indent=2)
            except Exception:
                pass

            error_display = dbc.Alert(
                [
                    html.H5(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Refinement Failed",
                        ],
                        className="alert-heading",
                    ),
                    html.Hr(),
                    html.P(f"HTTP Error: {error_msg}"),
                    html.Details(
                        [
                            html.Summary("Technical Details", className="fw-bold"),
                            html.Pre(details),
                        ],
                        className="mt-2",
                    ),
                ],
                color="danger",
            )
            return (
                error_display,
                None,
                True,
                True,
                True,
                "",
                request_payload,
                error_response,
            )

        except Exception as e:
            error_display = dbc.Alert(
                [
                    html.H5(
                        [
                            html.I(className="fas fa-bug me-2"),
                            "Unexpected Error",
                        ],
                        className="alert-heading",
                    ),
                    html.Hr(),
                    html.P(str(e)),
                    html.Details(
                        [
                            html.Summary("Stack Trace", className="fw-bold"),
                            html.Pre(traceback.format_exc()),
                        ],
                        className="mt-2",
                    ),
                ],
                color="danger",
            )
            return (
                error_display,
                None,
                True,
                True,
                True,
                "",
                request_payload,
                {"error": str(e), "traceback": traceback.format_exc()},
            )

    @callback(
        Output("gsasii-debug-collapse", "is_open"),
        Input("gsasii-toggle-debug-btn", "n_clicks"),
        State("gsasii-debug-collapse", "is_open"),
        prevent_initial_call=True,
    )
    def toggle_debug_panel(n_clicks, is_open):
        """Toggle debug panel visibility."""
        if n_clicks:
            return not is_open
        return is_open

    @callback(
        Output("file-data-store", "data", allow_duplicate=True),
        Output("gsasii-send-to-viz-button", "children"),
        Output("gsasii-send-to-viz-button", "color"),
        Input("gsasii-send-to-viz-button", "n_clicks"),
        State("gsasii-refinement-result-store", "data"),
        State("gsasii-chi-data-store", "data"),
        State("file-data-store", "data"),
        prevent_initial_call=True,
    )
    def send_gsasii_to_viz(n_clicks, refinement_result, chi_data, current_file_data):
        """
        Extract GSAS-II refinement results and add to file-data-store.

        This follows the same pattern as workflow results - adding calculated
        patterns as new "files" in file-data-store so they can be plotted
        alongside raw data.

        Args:
            n_clicks: Button click count
            refinement_result: GSAS-II refinement result dictionary
            chi_data: Original CHI file data
            current_file_data: Current files in file-data-store

        Returns:
            Tuple of (updated file_data, button content, button color)
        """
        if not n_clicks or not refinement_result:
            raise PreventUpdate

        try:
            # Extract data from refinement result
            fit_profile = refinement_result.get("fit_profile", {})
            
            # Get sample name from CHI data or refinement result
            base_name = (
                chi_data.get("filename", "GSAS-II Refinement")
                if chi_data
                else "GSAS-II Refinement"
            )
            
            # Create copy of current file data (or empty dict)
            updated_file_data = current_file_data.copy() if current_file_data else {}
            
            # Extract Q and intensity data
            # CRITICAL: GSAS-II worker returns "two_theta" (actually Q), "y_obs", "y_calc", "y_diff"
            q_values = fit_profile.get("two_theta", [])
            calc_intensity = fit_profile.get("y_calc", [])
            obs_intensity = fit_profile.get("y_obs", [])
            residual = fit_profile.get("y_diff", [])
            
            # Ensure all arrays are lists (not numpy arrays)
            if hasattr(q_values, 'tolist'):
                q_values = q_values.tolist()
            if hasattr(calc_intensity, 'tolist'):
                calc_intensity = calc_intensity.tolist()
            if hasattr(obs_intensity, 'tolist'):
                obs_intensity = obs_intensity.tolist()
            if hasattr(residual, 'tolist'):
                residual = residual.tolist()
            
            # Validate we have data
            if not q_values or not calc_intensity:
                print("Error: No data in GSAS-II fit_profile")
                raise PreventUpdate
            
            # Calculate metadata (must match file_upload.py structure)
            num_points = len(q_values)
            q_range = [min(q_values), max(q_values)]
            calc_range = [min(calc_intensity), max(calc_intensity)]
            obs_range = [min(obs_intensity), max(obs_intensity)]
            diff_range = [min(residual), max(residual)]
            
            # Get refinement metadata for context
            fit_quality = refinement_result.get("fit_quality", {})
            metadata = {
                "source": "GSAS-II Refinement",
                "Rwp": fit_quality.get("Rwp"),
                "chi2": fit_quality.get("chi2"),
            }
            
            # Add calculated pattern as a new file
            # CRITICAL: Must match file_upload.py structure exactly
            calc_filename = f"{base_name} (Calculated)"
            updated_file_data[calc_filename] = {
                "filename": calc_filename,
                "q": q_values,
                "intensity": calc_intensity,
                "metadata": metadata,
                "num_points": num_points,
                "q_range": q_range,
                "intensity_range": calc_range,
            }
            
            # Add observed pattern
            obs_filename = f"{base_name} (Observed)"
            updated_file_data[obs_filename] = {
                "filename": obs_filename,
                "q": q_values,
                "intensity": obs_intensity,
                "metadata": metadata,
                "num_points": num_points,
                "q_range": q_range,
                "intensity_range": obs_range,
            }
            
            # Add difference curve
            diff_filename = f"{base_name} (Difference)"
            updated_file_data[diff_filename] = {
                "filename": diff_filename,
                "q": q_values,
                "intensity": residual,
                "metadata": metadata,
                "num_points": num_points,
                "q_range": q_range,
                "intensity_range": diff_range,
            }

            # Return updated data and success feedback
            button_content = [
                html.I(className="fas fa-check me-1"),
                "Sent to Visualization!",
            ]
            button_color = "success"

            return updated_file_data, button_content, button_color

        except Exception as e:
            print(f"Error sending GSAS-II data to viz: {e}")
            traceback.print_exc()
            
            # Return error feedback
            button_content = [
                html.I(className="fas fa-exclamation-triangle me-1"),
                "Error - Check Console",
            ]
            button_color = "danger"
            
            raise PreventUpdate from None

    @callback(
        Output("gsasii-debug-request", "children"),
        Output("gsasii-debug-response", "children"),
        Output("gsasii-debug-summary", "children"),
        Input("gsasii-debug-request-store", "data"),
        Input("gsasii-debug-response-store", "data"),
    )
    def update_debug_display(request_data, response_data):
        """Update debug panel with request and response data."""
        # Format request
        if request_data:
            request_text = json.dumps(request_data, indent=2)
        else:
            request_text = "No request sent yet"

        # Format response
        if response_data:
            response_text = json.dumps(response_data, indent=2)
        else:
            response_text = "No response received yet"

        # Create summary
        if request_data and response_data:
            summary_items = []

            # Request summary
            summary_items.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.Strong("Request Summary")),
                        dbc.CardBody(
                            [
                                html.P(
                                    [
                                        html.Strong("Sample: "),
                                        request_data.get("sample_name", "N/A"),
                                    ]
                                ),
                                html.P(
                                    [
                                        html.Strong("Cycles: "),
                                        str(request_data.get("cycles", "N/A")),
                                    ]
                                ),
                                html.P(
                                    [
                                        html.Strong("Data Points: "),
                                        str(
                                            len(
                                                request_data.get(
                                                    "diffraction_data", {}
                                                ).get("intensity", [])
                                            )
                                        ),
                                    ]
                                ),
                                html.P(
                                    [
                                        html.Strong("CIF File: "),
                                        request_data.get("recipe", {}).get(
                                            "cif_file", "N/A"
                                        ),
                                    ]
                                ),
                                html.P(
                                    [
                                        html.Strong("Instrument: "),
                                        request_data.get("recipe", {}).get(
                                            "instrument_file", "N/A"
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ],
                    className="mb-3",
                )
            )

            # Response summary
            if "error" in response_data:
                summary_items.append(
                    dbc.Alert(
                        [
                            html.H5(
                                [
                                    html.I(
                                        className="fas fa-exclamation-triangle me-2"
                                    ),
                                    "Error",
                                ]
                            ),
                            html.P(response_data.get("error", "Unknown error")),
                        ],
                        color="danger",
                    )
                )
            else:
                summary_items.append(
                    dbc.Card(
                        [
                            dbc.CardHeader(html.Strong("Response Summary")),
                            dbc.CardBody(
                                [
                                    html.P(
                                        [
                                            html.Strong("Success: "),
                                            "✅ Yes"
                                            if response_data.get("success")
                                            else "❌ No",
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Rwp: "),
                                            f"{response_data.get('fit_quality', {}).get('Rwp', 'N/A')}%"
                                            if isinstance(
                                                response_data.get(
                                                    "fit_quality", {}
                                                ).get("Rwp"),
                                                (int, float),
                                            )
                                            else "N/A",
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Execution Time: "),
                                            f"{response_data.get('execution_time_s', 'N/A')} seconds"
                                            if response_data.get("execution_time_s")
                                            else "N/A",
                                        ]
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Warnings: "),
                                            str(len(response_data.get("warnings", []))),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        className="mb-3",
                    )
                )

            summary_content = html.Div(summary_items)
        else:
            summary_content = dbc.Alert(
                "Run a refinement to see debug info",
                color="info",
            )

        return request_text, response_text, summary_content


def create_results_display(result: dict[str, Any]) -> html.Div:
    """
    Create formatted results display from refinement result.

    Args:
        result: Refinement result dictionary from GSAS-II service

    Returns:
        HTML div with formatted results
    """
    components = []

    # Fit quality metrics
    if "fit_quality" in result:
        fit_quality = result["fit_quality"]
        components.append(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H6(
                            [html.I(className="fas fa-chart-line me-2"), "Fit Quality"]
                        )
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Strong("Rwp:"),
                                            html.Br(),
                                            html.H4(
                                                f"{fit_quality.get('Rwp', 'N/A'):.2f}%"
                                                if isinstance(
                                                    fit_quality.get("Rwp"), (int, float)
                                                )
                                                else "N/A",
                                                className="text-primary",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Strong("χ²:"),
                                            html.Br(),
                                            html.H4(
                                                f"{fit_quality.get('chi2', 'N/A'):.3f}"
                                                if isinstance(
                                                    fit_quality.get("chi2"),
                                                    (int, float),
                                                )
                                                else "N/A",
                                                className="text-info",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Strong("GoF:"),
                                            html.Br(),
                                            html.H4(
                                                f"{fit_quality.get('GoF', 'N/A'):.2f}"
                                                if isinstance(
                                                    fit_quality.get("GoF"), (int, float)
                                                )
                                                else "N/A",
                                                className="text-success",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            )
        )

    # Cell parameters
    if "cell" in result:
        cell = result["cell"]

        # Create table rows for cell parameters
        cell_rows = []
        for param in ["a", "b", "c", "alpha", "beta", "gamma"]:
            if param in cell:
                param_data = cell[param]
                if isinstance(param_data, dict):
                    value = param_data.get("value", "N/A")
                    esd = param_data.get("esd", 0)
                    cell_rows.append(
                        html.Tr(
                            [
                                html.Td(html.Strong(param), style={"width": "20%"}),
                                html.Td(
                                    f"{value:.6f}"
                                    if isinstance(value, (int, float))
                                    else str(value),
                                    style={"width": "40%"},
                                ),
                                html.Td(
                                    f"± {esd:.6f}"
                                    if isinstance(esd, (int, float)) and esd > 0
                                    else "—",
                                    className="text-muted",
                                    style={"width": "40%"},
                                ),
                            ]
                        )
                    )

        if cell_rows:
            components.append(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H6(
                                [
                                    html.I(className="fas fa-cube me-2"),
                                    "Cell Parameters",
                                ]
                            )
                        ),
                        dbc.CardBody(
                            [
                                html.Div(
                                    dbc.Table(
                                        [
                                            html.Thead(
                                                html.Tr(
                                                    [
                                                        html.Th("Parameter"),
                                                        html.Th("Value"),
                                                        html.Th("ESD"),
                                                    ]
                                                )
                                            ),
                                            html.Tbody(cell_rows),
                                        ],
                                        bordered=True,
                                        hover=True,
                                        size="sm",
                                    ),
                                    style={"maxHeight": "300px", "overflowY": "auto"},
                                ),
                            ]
                        ),
                    ],
                    className="mb-3",
                )
            )

    # Refinement plot
    if "plot_image" in result and result["plot_image"]:
        try:
            # Decode base64 image
            plot_img_src = f"data:image/png;base64,{result['plot_image']}"
            components.append(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H6(
                                [
                                    html.I(className="fas fa-chart-area me-2"),
                                    "Refinement Plot",
                                ]
                            )
                        ),
                        dbc.CardBody(
                            [
                                html.Img(
                                    src=plot_img_src,
                                    style={"width": "100%", "maxWidth": "1000px"},
                                )
                            ],
                            className="text-center",
                        ),
                    ],
                    className="mb-3",
                )
            )
        except Exception:
            pass

    # Metadata
    metadata_items = []
    if "execution_time_s" in result:
        metadata_items.append(
            html.Li(
                [
                    html.Strong("Execution Time: "),
                    f"{result['execution_time_s']:.2f} seconds",
                ]
            )
        )
    elif "execution_time" in result:
        metadata_items.append(
            html.Li(
                [
                    html.Strong("Execution Time: "),
                    f"{result['execution_time']:.2f} seconds",
                ]
            )
        )
    if "request_id" in result:
        metadata_items.append(
            html.Li(
                [
                    html.Strong("Request ID: "),
                    html.Code(result["request_id"]),
                ]
            )
        )
    if "filename" in result:
        metadata_items.append(
            html.Li(
                [
                    html.Strong("Data File: "),
                    result["filename"],
                ]
            )
        )
    if "warnings" in result and result["warnings"]:
        metadata_items.append(
            html.Li(
                [
                    html.Strong("Warnings: "),
                    html.Br(),
                    html.Ul([html.Li(w) for w in result["warnings"]]),
                ]
            )
        )

    if metadata_items:
        components.append(
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H6(
                            [html.I(className="fas fa-info-circle me-2"), "Metadata"]
                        )
                    ),
                    dbc.CardBody([html.Ul(metadata_items, className="mb-0")]),
                ],
                className="mb-3",
            )
        )

    return html.Div(components)

"""
Analysis Callbacks

Handles peak analysis service integration for the dashboard.
Provides real-time peak detection, parameter controls, and results visualization.
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import Input, Output, State, html

from robomage.clients.peak_analysis_client import (
    PeakAnalysisClient,
    PeakAnalysisServiceError,
)


def register_callbacks(app):
    """Register all analysis related callbacks."""
    register_service_health_callback(app)
    register_analysis_callback(app)
    register_service_status_update(app)


def register_service_health_callback(app):
    """Register callback to check service health status."""

    @app.callback(
        [
            Output("service-status-badge", "children"),
            Output("service-status-badge", "color"),
            Output("service-status", "children"),
            Output("service-status", "className"),
        ],
        [Input("main-tabs", "active_tab")],
        prevent_initial_call=False,
    )
    def check_service_health(active_tab):
        """
        Check if peak analysis service is available.

        Args:
            active_tab: Currently active tab ID

        Returns:
            Tuple of (badge content, badge color, status text, status class)
        """
        try:
            client = PeakAnalysisClient(timeout=2.0)
            health = client.health_check()

            if health.get("status") == "healthy":
                return (
                    [
                        html.I(className="fas fa-check-circle me-1"),
                        "Connected",
                    ],
                    "success",
                    "Connected",
                    "text-success",
                )
        except Exception:
            pass

        return (
            [
                html.I(className="fas fa-times-circle me-1"),
                "Not Connected",
            ],
            "warning",
            "Not Connected",
            "text-warning",
        )


def register_service_status_update(app):
    """Register callback to update service connection status periodically."""

    # Use interval component if needed for periodic updates
    # For now, status updates when switching tabs


def register_analysis_callback(app):
    """Register callback to perform peak analysis."""

    @app.callback(
        [
            Output("analysis-summary", "children"),
            Output("analysis-results-store", "data"),
        ],
        [Input("run-analysis-btn", "n_clicks")],
        [
            State("file-data-store", "data"),
            State("sensitivity-slider", "value"),
            State("profile-selector", "value"),
            State("min-prominence-input", "value"),
            State("min-distance-input", "value"),
        ],
        prevent_initial_call=True,
    )
    def run_peak_analysis(
        n_clicks, file_data, sensitivity, profile, min_prominence, min_distance
    ):
        """
        Execute peak analysis on loaded diffraction data.

        Args:
            n_clicks: Number of times button clicked
            file_data: Loaded diffraction data from store
            sensitivity: Peak detection sensitivity parameter
            profile: Peak profile type (gaussian, lorentzian, voigt)
            min_prominence: Minimum peak prominence
            min_distance: Minimum distance between peaks

        Returns:
            Tuple of (analysis summary UI, results data for store)
        """
        if not file_data:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "No data loaded. Please upload files in the Data Import tab.",
                    ],
                    color="warning",
                ),
                None,
            )

        try:
            # Initialize client
            client = PeakAnalysisClient()

            # Check service health first
            try:
                health = client.health_check()
                if health.get("status") != "healthy":
                    raise PeakAnalysisServiceError(
                        "service_unavailable", "Service is not healthy"
                    )
            except Exception as e:
                return (
                    dbc.Alert(
                        [
                            html.I(className="fas fa-exclamation-circle me-2"),
                            f"Cannot connect to peak analysis service: {str(e)}",
                            html.Br(),
                            html.Small(
                                "Make sure the service is running on port 8001",
                                className="text-muted",
                            ),
                        ],
                        color="danger",
                    ),
                    None,
                )

            # Analyze each loaded file
            results = {}
            for filename, data in file_data.items():
                try:
                    # Extract Q and intensity arrays
                    q_values = data.get("q_values", [])
                    intensities = data.get("intensities", [])

                    if not q_values or not intensities:
                        continue

                    # Build analysis configuration
                    config = {
                        "peak_detection": {
                            "min_prominence": min_prominence or 0.01,
                            "min_distance": min_distance or 0.1,
                        },
                        "peak_fitting": {
                            "profile_type": profile or "gaussian",
                            "fit_background": True,
                        },
                    }

                    # Call analysis service
                    response = client.analyze_peaks(
                        q_values=q_values,
                        intensities=intensities,
                        config=config,
                    )

                    # Store results
                    results[filename] = response

                except Exception as e:
                    print(f"Error analyzing {filename}: {e}")
                    continue

            if not results:
                return (
                    dbc.Alert(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Analysis failed for all files. Check data format.",
                        ],
                        color="warning",
                    ),
                    None,
                )

            # Create summary UI
            summary_ui = create_analysis_summary_ui(results)

            return summary_ui, results

        except PeakAnalysisServiceError as e:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        f"Analysis error: {e.message}",
                    ],
                    color="danger",
                ),
                None,
            )
        except Exception as e:
            return (
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        f"Unexpected error: {str(e)}",
                    ],
                    color="danger",
                ),
                None,
            )


def create_analysis_summary_ui(results: dict[str, Any]) -> html.Div:
    """
    Create UI component displaying analysis results summary.

    Args:
        results: Dictionary of analysis results by filename

    Returns:
        Dash HTML component with results summary
    """
    if not results:
        return html.P("No results available", className="text-muted")

    # Create summary cards for each file
    summary_cards = []

    for filename, result in results.items():
        peaks_detected = result.get("peaks_detected", 0)
        peak_list = result.get("peak_list", [])
        fit_quality = result.get("fit_quality", {})

        # Build peak table
        if peak_list:
            peak_rows = []
            for i, peak in enumerate(peak_list[:10], 1):  # Show first 10 peaks
                peak_rows.append(
                    html.Tr(
                        [
                            html.Td(str(i)),
                            html.Td(f"{peak.get('position', 0):.3f}"),
                            html.Td(f"{peak.get('d_spacing', 0):.3f}"),
                            html.Td(f"{peak.get('intensity', 0):.0f}"),
                            html.Td(f"{peak.get('fwhm', 0):.3f}"),
                        ]
                    )
                )

            peak_table = dbc.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("#"),
                                html.Th("Q (Å⁻¹)"),
                                html.Th("d (Å)"),
                                html.Th("Intensity"),
                                html.Th("FWHM"),
                            ]
                        )
                    ),
                    html.Tbody(peak_rows),
                ],
                bordered=True,
                hover=True,
                size="sm",
                className="mt-2",
            )
        else:
            peak_table = html.P("No peaks detected", className="text-muted")

        # Create summary card
        card = dbc.Card(
            [
                dbc.CardHeader(
                    html.H6(
                        [
                            html.I(className="fas fa-file me-2"),
                            filename,
                        ]
                    )
                ),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Strong("Peaks Detected: "),
                                        html.Span(
                                            str(peaks_detected),
                                            className="text-primary",
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        html.Strong("Fit Quality (R²): "),
                                        html.Span(
                                            f"{fit_quality.get('r_squared', 0):.3f}",
                                            className=(
                                                "text-success"
                                                if fit_quality.get("r_squared", 0) > 0.9
                                                else "text-warning"
                                            ),
                                        ),
                                    ],
                                    width=6,
                                ),
                            ],
                            className="mb-2",
                        ),
                        html.Hr(),
                        html.H6("Peak List:", className="mt-2"),
                        peak_table,
                    ]
                ),
            ],
            className="mb-3",
        )

        summary_cards.append(card)

    return html.Div(summary_cards)

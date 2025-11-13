"""
Plotting Callbacks

Handles interactive plotting and visualization for diffraction data.
Creates publication-quality plots with customizable styling.
"""

from typing import Any

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, html


def register_callbacks(app):
    """Register all plotting related callbacks."""
    register_main_plot_callback(app)
    register_plot_statistics_callback(app)
    register_peak_overlay_callback(app)


def register_main_plot_callback(app):
    """Register the main plot callback."""

    @app.callback(
        Output("main-plot", "figure"),
        [
            Input("file-data-store", "data"),
            Input("wavelength-store", "data"),
            Input("x-axis-selector", "value"),
            Input("y-axis-selector", "value"),
            Input("plot-type-selector", "value"),
            Input("analysis-results-store", "data"),
        ],
    )
    def update_main_plot(
        file_data, wavelength_data, x_axis, y_axis, plot_type, analysis_results
    ):
        """
        Update the main diffraction pattern plot with optional peak overlays.

        Args:
            file_data: Dictionary of loaded file data
            wavelength_data: Current wavelength settings
            x_axis: X-axis selection (q, two_theta, d_spacing)
            y_axis: Y-axis selection (raw, normalized, log)
            plot_type: Plot type (line, scatter, area)
            analysis_results: Peak analysis results from service

        Returns:
            Updated plotly figure
        """
        if not file_data:
            return create_empty_plot()

        # Create the plot
        fig = go.Figure()

        # Plot each loaded file
        colors = px.colors.qualitative.Set1
        for i, (filename, data) in enumerate(file_data.items()):
            color = colors[i % len(colors)]

            # Get x and y data
            x_data, x_label = get_x_data(data, x_axis, wavelength_data)
            y_data, y_label = get_y_data(data, y_axis)

            # Add trace based on plot type
            if plot_type == "line":
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="lines",
                        name=filename,
                        line=dict(color=color, width=2),
                        hovertemplate=f"<b>{filename}</b><br>"
                        + f"{x_label}: %{{x:.3f}}<br>"
                        + f"{y_label}: %{{y:.0f}}<extra></extra>",
                    )
                )
            elif plot_type == "scatter":
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="markers",
                        name=filename,
                        marker=dict(color=color, size=4),
                        hovertemplate=f"<b>{filename}</b><br>"
                        + f"{x_label}: %{{x:.3f}}<br>"
                        + f"{y_label}: %{{y:.0f}}<extra></extra>",
                    )
                )
            elif plot_type == "area":
                # Helper function to convert color to rgba with alpha
                def color_to_rgba(color_str, alpha=0.3):
                    """Convert color to rgba format with specified alpha."""
                    if color_str.startswith("#"):
                        # Hex color
                        rgb_tuple = px.colors.hex_to_rgb(color_str)
                        return (
                            f"rgba({rgb_tuple[0]}, {rgb_tuple[1]}, {rgb_tuple[2]}, "
                            f"{alpha})"
                        )
                    elif color_str.startswith("rgb("):
                        # RGB color - extract numbers and add alpha
                        rgb_values = color_str[4:-1]  # Remove 'rgb(' and ')'
                        return f"rgba({rgb_values}, {alpha})"
                    else:
                        # Fallback to a default color
                        return f"rgba(128, 128, 128, {alpha})"

                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="lines",
                        fill="tonexty" if i > 0 else "tozeroy",
                        name=filename,
                        line=dict(color=color, width=1),
                        fillcolor=color_to_rgba(color, 0.3),
                        hovertemplate=f"<b>{filename}</b><br>"
                        + f"{x_label}: %{{x:.3f}}<br>"
                        + f"{y_label}: %{{y:.0f}}<extra></extra>",
                    )
                )

        # Add peak annotations if analysis results available
        if analysis_results:
            for filename, result in analysis_results.items():
                if filename in file_data:
                    data = file_data[filename]
                    peak_list = result.get("peak_list", [])

                    for peak in peak_list:
                        # Get peak position in current x-axis units
                        peak_q = peak.get("position", 0)
                        peak_intensity = peak.get("intensity", 0)

                        # Convert to appropriate x-axis
                        if x_axis == "q":
                            peak_x = peak_q
                        elif x_axis == "two_theta":
                            if (
                                wavelength_data
                                and "current_wavelength" in wavelength_data
                            ):
                                wavelength = wavelength_data["current_wavelength"]
                            else:
                                wavelength = 0.1665
                            sin_theta = np.clip(
                                peak_q * wavelength / (4 * np.pi), -1.0, 1.0
                            )
                            peak_x = 2 * np.arcsin(sin_theta) * 180 / np.pi
                        elif x_axis == "d_spacing":
                            peak_x = 2 * np.pi / peak_q
                        else:
                            peak_x = peak_q

                        # Convert y-axis for peak position
                        if y_axis == "normalized":
                            intensity_data = np.array(data["intensity"])
                            min_val, max_val = (
                                intensity_data.min(),
                                intensity_data.max(),
                            )
                            if max_val > min_val:
                                peak_y = (peak_intensity - min_val) / (
                                    max_val - min_val
                                )
                            else:
                                peak_y = peak_intensity
                        else:
                            peak_y = peak_intensity

                        # Add peak marker
                        fig.add_trace(
                            go.Scatter(
                                x=[peak_x],
                                y=[peak_y],
                                mode="markers",
                                marker=dict(
                                    symbol="triangle-up",
                                    size=10,
                                    color="red",
                                    line=dict(width=1, color="darkred"),
                                ),
                                name=f"Peak {peak.get('d_spacing', 0):.2f}Å",
                                showlegend=False,
                                hovertemplate=(
                                    f"<b>Peak</b><br>"
                                    f"Q: {peak_q:.3f} Å⁻¹<br>"
                                    f"d: {peak.get('d_spacing', 0):.3f} Å<br>"
                                    f"Intensity: {peak_intensity:.0f}<br>"
                                    f"FWHM: {peak.get('fwhm', 0):.3f}<br>"
                                    "<extra></extra>"
                                ),
                            )
                        )

        # Update layout
        fig.update_layout(
            title={
                "text": "Powder Diffraction Pattern",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16},
            },
            xaxis=dict(
                title=x_label,
                showgrid=True,
                gridwidth=1,
                gridcolor="lightgray",
                showline=True,
                linewidth=1,
                linecolor="black",
                mirror=True,
            ),
            yaxis=dict(
                title=y_label,
                showgrid=True,
                gridwidth=1,
                gridcolor="lightgray",
                showline=True,
                linewidth=1,
                linecolor="black",
                mirror=True,
                type="log" if y_axis == "log" else "linear",
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font={"family": "Arial, sans-serif", "size": 12},
            hovermode="closest",
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="gray",
                borderwidth=1,
            ),
            margin=dict(l=60, r=20, t=60, b=60),
        )

        return fig


def get_x_data(
    data: dict[str, Any],
    x_axis: str,
    wavelength_data: dict[str, Any] | None = None,
) -> tuple[list[float], str]:
    """
    Get X-axis data and label.

    Args:
        data: File data dictionary
        x_axis: X-axis selection
        wavelength_data: Wavelength settings from store

    Returns:
        Tuple of (x_data, x_label)
    """
    q_data = np.array(data["q"])

    if x_axis == "q":
        return q_data.tolist(), "Q (Å⁻¹)"
    elif x_axis == "two_theta":
        # Get wavelength from store or use default
        if wavelength_data and "current_wavelength" in wavelength_data:
            wavelength = wavelength_data["current_wavelength"]
        else:
            wavelength = 0.1665  # Default to synchrotron as specified

        # Convert Q to 2θ using actual wavelength
        # Formula: Q = 4π sin(θ) / λ, so θ = arcsin(Q λ / 4π)
        sin_theta = q_data * wavelength / (4 * np.pi)

        # Clip values to valid range for arcsin to avoid warnings
        sin_theta = np.clip(sin_theta, -1.0, 1.0)

        two_theta = 2 * np.arcsin(sin_theta) * 180 / np.pi
        return two_theta.tolist(), "2θ (degrees)"
    elif x_axis == "d_spacing":
        # Convert Q to d-spacing: d = 2π/Q
        d_spacing = 2 * np.pi / q_data
        return d_spacing.tolist(), "d-spacing (Å)"
    else:
        return q_data.tolist(), "Q (Å⁻¹)"


def get_y_data(data: dict[str, Any], y_axis: str) -> tuple[list[float], str]:
    """
    Get Y-axis data and label.

    Args:
        data: File data dictionary
        y_axis: Y-axis selection

    Returns:
        Tuple of (y_data, y_label)
    """
    intensity_data = np.array(data["intensity"])

    if y_axis == "raw":
        return intensity_data.tolist(), "Intensity (counts)"
    elif y_axis == "normalized":
        # Normalize to 0-1 range
        min_val = intensity_data.min()
        max_val = intensity_data.max()
        if max_val > min_val:
            normalized = (intensity_data - min_val) / (max_val - min_val)
        else:
            normalized = intensity_data
        return normalized.tolist(), "Normalized Intensity"
    elif y_axis == "log":
        # Use raw data but plot will be log scale
        return intensity_data.tolist(), "Intensity (counts)"
    else:
        return intensity_data.tolist(), "Intensity (counts)"


def create_empty_plot() -> go.Figure:
    """
    Create an empty plot placeholder.

    Returns:
        Empty plotly figure
    """
    fig = go.Figure()

    fig.add_annotation(
        text="Upload diffraction data files to display patterns",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        xanchor="center",
        yanchor="middle",
        showarrow=False,
        font=dict(size=16, color="gray"),
    )

    fig.update_layout(
        title={
            "text": "Powder Diffraction Pattern",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16},
        },
        xaxis=dict(
            title="Q (Å⁻¹)",
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray",
            showline=True,
            linewidth=1,
            linecolor="black",
            mirror=True,
            range=[0, 10],
        ),
        yaxis=dict(
            title="Intensity (counts)",
            showgrid=True,
            gridwidth=1,
            gridcolor="lightgray",
            showline=True,
            linewidth=1,
            linecolor="black",
            mirror=True,
            range=[0, 1000],
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif", "size": 12},
        margin=dict(l=60, r=20, t=60, b=60),
    )

    return fig


def register_plot_statistics_callback(app):
    """Register plot statistics callback."""

    @app.callback(
        Output("plot-statistics", "children"),
        [Input("file-data-store", "data")],
    )
    def update_plot_statistics(file_data):
        """
        Update plot statistics display.

        Args:
            file_data: Dictionary of loaded file data

        Returns:
            Updated statistics components
        """
        if not file_data:
            return [html.P("Load data to view statistics", className="text-muted")]

        stats_items = []

        for filename, data in file_data.items():
            q_data = np.array(data["q"])
            intensity_data = np.array(data["intensity"])

            # Calculate statistics
            num_points = len(q_data)
            q_min, q_max = q_data.min(), q_data.max()
            intensity_min, intensity_max = intensity_data.min(), intensity_data.max()
            intensity_mean = intensity_data.mean()

            stats_items.extend(
                [
                    html.H6(filename, className="fw-bold text-primary"),
                    html.P(
                        [html.Strong("Points: "), f"{num_points:,}"],
                        className="mb-1",
                    ),
                    html.P(
                        [html.Strong("Q range: "), f"{q_min:.3f} - {q_max:.3f} Å⁻¹"],
                        className="mb-1",
                    ),
                    html.P(
                        [
                            html.Strong("Intensity: "),
                            f"{intensity_min:.0f} - {intensity_max:.0f} "
                            f"(avg: {intensity_mean:.0f})",
                        ],
                        className="mb-3",
                    ),
                ]
            )

        return stats_items


def register_peak_overlay_callback(app):
    """
    Register callback for toggling peak overlays on visualization.

    This is a placeholder for future peak display controls.
    Peak overlays are currently integrated into the main plot callback.
    """
    # Peak overlays are handled in register_main_plot_callback
    # This function is here for future enhancements like:
    # - Toggle peak visibility
    # - Peak labeling options
    # - Fitted curve display
    pass

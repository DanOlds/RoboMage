"""
Plotting Callbacks

Handles interactive plotting and visualization for diffraction data.
Creates publication-quality plots with customizable styling.
"""

from typing import Any

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output


def register_callbacks(app):
    """Register all plotting related callbacks."""

    @app.callback(
        Output("main-plot", "figure"),
        [
            Input("file-data-store", "data"),
            Input("x-axis-selector", "value"),
            Input("y-axis-selector", "value"),
            Input("plot-type-selector", "value"),
        ],
    )
    def update_main_plot(file_data, x_axis, y_axis, plot_type):
        """
        Update the main diffraction pattern plot.

        Args:
            file_data: Dictionary of loaded file data
            x_axis: X-axis selection (q, two_theta, d_spacing)
            y_axis: Y-axis selection (raw, normalized, log)
            plot_type: Plot type (line, scatter, area)

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
            x_data, x_label = get_x_data(data, x_axis)
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
                fig.add_trace(
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="lines",
                        fill="tonexty" if i > 0 else "tozeroy",
                        name=filename,
                        line=dict(color=color, width=1),
                        fillcolor=(
                            f"rgba{tuple(list(px.colors.hex_to_rgb(color)) + [0.3])}"
                        ),
                        hovertemplate=f"<b>{filename}</b><br>"
                        + f"{x_label}: %{{x:.3f}}<br>"
                        + f"{y_label}: %{{y:.0f}}<extra></extra>",
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


def get_x_data(data: dict[str, Any], x_axis: str) -> tuple[list[float], str]:
    """
    Get X-axis data and label.

    Args:
        data: File data dictionary
        x_axis: X-axis selection

    Returns:
        Tuple of (x_data, x_label)
    """
    q_data = np.array(data["q"])

    if x_axis == "q":
        return q_data.tolist(), "Q (Å⁻¹)"
    elif x_axis == "two_theta":
        # Convert Q to 2θ (assuming Cu Kα radiation, λ = 1.5406 Å)
        wavelength = 1.5406
        two_theta = 2 * np.arcsin(q_data * wavelength / (4 * np.pi)) * 180 / np.pi
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

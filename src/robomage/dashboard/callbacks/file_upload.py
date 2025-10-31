"""
File Upload Callbacks

Handles file upload, validation, and data loading for the dashboard.
Integrates with RoboMage data loaders for diffraction file support.
"""

import base64
import io
from typing import Any

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, html
from dash.dependencies import ALL
import dash


def register_callbacks(app):
    """Register all file upload related callbacks."""
    register_file_upload_callbacks(app)
    register_wavelength_callbacks(app)


def register_file_upload_callbacks(app):

    @app.callback(
        [
            Output("file-data-store", "data"),
            Output("file-list", "children"),
            Output("file-info", "children"),
            Output("status-text", "children"),
        ],
        [
            Input("upload-data", "contents"),
            Input({"type": "remove-file-btn", "filename": ALL}, "n_clicks"),
        ],
        [State("upload-data", "filename"), State("file-data-store", "data")],
        prevent_initial_call=True,
    )
    def handle_file_upload_and_remove(list_of_contents, remove_clicks, list_of_names, existing_data):
        ctx = dash.callback_context
        if not existing_data:
            existing_data = {}
        new_data = existing_data.copy()

        # Determine what triggered the callback
        if ctx.triggered:
            prop_id = ctx.triggered[0]["prop_id"]
            if prop_id.startswith('{') and 'remove-file-btn' in prop_id:
                # Find which button was clicked by comparing remove_clicks to previous state
                # The order of remove_clicks matches the order of files in new_data
                filenames = list(new_data.keys())
                for idx, n in enumerate(remove_clicks):
                    if n and n > 0 and idx < len(filenames):
                        filename_to_remove = filenames[idx]
                        if filename_to_remove in new_data:
                            del new_data[filename_to_remove]
                        break
            elif list_of_contents:
                for content, name in zip(list_of_contents, list_of_names, strict=False):
                    try:
                        file_data = parse_uploaded_file(content, name)
                        if file_data:
                            new_data[name] = file_data
                    except Exception as e:
                        print(f"Error processing file {name}: {e}")
                        continue
            else:
                from dash import no_update
                return no_update, no_update, no_update, no_update

        # Create updated UI components
        file_list = create_file_list(new_data)
        file_info = create_file_info(new_data)
        num_files = len(new_data)
        if num_files == 0:
            status = "No files loaded"
        elif num_files == 1:
            status = "Loaded 1 file"
        else:
            status = f"Loaded {num_files} files"
        return new_data, file_list, file_info, status


def parse_uploaded_file(content: str, filename: str) -> dict[str, Any] | None:
    """
    Parse an uploaded file and return data structure.

    Args:
        content: Base64 encoded file content
        filename: Original filename

    Returns:
        Dictionary with file data and metadata
    """
    try:
        # Decode the file content
        content_type, content_string = content.split(",")
        decoded = base64.b64decode(content_string)

        # Create a temporary file-like object
        file_obj = io.StringIO(decoded.decode("utf-8"))

        # Try to parse as diffraction data
        # First, let's try to read it as a simple two-column format
        lines = file_obj.getvalue().strip().split("\n")

        # Skip comment lines and parse data
        data_lines = []
        metadata = {"filename": filename, "comments": []}

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#") or line.startswith("!"):
                metadata["comments"].append(line)
                continue

            # Try to parse as numeric data
            try:
                parts = line.split()
                if len(parts) >= 2:
                    q = float(parts[0])
                    intensity = float(parts[1])
                    data_lines.append([q, intensity])
            except ValueError:
                continue

        if not data_lines:
            return None

        # Convert to arrays
        data_array = pd.DataFrame(data_lines, columns=["q", "intensity"])

        # Create data structure
        file_data = {
            "filename": filename,
            "q": data_array["q"].tolist(),
            "intensity": data_array["intensity"].tolist(),
            "metadata": metadata,
            "num_points": len(data_array),
            "q_range": [data_array["q"].min(), data_array["q"].max()],
            "intensity_range": [
                data_array["intensity"].min(),
                data_array["intensity"].max(),
            ],
        }

        return file_data

    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return None


def create_file_list(data: dict[str, Any]) -> list:
    """
    Create the file list component.

    Args:
        data: Dictionary of loaded file data

    Returns:
        List of file list components
    """
    if not data:
        return [html.P("No files loaded", className="text-muted small")]

    file_items = []
    for filename, file_data in data.items():
        file_items.append(
            dbc.ListGroupItem(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Strong(filename, className="small"),
                                    html.Br(),
                                    html.Small(
                                        f"{file_data['num_points']} points",
                                        className="text-muted",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-times"),
                                        size="sm",
                                        color="outline-danger",
                                        id={
                                            "type": "remove-file-btn",
                                            "filename": filename,
                                        },
                                        n_clicks=0,
                                        title="Remove file",
                                    )
                                ],
                                width=4,
                                className=(
                                    "d-flex align-items-center "
                                    "justify-content-end"
                                ),
                            ),
                        ]
                    )
                ],
                id={"type": "file-item", "filename": filename},
            )
        )

    return [dbc.ListGroup(file_items, flush=True)]


def create_file_info(data: dict[str, Any]) -> list:
    """
    Create the file information component.

    Args:
        data: Dictionary of loaded file data

    Returns:
        List of file info components
    """
    if not data:
        return [html.P("Select a file to view details", className="text-muted small")]

    # For now, show info for the first file
    if data:
        filename = list(data.keys())[0]
        file_data = data[filename]

        info_items = [
            html.H6("Current File", className="small fw-bold"),
            html.P(filename, className="small"),
            html.H6("Data Points", className="small fw-bold"),
            html.P(f"{file_data['num_points']:,}", className="small"),
            html.H6("Q Range (Å⁻¹)", className="small fw-bold"),
            html.P(
                f"{file_data['q_range'][0]:.3f} - {file_data['q_range'][1]:.3f}",
                className="small",
            ),
            html.H6("Intensity Range", className="small fw-bold"),
            html.P(
                (
                    f"{file_data['intensity_range'][0]:.0f} - "
                    f"{file_data['intensity_range'][1]:.0f}"
                ),
                className="small",
            ),
        ]

        return info_items

    return [html.P("No file information available", className="text-muted small")]


def register_wavelength_callbacks(app):
    """Register wavelength management callbacks."""
    
    @app.callback(
        [
            Output("custom-wavelength-div", "style"),
            Output("wavelength-store", "data"),
            Output("current-wavelength-display", "children"),
        ],
        [
            Input("wavelength-selector", "value"),
            Input("custom-wavelength-input", "value"),
        ],
    )
    def handle_wavelength_selection(selected_wavelength, custom_value):
        """
        Handle wavelength selection and custom input.
        
        Args:
            selected_wavelength: Selected wavelength from dropdown
            custom_value: Custom wavelength input value
            
        Returns:
            Custom input visibility, wavelength data, display text
        """
        # Show/hide custom input
        if selected_wavelength == "custom":
            custom_style = {"display": "block"}
            if custom_value and custom_value > 0:
                wavelength = custom_value
                display_text = f"{wavelength:.4f} Å (custom)"
            else:
                wavelength = 0.1665  # Default fallback
                display_text = "0.1665 Å (enter custom value)"
        else:
            custom_style = {"display": "none"}
            wavelength = selected_wavelength
            
            # Format display text with source name
            source_names = {
                0.1665: "0.1665 Å (synchrotron)",
                1.5406: "1.5406 Å (Cu Kα)",
                0.7107: "0.7107 Å (Mo Kα)", 
                2.2897: "2.2897 Å (Cr Kα)",
            }
            display_text = source_names.get(wavelength, f"{wavelength:.4f} Å")
        
        # Store wavelength data
        wavelength_data = {
            "current_wavelength": wavelength,
            "source_type": "custom" if selected_wavelength == "custom" else "standard",
        }
        
        return custom_style, wavelength_data, display_text

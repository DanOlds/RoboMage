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


def register_callbacks(app):
    """Register all file upload related callbacks."""

    @app.callback(
        [
            Output("file-data-store", "data"),
            Output("file-list", "children"),
            Output("file-info", "children"),
            Output("status-text", "children"),
        ],
        [Input("upload-data", "contents")],
        [State("upload-data", "filename"), State("file-data-store", "data")],
    )
    def handle_file_upload(list_of_contents, list_of_names, existing_data):
        """
        Handle file upload and update file list and data store.

        Args:
            list_of_contents: List of file contents (base64 encoded)
            list_of_names: List of filenames
            existing_data: Previously loaded data

        Returns:
            Updated data store, file list, file info, and status
        """
        if not list_of_contents:
            # No new files uploaded
            if existing_data:
                return (
                    existing_data,
                    create_file_list(existing_data),
                    create_file_info(existing_data),
                    "Dashboard Ready",
                )
            else:
                return (
                    {},
                    [html.P("No files loaded", className="text-muted small")],
                    [
                        html.P(
                            "Select a file to view details",
                            className="text-muted small",
                        )
                    ],
                    "Dashboard Ready",
                )

        # Initialize data store if needed
        if not existing_data:
            existing_data = {}

        new_data = existing_data.copy()

        # Process each uploaded file
        for content, name in zip(list_of_contents, list_of_names, strict=False):
            try:
                # Parse the uploaded file
                file_data = parse_uploaded_file(content, name)
                if file_data:
                    new_data[name] = file_data

            except Exception as e:
                print(f"Error processing file {name}: {e}")
                continue

        # Create updated UI components
        file_list = create_file_list(new_data)
        file_info = create_file_info(new_data)

        num_files = len(new_data)
        if num_files == 1:
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
                                        html.I(className="fas fa-eye"),
                                        size="sm",
                                        color="outline-primary",
                                        id={
                                            "type": "view-file-btn",
                                            "filename": filename,
                                        },
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

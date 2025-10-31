"""
Main Dash Application for RoboMage Dashboard

Interactive visualization dashboard for powder diffraction analysis.
Supports standalone file loading and service integration for peak analysis.
"""


import os
import sys

import dash
import dash_bootstrap_components as dbc

from robomage.dashboard.callbacks import file_upload, plotting
from robomage.dashboard.layouts.main_layout import create_main_layout

# Add the project root to Python path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def create_app(debug: bool = False) -> dash.Dash:
    """
    Create and configure the main Dash application.

    Args:
        debug: Enable debug mode for development

    Returns:
        Configured Dash application
    """
    # Initialize Dash app with Bootstrap theme
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
        title="RoboMage Dashboard",
        update_title="Loading...",
        suppress_callback_exceptions=True,
    )

    # Set the layout
    app.layout = create_main_layout()

    # Register callbacks
    file_upload.register_callbacks(app)
    plotting.register_callbacks(app)

    return app


def run_dashboard(
    host: str = "127.0.0.1", port: int = 8050, debug: bool = False
) -> None:
    """
    Run the RoboMage dashboard server.

    Args:
        host: Host address to bind to
        port: Port to run on (default 8050)
        debug: Enable debug mode for development
    """
    app = create_app(debug=debug)

    print("🔬 RoboMage Dashboard starting...")
    print(f"📊 Access dashboard at: http://{host}:{port}")
    print(f"🔍 Debug mode: {'ON' if debug else 'OFF'}")

    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    # Command line interface for running the dashboard
    import argparse

    parser = argparse.ArgumentParser(description="RoboMage Visualization Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8050, help="Port number")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    run_dashboard(host=args.host, port=args.port, debug=args.debug)

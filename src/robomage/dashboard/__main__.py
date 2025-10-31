"""
RoboMage Dashboard Module Entry Point

Run the dashboard with: python -m robomage.dashboard
"""

from robomage.dashboard.app import run_dashboard

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RoboMage Visualization Dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8050, help="Port number")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    run_dashboard(host=args.host, port=args.port, debug=args.debug)

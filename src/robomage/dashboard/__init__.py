"""
RoboMage Dashboard Package

Dash-based visualization dashboard for interactive powder diffraction analysis.
Integrates with RoboMage microservices for real-time peak analysis and
publication-quality plotting.

Main Components:
- app: Main Dash application
- layouts: Dashboard page layouts
- callbacks: Interactive callback functions
- components: Reusable UI components
- utils: Dashboard utilities and styling

Usage:
    python -m robomage.dashboard
"""

from .app import create_app, run_dashboard

__all__ = ["create_app", "run_dashboard"]

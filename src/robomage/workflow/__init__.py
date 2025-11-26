"""
Workflow system for RoboMage.

Provides node types and handlers for building multi-step analysis pipelines.
"""

from .nodes import data_nodes, analysis_nodes, output_nodes

__all__ = ["data_nodes", "analysis_nodes", "output_nodes"]

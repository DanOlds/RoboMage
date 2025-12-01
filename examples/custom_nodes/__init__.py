"""
Custom Node Examples

This package contains example node implementations demonstrating
different complexity levels and patterns for RoboMage workflow development.

Examples:
    - template_node: Minimal "Hello World" example with extensive comments
    - background_subtraction_node: Medium complexity data processing
    - peak_width_analysis_node: Advanced scientific analysis with scipy

See README.md for integration and usage guide.
"""

__all__ = [
    "template_node_handler",
    "background_subtraction_handler",
    "peak_width_analysis_handler",
]

from .template_node import template_node_handler
from .background_subtraction_node import background_subtraction_handler
from .peak_width_analysis_node import peak_width_analysis_handler

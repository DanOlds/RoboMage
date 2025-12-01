"""
Template Node - Minimal Example

This is a minimal "Hello World" workflow node demonstrating the basic
structure and patterns for RoboMage node development.

Use this as a starting point for creating your own custom nodes.

Author: RoboMage Team
Date: December 1, 2025
"""

import logging
from typing import Any

# REQUIRED: Import ExecutionContext from orchestrator
from robomage.orchestrator import ExecutionContext

# OPTIONAL: Import if working with DiffractionData
from robomage.data.models import DiffractionData

# BEST PRACTICE: Create module-level logger
logger = logging.getLogger(__name__)


# ==============================================================================
# HANDLER FUNCTION
# ==============================================================================
#
# Node handlers are async functions with this exact signature:
#   async def handler(config, inputs, context) -> Any
#
# - config: dict with node configuration from workflow JSON
# - inputs: dict with outputs from upstream nodes (node_id -> data)
# - context: ExecutionContext for shared state and metadata
# - return: Any serializable data for downstream nodes
#
async def template_node_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext,
) -> list[dict[str, Any]]:
    """
    Template node demonstrating basic patterns.

    This node accepts a list of DiffractionData objects, applies a simple
    transformation (multiplication by a scale factor), and returns a
    structured result.

    Config Parameters:
        - scale_factor: float (multiplier for intensities, default: 1.0)
        - description: str (optional description to include in output)

    Inputs:
        - input: List[DiffractionData] (diffraction data to process)

    Outputs:
        List of dictionaries with processing results:
        [
            {
                "filename": str,
                "original_max": float,
                "scaled_max": float,
                "scale_factor": float,
                "description": str
            },
            ...
        ]

    Example Configuration:
        {
            "scale_factor": 2.0,
            "description": "Test scaling"
        }

    Raises:
        ValueError: If no input data provided or invalid configuration
    """

    # ==========================================================================
    # STEP 1: EXTRACT AND VALIDATE CONFIGURATION
    # ==========================================================================
    #
    # Use config.get(key, default) for optional parameters
    # Use config[key] for required parameters (raises KeyError if missing)
    #

    # Optional parameter with default
    scale_factor = config.get("scale_factor", 1.0)

    # Validate parameter value
    if scale_factor <= 0:
        raise ValueError(f"scale_factor must be positive, got {scale_factor}")

    # Optional string parameter
    description = config.get("description", "Template node processing")

    # Log configuration (helps with debugging)
    logger.info(
        f"Template node starting: scale_factor={scale_factor}, description='{description}'"
    )

    # ==========================================================================
    # STEP 2: EXTRACT AND VALIDATE INPUTS
    # ==========================================================================
    #
    # Inputs come from upstream nodes connected by workflow edges
    # Convention: use "input" as the key for primary data flow
    #

    # Get input data (returns empty list if key not present)
    input_files = inputs.get("input", [])

    # CRITICAL: Always validate that input is not empty
    if not input_files:
        raise ValueError("No input data provided to template node")

    # OPTIONAL: Validate input type
    if not isinstance(input_files, list):
        raise ValueError(f"Expected list input, got {type(input_files).__name__}")

    # OPTIONAL: Validate each item in list
    for i, file in enumerate(input_files):
        if not isinstance(file, DiffractionData):
            raise ValueError(
                f"Item {i} is not DiffractionData, got {type(file).__name__}"
            )

    logger.info(f"Processing {len(input_files)} files")

    # ==========================================================================
    # STEP 3: PROCESS DATA
    # ==========================================================================
    #
    # Implement your node's core logic here
    # Use try/except for error handling
    # Log progress for debugging
    #

    results = []
    errors = []

    for i, file in enumerate(input_files):
        try:
            # Log progress (helps track down issues)
            logger.debug(f"Processing file {i+1}/{len(input_files)}: {file.filename}")

            # Access DiffractionData fields
            original_intensities = file.intensities  # numpy array
            q_values = file.q_values  # numpy array
            filename = file.filename  # string

            # Perform simple transformation
            scaled_intensities = original_intensities * scale_factor

            # Calculate metrics
            original_max = float(original_intensities.max())
            scaled_max = float(scaled_intensities.max())

            # PATTERN: Return structured dictionaries rather than raw arrays
            # This makes results easier to use in downstream nodes and inspection
            result = {
                "filename": filename,
                "original_max": original_max,
                "scaled_max": scaled_max,
                "scale_factor": scale_factor,
                "description": description,
                "num_points": len(q_values),
            }

            results.append(result)

        except Exception as e:
            # BEST PRACTICE: Log errors but continue processing other files
            error_msg = f"File {i+1} ({file.filename}): {str(e)}"
            logger.warning(f"Failed to process file: {error_msg}")
            errors.append(error_msg)

    # ==========================================================================
    # STEP 4: VALIDATE RESULTS
    # ==========================================================================
    #
    # Check if any files were successfully processed
    # Provide detailed error information if all failed
    #

    if not results:
        # All files failed - construct helpful error message
        error_details = "\n  - ".join(errors) if errors else "Unknown error"
        raise ValueError(f"No files processed successfully.\nErrors:\n  - {error_details}")

    # ==========================================================================
    # STEP 5: LOG COMPLETION AND RETURN RESULTS
    # ==========================================================================

    logger.info(
        f"Template node complete: {len(results)} files processed, {len(errors)} failed"
    )

    # Return structured data for downstream nodes
    return results


# ==============================================================================
# ADVANCED EXAMPLE: Returning Modified DiffractionData
# ==============================================================================
#
# If your node needs to return modified DiffractionData objects
# (rather than analysis results), use this pattern:
#


async def template_transform_handler(
    config: dict[str, Any],
    inputs: dict[str, Any],
    context: ExecutionContext,
) -> list[DiffractionData]:
    """
    Alternative template showing how to return modified DiffractionData.

    Config Parameters:
        - scale_factor: float (multiplier, default: 1.0)

    Inputs:
        - input: List[DiffractionData]

    Outputs:
        List[DiffractionData] with scaled intensities
    """
    scale_factor = config.get("scale_factor", 1.0)
    input_files = inputs.get("input", [])

    if not input_files:
        raise ValueError("No input data provided")

    logger.info(f"Transforming {len(input_files)} files with scale={scale_factor}")

    transformed = []

    for file in input_files:
        # DiffractionData is immutable - create new instance
        new_data = DiffractionData(
            q_values=file.q_values,  # Keep original Q-values
            intensities=file.intensities * scale_factor,  # Scale intensities
            filename=file.filename,  # Preserve metadata
            sample_name=file.sample_name,  # Preserve metadata
        )
        transformed.append(new_data)

    logger.info(f"Transformation complete: {len(transformed)} files")

    return transformed


# ==============================================================================
# USAGE NOTES
# ==============================================================================
#
# 1. REGISTRATION:
#    Register your handler with the workflow orchestrator:
#
#    from my_nodes import template_node_handler
#    orchestrator.register_node_handler("template_node", template_node_handler)
#
#
# 2. WORKFLOW JSON:
#    Use your node in workflow definitions:
#
#    {
#      "nodes": [
#        {
#          "id": "process_1",
#          "type": "template_node",
#          "config": {
#            "scale_factor": 2.0,
#            "description": "Double intensities"
#          }
#        }
#      ]
#    }
#
#
# 3. TESTING:
#    Test your handler directly:
#
#    import pytest
#    from robomage.orchestrator import ExecutionContext
#
#    @pytest.mark.asyncio
#    async def test_template_node():
#        config = {"scale_factor": 2.0}
#        inputs = {"input": [test_data]}
#        context = ExecutionContext()
#
#        result = await template_node_handler(config, inputs, context)
#
#        assert len(result) == 1
#        assert result[0]["scale_factor"] == 2.0
#
# ==============================================================================

#!/usr/bin/env python
"""
GSAS-II Worker Script

Standalone refinement worker that runs in the GSAS-II pixi environment.
Reads input from JSON, performs GSAS-II refinement, writes output to JSON.

This script is spawned as a subprocess by the main GSAS-II service to enable
cross-environment operation (service in RoboMage env, refinement in GSAS-II env).

Usage:
    python gsasii_worker.py input.json output.json

Input JSON format:
    {
        "chi_file": "/path/to/data.chi",
        "recipe": {...},
        "sample_name": "sample1",
        "cycles": 5,
        "save_gpx": false,
        "generate_plot": true
    }

Output JSON format:
    {
        "cell": {...},
        "fit_quality": {...},
        "fit_profile": {...},
        "plot_image": "base64...",
        "convergence": "converged",
        "success": true
    }
"""

import json
import logging
import sys
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("gsasii_worker")


def read_input(input_path: Path) -> dict:
    """Read and parse input JSON."""
    logger.info(f"Reading input from {input_path}")
    with open(input_path) as f:
        data = json.load(f)
    logger.info(f"Input loaded: {list(data.keys())}")
    return data


def write_output(output_path: Path, data: dict) -> None:
    """Write output JSON."""
    logger.info(f"Writing output to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Output written: {output_path.stat().st_size} bytes")


def perform_refinement(input_data: dict) -> dict:
    """
    Perform GSAS-II refinement using the input parameters.
    
    This imports GSAS-II and runs the refinement in the current environment.
    """
    import base64
    import io
    import shutil
    import tempfile
    
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import yaml
    
    # Import GSAS-II (only available in GSAS-II environment)
    try:
        import sys
        sys.path.insert(0, '/nsls2/users/dolds/dev/GSAS-II/GSAS-II')
        from GSASII import GSASIIscriptable as G2
        logger.info("✓ GSAS-II imported successfully")
    except ImportError as e:
        raise ImportError(f"GSAS-II not available in this environment: {e}")
    
    def generate_fit_plot(hist, sample_name: str, temp_dir: Path) -> str:
        """Generate fit plot and return as base64."""
        logger.info("Generating fit plot...")
        
        x_data = hist.getdata('x')
        y_obs = hist.getdata('yobs')
        y_calc = hist.getdata('ycalc')
        y_bkg = hist.getdata('background')  # 'background' not 'ybackground'
        y_diff = y_obs - y_calc
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True,
                                         gridspec_kw={'height_ratios': [3, 1]})
        
        # Main plot
        ax1.plot(x_data, y_obs, 'ko', markersize=2, label='Observed')
        ax1.plot(x_data, y_calc, 'r-', linewidth=1, label='Calculated')
        ax1.plot(x_data, y_bkg, 'g--', linewidth=1, label='Background')
        ax1.set_ylabel('Intensity')
        ax1.legend()
        ax1.set_title(f'GSAS-II Refinement: {sample_name}')
        ax1.grid(True, alpha=0.3)
        
        # Difference plot
        ax2.plot(x_data, y_diff, 'b-', linewidth=1)
        ax2.axhline(y=0, color='k', linestyle='--', linewidth=0.5)
        ax2.set_xlabel('2θ (degrees)')
        ax2.set_ylabel('Obs - Calc')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        
        # Encode as base64
        img_data = base64.b64encode(buf.read()).decode('utf-8')
        logger.info(f"Generated plot: {len(img_data)} bytes (base64)")
        
        return img_data
    
    # Extract parameters
    chi_file = Path(input_data["chi_file"])
    recipe = input_data["recipe"]
    sample_name = input_data.get("sample_name", "sample")
    cycles = input_data.get("cycles", 5)
    save_gpx = input_data.get("save_gpx", False)
    generate_plot = input_data.get("generate_plot", True)
    
    logger.info(f"Starting refinement: {chi_file.name}")
    logger.info(f"Sample: {sample_name}, Cycles: {cycles}")
    
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix=f"gsasii_{sample_name}_"))
    logger.info(f"Temp directory: {temp_dir}")
    
    try:
        # Resolve recipe files
        instrument_file = resolve_recipe_file(recipe["instrument_file"], ".instprm", temp_dir)
        cif_file = resolve_recipe_file(recipe["cif_file"], ".cif", temp_dir)
        
        # Read recipe YAML if it's a file
        refinement_dict = recipe["refinement_dict"]
        if isinstance(refinement_dict, str):
            recipe_path = resolve_recipe_file(refinement_dict, ".yaml", temp_dir)
            with open(recipe_path) as f:
                refinement_dict = yaml.safe_load(f)
        
        phase_name = recipe["phase_name"]
        
        # Create GSAS-II project
        gpx_file = temp_dir / f"{sample_name}.gpx"
        project = G2.G2Project(newgpx=str(gpx_file))
        logger.info(f"Created project: {gpx_file}")
        
        # Add powder histogram
        hist = project.add_powder_histogram(
            str(chi_file),
            str(instrument_file),
            phases=[]
        )
        logger.info(f"Added histogram: {hist.name}")
        
        # Add phase from CIF
        phase = project.add_phase(
            str(cif_file),
            phasename=phase_name,
            histograms=[hist]
        )
        logger.info(f"Added phase: {phase.name}")
        
        # Apply refinement recipe
        apply_refinement_recipe(project, hist, phase, refinement_dict, cycles)
        
        # Perform refinement
        logger.info(f"Starting {cycles} refinement cycles...")
        project.do_refinements([refinement_dict])
        logger.info("✓ Refinement completed")
        
        # Extract results
        result = extract_results(project, hist, phase)
        
        # Generate plot if requested
        if generate_plot:
            plot_data = generate_fit_plot(hist, sample_name, temp_dir)
            result["plot_image"] = plot_data
        else:
            result["plot_image"] = None
        
        # Save GPX if requested
        if save_gpx:
            output_gpx = temp_dir / f"{sample_name}_refined.gpx"
            project.save(str(output_gpx))
            logger.info(f"Saved GPX: {output_gpx}")
            result["gpx_file"] = str(output_gpx)
        else:
            result["gpx_file"] = None
        
        result["success"] = True
        result["convergence"] = "converged"  # TODO: Check actual convergence
        
        return result
        
    finally:
        # Cleanup temp directory
        if not save_gpx:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temp directory")


def resolve_recipe_file(content: str, extension: str, temp_dir: Path) -> Path:
    """
    Resolve recipe file reference (filename or absolute path).
    
    Searches in:
    1. Absolute path (if given)
    2. Service assets directory
    3. GSAS-II pixi directory assets
    """
    # If it's an absolute path and exists, use it
    path = Path(content)
    if path.is_absolute() and path.exists():
        logger.info(f"Using absolute path: {path}")
        return path
    
    # Search in service assets
    service_assets = Path(__file__).parent / "assets"
    
    # Try different locations
    search_paths = [
        service_assets / "recipes" / content,
        service_assets / "cifs" / content,
        service_assets / "instruments" / content,
        service_assets / content,
    ]
    
    for search_path in search_paths:
        if search_path.exists():
            logger.info(f"Found file in assets: {search_path}")
            return search_path
    
    raise FileNotFoundError(f"Could not find recipe file: {content}")


def apply_refinement_recipe(project, hist, phase, recipe_dict: dict, cycles: int) -> None:
    """Apply refinement recipe settings to GSAS-II project."""
    logger.info("Applying refinement recipe...")
    
    # Set limits
    limits = recipe_dict.get("Limits", [0.5, 16.0])
    hist.set_refinements({"Limits": limits})
    logger.info(f"Set limits: {limits}")
    
    # Background refinement
    bg_config = recipe_dict.get("Background", {})
    if bg_config:
        hist.set_refinements({"Background": bg_config})
        logger.info(f"Background: {bg_config}")
    
    # Sample parameters
    sample_params = recipe_dict.get("Sample Parameters", [])
    if sample_params:
        hist.set_refinements({"Sample Parameters": sample_params})
        logger.info(f"Sample parameters: {sample_params}")
    
    # Phase parameters
    phase_config = recipe_dict.get("Phases", {}).get(phase.name, {})
    if phase_config:
        # Cell refinement
        if phase_config.get("Cell"):
            phase.set_refinements({"Cell": True})
            logger.info("Cell refinement enabled")
        
        # Size/strain
        if phase_config.get("Size"):
            phase.set_refinements({"Size": {"type": "isotropic", "refine": True}})
            logger.info("Size refinement enabled")
        
        mustrain = phase_config.get("Mustrain", {})
        if mustrain.get("refine"):
            phase.set_refinements({"Mustrain": mustrain})
            logger.info(f"Microstrain refinement enabled: {mustrain}")


def extract_results(project, hist, phase) -> dict:
    """Extract refinement results from GSAS-II project."""
    logger.info("Extracting results...")
    
    # Cell parameters - use get_cell() method
    cell_list, esd_list = phase.get_cell_and_esd()
    cell = {
        "a": {"value": cell_list.get('length_a', 0.0), "esd": esd_list.get('length_a', 0.0)},
        "b": {"value": cell_list.get('length_b', 0.0), "esd": esd_list.get('length_b', 0.0)},
        "c": {"value": cell_list.get('length_c', 0.0), "esd": esd_list.get('length_c', 0.0)},
        "alpha": {"value": cell_list.get('angle_alpha', 90.0), "esd": esd_list.get('angle_alpha', 0.0)},
        "beta": {"value": cell_list.get('angle_beta', 90.0), "esd": esd_list.get('angle_beta', 0.0)},
        "gamma": {"value": cell_list.get('angle_gamma', 90.0), "esd": esd_list.get('angle_gamma', 0.0)},
        "volume": {"value": cell_list.get('volume', 0.0), "esd": esd_list.get('volume', 0.0)},
    }
    logger.info(f"Cell a = {cell['a']['value']:.6f} Å")
    
    # Fit quality - use residuals property
    residuals = hist.residuals
    fit_quality = {
        "Rwp": residuals.get('wR', 0.0),
        "chi2": residuals.get('chi2', None),
        "GoF": residuals.get('GOF', None),
    }
    logger.info(f"Rwp = {fit_quality['Rwp']:.3f}%")
    
    # Fit profile - use getdata() method
    two_theta = hist.getdata('x')
    y_obs = hist.getdata('yobs')
    y_calc = hist.getdata('ycalc')
    y_bkg = hist.getdata('background')  # 'background' not 'ybackground'
    y_diff = y_obs - y_calc
    y_weights = hist.getdata('yweight')
    q_values = hist.getdata('q')
    d_spacings = hist.getdata('d')
    
    fit_profile = {
        "two_theta": two_theta.tolist() if hasattr(two_theta, 'tolist') else list(two_theta),
        "q_values": q_values.tolist() if hasattr(q_values, 'tolist') else list(q_values),
        "d_spacings": d_spacings.tolist() if hasattr(d_spacings, 'tolist') else list(d_spacings),
        "y_obs": y_obs.tolist() if hasattr(y_obs, 'tolist') else list(y_obs),
        "y_calc": y_calc.tolist() if hasattr(y_calc, 'tolist') else list(y_calc),
        "y_diff": y_diff.tolist() if hasattr(y_diff, 'tolist') else [],
        "y_bkg": y_bkg.tolist() if hasattr(y_bkg, 'tolist') else list(y_bkg),
        "y_weights": y_weights.tolist() if hasattr(y_weights, 'tolist') else list(y_weights),
    }
    
    # Collect all refined parameters
    parameters = {
        "cell": cell_list,
        "cell_esd": esd_list,
        "residuals": residuals,
    }
    
    return {
        "parameters": parameters,
        "cell": cell,
        "fit_quality": fit_quality,
        "fit_profile": fit_profile,
    }


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python gsasii_worker.py input.json output.json", file=sys.stderr)
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    
    try:
        # Read input
        input_data = read_input(input_path)
        
        # Perform refinement
        result = perform_refinement(input_data)
        
        # Write output
        write_output(output_path, result)
        
        logger.info("✓ Worker completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"✗ Worker failed: {e}")
        logger.error(traceback.format_exc())
        
        # Write error output
        error_output = {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
        write_output(output_path, error_output)
        sys.exit(1)


if __name__ == "__main__":
    main()

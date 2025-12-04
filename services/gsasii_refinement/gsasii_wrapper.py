"""GSAS-II Wrapper Module

Core refinement functionality using subprocess worker pattern.
Spawns gsasii_worker.py in GSAS-II environment for cross-env operation.

Architecture:
- Service runs in RoboMage environment (has FastAPI, etc.)
- Worker runs in GSAS-II environment (has GSAS-II installed)
- Communication via temp JSON files
- Process management with timeouts and cleanup

Key differences from autoxrd:
- Array input (not file paths)
- Dict output (not CSV/TXT files)
- Subprocess-based execution
- Cross-environment support
"""

import base64
import io
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import matplotlib
matplotlib.use('Agg')  # Headless backend for server use
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger("gsasii_wrapper")


# ============================================================================
# Configuration
# ============================================================================

# GSAS-II environment location
GSASII_ENV_PATH = Path("/nsls2/users/dolds/dev/GSAS-II/pixi")
GSASII_PYTHON = "pixi run python"  # Command to run Python in GSAS-II env

# Worker script location (same directory as this file)
WORKER_SCRIPT = Path(__file__).parent / "gsasii_worker.py"

# Subprocess timeout (seconds)
REFINEMENT_TIMEOUT = 300  # 5 minutes


# ============================================================================
# File Resolution (Paths + Base64)
# ============================================================================


def is_base64_content(s: str) -> bool:
    """
    Check if string is base64-encoded content vs a file path/name.
    
    Base64 indicators:
    - Starts with "data:" (data URI)
    - Very long string with no path separators
    - Contains padding characters '='
    """
    if s.startswith("data:"):
        return True
    
    # If it looks like a path, it's not base64
    if "/" in s or "\\" in s or s.endswith((".yaml", ".cif", ".CIF", ".instprm")):
        return False
    
    # If it's very long and has '=', likely base64
    if len(s) > 100 and "=" in s[-10:]:
        return True
    
    return False


def resolve_file(
    content: str,
    extension: str,
    temp_dir: Path,
    assets_dir: Optional[Path] = None
) -> Path:
    """
    Resolve file reference to an actual file path.
    
    Supports three modes:
    1. Base64-encoded content → decode to temp file
    2. Absolute path → use as-is
    3. Filename only → search in assets directory
    
    Args:
        content: File path, filename, or base64-encoded content
        extension: File extension (e.g., ".cif", ".instprm")
        temp_dir: Directory for temporary files
        assets_dir: Optional assets directory to search for files
        
    Returns:
        Path to the resolved file
        
    Raises:
        FileNotFoundError: If file cannot be found
        ValueError: If base64 decoding fails
    """
    # Mode 1: Base64-encoded content
    if is_base64_content(content):
        logger.info(f"Decoding base64 content to temp{extension}")
        
        # Strip data URI prefix if present
        if content.startswith("data:"):
            content = content.split(",", 1)[1]
        
        try:
            data = base64.b64decode(content)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 content: {e}")
        
        temp_file = temp_dir / f"temp{extension}"
        temp_file.write_bytes(data)
        logger.info(f"Wrote {len(data)} bytes to {temp_file}")
        return temp_file
    
    # Mode 2: Absolute path
    path = Path(content)
    if path.is_absolute():
        if not path.exists():
            raise FileNotFoundError(f"File not found: {content}")
        logger.info(f"Using absolute path: {path}")
        return path
    
    # Mode 3: Filename - search in assets directory
    if assets_dir is not None:
        # Try exact filename
        candidate = assets_dir / content
        if candidate.exists():
            logger.info(f"Found in assets: {candidate}")
            return candidate
        
        # Try adding extension if not present
        if not content.endswith(extension):
            candidate = assets_dir / (content + extension)
            if candidate.exists():
                logger.info(f"Found in assets with extension: {candidate}")
                return candidate
    
    # Last resort: treat as relative to current directory
    if path.exists():
        logger.info(f"Using relative path: {path}")
        return path
    
    raise FileNotFoundError(
        f"Could not resolve file: {content}\n"
        f"Searched: assets_dir={assets_dir}, cwd={Path.cwd()}"
    )


# ============================================================================
# Chi File I/O
# ============================================================================


def write_chi_file(path: Path, q: List[float], intensity: List[float]) -> None:
    """
    Write diffraction data to .chi format (two-column ASCII).
    
    Format:
        # Q(A^-1)  Intensity
        0.5000  100.0
        0.5100  105.2
        ...
    
    Args:
        path: Output file path
        q: Q values (Å⁻¹)
        intensity: Intensity values
    """
    logger.info(f"Writing {len(q)} points to {path}")
    
    with path.open('w') as f:
        f.write("# Q(A^-1)  Intensity\n")
        for q_val, i_val in zip(q, intensity):
            f.write(f"{q_val:.6f}  {i_val:.6f}\n")
    
    logger.info(f"Chi file written: {path.stat().st_size} bytes")


def read_chi_file(path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Read diffraction data from .chi file.
    
    Args:
        path: Path to .chi file
        
    Returns:
        Tuple of (x_values, intensity) arrays
    """
    data = np.loadtxt(path, comments="#")
    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError(f"Invalid .chi file format: {path}")
    
    return data[:, 0], data[:, 1]


# ============================================================================
# GSAS-II Refinement
# ============================================================================


def run_gsasii_refinement(
    chi_data: Tuple[List[float], List[float]],
    recipe: Dict[str, Any],
    sample_name: str,
    cycles: int = 5,
    temp_dir: Optional[Path] = None,
    save_gpx: bool = False,
    generate_plot: bool = True
) -> Dict[str, Any]:
    """
    Execute GSAS-II Rietveld refinement via subprocess worker.
    
    This function prepares input, spawns gsasii_worker.py in the GSAS-II
    environment, and collects results. Enables cross-environment operation
    without requiring GSAS-II in the current environment.
    
    Args:
        chi_data: Tuple of (q, intensity) arrays
        recipe: Refinement recipe dict with keys:
            - instrument_file: str (path, filename, or base64)
            - cif_file: str (path, filename, or base64)
            - phase_name: str
            - refinement_dict: dict (GSAS-II format)
        sample_name: Sample identifier for labeling
        cycles: Number of refinement cycles (0 = calculate only)
        temp_dir: Optional temporary directory (created if None)
        save_gpx: Whether to save GSAS-II project file
        generate_plot: Whether to generate fit plot
        
    Returns:
        Dict with keys:
            - cell: dict (unit cell with ESDs)
            - fit_quality: dict (Rwp, chi2, etc.)
            - fit_profile: dict (obs, calc, diff arrays)
            - plot_image: str (base64 PNG, if generate_plot=True)
            - gpx_file: str (if save_gpx=True)
            - convergence: str ("converged", "failed", etc.)
            - success: bool
            
    Raises:
        FileNotFoundError: If worker script or GSAS-II env not found
        subprocess.TimeoutExpired: If refinement exceeds timeout
        RuntimeError: If worker process fails
    """
    # Create temp directory if needed
    temp_dir_created = temp_dir is None
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="gsasii_"))
        logger.info(f"Created temp directory: {temp_dir}")
    else:
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # ====================================================================
        # 1. Prepare Input Files
        # ====================================================================
        
        logger.info(f"Starting refinement: sample={sample_name}, cycles={cycles}")
        
        # Write diffraction data to .chi file
        q_array, intensity_array = chi_data
        chi_file = temp_dir / f"{sample_name}.chi"
        write_chi_file(chi_file, q_array, intensity_array)
        logger.info(f"Wrote chi file: {chi_file} ({len(q_array)} points)")
        
        # Prepare worker input JSON
        worker_input = {
            "chi_file": str(chi_file),
            "recipe": recipe,
            "sample_name": sample_name,
            "cycles": cycles,
            "save_gpx": save_gpx,
            "generate_plot": generate_plot,
        }
        
        input_json = temp_dir / "worker_input.json"
        output_json = temp_dir / "worker_output.json"
        
        with open(input_json, 'w') as f:
            json.dump(worker_input, f, indent=2)
        logger.info(f"Wrote worker input: {input_json}")
        
        # ====================================================================
        # 2. Spawn Worker Process
        # ====================================================================
        
        # Verify worker script exists
        if not WORKER_SCRIPT.exists():
            raise FileNotFoundError(f"Worker script not found: {WORKER_SCRIPT}")
        
        # Verify GSAS-II environment exists
        if not GSASII_ENV_PATH.exists():
            raise FileNotFoundError(
                f"GSAS-II environment not found: {GSASII_ENV_PATH}\n"
                f"Ensure GSAS-II is installed at this location."
            )
        
        # Build command to run worker in GSAS-II environment
        cmd = [
            "bash", "-c",
            f"cd {GSASII_ENV_PATH} && "
            f"{GSASII_PYTHON} {WORKER_SCRIPT} {input_json} {output_json}"
        ]
        
        logger.info(f"Running worker: {' '.join(cmd)}")
        
        # Execute worker process
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=REFINEMENT_TIMEOUT,
                check=False,  # Don't raise on non-zero exit
            )
            
            logger.info(f"Worker exit code: {result.returncode}")
            
            if result.stdout:
                logger.info(f"Worker stdout:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"Worker stderr:\n{result.stderr}")
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Worker timeout after {REFINEMENT_TIMEOUT}s")
            raise RuntimeError(
                f"Refinement timeout after {REFINEMENT_TIMEOUT}s. "
                f"Try reducing data range or refinement cycles."
            ) from e
        
        # ====================================================================
        # 3. Read Worker Output
        # ====================================================================
        
        if not output_json.exists():
            raise RuntimeError(
                f"Worker did not create output file: {output_json}\n"
                f"Exit code: {result.returncode}\n"
                f"Stderr: {result.stderr}"
            )
        
        with open(output_json) as f:
            worker_output = json.load(f)
        
        logger.info(f"Read worker output: {list(worker_output.keys())}")
        
        # Check if worker succeeded
        if not worker_output.get("success", False):
            error_msg = worker_output.get("error", "Unknown error")
            traceback = worker_output.get("traceback", "")
            raise RuntimeError(
                f"Worker refinement failed: {error_msg}\n"
                f"Traceback:\n{traceback}"
            )
        
        logger.info(f"✓ Refinement successful: "
                   f"Rwp={worker_output['fit_quality']['Rwp']:.3f}%")
        
        return worker_output
        
    finally:
        # Cleanup temp directory unless saving GPX
        if temp_dir_created and not save_gpx:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temp directory")


# ============================================================================
# Legacy function (now deprecated)
# ============================================================================

def run_gsasii_refinement_direct(
    chi_data: Tuple[List[float], List[float]],
    recipe: Dict[str, Any],
    sample_name: str,
    cycles: int = 5,
    temp_dir: Optional[Path] = None,
    save_gpx: bool = False,
    generate_plot: bool = True
) -> Dict[str, Any]:
    """
    DEPRECATED: Direct GSAS-II refinement (requires GSAS-II in current env).
    
    Use run_gsasii_refinement() instead, which uses subprocess worker pattern.
    
    This function is kept for reference but will fail unless GSAS-II is
    installed in the current Python environment.
    """
    # Import GSAS-II (fail fast if not available)
    try:
        from GSASII import GSASIIscriptable as G2  # type: ignore
    except ImportError as e:
        raise ImportError(
            "GSASIIscriptable not found. "
            "Use run_gsasii_refinement() which uses subprocess worker, "
            "or ensure GSAS-II is installed in current environment."
        ) from e
    
    # ... rest of original implementation ...
    
    # Create temp directory if needed
    temp_dir_created = temp_dir is None
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="gsasii_"))
        logger.info(f"Created temp directory: {temp_dir}")
    else:
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    warnings: List[str] = []
    
    try:
        # Get assets directory (bundled with service)
        service_dir = Path(__file__).parent
        assets_dir = service_dir / "assets"
        
        # ====================================================================
        # 1. Prepare Input Files
        # ====================================================================
        
        logger.info(f"Starting refinement: sample={sample_name}, cycles={cycles}")
        
        # Write diffraction data to .chi file
        q_array, intensity_array = chi_data
        chi_file = temp_dir / f"{sample_name}.chi"
        write_chi_file(chi_file, q_array, intensity_array)
        
        # Resolve instrument file (search in assets/instruments/)
        instrument_file = resolve_file(
            recipe["instrument_file"],
            ".instprm",
            temp_dir,
            assets_dir / "instruments"
        )
        
        # Resolve CIF file (search in assets/cifs/)
        cif_file = resolve_file(
            recipe["cif_file"],
            ".cif",
            temp_dir,
            assets_dir / "cifs"
        )
        
        logger.info(f"Files resolved: chi={chi_file.name}, "
                   f"inst={instrument_file.name}, cif={cif_file.name}")
        
        # ====================================================================
        # 2. Create GSAS-II Project
        # ====================================================================
        
        gpx_path = temp_dir / f"{sample_name}.gpx"
        logger.info(f"Creating GSAS-II project: {gpx_path}")
        
        proj = G2.G2Project(newgpx=str(gpx_path))
        
        # Add histogram (data + instrument parameters)
        hist = proj.add_powder_histogram(str(chi_file), str(instrument_file))
        logger.info(f"Added powder histogram: {hist}")
        
        # Add phase (crystal structure)
        phase = proj.add_phase(
            str(cif_file),
            phasename=recipe["phase_name"],
            histograms=[hist]
        )
        logger.info(f"Added phase: {recipe['phase_name']}")
        
        # ====================================================================
        # 3. Configure Refinement
        # ====================================================================
        
        # Set number of cycles
        proj.set_Controls('cycles', cycles)
        logger.info(f"Set refinement cycles: {cycles}")
        
        # Get refinement dictionary from recipe
        refinement_dict = recipe["refinement_dict"]
        logger.debug(f"Refinement dict: {refinement_dict}")
        
        # ====================================================================
        # 4. Execute Refinement
        # ====================================================================
        
        logger.info(f"Starting do_refinements() for {recipe['phase_name']}")
        proj.do_refinements([refinement_dict])
        logger.info(f"Refinement complete for {recipe['phase_name']}")
        
        # ====================================================================
        # 5. Extract Results
        # ====================================================================
        
        # Cell parameters
        cell, cell_esds = phase.get_cell_and_esd()
        logger.info(f"Extracted cell parameters: a={cell.get('length_a'):.4f}")
        
        # Fit quality
        rwp = hist.residuals.get("wR")
        logger.info(f"Fit quality: Rwp={rwp:.3f}%")
        
        # Check for poor fits
        if rwp > 20.0:
            warnings.append(f"High Rwp value ({rwp:.1f}%) - poor fit quality")
        
        # Profile data
        two_theta = hist.getdata(datatype="X")
        q_values = hist.getdata(datatype="Q")
        d_spacings = hist.getdata(datatype="d")
        y_obs = hist.getdata(datatype="Yobs")
        y_weights = hist.getdata(datatype="Yweight")
        y_calc = hist.getdata(datatype="Ycalc")
        y_bkg = hist.getdata(datatype="Background")
        y_diff = hist.getdata(datatype="Residual")
        
        # ====================================================================
        # 6. Build Result Dictionary
        # ====================================================================
        
        results = {
            "parameters": {
                "Rwp": rwp,
                "cell_a": cell.get("length_a"),
                "cell_a_esd": cell_esds.get("length_a"),
                "cell_b": cell.get("length_b"),
                "cell_b_esd": cell_esds.get("length_b"),
                "cell_c": cell.get("length_c"),
                "cell_c_esd": cell_esds.get("length_c"),
                "cell_alpha": cell.get("angle_alpha"),
                "cell_alpha_esd": cell_esds.get("angle_alpha"),
                "cell_beta": cell.get("angle_beta"),
                "cell_beta_esd": cell_esds.get("angle_beta"),
                "cell_gamma": cell.get("angle_gamma"),
                "cell_gamma_esd": cell_esds.get("angle_gamma"),
                "cell_volume": cell.get("volume"),
                "cell_volume_esd": cell_esds.get("volume"),
            },
            "cell": {
                "a": {
                    "value": cell.get("length_a"),
                    "esd": cell_esds.get("length_a")
                },
                "b": {
                    "value": cell.get("length_b"),
                    "esd": cell_esds.get("length_b")
                },
                "c": {
                    "value": cell.get("length_c"),
                    "esd": cell_esds.get("length_c")
                },
                "alpha": {
                    "value": cell.get("angle_alpha"),
                    "esd": cell_esds.get("angle_alpha")
                },
                "beta": {
                    "value": cell.get("angle_beta"),
                    "esd": cell_esds.get("angle_beta")
                },
                "gamma": {
                    "value": cell.get("angle_gamma"),
                    "esd": cell_esds.get("angle_gamma")
                },
                "volume": {
                    "value": cell.get("volume"),
                    "esd": cell_esds.get("volume")
                }
            },
            "fit_quality": {
                "Rwp": rwp,
                "chi2": hist.residuals.get("chi2") if hasattr(hist.residuals, "get") else None,
                "GoF": None  # GSAS-II doesn't directly provide GoF in residuals
            },
            "fit_profile": {
                "two_theta": two_theta.tolist() if isinstance(two_theta, np.ndarray) else two_theta,
                "q_values": q_values.tolist() if isinstance(q_values, np.ndarray) else q_values,
                "d_spacings": d_spacings.tolist() if isinstance(d_spacings, np.ndarray) else d_spacings,
                "y_obs": y_obs.tolist() if isinstance(y_obs, np.ndarray) else y_obs,
                "y_calc": y_calc.tolist() if isinstance(y_calc, np.ndarray) else y_calc,
                "y_diff": y_diff.tolist() if isinstance(y_diff, np.ndarray) else y_diff,
                "y_bkg": y_bkg.tolist() if isinstance(y_bkg, np.ndarray) else y_bkg,
                "y_weights": y_weights.tolist() if isinstance(y_weights, np.ndarray) else y_weights,
            },
            "warnings": warnings
        }
        
        # ====================================================================
        # 7. Generate Plot (Optional)
        # ====================================================================
        
        if generate_plot:
            logger.info("Generating fit plot")
            plot_image = create_fit_plot(
                results["fit_profile"],
                sample_name,
                recipe["phase_name"],
                rwp
            )
            results["plot_image"] = plot_image
        
        # ====================================================================
        # 8. Handle GPX File
        # ====================================================================
        
        if save_gpx:
            results["gpx_path"] = str(gpx_path)
            logger.info(f"GPX file saved: {gpx_path}")
        else:
            results["gpx_path"] = None
            # Will be cleaned up with temp_dir
        
        logger.info(f"Refinement successful: Rwp={rwp:.3f}%")
        return results
        
    except Exception as e:
        logger.error(f"Refinement failed: {str(e)}", exc_info=True)
        raise RuntimeError(f"GSAS-II refinement failed: {str(e)}") from e
        
    finally:
        # Cleanup temp directory if we created it and not saving GPX
        if temp_dir_created and not save_gpx:
            logger.info(f"Cleaning up temp directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================================
# Plotting
# ============================================================================


def create_fit_plot(
    fit_profile: Dict[str, List[float]],
    sample_name: str,
    phase_name: str,
    rwp: float
) -> str:
    """
    Create fit comparison plot (observed vs calculated vs difference).
    
    Args:
        fit_profile: Dict with keys: two_theta, y_obs, y_calc, y_diff
        sample_name: Sample name for title
        phase_name: Phase name for title
        rwp: Rwp value for title
        
    Returns:
        Base64-encoded PNG image (data URI format)
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    
    tt = fit_profile["two_theta"]
    y_obs = fit_profile["y_obs"]
    y_calc = fit_profile["y_calc"]
    y_diff = fit_profile["y_diff"]
    
    # Plot observed as open circles
    ax.scatter(
        tt, y_obs,
        marker="o",
        edgecolor="black",
        facecolor="None",
        label="Observed",
        s=5,
        alpha=0.6
    )
    
    # Plot calculated as red line
    ax.plot(tt, y_calc, label="Calculated", color="red", alpha=0.9, linewidth=1.5)
    
    # Plot difference as gray line
    ax.plot(tt, y_diff, label="Difference", color="gray", alpha=0.7, linewidth=1)
    
    # Labels and title
    ax.set_xlabel(r"2θ (°)", fontsize=11)
    ax.set_ylabel("Intensity (counts)", fontsize=11)
    ax.set_title(
        f"{sample_name} • {phase_name} (Rwp={rwp:.3f}%)",
        fontsize=12,
        fontweight="bold"
    )
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.3, linestyle="--")
    
    fig.tight_layout()
    
    # Save to bytes buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    # Encode as base64
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"

"""Data input/output utilities for RoboMage."""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional, Dict, Any


def load_chi_file(filepath: str | Path) -> pd.DataFrame:
    """
    Load a .chi file containing Q and intensity data.
    
    Args:
        filepath: Path to the .chi file
        
    Returns:
        DataFrame with columns ['Q', 'intensity']
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is invalid
    """
    filepath = Path(filepath)
    
    if not filepath.suffix.lower() == '.chi':
        raise ValueError(f"Expected .chi file, got: {filepath.suffix}")
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    try:
        # Read the file, skipping comment lines that start with #
        data = np.loadtxt(filepath, comments='#')
        
        if data.shape[1] != 2:
            raise ValueError(f"Expected 2 columns, got {data.shape[1]}")
            
        # Create DataFrame with meaningful column names
        df = pd.DataFrame(data, columns=['Q', 'intensity'])
        
        return df
        
    except Exception as e:
        raise ValueError(f"Failed to parse {filepath}: {e}")


def get_data_info(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary information about loaded diffraction data.
    
    Args:
        df: DataFrame containing Q and intensity columns
        
    Returns:
        Dictionary with data statistics
    """
    return {
        'num_points': len(df),
        'q_range': (df['Q'].min(), df['Q'].max()),
        'q_step_mean': df['Q'].diff().mean(),
        'q_step_std': df['Q'].diff().std(),
        'intensity_range': (df['intensity'].min(), df['intensity'].max()),
        'intensity_mean': df['intensity'].mean(),
        'intensity_std': df['intensity'].std(),
    }


def load_test_data() -> pd.DataFrame:
    """
    Load the standard test dataset (SRM 660b).
    
    Returns:
        DataFrame with the test diffraction pattern
    """
    # Get the project root directory
    current_file = Path(__file__)
    project_root = current_file.parents[2]  # Go up from src/robomage/data_io.py to root
    
    test_file = project_root / "pdf_SRM_660b_q.chi"
    
    if not test_file.exists():
        raise FileNotFoundError(f"Test data file not found: {test_file}")
    
    return load_chi_file(test_file)
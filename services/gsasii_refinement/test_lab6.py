"""Test GSAS-II Service with LaB6 Data

Manual test script to verify the service works with DRX Demo assets.
Requires GSAS-II to be installed.

Usage:
    python test_lab6.py
"""

import json
import sys
from pathlib import Path

# Add service to path
service_dir = Path(__file__).parent
sys.path.insert(0, str(service_dir.parent.parent))

from services.gsasii_refinement.gsasii_wrapper import (
    run_gsasii_refinement,
    read_chi_file
)


def load_recipe(recipe_path: Path) -> dict:
    """Load YAML recipe file"""
    import yaml
    with recipe_path.open() as f:
        return yaml.safe_load(f)


def main():
    print("=" * 70)
    print("GSAS-II Service Test - LaB6 IPF Fit")
    print("=" * 70)
    
    # Paths
    service_dir = Path(__file__).parent
    assets_dir = service_dir / "assets"
    
    # Check GSAS-II
    try:
        from GSASII import GSASIIscriptable as G2  # noqa: F401
        print("✓ GSAS-II found")
    except ImportError:
        print("✗ GSAS-II not available - cannot run test")
        print("  Install GSAS-II via pixi or conda")
        return 1
    
    # Load LaB6 data from DRX Demo
    print("\n1. Loading LaB6 diffraction data...")
    autoxrd_data = Path("/nsls2/users/dolds/dev/autoxrd/on-the-fly/test/"
                       "user_data_DRX_test/DRX_data_to_be_dropped_in/"
                       "xrd_LaB6_660c_std_brac2/integration")
    
    chi_files = list(autoxrd_data.glob("*.chi"))
    if not chi_files:
        print(f"✗ No .chi files found in {autoxrd_data}")
        return 1
    
    chi_file = chi_files[0]
    print(f"  Using: {chi_file.name}")
    
    q, intensity = read_chi_file(chi_file)
    print(f"  Data points: {len(q)}")
    print(f"  Q range: {q.min():.3f} - {q.max():.3f} Å⁻¹")
    
    # Load recipe
    print("\n2. Loading IPF fit recipe...")
    recipe_path = assets_dir / "recipes" / "IPF_fit_recipe.yaml"
    recipe = load_recipe(recipe_path)
    print(f"  Phase: {recipe['phase_name']}")
    print(f"  Instrument: {recipe['instrument_file']}")
    print(f"  CIF: {recipe['cif_file']}")
    
    # Run refinement
    print("\n3. Running GSAS-II refinement...")
    print("  (This may take 30-60 seconds)")
    
    try:
        result = run_gsasii_refinement(
            chi_data=(q.tolist(), intensity.tolist()),
            recipe=recipe,
            sample_name="LaB6_test",
            cycles=5,
            save_gpx=False,
            generate_plot=True
        )
        
        print("  ✓ Refinement complete!")
        
    except Exception as e:
        print(f"  ✗ Refinement failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Display results
    print("\n4. Results:")
    print(f"  Rwp: {result['fit_quality']['Rwp']:.3f}%")
    print(f"  Cell a: {result['cell']['a']['value']:.6f} ± "
          f"{result['cell']['a']['esd']:.6f} Å")
    print(f"  Cell volume: {result['cell']['volume']['value']:.4f} ± "
          f"{result['cell']['volume']['esd']:.4f} ų")
    
    if result['warnings']:
        print(f"\n  Warnings:")
        for warning in result['warnings']:
            print(f"    - {warning}")
    
    # Save results
    output_dir = service_dir / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n5. Saving results to {output_dir}/...")
    
    # Save JSON
    result_copy = result.copy()
    if 'plot_image' in result_copy:
        del result_copy['plot_image']  # Too large for JSON readability
    
    with (output_dir / "lab6_result.json").open('w') as f:
        json.dump(result_copy, f, indent=2)
    print(f"  ✓ Saved: lab6_result.json")
    
    # Save plot
    if result.get('plot_image'):
        import base64
        img_data = result['plot_image'].split(',', 1)[1]
        img_bytes = base64.b64decode(img_data)
        with (output_dir / "lab6_fit.png").open('wb') as f:
            f.write(img_bytes)
        print(f"  ✓ Saved: lab6_fit.png")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

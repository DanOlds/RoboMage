from robomage.config.refinement_schema import (
    InstrumentConfig,
    PhaseConfig,
    RefinementConfig,
)


def test_minimal_config_ok():
    cfg = RefinementConfig(
        instrument=InstrumentConfig(beamline="XPD", wavelength=0.184),
        phases=[PhaseConfig(name="LiCoO2", cif_path="data/LiCoO2.cif")],
        q_range=[0.5, 8.0],
    )
    assert cfg.instrument.beamline == "XPD"
    assert cfg.q_range[1] > cfg.q_range[0]

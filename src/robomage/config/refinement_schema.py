from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class InstrumentConfig(BaseModel):
    beamline: str = Field(..., description="e.g., 'XPD', 'PDF'")
    wavelength: float = Field(..., gt=0, description="Å")
    zero_shift: float = Field(0.0, description="degrees")


class PhaseConfig(BaseModel):
    name: str
    cif_path: str
    refine_cell: bool = True
    refine_profile: bool = False


class BackgroundModel(BaseModel):
    model: str = Field(default="chebyshev")
    order: int = Field(default=6, ge=1, le=12)


class RefinementConfig(BaseModel):
    schema_version: str = "1.0"
    instrument: InstrumentConfig
    phases: list[PhaseConfig]
    background: BackgroundModel = Field(default_factory=lambda: BackgroundModel())
    q_range: list[float] = Field(..., min_length=2, max_length=2)  # <- updated
    constraints: list[str] | None = None
    engine: str = Field("gsas2")
    max_iterations: int = Field(50, ge=1, le=500)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))  # <- updated

    @field_validator("q_range")
    @classmethod
    def _validate_qrange(cls, v: list[float]):
        if v[1] <= v[0]:
            raise ValueError("q_range must be [Qmin, Qmax] with Qmax > Qmin")
        return v

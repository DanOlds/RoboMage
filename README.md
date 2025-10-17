# 🧙‍♂️ RoboMage — Automated Powder Diffraction Framework

**RoboMage** is a modular Python framework for automating **Rietveld refinement and powder diffraction analysis** across NSLS-II beamlines.

### 🔍 Key Features
- Automated, reproducible diffraction refinement pipelines.
- Modular architecture with GSAS-II integration and future diffpy-CMI support.
- Data ingestion from local files or Tiled/Databroker sources.
- Provenance tracking and persistent results database.
- Simple CLI, notebook, and planned web interfaces.

### ⚙️ Core Stack
- **Python / Pixi / Pydantic / GSAS-II**
- **SQLite → PostgreSQL**
- **Ruff + mypy + pytest + GitHub Actions**

### 🚀 Quick Start

```powershell
git clone https://github.com/<your-username>/RoboMage.git
cd RoboMage
pixi install
pixi run test
```

Open the project in VS Code:
```powershell
code .
```

### 📈 Status
Week 1 complete:
- Repo scaffolded and tested
- Schema validated
- Linting and CI active

---
> Developed at **Brookhaven National Laboratory (BNL)** at the **NSLS-II**.

# 🧙‍♂️ RoboMage — Automated Powder Diffraction Framework

![CI](https://github.com/DanOlds/RoboMage/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/github/license/DanOlds/RoboMage)
![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)

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
git clone https://github.com/DanOlds/RoboMage.git
cd RoboMage
pixi install
pixi run test
```

Open the project in VS Code:
```powershell
code .
```

### 📈 Status
**Week 1** ✅ Complete:
- Repo scaffolded and tested
- Schema validated
- Linting and CI active

**Week 2** 📋 Planned:
- Data pipeline MVP (see [`docs/sprint-2-data-pipeline.md`](docs/sprint-2-data-pipeline.md))

---
> Developed at **Brookhaven National Laboratory (BNL)** at the **NSLS-II**.

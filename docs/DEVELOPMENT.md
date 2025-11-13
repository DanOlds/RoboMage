# RoboMage Development Guide

## ⚠️ Environment Management: Pixi Only

**CRITICAL**: This project uses **Pixi exclusively** for dependency and task management. 

**Do NOT use:**
- ❌ `pip install`
- ❌ `conda install` / `conda create`
- ❌ `python -m venv`
- ❌ Traditional `requirements.txt` or `environment.yml`

**Always use pixi commands** as shown below.

## 🚀 Getting Started

### First-Time Setup

1. **Install Pixi** (one-time):
   ```bash
   # macOS/Linux
   curl -fsSL https://pixi.sh/install.sh | bash
   
   # Windows (PowerShell)
   iwr -useb https://pixi.sh/install.ps1 | iex
   ```

2. **Clone and setup RoboMage**:
   ```bash
   git clone https://github.com/DanOlds/RoboMage.git
   cd RoboMage
   pixi install  # Creates environment and installs all dependencies
   ```

3. **Verify installation**:
   ```bash
   pixi run test  # Should pass all 51 tests
   ```

## 📋 Common Development Commands

### Quality Checks (Use Before Commits)
```bash
# Run all checks (format, lint, typecheck, test)
pixi run check

# Individual quality checks
pixi run format      # Format code with ruff
pixi run lint        # Check code quality with ruff
pixi run typecheck   # Type checking with mypy
pixi run test        # Run all pytest tests
```

### Running the Application

```bash
# Start the dashboard
pixi run python -m robomage.dashboard

# Start the peak analysis service
pixi run python services/peak_analysis/main.py

# Run CLI tools
pixi run python -m robomage sample.chi --plot
pixi run python peak_analyzer.py sample.chi --output results/
```

### Development Workflow

```bash
# 1. Make your changes
# Edit files in src/robomage/ or tests/

# 2. Run quality checks
pixi run check

# 3. If checks fail, fix issues:
pixi run format    # Auto-fix formatting
pixi run lint      # See what needs manual fixing
pixi run typecheck # Check type errors
pixi run test      # Verify tests still pass

# 4. Commit when all checks pass
git add .
git commit -m "Your commit message"
```

### Testing

```bash
# Run all tests
pixi run test

# Run specific test file
pixi run pytest tests/test_data_models.py

# Run tests with coverage
pixi run pytest --cov=src/robomage

# Run tests matching a pattern
pixi run pytest -k "test_peak"

# Verbose output
pixi run pytest -v

# Stop on first failure
pixi run pytest -x
```

### Managing Dependencies

```bash
# Add a new dependency
pixi add numpy pandas  # Runtime dependencies
pixi add --feature dev pytest ruff  # Development dependencies

# Update dependencies
pixi update

# List installed packages
pixi list

# Remove a dependency
pixi remove package-name
```

## 🏗️ Project Structure

```
RoboMage/
├── pixi.toml              # Environment config and task definitions (KEY FILE)
├── pyproject.toml         # Python package metadata and tool configs
├── src/robomage/          # Main package source code
│   ├── data/              # Data models and loaders
│   ├── dashboard/         # Dash visualization dashboard
│   │   ├── callbacks/     # Dashboard callbacks (file_upload, plotting, analysis)
│   │   └── layouts/       # Dashboard UI layouts
│   └── clients/           # HTTP clients for services
├── services/              # Independent microservices
│   └── peak_analysis/     # FastAPI peak analysis service
├── tests/                 # Test suite (51 tests)
└── examples/              # Example scripts and tutorials
```

## 🔧 Key Configuration Files

### pixi.toml
- Defines project dependencies (runtime + dev)
- Defines task shortcuts (`test`, `check`, `format`, etc.)
- Platform-specific configurations
- **This is the single source of truth for dependencies**

### pyproject.toml
- Python package metadata
- Tool configurations (ruff, mypy, pytest)
- Does NOT define dependencies (that's pixi.toml)

## 🐛 Troubleshooting

### "Command not found" errors
**Problem**: Running `python`, `pytest`, etc. directly
**Solution**: Always use `pixi run` prefix:
```bash
pixi run python script.py
pixi run pytest tests/
```

### Dependencies not installing
**Problem**: Tried `pip install` or `conda install`
**Solution**: Use pixi commands:
```bash
pixi install        # Install all dependencies from pixi.toml
pixi add package    # Add new dependency
```

### Tests failing after checkout
**Problem**: Environment out of sync
**Solution**: Reinstall environment:
```bash
pixi install --force
pixi run test
```

### MyPy errors in dashboard code
**Expected**: Dashboard code is excluded from strict type checking
**Solution**: This is intentional. Core library (`src/robomage/data/`, etc.) must pass strict mypy, dashboard code has relaxed rules.

## 📊 CI/CD Pipeline

GitHub Actions automatically runs on every push:
1. `pixi install` - Setup environment
2. `pixi run format --check` - Verify formatting
3. `pixi run lint` - Check code quality
4. `pixi run typecheck` - Type checking
5. `pixi run test` - Run test suite

All checks must pass before merging to main.

## 🎯 Best Practices

### Always Use Pixi
- ✅ `pixi run test` 
- ✅ `pixi run python script.py`
- ✅ `pixi add new-package`
- ❌ `python script.py` (uses system Python)
- ❌ `pip install package` (wrong environment)

### Before Committing
```bash
pixi run check  # Runs format, lint, typecheck, test
```

### Adding New Features
1. Create feature branch from `main`
2. Implement feature with tests
3. Run `pixi run check` locally
4. Push and create PR
5. Wait for CI to pass
6. Merge to main

### Working with Services
```bash
# Terminal 1: Start service
pixi run python services/peak_analysis/main.py

# Terminal 2: Start dashboard
pixi run python -m robomage.dashboard

# Terminal 3: Run tests
pixi run pytest tests/test_dashboard_analysis.py
```

## 📖 Additional Resources

- **[Architecture Guide](.github/copilot-instructions.md)** - Microservices architecture, patterns
- **[Sprint 4 Plan](sprint-4-visualization-dashboard.md)** - Dashboard implementation details
- **[LLM Chat Guide](llm-chat-guide.md)** - Starting AI assistant conversations
- **[Examples](../examples/)** - Working code samples
- **[Pixi Documentation](https://pixi.sh/latest/)** - Official pixi docs

## 🆘 Getting Help

1. Check this guide first
2. Review `.github/copilot-instructions.md` for architecture patterns
3. Look at `examples/` for usage patterns
4. Check existing tests for examples
5. Review pixi documentation at https://pixi.sh

---

**Remember**: When in doubt, use `pixi run` before any command!

# Copilot Instructions for AWSM

## Repository Description
AWSM (Automated Water Supply Model) is a Python-based framework for executing the **iSnobal** snow mass and energy model. It integrates with the **Spatial Modeling for Resources Framework (SMRF)** and uses **pysnobal** as the underlying interface for iSnobal. AWSM acts as a central execution wrapper that manages data flow, initialization, and sequential execution of these models.

## Repository Structure
The project follows a standard Python package structure:
- `awsm/`: Main package directory.
  - `cli.py`: Command-line interface implementation using `argparse`.
  - `framework/`: Core logic for model execution and flow control.
  - `interface/`: Adapters and wrappers for `pysnobal` and `SMRF`.
  - `data/`: Default configuration files and static resources.
  - `tests/`: Unit and integration tests.
- `docs/`: Sphinx documentation and configuration.
- `notebooks/`: Jupyter notebooks for analysis and demonstrations.
- `scripts/`: Helper scripts for deployment or data processing.
- `pyproject.toml` & `Makefile`: Build system and task automation.

## Key Guidelines

### 1. Code Style & Standards
Adhere to the specialized iSnobal organization agents defined in `.github/instructions/`:
- **Python Style**: Follow `python-style-agent.md` for Ruff formatting, type hints, and naming conventions.
- **Legacy Migration**: Consult `legacy-migrator-agent.md` when refactoring complex or obscure legacy code to improve clarity without changing logic.
- **Documentation**: Follow the `documentation-agent.md` for NumPy-style docstrings and RST formatting.
- **Dependencies**: Consult `dependency-modernization-agent.md` for Conda-based environment management (avoiding `pip` where possible).
- **Performance**: Use `performance-cython-agent.md` for C/Cython optimizations and NumPy vectorization strategies.
- **Snow Physics**: Defer to `snow-physics-agent.md` for two-layer snowpack logic and energy balance correctness.

### 2. Domain Context
- **Models**: Always consider the relationship between `SMRF` (forcing data/spatial modeling), `pysnobal` (iSnobal wrapper), and `AWSM` (orchestrator).
- **Config Files**: AWSM heavily relies on `.ini` configuration files. Ensure any changes to parameters are reflected in the expected config structure.

### 3. Review Style
When providing feedback or reviewing code:
- **Conciseness**: Be short and concise; explain the "why" behind recommendations.
- **Clarification**: Ask clarifying questions when code intent is unclear.
- **Efficiency**: Do not repeat comments that were previously resolved on new pushes.
- **Context**: Do not repeat any information that was already in the PR description.
- **Prioritization**: Focus on logic over purely technical changes.

### 4. Testing
Follow the specialized `testing-coverage-agent.md` for detailed quality and coverage standards:
- **Framework**: Use the standard Python `unittest` framework for all tests.
- **Location**: Place new tests in `awsm/tests`.
- **Execution**:
  - Run all tests: `make test`
  - Run specific test file: `python -m unittest awsm/tests/test_filename.py`
  - Discover and run: `python -m unittest discover`

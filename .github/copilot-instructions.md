# Copilot Instructions for AWSM

## Repository Description
The **Automated Water Supply Model (AWSM)** is the central execution framework for the iSnobal modeling suite. 
It orchestrates the entire workflow by integrating **SMRF** (for meteorological forcing data distribution) 
and **PySnobal** (the wrapper for the iSnobal snow mass and energy balance model). AWSM provides a unified 
interface to configure, initialize, and execute spatially distributed snow models over a Digital Elevation Model (DEM).

## Repository Structure
The project follows a modular Python structure focused on orchestration and interfacing:
- `awsm/`: Main package directory.
  - `cli.py`: Command-line interface for model execution and date-range management.
  - `framework/`: Core orchestration logic, state management, and execution loops.
  - `interface/`: Connectors for interacting with SMRF and PySnobal APIs.
  - `data/`: Internal data resources and configuration templates.
  - `tests/`: Unit and integration tests for the framework.
- `scripts/`: Utility scripts for post-processing or data management.
- `notebooks/`: workflow examples for model execution and analysis.
- `pyproject.toml` & `Makefile`: Build system and task automation.

## Key Guidelines

### 1. Code Style & Standards
Adhere to the specialized iSnobal organization agents defined in **`iSnobal/.github`**:
- **Python Style**: Follow `@iSnobal/.github/instructions/python-style-agent.md` for Ruff formatting, mandatory type hints (Python 3.9+), and naming conventions.
- **Legacy Migration**: Consult `@iSnobal/.github/instructions/legacy-migrator-agent.md` when refactoring the central execution loops or initialization logic.
- **Documentation**: Follow `@iSnobal/.github/instructions/documentation-agent.md` for NumPy-style docstrings.
- **Dependencies**: Consult `@iSnobal/.github/instructions/dependency-modernization-agent.md` for Python environment management.
- **Performance**: Use `@iSnobal/.github/instructions/performance-cython-agent.md` for optimizing the framework's data handling and state transitions.

### 2. Domain Context
- **Orchestration**: AWSM's primary role is managing the **state** (initialization files) and **forcing data flow** between SMRF outputs and iSnobal inputs.
- **Initialization**: AWSM handles finding previous snow states. It ensures that the correct files are used for each model run, especially when running over multiple dates.
- **Ecosystem**: 
    - **SMRF** is called to distribute point/gridded data over the DEM.
    - **PySnobal** is the wrapper used to invoke the iSnobal binaries.
- **Configuration**: AWSM uses `.ini` files (via `inicheck`). Ensure any new CLI parameters or model options are correctly mapped to the configuration framework.

### 3. Review Style
When providing feedback or reviewing code:
- **Conciseness**: Be short and concise; explain the "why" behind recommendations.
- **Clarification**: Ask clarifying questions when code intent is unclear.
- **Efficiency**: Do not repeat comments that were previously resolved on new pushes.
- **Context**: Do not repeat any information that was already in the PR description.
- **Prioritization**: Focus on logic correctness and framework stability over purely technical changes.

### 4. Testing & Build
Follow the specialized `@iSnobal/.github/instructions/testing-coverage-agent.md`:
- **Framework**: Use the standard Python `unittest` framework.
- **Location**: Place new tests in `awsm/tests`.
- **Execution**:
  - Run all tests: `make tests`
  - Clean build artifacts: `make clean`
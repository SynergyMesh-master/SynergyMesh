# MachineNativeOps AAPS

**Autonomous Agent Platform System** - A minimal system skeleton with immutable
governance and self-healing capabilities.

## 🏗️ Architecture

This project follows a **FHS-compliant minimal system skeleton** design with
clear separation between governance and workspace:

```
/
├── bin/                   # Essential user command binaries (FHS)
├── etc/                   # Host-specific system configuration (FHS)
├── home/                  # User home directories (FHS)
├── lib/                   # Essential shared libraries (FHS)
├── sbin/                  # System administration binaries (FHS)
├── srv/                   # Service data (FHS)
├── usr/                   # Secondary hierarchy for user data (FHS)
├── var/                   # Variable data (FHS)
│
├── controlplane/          # Governance Layer (Immutable)
│   ├── baseline/          # Immutable baseline configuration
│   │   ├── config/        # Core configuration files (12 files)
│   │   ├── registries/    # Module and URN registries (4 files)
│   │   ├── specifications/# System specifications (8 files)
│   │   ├── integration/   # Integration configuration (1 file)
│   │   ├── documentation/ # Architecture documentation
│   │   └── validation/    # Validation scripts and tools
│   ├── governance/        # Governance documentation and policies
│   │   ├── docs/          # All governance documentation
│   │   ├── policies/      # Governance policies
│   │   └── reports/       # Implementation reports
│   └── overlay/           # Runtime overlays and evidence
│
├── workspace/             # Work Layer (Mutable)
│   ├── projects/          # Project files and scripts
│   ├── config/            # Project configurations
│   ├── docs/              # Project documentation
│   └── artifacts/         # Build artifacts and reports
│
├── root.bootstrap.yaml    # System bootstrap configuration
├── root.env.sh            # Environment variables
└── root.fs.map            # Filesystem mappings
```

### FHS Compliance

This project follows the Filesystem Hierarchy Standard (FHS) 3.0:

- ✅ **8/8 applicable FHS directories** implemented
- ✅ **Clean root layer** with only 3 bootstrap files
- ✅ **Standards-compliant** structure
- ✅ **Industry best practices** followed

See [FHS_IMPLEMENTATION.md](FHS_IMPLEMENTATION.md) for detailed documentation.

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Source environment variables
source root.env.sh

# Verify controlplane paths
echo $CONTROLPLANE_PATH
echo $WORKSPACE_PATH
```

### 2. Run Validation

```bash
# Execute validation system
python3 controlplane/baseline/validation/validate-root-specs.py

# View validation results
cat controlplane/overlay/evidence/validation/validation.report.json
```

### 3. Explore Structure

```bash
# View baseline configuration
ls -la controlplane/baseline/config/

# View governance documents
ls -la controlplane/governance/docs/

# View project files
ls -la workspace/
```

## 📚 Documentation

### Core Documentation

- **FHS Implementation**: [FHS_IMPLEMENTATION.md](FHS_IMPLEMENTATION.md)
- **Architecture**: [controlplane/baseline/documentation/BASELINE_ARCHITECTURE.md](controlplane/baseline/documentation/BASELINE_ARCHITECTURE.md)
- **Usage Guide**: [controlplane/CONTROLPLANE_USAGE.md](controlplane/CONTROLPLANE_USAGE.md)

### Governance Documentation

- **Governance Docs**: [controlplane/governance/docs/](controlplane/governance/docs/)
- **Policies**: [controlplane/governance/policies/](controlplane/governance/policies/)
- **Reports**: [controlplane/governance/reports/](controlplane/governance/reports/)

### Project Documentation

- **Project Docs**: [workspace/docs/](workspace/docs/)
- **Configuration**: [workspace/config/](workspace/config/)

## 🎯 Key Principles

### 1. FHS Compliance

- Follows Filesystem Hierarchy Standard (FHS) 3.0
- Industry-standard directory structure
- Clean separation of concerns

### 2. Minimal System Skeleton

- Root directory contains only FHS directories and 3 bootstrap files
- All governance in `controlplane/`
- All work in `workspace/`

### 3. Immutable Governance

- `controlplane/baseline/` is read-only
- Changes require explicit governance approval
- Version control tracks all governance changes

### 4. Self-Healing Without Pollution

- Runtime state in `controlplane/overlay/`
- Self-healing writes only to overlay
- Baseline remains pristine

### 5. Evidence-Based Validation

- All operations produce evidence
- Evidence stored in `controlplane/overlay/evidence/`
- Comprehensive validation system (50 checks)

## 🔧 Validation System

The project includes a comprehensive validation system:

- **5 Validation Stages**: Structural, Syntax, Semantic, Integration, Security
- **50 Automated Checks**: Complete coverage of baseline configuration
- **Evidence Generation**: All validation produces auditable evidence
- **Pass/Fail Reporting**: Clear validation status

### Run Validation

```bash
python3 controlplane/baseline/validation/validate-root-specs.py
```

### View Results

```bash
# JSON report
cat controlplane/overlay/evidence/validation/validation.report.json

# Markdown report
cat controlplane/overlay/evidence/validation/validation.report.md

# Manifest
cat controlplane/overlay/evidence/validation/controlplane.manifest.json
```

## 🛠️ Development

### Project Structure

- **Baseline Configuration**: `controlplane/baseline/config/` (12 files)
- **Specifications**: `controlplane/baseline/specifications/` (8 files)
- **Registries**: `controlplane/baseline/registries/` (4 files)
- **Integration Rules**: `controlplane/baseline/integration/` (1 file)
- **Validation System**: `controlplane/baseline/validation/` (multiple files)

### Environment Variables

After sourcing `root.env.sh`, you have access to:

- `CONTROLPLANE_PATH`: Controlplane root
- `CONTROLPLANE_CONFIG`: Configuration directory
- `CONTROLPLANE_SPECS`: Specifications directory
- `CONTROLPLANE_REGISTRIES`: Registries directory
- `CONTROLPLANE_VALIDATION`: Validation directory
- `WORKSPACE_PATH`: Workspace root
- `FHS_BIN`, `FHS_SBIN`, `FHS_ETC`, etc.: FHS directories

## 📊 Status

- ✅ **FHS Compliance**: Complete (8/8 applicable directories)
- ✅ **Controlplane Architecture**: Complete (26 files)
- ✅ **Validation System**: Operational (50/50 checks passing)
- ✅ **Evidence Generation**: Working
- ✅ **Documentation**: Complete
- ✅ **Root Integration**: Complete

## 🔗 Links

- **GitHub Repository**: [MachineNativeOps/machine-native-ops](https://github.com/MachineNativeOps/machine-native-ops)
- **Issues**: [GitHub Issues](https://github.com/MachineNativeOps/machine-native-ops/issues)
- **Pull Requests**: [GitHub PRs](https://github.com/MachineNativeOps/machine-native-ops/pulls)

## 📝 License

See LICENSE file for details.

---

**Version**: 2.0.0 (FHS Compliant)
**Last Updated**: 2025-12-25
**Maintained By**: MachineNativeOps Team
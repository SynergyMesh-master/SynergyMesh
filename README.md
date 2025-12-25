# MachineNativeOps AAPS

**Autonomous Agent Platform System** - A minimal system skeleton with immutable governance and self-healing capabilities.

## 🏗️ Architecture

This project follows a **minimal system skeleton** design with clear separation between governance and workspace:

```
/
├── controlplane/          # Governance Layer (Immutable)
│   ├── baseline/          # Immutable baseline configuration
│   ├── overlay/           # Runtime state and evidence
│   ├── active/            # Synthesized read-only view
│   └── governance/        # Governance documents and policies
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

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Source environment variables
source root.env.sh

# Verify controlplane paths
echo $MACHINENATIVEOPS_CONTROLPLANE
echo $MACHINENATIVEOPS_BASELINE
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
ls -la workspace/projects/
```

## 📚 Documentation

### Controlplane Documentation
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

### 1. Minimal System Skeleton
- Root directory contains only essential bootstrap files
- All governance in `controlplane/`
- All work in `workspace/`

### 2. Immutable Governance
- `controlplane/baseline/` is read-only
- Changes require explicit governance approval
- Version control tracks all governance changes

### 3. Self-Healing Without Pollution
- Runtime state in `controlplane/overlay/`
- Self-healing writes only to overlay
- Baseline remains pristine

### 4. Evidence-Based Validation
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

- **Baseline Configuration**: `controlplane/baseline/config/` (10 files)
- **Specifications**: `controlplane/baseline/specifications/` (5 files)
- **Registries**: `controlplane/baseline/registries/` (2 files)
- **Integration Rules**: `controlplane/baseline/integration/` (1 file)
- **Validation System**: `controlplane/baseline/validation/` (3 files)

### Environment Variables

After sourcing `root.env.sh`, you have access to:

- `MACHINENATIVEOPS_CONTROLPLANE`: Controlplane root
- `MACHINENATIVEOPS_BASELINE`: Baseline directory
- `MACHINENATIVEOPS_OVERLAY`: Overlay directory
- `MACHINENATIVEOPS_ACTIVE`: Active view
- And 14 more subdirectory paths

## 📊 Status

- ✅ **Controlplane Architecture**: Complete
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

**Version**: 1.0.0  
**Last Updated**: 2025-12-23  
**Maintained By**: MachineNativeOps Team
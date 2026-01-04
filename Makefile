# ═══════════════════════════════════════════════════════════════════════════════
#                    Machine Native Ops - Root Makefile
#                    Workspace Delegation & Top-Level Targets
# ═══════════════════════════════════════════════════════════════════════════════
#
# This Makefile delegates most operations to workspace/Makefile while providing
# convenient top-level targets for common operations.
#
# Usage:
#   make all-kg          - Run all knowledge graph generation (delegates to workspace)
#   make check-drift     - Check if generated files are up-to-date
#   make clean-generated - Remove all generated YAML files
#   make help            - Show this help message
#
# ═══════════════════════════════════════════════════════════════════════════════

.PHONY: all-kg kg mndoc superroot check-drift clean-generated analyze-reports help install

# Default target
.DEFAULT_GOAL := help

# Workspace directory
WORKSPACE := workspace

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────
help:
	@echo "Machine Native Ops - Root Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make all-kg          - Run all knowledge graph generation"
	@echo "  make kg              - Build knowledge graph"
	@echo "  make mndoc           - Generate MN-DOC from README"
	@echo "  make superroot       - Generate SuperRoot entities"
	@echo "  make check-drift     - Check for drift in generated files"
	@echo "  make clean-generated - Remove generated YAML files"
	@echo "  make analyze-reports - Analyze root-level reports"
	@echo "  make install         - Install dependencies (npm + workspace)"
	@echo "  make help            - Show this help message"
	@echo ""
	@echo "For workspace-specific operations, use: make -C $(WORKSPACE) <target>"

# ─────────────────────────────────────────────────────────────────────────────
# Delegation Targets - Forward to workspace Makefile
# ─────────────────────────────────────────────────────────────────────────────
all-kg:
	@$(MAKE) -C $(WORKSPACE) all-kg

kg:
	@$(MAKE) -C $(WORKSPACE) kg

mndoc:
	@$(MAKE) -C $(WORKSPACE) mndoc

superroot:
	@$(MAKE) -C $(WORKSPACE) superroot

check-drift:
	@$(MAKE) -C $(WORKSPACE) check-drift

clean-generated:
	@$(MAKE) -C $(WORKSPACE) clean-generated

analyze-reports:
	@$(MAKE) -C $(WORKSPACE) analyze-reports

# ─────────────────────────────────────────────────────────────────────────────
# Root-Level Targets
# ─────────────────────────────────────────────────────────────────────────────
install:
	@echo "📦 Installing dependencies (npm workspaces handles all subdirectories)..."
	npm install
	@echo "✅ Installation complete"

#!/bin/bash
# Root Environment Configuration
# 根層環境配置 - 只負責啟動時環境變數

# Controlplane 路徑
export CONTROLPLANE_PATH="./controlplane"
export CONTROLPLANE_CONFIG="${CONTROLPLANE_PATH}/config"
export CONTROLPLANE_SPECS="${CONTROLPLANE_PATH}/specifications"
export CONTROLPLANE_REGISTRIES="${CONTROLPLANE_PATH}/registries"
export CONTROLPLANE_VALIDATION="${CONTROLPLANE_PATH}/validation"

# Workspace 路徑
export WORKSPACE_PATH="./workspace"

# FHS 路徑
export FHS_BIN="./bin"
export FHS_SBIN="./sbin"
export FHS_ETC="./etc"
export FHS_LIB="./lib"
export FHS_VAR="./var"
export FHS_USR="./usr"
export FHS_HOME="./home"
export FHS_TMP="./tmp"
export FHS_OPT="./opt"
export FHS_SRV="./srv"
export FHS_INITD="./init.d"

# 啟動模式
export BOOT_MODE="${BOOT_MODE:-production}"

# 版本信息
export MACHINENATIVEOPS_VERSION="v1.0.0"
export CONTROLPLANE_VERSION="v1.0.0"

echo "✅ MachineNativeOps Taxonomy Root Layer 環境已加載"
echo "   Controlplane: ${CONTROLPLANE_PATH}"
echo "   Workspace: ${WORKSPACE_PATH}"
echo "   Boot Mode: ${BOOT_MODE}"

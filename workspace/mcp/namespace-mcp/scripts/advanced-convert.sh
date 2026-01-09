#!/bin/bash
# MachineNativeOps 高級命名空間 MCP 轉換腳本 (佔位版)
# 版本: 1.0.0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJECT_ROOT/src"

usage() {
    cat <<EOF
用法: $0 <source_path> <target_path> [--config <path>] [--disable-semantic] [--verbose]
說明: 薄封裝高級轉換器入口，預設啟用語意層，可透過 --disable-semantic 關閉。
EOF
}

if [ $# -lt 2 ]; then
    usage
    exit 1
fi

SOURCE_PATH="$1"
TARGET_PATH="$2"
shift 2

EXTRA_ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --config|-c)
            EXTRA_ARGS+=("--config" "$2")
            shift 2
            ;;
        --disable-semantic)
            EXTRA_ARGS+=("--disable-semantic")
            shift
            ;;
        --verbose|-v)
            EXTRA_ARGS+=("--verbose")
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "未知參數: $1"
            usage
            exit 1
            ;;
    esac
done

if ! command -v python3 >/dev/null 2>&1; then
    echo "未找到 python3，請先安裝 Python 3.8+"
    exit 1
fi

if [ ${#EXTRA_ARGS[@]} -eq 0 ]; then
    python3 "$SRC_DIR/advanced_converter.py" "$SOURCE_PATH" "$TARGET_PATH"
else
    python3 "$SRC_DIR/advanced_converter.py" "$SOURCE_PATH" "$TARGET_PATH" "${EXTRA_ARGS[@]}"
fi

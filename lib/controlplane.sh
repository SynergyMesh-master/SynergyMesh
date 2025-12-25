#!/usr/bin/env bash
# Controlplane Shell 配置庫
# 提供 Shell 函數讓 bash 腳本使用 controlplane 配置

# 顏色定義
readonly CP_COLOR_RESET='\033[0m'
readonly CP_COLOR_RED='\033[0;31m'
readonly CP_COLOR_GREEN='\033[0;32m'
readonly CP_COLOR_YELLOW='\033[1;33m'
readonly CP_COLOR_BLUE='\033[0;34m'

# 找到儲存庫根目錄
cp_find_repo_root() {
    local current_dir="$PWD"
    while [[ "$current_dir" != "/" ]]; do
        if [[ -d "$current_dir/.git" ]]; then
            echo "$current_dir"
            return 0
        fi
        current_dir="$(dirname "$current_dir")"
    done
    echo "$PWD"
}

# 初始化 controlplane 路徑
CP_REPO_ROOT="${CP_REPO_ROOT:-$(cp_find_repo_root)}"
CP_BASELINE_PATH="${CP_BASELINE_PATH:-$CP_REPO_ROOT/controlplane/baseline}"
CP_OVERLAY_PATH="${CP_OVERLAY_PATH:-$CP_REPO_ROOT/controlplane/overlay}"
CP_ACTIVE_PATH="${CP_ACTIVE_PATH:-$CP_REPO_ROOT/controlplane/active}"

# 日誌函數
cp_log_info() {
    echo -e "${CP_COLOR_BLUE}ℹ${CP_COLOR_RESET} $*"
}

cp_log_success() {
    echo -e "${CP_COLOR_GREEN}✓${CP_COLOR_RESET} $*"
}

cp_log_warning() {
    echo -e "${CP_COLOR_YELLOW}⚠${CP_COLOR_RESET} $*"
}

cp_log_error() {
    echo -e "${CP_COLOR_RED}✗${CP_COLOR_RESET} $*" >&2
}

# 檢查 controlplane 是否存在
cp_check_exists() {
    if [[ ! -d "$CP_BASELINE_PATH" ]]; then
        cp_log_error "Controlplane baseline not found at: $CP_BASELINE_PATH"
        return 1
    fi
    return 0
}

# 獲取 YAML 配置值 (使用 yq 或 python)
cp_get_yaml_value() {
    local yaml_file="$1"
    local key_path="$2"
    local default_value="${3:-}"
    
    if [[ -z "$yaml_file" || -z "$key_path" || ! -f "$yaml_file" ]]; then
        echo "$default_value"
        return 1
    fi
    
    # 優先 yq
    if command -v yq >/dev/null 2>&1; then
        local value
        value="$(yq eval "$key_path" "$yaml_file" 2>/dev/null)"
        if [[ -n "$value" && "$value" != "null" ]]; then
            echo "$value"
            return 0
        fi
    fi
    
    # Python fallback（dot path）
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$yaml_file" "$key_path" "$default_value" <<'PY'
import sys, json
try:
    import yaml
except Exception:
    print(sys.argv[3])
    sys.exit(1)

yaml_file, key_path, default_value = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
except Exception:
    print(default_value)
    sys.exit(1)

value = data
for key in key_path.split("."):
    if isinstance(value, dict) and key in value:
        value = value[key]
    else:
        value = None
        break

if value is None:
    print(default_value)
    sys.exit(1)

# scalar -> print as is; list/dict -> json string
if isinstance(value, (dict, list)):
    print(json.dumps(value, ensure_ascii=False))
else:
    print(value)
sys.exit(0)
PY
        return $?
    fi
    
    echo "$default_value"
    return 1
}

# 獲取 baseline 配置
cp_get_baseline_config() {
    local config_name="$1"
    local key_path="${2:-}"
    local default_value="${3:-}"
    
    local config_file="$CP_BASELINE_PATH/config/$config_name"
    
    if [[ -z "$key_path" ]]; then
        cat "$config_file" 2>/dev/null
    else
        cp_get_yaml_value "$config_file" "$key_path" "$default_value"
    fi
}

# 獲取規範
cp_get_specification() {
    local spec_name="$1"
    local key_path="${2:-}"
    local default_value="${3:-}"
    
    local spec_file="$CP_BASELINE_PATH/specifications/$spec_name"
    
    if [[ -z "$key_path" ]]; then
        cat "$spec_file" 2>/dev/null
    else
        cp_get_yaml_value "$spec_file" "$key_path" "$default_value"
    fi
}

# 獲取註冊表
cp_get_registry() {
    local registry_name="$1"
    local key_path="${2:-}"
    local default_value="${3:-}"
    
    local registry_file="$CP_BASELINE_PATH/registries/$registry_name"
    
    if [[ -z "$key_path" ]]; then
        cat "$registry_file" 2>/dev/null
    else
        cp_get_yaml_value "$registry_file" "$key_path" "$default_value"
    fi
}

# 驗證名稱是否符合 kebab-case
cp_validate_name() {
    local name="$1"
    local name_type="${2:-file}"
    
    case "$name_type" in
        file)
            # 檢查 kebab-case，允許以點分段的名稱（仍保守）
            if [[ ! "$name" =~ ^[a-z][a-z0-9-]*(\.[a-z0-9-]+)*$ ]]; then
                cp_log_error "File name must be kebab-case (dots allowed as segments): $name"
                return 1
            fi

            # 明確禁止雙副檔名封裝
            if [[ "$name" =~ \.(yaml|yml|json|toml|sh)\.txt$ ]]; then
                cp_log_error "Forbidden double-extension wrapper (use a single real extension): $name"
                return 1
            fi

            # 檢查雙重擴展名（多個 dot）
            local dot_count
            dot_count="$(echo "$name" | tr -cd '.' | wc -c | tr -d ' ')"

            if [[ $dot_count -gt 1 ]]; then
                # 從 baseline 讀取多段檔名允許清單（預設 []）
                local rules_json
                rules_json="$(cp_get_baseline_config "root.naming-policy.yaml" "naming.file.multi_dot_allow_regexes" "[]")"

                local allowed="false"
                if command -v python3 >/dev/null 2>&1; then
                    allowed="$(PYTHONPATH="$CP_REPO_ROOT/lib:${PYTHONPATH:-}" python3 - "$name" "$rules_json" <<'PY'
import sys
from controlplane import validate_name_allowlist
name = sys.argv[1]
raw = sys.argv[2]
print("true" if validate_name_allowlist(name, raw) else "false")
PY
)"
                fi

                # 若未命中 allowlist：回退到現行保守允許（維持既有行為）
                if [[ "$allowed" != "true" ]]; then
                    if [[ "$name" =~ ^root\.[a-z][a-z0-9-]*\.(yaml|yml|map|sh)$ ]]; then
                        : # 允許此格式（保守回退）
                    else
                        cp_log_error "File has double extension (forbidden): $name"
                        return 1
                    fi
                fi
            fi
            ;;
            
        directory)
            if [[ ! "$name" =~ ^[a-z][a-z0-9-]*$ ]]; then
                cp_log_error "Directory name must be kebab-case: $name"
                return 1
            fi
            ;;
            
        namespace)
            if [[ ! "$name" =~ ^[a-z][a-z0-9-]*$ ]]; then
                cp_log_error "Namespace must be kebab-case without dots: $name"
                return 1
            fi
            
            if [[ "$name" == *.* ]]; then
                cp_log_error "Namespace contains dots (use hyphens): $name"
                return 1
            fi
            ;;
            
        module)
            if [[ ! "$name" =~ ^[a-z][a-z0-9-]*$ ]]; then
                cp_log_error "Module name must be kebab-case: $name"
                return 1
            fi
            ;;
    esac
    
    return 0
}

# 運行驗證
cp_run_validation() {
    local verbose="${1:-false}"
    
    cp_log_info "Running controlplane validation..."
    
    local validator_script="$CP_BASELINE_PATH/validation/validate-root-specs.py"
    
    if [[ ! -f "$validator_script" ]]; then
        cp_log_error "Validator script not found: $validator_script"
        return 1
    fi
    
    if [[ "$verbose" == "true" ]]; then
        python3 "$validator_script" --verbose
    else
        python3 "$validator_script"
    fi
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        cp_log_success "Validation passed"
    else
        cp_log_error "Validation failed"
    fi
    
    return $exit_code
}

# 顯示 controlplane 狀態
cp_show_status() {
    echo "🎛️  Controlplane Status"
    echo "============================================================"
    echo "📁 Repository Root: $CP_REPO_ROOT"
    echo "📋 Baseline Path: $CP_BASELINE_PATH"
    echo "📝 Overlay Path: $CP_OVERLAY_PATH"
    echo "⚡ Active Path: $CP_ACTIVE_PATH"
    echo ""
    
    echo "Directory Status:"
    if [[ -d "$CP_BASELINE_PATH" ]]; then
        echo "  Baseline: ✅ Exists"
    else
        echo "  Baseline: ❌ Not found"
    fi
    
    if [[ -d "$CP_OVERLAY_PATH" ]]; then
        echo "  Overlay:  ✅ Exists"
    else
        echo "  Overlay:  ❌ Not found"
    fi
    
    if [[ -d "$CP_ACTIVE_PATH" ]]; then
        echo "  Active:   ✅ Exists"
    else
        echo "  Active:   ❌ Not found"
    fi
    
    if [[ -d "$CP_BASELINE_PATH" ]]; then
        echo ""
        echo "Baseline Content:"
        local config_count=$(find "$CP_BASELINE_PATH/config" -name "*.yaml" 2>/dev/null | wc -l)
        local spec_count=$(find "$CP_BASELINE_PATH/specifications" -name "*.yaml" 2>/dev/null | wc -l)
        local reg_count=$(find "$CP_BASELINE_PATH/registries" -name "*.yaml" 2>/dev/null | wc -l)
        
        echo "  Config files: $config_count"
        echo "  Spec files: $spec_count"
        echo "  Registry files: $reg_count"
    fi
}

# 合成 active 視圖
cp_synthesize_active() {
    cp_log_info "Synthesizing active view..."
    
    # 創建 active 目錄
    mkdir -p "$CP_ACTIVE_PATH"
    
    # 複製 baseline 配置
    if [[ -d "$CP_BASELINE_PATH/config" ]]; then
        # 使用 nullglob 確保沒有匹配時不會把萬用字元當成字串傳給 cp
        shopt -s nullglob
        local yaml_files=("$CP_BASELINE_PATH"/config/*.yaml)
        if ((${#yaml_files[@]} > 0)); then
            cp -r "${yaml_files[@]}" "$CP_ACTIVE_PATH/"
        else
            cp_log_info "No baseline YAML config files found in $CP_BASELINE_PATH/config"
        fi
        shopt -u nullglob
    fi
    
    # TODO: 合併 overlay 配置 (需要更複雜的邏輯)
    
    cp_log_success "Active view synthesized to: $CP_ACTIVE_PATH"
}

# 獲取命名規則
cp_get_naming_rules() {
    cp_get_baseline_config "root.naming-policy.yaml"
}

# 獲取治理策略
cp_get_governance_policy() {
    cp_get_baseline_config "root.governance.yaml"
}

# 獲取信任策略
cp_get_trust_policy() {
    cp_get_baseline_config "root.trust.yaml"
}

# 檢查是否為不可變
cp_is_baseline_immutable() {
    local immutable=$(cp_get_baseline_config "root.config.yaml" "metadata.annotations.machinenativeops.io/immutable" "false")
    [[ "$immutable" == "true" ]]
}

# 導出環境變量
cp_export_env() {
    export CP_REPO_ROOT
    export CP_BASELINE_PATH
    export CP_OVERLAY_PATH
    export CP_ACTIVE_PATH
    
    export CP_BASELINE_CONFIG="$CP_BASELINE_PATH/config"
    export CP_BASELINE_SPECS="$CP_BASELINE_PATH/specifications"
    export CP_BASELINE_REGISTRIES="$CP_BASELINE_PATH/registries"
    export CP_BASELINE_INTEGRATION="$CP_BASELINE_PATH/integration"
    export CP_BASELINE_VALIDATION="$CP_BASELINE_PATH/validation"
    export CP_BASELINE_DOCS="$CP_BASELINE_PATH/documentation"
    
    export CP_OVERLAY_CONFIG="$CP_OVERLAY_PATH/config"
    export CP_OVERLAY_EVIDENCE="$CP_OVERLAY_PATH/evidence"
    export CP_OVERLAY_RUNTIME="$CP_OVERLAY_PATH/runtime"
    export CP_OVERLAY_LOGS="$CP_OVERLAY_PATH/logs"
    
    cp_log_success "Controlplane environment variables exported"
}

# 使用示例
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 直接執行時顯示示例
    echo "📚 Controlplane Shell Library"
    echo "============================================================"
    echo ""
    echo "Usage: source lib/controlplane.sh"
    echo ""
    echo "Available functions:"
    echo "  cp_check_exists              - Check if controlplane exists"
    echo "  cp_show_status               - Show controlplane status"
    echo "  cp_get_baseline_config       - Get baseline config"
    echo "  cp_get_specification         - Get specification"
    echo "  cp_get_registry              - Get registry"
    echo "  cp_validate_name             - Validate name format"
    echo "  cp_run_validation            - Run validation"
    echo "  cp_synthesize_active         - Synthesize active view"
    echo "  cp_export_env                - Export environment variables"
    echo ""
    echo "Example:"
    echo "  source lib/controlplane.sh"
    echo "  cp_show_status"
    echo "  cp_validate_name 'my-file.yaml' 'file'"
    echo "  cp_run_validation"
fi

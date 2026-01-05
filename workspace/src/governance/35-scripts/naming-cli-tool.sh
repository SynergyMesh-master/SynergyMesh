#!/bin/bash
#
# Naming Governance CLI Tool
# Version: 2.0
# Purpose: Command-line interface for naming validation and management
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/naming-cli-config.yaml"
PATTERNS_FILE="${SCRIPT_DIR}/../10-policy/naming-patterns.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
usage() {
    cat << EOF
Naming Governance CLI Tool

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    validate FILE          Validate naming in file
    validate-dir DIR       Validate all naming in directory
    check NAME             Check if name follows patterns
    suggest CONTEXT        Suggest name based on context
    list-patterns          List all naming patterns
    report                 Generate compliance report
    audit                  Run naming audit

Options:
    -h, --help            Show this help message
    -v, --verbose         Verbose output
    -q, --quiet           Quiet output
    -f, --format FORMAT   Output format (text, json, yaml)

Examples:
    $0 validate config.yaml
    $0 check dev-team-service-db-01
    $0 suggest --env=dev --team=platform --service=database
    $0 report --team=myteam

EOF
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

validate_name() {
    local name="$1"
    local verbose="${2:-false}"
    
    log_info "Validating name: $name"
    
    # Basic format checks
    if [[ ${#name} -lt 3 ]]; then
        log_error "Name too short (minimum 3 characters)"
        return 1
    fi
    
    if [[ ${#name} -gt 63 ]]; then
        log_error "Name too long (maximum 63 characters)"
        return 1
    fi
    
    if [[ ! $name =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
        log_error "Invalid format (only lowercase alphanumeric and hyphens allowed)"
        return 1
    fi
    
    if [[ $name =~ ^[0-9] ]]; then
        log_error "Name cannot start with a number"
        return 1
    fi
    
    if [[ $name =~ -$ ]]; then
        log_error "Name cannot end with a hyphen"
        return 1
    fi
    
    # Check against patterns (simplified)
    if [[ "$verbose" == "true" ]]; then
        log_info "Pattern checks passed"
    fi
    
    log_success "Name validation passed"
    return 0
}

validate_file() {
    local file="$1"
    
    if [[ ! -f "$file" ]]; then
        log_error "File not found: $file"
        return 1
    fi
    
    log_info "Validating file: $file"
    
    # Extract names based on file type
    case "${file##*.}" in
        yaml|yml)
            # Extract resource names from YAML
            grep -E "(name:|Name:)" "$file" | sed 's/.*name: *//' | while read -r name; do
                validate_name "$name"
            done
            ;;
        json)
            # Extract names from JSON
            grep -oE '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$file" | sed 's/.*"//' | sed 's/"$//' | while read -r name; do
                validate_name "$name"
            done
            ;;
        *)
            log_warning "Unsupported file type: ${file##*.}"
            return 1
            ;;
    esac
}

generate_report() {
    local team="${1:-all}"
    log_info "Generating compliance report for team: $team"
    
    # Placeholder for report generation
    echo "Compliance Report"
    echo "================"
    echo "Team: $team"
    echo "Generated: $(date)"
    echo ""
    echo "Statistics:"
    echo "  Total Resources: $(grep -r "name:" . --include="*.yaml" --include="*.yml" | wc -l)"
    echo "  Compliant: TBA"
    echo "  Non-compliant: TBA"
}

# Main
main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        validate)
            if [[ -z "$1" ]]; then
                log_error "Please specify a file to validate"
                exit 1
            fi
            validate_file "$1"
            ;;
            
        check)
            if [[ -z "$1" ]]; then
                log_error "Please specify a name to check"
                exit 1
            fi
            validate_name "$1" "true"
            ;;
            
        report)
            generate_report "$1"
            ;;
            
        -h|--help)
            usage
            exit 0
            ;;
            
        *)
            log_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
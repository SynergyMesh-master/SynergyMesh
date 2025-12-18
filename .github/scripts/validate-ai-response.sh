#!/bin/bash
# AI Behavior Contract Validator
# Checks AI responses and commit messages for compliance with .github/AI-BEHAVIOR-CONTRACT.md

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contract violation patterns
VAGUE_PHRASES=(
  "seems to be"
  "might be"
  "might not"
  "appears to"
  "possibly"
  "perhaps"
  "probably"
  "maybe"
  "could be"
  "may have"
)

# Check if input is provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 <text-to-validate>"
  echo "       or: $0 --file <file-path>"
  echo "       or: $0 --commit <commit-sha>"
  exit 1
fi

# Initialize counters
violations=0
warnings=0

# Function to check for vague phrases
check_vague_language() {
  local text="$1"
  local found=0
  
  echo -e "\n${YELLOW}Checking for vague language (Contract Section 1)...${NC}"
  
  for phrase in "${VAGUE_PHRASES[@]}"; do
    if echo "$text" | grep -qi "$phrase"; then
      echo -e "${RED}  ✗ VIOLATION: Found prohibited phrase: '$phrase'${NC}"
      violations=$((violations + 1))
      found=1
    fi
  done
  
  if [ $found -eq 0 ]; then
    echo -e "${GREEN}  ✓ No vague language detected${NC}"
  fi
}

# Function to check for binary response structure
check_binary_response() {
  local text="$1"
  
  echo -e "\n${YELLOW}Checking for binary response structure (Contract Section 2)...${NC}"
  
  if echo "$text" | grep -qi "can_complete\|cannot_complete"; then
    echo -e "${GREEN}  ✓ Binary response structure found${NC}"
  elif echo "$text" | grep -qi "status:[[:space:]]*\(can\|cannot\)"; then
    echo -e "${GREEN}  ✓ Binary response structure found${NC}"
  else
    echo -e "${YELLOW}  ⚠ WARNING: No clear binary response (CAN_COMPLETE/CANNOT_COMPLETE)${NC}"
    warnings=$((warnings + 1))
  fi
  
  # Check for missing resources declaration when cannot complete
  if echo "$text" | grep -qi "cannot_complete\|cannot complete"; then
    if echo "$text" | grep -qi "missing.*:\|required.*:\|needed:\|blocking"; then
      echo -e "${GREEN}  ✓ Missing resources properly declared${NC}"
    else
      echo -e "${RED}  ✗ VIOLATION: CANNOT_COMPLETE without specific missing resources${NC}"
      violations=$((violations + 1))
    fi
  fi
}

# Function to check for task decomposition
check_task_decomposition() {
  local text="$1"
  
  echo -e "\n${YELLOW}Checking for task decomposition (Contract Section 3)...${NC}"
  
  if echo "$text" | grep -qi "too large\|too complex\|cannot handle"; then
    # Task size concern mentioned - check for decomposition
    if echo "$text" | grep -qi "subtask\|sub-task\|step 1\|task 1\|breakdown"; then
      echo -e "${GREEN}  ✓ Task properly decomposed${NC}"
    else
      echo -e "${RED}  ✗ VIOLATION: Task size concern without decomposition${NC}"
      violations=$((violations + 1))
    fi
  else
    echo -e "${GREEN}  ✓ No decomposition issues detected${NC}"
  fi
}

# Function to check for draft mode declaration
check_draft_mode() {
  local text="$1"
  
  echo -e "\n${YELLOW}Checking for draft mode compliance (Contract Section 4)...${NC}"
  
  if echo "$text" | grep -qi "will update\|will modify\|will change\|going to write"; then
    # Indicates file modification intent
    if echo "$text" | grep -qi "draft\|proposed\|suggestion\|for your review"; then
      echo -e "${GREEN}  ✓ Draft mode properly declared${NC}"
    else
      echo -e "${YELLOW}  ⚠ WARNING: File modification without explicit draft mode declaration${NC}"
      warnings=$((warnings + 1))
    fi
  else
    echo -e "${GREEN}  ✓ No draft mode issues detected${NC}"
  fi
}

# Main validation logic
validate_text() {
  local text="$1"
  
  echo -e "${GREEN}=== AI Behavior Contract Validation ===${NC}"
  echo "Validating against: .github/AI-BEHAVIOR-CONTRACT.md"
  echo ""
  
  check_vague_language "$text"
  check_binary_response "$text"
  check_task_decomposition "$text"
  check_draft_mode "$text"
  
  echo -e "\n${GREEN}=== Validation Summary ===${NC}"
  echo -e "Violations: ${RED}$violations${NC}"
  echo -e "Warnings: ${YELLOW}$warnings${NC}"
  
  if [ $violations -eq 0 ]; then
    if [ $warnings -eq 0 ]; then
      echo -e "\n${GREEN}✓ Contract compliance validated successfully!${NC}"
      return 0
    else
      echo -e "\n${YELLOW}⚠ Compliance check passed with warnings${NC}"
      return 0
    fi
  else
    echo -e "\n${RED}✗ Contract violations detected. Please review and fix.${NC}"
    return 1
  fi
}

# Parse arguments
case "$1" in
  --file)
    if [ ! -f "$2" ]; then
      echo "Error: File not found: $2"
      exit 1
    fi
    text=$(cat "$2")
    validate_text "$text"
    ;;
  --commit)
    text=$(git log -1 --pretty=%B "$2" 2>/dev/null || echo "")
    if [ -z "$text" ]; then
      echo "Error: Could not retrieve commit message for: $2"
      exit 1
    fi
    validate_text "$text"
    ;;
  *)
    # Treat as direct text input
    validate_text "$1"
    ;;
esac

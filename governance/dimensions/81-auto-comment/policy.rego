# =============================================================================
# SynergyMesh Governance - Auto Comment Policy
# 81-auto-comment: OPA Rego Policy
# =============================================================================

package governance.dimensions.auto_comment

import future.keywords.in
import future.keywords.if
import future.keywords.contains

# =============================================================================
# DEFAULT DENY
# =============================================================================
default allow := false

# =============================================================================
# MAIN ALLOW RULE
# =============================================================================
allow if {
    valid_workflow_context
    valid_comment_format
    not blocked_by_policy
}

# =============================================================================
# WORKFLOW CONTEXT VALIDATION
# =============================================================================
valid_workflow_context if {
    input.workflow_context.workflow != ""
    input.workflow_context.run_id != ""
    input.workflow_context.commit != ""
}

# =============================================================================
# COMMENT FORMAT VALIDATION
# =============================================================================
valid_comment_format if {
    input.comment.format == "markdown"
    count(input.comment.content) > 0
    count(input.comment.content) < 65536  # Max comment size
}

# =============================================================================
# POLICY BLOCKING RULES
# =============================================================================
blocked_by_policy if {
    input.error_type == "security_vulnerability"
    not input.security_review_approved
}

blocked_by_policy if {
    input.auto_fix_requested
    not auto_fix_allowed
}

# =============================================================================
# AUTO-FIX POLICY
# =============================================================================
auto_fix_allowed if {
    input.error_type in auto_fixable_error_types
    input.branch != "main"
    input.branch != "master"
}

auto_fixable_error_types := {
    "eslint",
    "prettier",
    "yamllint",
    "markdownlint",
    "formatting"
}

# =============================================================================
# ERROR CLASSIFICATION
# =============================================================================
error_requires_manual_review if {
    input.error_type in manual_review_error_types
}

manual_review_error_types := {
    "typescript_error",
    "test_failure",
    "security_vulnerability",
    "api_contract_violation",
    "build_failure"
}

# =============================================================================
# EVENT REGISTRY REQUIREMENTS
# =============================================================================
event_record_valid if {
    input.event.id != ""
    input.event.type == "auto-comment"
    input.event.timestamp != ""
    input.event.workflow != ""
    input.event.commit != ""
}

# =============================================================================
# COMMENT RATE LIMITING
# =============================================================================
rate_limit_exceeded if {
    input.recent_comments_count > 10
    input.time_window_minutes < 60
}

# =============================================================================
# HELPER RULES
# =============================================================================
is_production_branch if {
    input.branch in {"main", "master", "production"}
}

is_protected_workflow if {
    input.workflow in protected_workflows
}

protected_workflows := {
    "CI Pipeline",
    "Security Scan",
    "Deploy Production"
}

# =============================================================================
# AUDIT REQUIREMENTS
# =============================================================================
audit_required if {
    input.auto_fix_performed
}

audit_required if {
    is_production_branch
}

audit_required if {
    is_protected_workflow
}

# =============================================================================
# VIOLATION MESSAGES
# =============================================================================
violations contains msg if {
    not valid_workflow_context
    msg := "Invalid workflow context: missing required fields (workflow, run_id, commit)"
}

violations contains msg if {
    not valid_comment_format
    msg := "Invalid comment format: must be markdown with content size < 64KB"
}

violations contains msg if {
    blocked_by_policy
    input.error_type == "security_vulnerability"
    msg := "Security vulnerabilities require manual review before auto-comment"
}

violations contains msg if {
    input.auto_fix_requested
    not auto_fix_allowed
    msg := "Auto-fix not allowed: error type not auto-fixable or branch is protected"
}

violations contains msg if {
    rate_limit_exceeded
    msg := "Rate limit exceeded: too many comments in time window"
}

# =============================================================================
# RECOMMENDATIONS
# =============================================================================
recommendations contains rec if {
    error_requires_manual_review
    rec := {
        "type": "manual_review",
        "message": "This error type requires manual review",
        "error_type": input.error_type
    }
}

recommendations contains rec if {
    auto_fix_allowed
    not input.auto_fix_performed
    rec := {
        "type": "auto_fix_available",
        "message": "Auto-fix is available for this error type",
        "error_type": input.error_type
    }
}

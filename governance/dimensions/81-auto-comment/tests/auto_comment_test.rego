# =============================================================================
# SynergyMesh Governance - Auto Comment Policy Tests
# 81-auto-comment: OPA Rego Policy Tests
# =============================================================================

package governance.dimensions.auto_comment_test

import data.governance.dimensions.auto_comment
import future.keywords.in

# =============================================================================
# TEST: VALID WORKFLOW CONTEXT
# =============================================================================

test_valid_workflow_context_allow {
    auto_comment.valid_workflow_context with input as {
        "workflow_context": {
            "workflow": "CI Pipeline",
            "run_id": "12345",
            "commit": "abc123def"
        }
    }
}

test_invalid_workflow_context_missing_workflow {
    not auto_comment.valid_workflow_context with input as {
        "workflow_context": {
            "workflow": "",
            "run_id": "12345",
            "commit": "abc123def"
        }
    }
}

test_invalid_workflow_context_missing_run_id {
    not auto_comment.valid_workflow_context with input as {
        "workflow_context": {
            "workflow": "CI Pipeline",
            "run_id": "",
            "commit": "abc123def"
        }
    }
}

test_invalid_workflow_context_missing_commit {
    not auto_comment.valid_workflow_context with input as {
        "workflow_context": {
            "workflow": "CI Pipeline",
            "run_id": "12345",
            "commit": ""
        }
    }
}

# =============================================================================
# TEST: VALID COMMENT FORMAT
# =============================================================================

test_valid_comment_format {
    auto_comment.valid_comment_format with input as {
        "comment": {
            "format": "markdown",
            "content": "This is a test comment"
        }
    }
}

test_invalid_comment_format_not_markdown {
    not auto_comment.valid_comment_format with input as {
        "comment": {
            "format": "html",
            "content": "This is a test comment"
        }
    }
}

test_invalid_comment_format_empty_content {
    not auto_comment.valid_comment_format with input as {
        "comment": {
            "format": "markdown",
            "content": ""
        }
    }
}

# =============================================================================
# TEST: AUTO-FIX POLICY
# =============================================================================

test_auto_fix_allowed_eslint {
    auto_comment.auto_fix_allowed with input as {
        "error_type": "eslint",
        "branch": "feature/test"
    }
}

test_auto_fix_allowed_prettier {
    auto_comment.auto_fix_allowed with input as {
        "error_type": "prettier",
        "branch": "feature/test"
    }
}

test_auto_fix_not_allowed_main_branch {
    not auto_comment.auto_fix_allowed with input as {
        "error_type": "eslint",
        "branch": "main"
    }
}

test_auto_fix_not_allowed_master_branch {
    not auto_comment.auto_fix_allowed with input as {
        "error_type": "prettier",
        "branch": "master"
    }
}

test_auto_fix_not_allowed_typescript_error {
    not auto_comment.auto_fix_allowed with input as {
        "error_type": "typescript_error",
        "branch": "feature/test"
    }
}

# =============================================================================
# TEST: ERROR CLASSIFICATION
# =============================================================================

test_error_requires_manual_review_typescript {
    auto_comment.error_requires_manual_review with input as {
        "error_type": "typescript_error"
    }
}

test_error_requires_manual_review_test_failure {
    auto_comment.error_requires_manual_review with input as {
        "error_type": "test_failure"
    }
}

test_error_requires_manual_review_security {
    auto_comment.error_requires_manual_review with input as {
        "error_type": "security_vulnerability"
    }
}

test_error_not_requires_manual_review_eslint {
    not auto_comment.error_requires_manual_review with input as {
        "error_type": "eslint"
    }
}

# =============================================================================
# TEST: BLOCKED BY POLICY
# =============================================================================

test_blocked_security_without_review {
    auto_comment.blocked_by_policy with input as {
        "error_type": "security_vulnerability",
        "security_review_approved": false
    }
}

test_not_blocked_security_with_review {
    not auto_comment.blocked_by_policy with input as {
        "error_type": "security_vulnerability",
        "security_review_approved": true
    }
}

test_blocked_auto_fix_on_main {
    auto_comment.blocked_by_policy with input as {
        "auto_fix_requested": true,
        "error_type": "eslint",
        "branch": "main"
    }
}

# =============================================================================
# TEST: EVENT RECORD VALIDATION
# =============================================================================

test_event_record_valid {
    auto_comment.event_record_valid with input as {
        "event": {
            "id": "auto-comment-123",
            "type": "auto-comment",
            "timestamp": "2025-12-12T00:00:00Z",
            "workflow": "CI Pipeline",
            "commit": "abc123"
        }
    }
}

test_event_record_invalid_missing_id {
    not auto_comment.event_record_valid with input as {
        "event": {
            "id": "",
            "type": "auto-comment",
            "timestamp": "2025-12-12T00:00:00Z",
            "workflow": "CI Pipeline",
            "commit": "abc123"
        }
    }
}

test_event_record_invalid_wrong_type {
    not auto_comment.event_record_valid with input as {
        "event": {
            "id": "auto-comment-123",
            "type": "other-type",
            "timestamp": "2025-12-12T00:00:00Z",
            "workflow": "CI Pipeline",
            "commit": "abc123"
        }
    }
}

# =============================================================================
# TEST: RATE LIMITING
# =============================================================================

test_rate_limit_exceeded {
    auto_comment.rate_limit_exceeded with input as {
        "recent_comments_count": 15,
        "time_window_minutes": 30
    }
}

test_rate_limit_not_exceeded {
    not auto_comment.rate_limit_exceeded with input as {
        "recent_comments_count": 5,
        "time_window_minutes": 30
    }
}

test_rate_limit_not_exceeded_longer_window {
    not auto_comment.rate_limit_exceeded with input as {
        "recent_comments_count": 15,
        "time_window_minutes": 120
    }
}

# =============================================================================
# TEST: BRANCH PROTECTION
# =============================================================================

test_is_production_branch_main {
    auto_comment.is_production_branch with input as {
        "branch": "main"
    }
}

test_is_production_branch_master {
    auto_comment.is_production_branch with input as {
        "branch": "master"
    }
}

test_is_production_branch_production {
    auto_comment.is_production_branch with input as {
        "branch": "production"
    }
}

test_is_not_production_branch_feature {
    not auto_comment.is_production_branch with input as {
        "branch": "feature/test"
    }
}

# =============================================================================
# TEST: AUDIT REQUIREMENTS
# =============================================================================

test_audit_required_auto_fix {
    auto_comment.audit_required with input as {
        "auto_fix_performed": true,
        "branch": "feature/test",
        "workflow": "test-workflow"
    }
}

test_audit_required_production_branch {
    auto_comment.audit_required with input as {
        "auto_fix_performed": false,
        "branch": "main",
        "workflow": "test-workflow"
    }
}

test_audit_required_protected_workflow {
    auto_comment.audit_required with input as {
        "auto_fix_performed": false,
        "branch": "feature/test",
        "workflow": "CI Pipeline"
    }
}

# =============================================================================
# TEST: FULL ALLOW RULE
# =============================================================================

test_allow_valid_request {
    auto_comment.allow with input as {
        "workflow_context": {
            "workflow": "CI Pipeline",
            "run_id": "12345",
            "commit": "abc123def"
        },
        "comment": {
            "format": "markdown",
            "content": "This is a test comment"
        },
        "error_type": "eslint",
        "branch": "feature/test"
    }
}

test_deny_invalid_workflow_context {
    not auto_comment.allow with input as {
        "workflow_context": {
            "workflow": "",
            "run_id": "12345",
            "commit": "abc123def"
        },
        "comment": {
            "format": "markdown",
            "content": "This is a test comment"
        }
    }
}

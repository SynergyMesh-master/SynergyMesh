# =============================================================================
# OPA Tests: 99-metadata - Metadata Management Center
# =============================================================================
# Purpose: Test metadata governance policies
# Version: 1.0.0
# =============================================================================

package machinenativeops.governance.metadata

import future.keywords.if

# =============================================================================
# TEST: Metadata Classification
# =============================================================================

test_metadata_classification_required if {
    result := deny with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "test-metadata",
            "name": "Test Metadata"
        }
    }
    count(result) > 0
}

test_metadata_classification_valid if {
    result := deny with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "test-metadata",
            "name": "Test Metadata",
            "classification": "technical"
        },
        "spec": {
            "attributes": {}
        }
    }
    count([r | r := result[_]; contains(r, "classification")]) == 0
}

test_metadata_classification_invalid if {
    result := deny with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "test-metadata",
            "name": "Test Metadata",
            "classification": "invalid-type"
        }
    }
    count(result) > 0
}

# =============================================================================
# TEST: Lineage Graph DAG Validation
# =============================================================================

test_lineage_graph_no_nodes if {
    result := deny with input as {
        "kind": "LineageGraph",
        "metadata": {
            "id": "test-lineage",
            "name": "Test Lineage",
            "classification": "operational"
        },
        "spec": {
            "nodes": [],
            "edges": []
        }
    }
    count(result) > 0
}

test_lineage_graph_valid_dag if {
    result := deny with input as {
        "kind": "LineageGraph",
        "metadata": {
            "id": "test-lineage",
            "name": "Test Lineage",
            "classification": "operational"
        },
        "spec": {
            "nodes": [
                {"id": "node1", "type": "source"},
                {"id": "node2", "type": "target"}
            ],
            "edges": [
                {"source": "node1", "target": "node2", "relationship": "produces"}
            ]
        }
    }
    count([r | r := result[_]; contains(r, "cycle")]) == 0
}

test_lineage_graph_invalid_node_reference if {
    result := deny with input as {
        "kind": "LineageGraph",
        "metadata": {
            "id": "test-lineage",
            "name": "Test Lineage",
            "classification": "operational"
        },
        "spec": {
            "nodes": [
                {"id": "node1", "type": "source"}
            ],
            "edges": [
                {"source": "node1", "target": "node2", "relationship": "produces"}
            ]
        }
    }
    count(result) > 0
}

# =============================================================================
# TEST: Provenance Record Validation
# =============================================================================

test_provenance_record_required_fields if {
    result := deny with input as {
        "kind": "ProvenanceRecord",
        "metadata": {
            "id": "test-provenance",
            "name": "Test Provenance",
            "classification": "governance"
        },
        "spec": {}
    }
    count(result) >= 3  # Should have at least 3 errors (source, timestamp, actor)
}

test_provenance_record_valid if {
    result := deny with input as {
        "kind": "ProvenanceRecord",
        "metadata": {
            "id": "test-provenance",
            "name": "Test Provenance",
            "classification": "governance"
        },
        "spec": {
            "source": {
                "type": "git",
                "repository": "https://github.com/example/repo",
                "commit": "abc123"
            },
            "timestamp": "2025-12-19T00:00:00Z",
            "actor": {
                "type": "human",
                "id": "user123",
                "name": "John Doe"
            }
        }
    }
    count(result) == 0
}

# =============================================================================
# TEST: Knowledge Graph Validation
# =============================================================================

test_knowledge_graph_no_entities if {
    result := deny with input as {
        "kind": "KnowledgeGraph",
        "metadata": {
            "id": "test-knowledge",
            "name": "Test Knowledge Graph",
            "classification": "operational"
        },
        "spec": {
            "entities": [],
            "relationships": []
        }
    }
    count(result) > 0
}

test_knowledge_graph_valid if {
    result := deny with input as {
        "kind": "KnowledgeGraph",
        "metadata": {
            "id": "test-knowledge",
            "name": "Test Knowledge Graph",
            "classification": "operational"
        },
        "spec": {
            "entities": [
                {"id": "entity1", "type": "component", "name": "Component 1"},
                {"id": "entity2", "type": "component", "name": "Component 2"}
            ],
            "relationships": [
                {"source": "entity1", "target": "entity2", "type": "depends_on"}
            ]
        }
    }
    count(result) == 0
}

test_knowledge_graph_invalid_relationship_reference if {
    result := deny with input as {
        "kind": "KnowledgeGraph",
        "metadata": {
            "id": "test-knowledge",
            "name": "Test Knowledge Graph",
            "classification": "operational"
        },
        "spec": {
            "entities": [
                {"id": "entity1", "type": "component", "name": "Component 1"}
            ],
            "relationships": [
                {"source": "entity1", "target": "entity2", "type": "depends_on"}
            ]
        }
    }
    count(result) > 0
}

# =============================================================================
# TEST: Data Sensitivity Policies
# =============================================================================

test_pii_data_requires_owner if {
    result := deny with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "test-pii",
            "name": "Test PII Data",
            "classification": "business",
            "sensitivity": "pii"
        },
        "spec": {
            "attributes": {}
        }
    }
    count(result) > 0
}

test_pii_data_with_owner_valid if {
    result := deny with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "test-pii",
            "name": "Test PII Data",
            "classification": "business",
            "sensitivity": "pii",
            "owner": "data-team"
        },
        "spec": {
            "attributes": {}
        }
    }
    count([r | r := result[_]; contains(r, "owner")]) == 0
}

# =============================================================================
# TEST: Naming Convention Policies
# =============================================================================

test_id_kebab_case_valid if {
    result := deny with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "valid-kebab-case-id",
            "name": "Valid ID",
            "classification": "technical"
        },
        "spec": {
            "attributes": {}
        }
    }
    count([r | r := result[_]; contains(r, "kebab-case")]) == 0
}

test_id_kebab_case_invalid if {
    result := deny with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "Invalid_ID_With_Underscores",
            "name": "Invalid ID",
            "classification": "technical"
        },
        "spec": {
            "attributes": {}
        }
    }
    count(result) > 0
}

# =============================================================================
# TEST: Quality Metrics
# =============================================================================

test_quality_score_warning if {
    result := warn with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "test-metadata",
            "name": "Test Metadata",
            "classification": "technical"
        },
        "spec": {
            "attributes": {}
        },
        "status": {
            "state": "active",
            "quality_score": 0.5
        }
    }
    count(result) > 0
}

test_completeness_ratio_warning if {
    result := warn with input as {
        "kind": "MetadataEntry",
        "metadata": {
            "id": "test-metadata",
            "name": "Test Metadata",
            "classification": "technical"
        },
        "spec": {
            "attributes": {}
        },
        "status": {
            "state": "active",
            "completeness_ratio": 0.5
        }
    }
    count(result) > 0
}

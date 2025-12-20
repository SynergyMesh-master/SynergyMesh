# =============================================================================
# OPA Policy: 99-metadata - Metadata Management Center
# =============================================================================
# Purpose: Enforce metadata governance, lineage, provenance, and knowledge base policies
# Version: 1.0.0
# =============================================================================

package machinenativeops.governance.metadata

import future.keywords.contains
import future.keywords.if
import future.keywords.in

# =============================================================================
# METADATA CLASSIFICATION POLICIES
# =============================================================================

# Deny if metadata classification is missing
deny[msg] {
    input.kind == "MetadataEntry"
    not input.metadata.classification
    msg := "Metadata entry must have a classification (technical, business, operational, governance)"
}

# Deny if classification is invalid
deny[msg] {
    input.kind == "MetadataEntry"
    classification := input.metadata.classification
    not classification in ["technical", "business", "operational", "governance"]
    msg := sprintf("Invalid classification '%s'. Must be one of: technical, business, operational, governance", [classification])
}

# Warn if technical metadata is missing required attributes
warn[msg] {
    input.kind == "MetadataEntry"
    input.metadata.classification == "technical"
    not input.spec.attributes.data_source
    msg := "Technical metadata should include 'data_source' attribute"
}

warn[msg] {
    input.kind == "MetadataEntry"
    input.metadata.classification == "technical"
    not input.spec.attributes.format
    msg := "Technical metadata should include 'format' attribute"
}

# Warn if business metadata is missing required attributes
warn[msg] {
    input.kind == "MetadataEntry"
    input.metadata.classification == "business"
    not input.spec.attributes.business_terms
    msg := "Business metadata should include 'business_terms' attribute"
}

warn[msg] {
    input.kind == "MetadataEntry"
    input.metadata.classification == "business"
    not input.metadata.owner
    msg := "Business metadata should have an owner specified"
}

# =============================================================================
# LINEAGE GRAPH POLICIES
# =============================================================================

# Deny if lineage graph has no nodes
deny[msg] {
    input.kind == "LineageGraph"
    count(input.spec.nodes) == 0
    msg := "Lineage graph must have at least one node"
}

# Deny if lineage graph has cycles (DAG validation)
deny[msg] {
    input.kind == "LineageGraph"
    has_cycle
    msg := "Lineage graph must be a directed acyclic graph (DAG). Cycles detected."
}

# Helper: Check if graph has cycles
has_cycle {
    input.kind == "LineageGraph"
    some edge1, edge2 in input.spec.edges
    edge1.source == edge2.target
    edge1.target == edge2.source
}

# Warn if node is not referenced in any edge
warn[msg] {
    input.kind == "LineageGraph"
    some node in input.spec.nodes
    node_id := node.id
    not is_node_referenced(node_id)
    msg := sprintf("Node '%s' is not referenced in any edge (orphan node)", [node_id])
}

# Helper: Check if node is referenced in edges
is_node_referenced(node_id) {
    some edge in input.spec.edges
    edge.source == node_id
}

is_node_referenced(node_id) {
    some edge in input.spec.edges
    edge.target == node_id
}

# Deny if edge references non-existent node
deny[msg] {
    input.kind == "LineageGraph"
    some edge in input.spec.edges
    not node_exists(edge.source)
    msg := sprintf("Edge references non-existent source node: '%s'", [edge.source])
}

deny[msg] {
    input.kind == "LineageGraph"
    some edge in input.spec.edges
    not node_exists(edge.target)
    msg := sprintf("Edge references non-existent target node: '%s'", [edge.target])
}

# Helper: Check if node exists
node_exists(node_id) {
    some node in input.spec.nodes
    node.id == node_id
}

# =============================================================================
# PROVENANCE RECORD POLICIES
# =============================================================================

# Deny if provenance record is missing required fields
deny[msg] {
    input.kind == "ProvenanceRecord"
    not input.spec.source
    msg := "Provenance record must include source information"
}

deny[msg] {
    input.kind == "ProvenanceRecord"
    not input.spec.timestamp
    msg := "Provenance record must include timestamp"
}

deny[msg] {
    input.kind == "ProvenanceRecord"
    not input.spec.actor
    msg := "Provenance record must include actor information"
}

# Warn if provenance source is git but missing commit
warn[msg] {
    input.kind == "ProvenanceRecord"
    input.spec.source.type == "git"
    not input.spec.source.commit
    msg := "Git provenance source should include commit SHA"
}

# Warn if provenance source is build but missing pipeline info
warn[msg] {
    input.kind == "ProvenanceRecord"
    input.spec.source.type == "build"
    not input.spec.source.pipeline
    msg := "Build provenance source should include pipeline name"
}

# Warn if no artifacts are attached
warn[msg] {
    input.kind == "ProvenanceRecord"
    not input.spec.artifacts
    msg := "Provenance record should include related artifacts (e.g., SBOM, attestation)"
}

# =============================================================================
# KNOWLEDGE GRAPH POLICIES
# =============================================================================

# Deny if knowledge graph has no entities
deny[msg] {
    input.kind == "KnowledgeGraph"
    count(input.spec.entities) == 0
    msg := "Knowledge graph must have at least one entity"
}

# Warn if entity has no relationships
warn[msg] {
    input.kind == "KnowledgeGraph"
    some entity in input.spec.entities
    entity_id := entity.id
    not has_relationships(entity_id)
    msg := sprintf("Entity '%s' has no relationships (isolated entity)", [entity_id])
}

# Helper: Check if entity has relationships
has_relationships(entity_id) {
    some rel in input.spec.relationships
    rel.source == entity_id
}

has_relationships(entity_id) {
    some rel in input.spec.relationships
    rel.target == entity_id
}

# Deny if relationship references non-existent entity
deny[msg] {
    input.kind == "KnowledgeGraph"
    some rel in input.spec.relationships
    not entity_exists(rel.source)
    msg := sprintf("Relationship references non-existent source entity: '%s'", [rel.source])
}

deny[msg] {
    input.kind == "KnowledgeGraph"
    some rel in input.spec.relationships
    not entity_exists(rel.target)
    msg := sprintf("Relationship references non-existent target entity: '%s'", [rel.target])
}

# Helper: Check if entity exists
entity_exists(entity_id) {
    some entity in input.spec.entities
    entity.id == entity_id
}

# Info: Report diagnostic findings
info[msg] {
    input.kind == "KnowledgeGraph"
    input.spec.diagnostics
    orphan_count := count(input.spec.diagnostics.orphan_components)
    orphan_count > 0
    msg := sprintf("Knowledge graph diagnostics: %d orphan components detected", [orphan_count])
}

info[msg] {
    input.kind == "KnowledgeGraph"
    input.spec.diagnostics
    dead_config_count := count(input.spec.diagnostics.dead_configs)
    dead_config_count > 0
    msg := sprintf("Knowledge graph diagnostics: %d dead configs detected", [dead_config_count])
}

info[msg] {
    input.kind == "KnowledgeGraph"
    input.spec.diagnostics
    broken_link_count := count(input.spec.diagnostics.broken_links)
    broken_link_count > 0
    msg := sprintf("Knowledge graph diagnostics: %d broken links detected", [broken_link_count])
}

# =============================================================================
# DATA SENSITIVITY POLICIES
# =============================================================================

# Deny if PII data doesn't have proper sensitivity marking
deny[msg] {
    input.metadata.sensitivity == "pii"
    not input.metadata.owner
    msg := "PII data must have an owner specified"
}

# Warn if restricted data is missing compliance requirements
warn[msg] {
    input.metadata.sensitivity in ["restricted", "confidential", "pii"]
    not input.spec.attributes.compliance_requirements
    msg := sprintf("Sensitive data (%s) should specify compliance requirements", [input.metadata.sensitivity])
}

# =============================================================================
# METADATA QUALITY POLICIES
# =============================================================================

# Warn if quality score is below threshold
warn[msg] {
    input.status.quality_score
    input.status.quality_score < 0.7
    msg := sprintf("Metadata quality score (%.2f) is below recommended threshold (0.7)", [input.status.quality_score])
}

# Warn if completeness ratio is below threshold
warn[msg] {
    input.status.completeness_ratio
    input.status.completeness_ratio < 0.8
    msg := sprintf("Metadata completeness ratio (%.2f) is below recommended threshold (0.8)", [input.status.completeness_ratio])
}

# =============================================================================
# NAMING CONVENTION POLICIES
# =============================================================================

# Deny if ID doesn't follow kebab-case
deny[msg] {
    not regex.match(`^[a-z0-9]+(-[a-z0-9]+)*$`, input.metadata.id)
    msg := sprintf("Metadata ID '%s' must follow kebab-case naming convention", [input.metadata.id])
}

# =============================================================================
# LIFECYCLE POLICIES
# =============================================================================

# Warn if metadata is in draft state for too long
warn[msg] {
    input.status.state == "draft"
    # Note: In real implementation, would check timestamp delta
    msg := "Metadata has been in draft state. Consider validating and activating."
}

# Deny if archived metadata is being modified
deny[msg] {
    input.status.state == "archived"
    msg := "Cannot modify archived metadata. Create a new version instead."
}

# =============================================================================
# COMPLIANCE POLICIES
# =============================================================================

# Info: Report compliance framework alignment
info[msg] {
    input.spec.attributes.compliance_requirements
    count(input.spec.attributes.compliance_requirements) > 0
    msg := sprintf("Metadata aligned with %d compliance requirement(s)", [count(input.spec.attributes.compliance_requirements)])
}

# =============================================================================
# AUDIT TRAIL POLICIES
# =============================================================================

# Warn if metadata is missing creation timestamp
warn[msg] {
    not input.metadata.created_at
    msg := "Metadata should include creation timestamp for audit trail"
}

# Warn if metadata is missing update timestamp
warn[msg] {
    not input.metadata.updated_at
    msg := "Metadata should include update timestamp for audit trail"
}

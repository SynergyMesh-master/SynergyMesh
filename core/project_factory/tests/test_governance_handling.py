"""Governance-focused tests for Project Factory."""

from core.project_factory.factory import ProjectFactory
from core.project_factory.spec import ProjectSpec, ProjectType, Language


def _build_spec() -> ProjectSpec:
    spec = ProjectSpec(
        name="governance-service",
        type=ProjectType.MICROSERVICE,
        language=Language.PYTHON,
        framework="fastapi",
        description="Governance handling test service",
    )
    spec.governance.compliance = ["ISO-27001"]
    spec.governance.security_level = "critical"
    spec.governance.audit_trail = False
    spec.governance.sbom = False
    spec.governance.provenance = "slsa-level-2"
    spec.governance.license = "Apache-2.0"
    return spec


def test_governance_context_and_metadata():
    """Ensure governance values flow into context and metadata."""
    spec = _build_spec()
    factory = ProjectFactory()

    context = factory._prepare_context(spec)
    assert context["provenance_level"] == "slsa-level-2"
    assert context["sbom_enabled"] is False
    assert context["audit_trail_enabled"] is False

    metadata = factory._create_metadata(spec, context)
    governance_meta = metadata["governance"]

    assert governance_meta["provenance"] == "slsa-level-2"
    assert governance_meta["sbom"] is False
    assert governance_meta["audit_trail"] is False
    assert metadata["spec"]["governance"]["license"] == "Apache-2.0"


def test_compliance_template_reflects_governance():
    """COMPLIANCE document should show governance spec values."""
    spec = _build_spec()
    factory = ProjectFactory()
    context = factory._prepare_context(spec)

    content = factory.template_engine.render("governance/compliance.md.j2", context)

    assert "SLSA Provenance**: slsa-level-2" in content
    assert "SBOM**: Not requested" in content
    assert "Audit trail disabled per project specification" in content

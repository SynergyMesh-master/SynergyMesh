"""
Unified pipeline manifest loader (MCP integration, concept draft).

Artifacts:
- Manifest: workspace/mcp/pipelines/unified-pipeline-config.yaml
- Schema:   workspace/mcp/schemas/unified-pipeline.schema.json
- TS types: workspace/mcp/types/unifiedPipeline.ts
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml


MANIFEST_PATH = Path("workspace/mcp/pipelines/unified-pipeline-config.yaml")
SCHEMA_PATH = Path("workspace/mcp/schemas/unified-pipeline.schema.json")


@dataclass
class InputUnification:
    protocols: List[str]
    normalization: str
    validation: str
    timeout: int  # milliseconds


@dataclass
class CoreScheduling:
    maxParallelAgents: int
    taskDecomposition: str
    resourceArbitration: str
    loadBalancing: str
    syncBarrier: str


@dataclass
class PipelineEntry:
    name: str
    type: str
    entrypoint: Optional[str] = None
    worldClassValidationRef: Optional[str] = None
    policies: Optional[str] = None
    manifests: Optional[str] = None
    dashboards: Optional[str] = None


@dataclass
class ToolAdapter:
    name: str
    path: str


@dataclass
class McpIntegration:
    serverRef: str
    toolAdapters: List[ToolAdapter]
    realTimeSync: str


@dataclass
class Outputs:
    auditLog: str
    evidenceChain: str
    statusReport: str
    autoRemediation: str
    notifications: str


@dataclass
class UnifiedPipelineSpec:
    inputUnification: InputUnification
    coreScheduling: CoreScheduling
    pipelines: List[PipelineEntry]
    mcpIntegration: McpIntegration
    outputs: Outputs


@dataclass
class UnifiedPipelineManifest:
    apiVersion: str
    kind: str
    metadata: dict
    spec: UnifiedPipelineSpec


def load_manifest(path: Path = MANIFEST_PATH) -> UnifiedPipelineManifest:
    """Load YAML manifest into typed dataclasses with minimal required-field validation."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key in ("apiVersion", "kind", "metadata", "spec"):
        if key not in data:
            raise ValueError(f"Missing required top-level key: {key}")
    spec = data["spec"]
    for section in ("inputUnification", "coreScheduling", "mcpIntegration", "outputs"):
        if section not in spec:
            raise ValueError(f"Missing required spec section: {section}")
    pipelines_data = spec["pipelines"]
    if not isinstance(pipelines_data, list):
        raise ValueError("spec.pipelines must be a list")
    pipelines = [_safe_construct(PipelineEntry, p, "pipelines[*]") for p in pipelines_data]

    adapters_data = spec["mcpIntegration"]["toolAdapters"]
    if not isinstance(adapters_data, list):
        raise ValueError("spec.mcpIntegration.toolAdapters must be a list")
    adapters = [_safe_construct(ToolAdapter, t, "mcpIntegration.toolAdapters[*]") for t in adapters_data]
    return UnifiedPipelineManifest(
        apiVersion=data["apiVersion"],
        kind=data["kind"],
        metadata=data["metadata"],
        spec=UnifiedPipelineSpec(
            inputUnification=_safe_construct(InputUnification, spec["inputUnification"], "inputUnification"),
            coreScheduling=_safe_construct(CoreScheduling, spec["coreScheduling"], "coreScheduling"),
            pipelines=pipelines,
            mcpIntegration=_safe_construct(
                McpIntegration,
                {
                    "serverRef": spec["mcpIntegration"]["serverRef"],
                    "toolAdapters": adapters,
                    "realTimeSync": spec["mcpIntegration"]["realTimeSync"],
                },
                "mcpIntegration",
            ),
            outputs=_safe_construct(Outputs, spec["outputs"], "outputs"),
        ),
    )


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    """Load JSON Schema for optional validation tooling."""
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_construct(cls, data: dict, label: str):
    try:
        return cls(**data)
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError(f"Failed constructing {label} for {cls.__name__}: {exc}") from exc


__all__ = [
    "load_manifest",
    "load_schema",
    "UnifiedPipelineManifest",
    "UnifiedPipelineSpec",
    "InputUnification",
    "CoreScheduling",
    "PipelineEntry",
    "McpIntegration",
    "ToolAdapter",
    "Outputs",
]

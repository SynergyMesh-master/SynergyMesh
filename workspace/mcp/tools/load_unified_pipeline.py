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
from typing import List, Optional, Union

import yaml


MANIFEST_PATH = Path("workspace/mcp/pipelines/unified-pipeline-config.yaml")
SCHEMA_PATH = Path("workspace/mcp/schemas/unified-pipeline.schema.json")


@dataclass
class InputUnification:
    protocols: List[str]
    normalization: str
    validation: str
    timeout: Union[str, int]


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
    """Load YAML manifest into typed dataclasses (schema validation optional)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    spec = data["spec"]
    pipelines = [PipelineEntry(**p) for p in spec.get("pipelines", [])]
    adapters = [ToolAdapter(**t) for t in spec.get("mcpIntegration", {}).get("toolAdapters", [])]
    return UnifiedPipelineManifest(
        apiVersion=data["apiVersion"],
        kind=data["kind"],
        metadata=data["metadata"],
        spec=UnifiedPipelineSpec(
            inputUnification=InputUnification(**spec["inputUnification"]),
            coreScheduling=CoreScheduling(**spec["coreScheduling"]),
            pipelines=pipelines,
            mcpIntegration=McpIntegration(
                serverRef=spec["mcpIntegration"]["serverRef"],
                toolAdapters=adapters,
                realTimeSync=spec["mcpIntegration"]["realTimeSync"],
            ),
            outputs=Outputs(**spec["outputs"]),
        ),
    )


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    """Load JSON Schema for optional validation tooling."""
    return json.loads(path.read_text(encoding="utf-8"))


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

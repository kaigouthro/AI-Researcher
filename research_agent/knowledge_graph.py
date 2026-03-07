"""Topic-scoped knowledge graph primitives for research agents.

The graph is persisted as JSON so agents can read/write it without requiring an
external graph database during local runs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


NodeType = Literal["Idea", "Concept", "Artifact", "Claim", "Agent", "Dimension", "Evidence"]


class GraphNode(BaseModel):
    uid: str
    node_type: NodeType
    title: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class GraphEvidence(BaseModel):
    uid: str
    evidence_type: str = "quote"
    snippet: str = ""
    locator: dict[str, Any] = Field(default_factory=dict)
    artifact_uid: str | None = None
    confidence: float = 1.0
    source_url: str | None = None


class DependencyEdge(BaseModel):
    uid: str
    source_uid: str
    target_uid: str
    dependency_type: str = "foundational"
    dimensions: list[str] = Field(default_factory=list)
    confidence: float = 1.0
    status: str = "proposed"
    justification: str = ""
    citation_count: int = 0
    evidence_uids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TopicKnowledgeGraph(BaseModel):
    schema_version: str = "kg.schema.v1"
    topic_id: str
    created_at: str
    updated_at: str
    nodes: dict[str, GraphNode] = Field(default_factory=dict)
    dependencies: dict[str, DependencyEdge] = Field(default_factory=dict)
    evidence: dict[str, GraphEvidence] = Field(default_factory=dict)

    def upsert_node(
        self,
        uid: str,
        node_type: NodeType,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        source_references: list[str] | None = None,
        properties: dict[str, Any] | None = None,
    ) -> GraphNode:
        now = utc_now()
        existing = self.nodes.get(uid)
        if existing:
            existing.node_type = node_type
            existing.title = title
            existing.description = description
            existing.tags = sorted(set(tags or []))
            existing.source_references = sorted(set(source_references or []))
            existing.properties = properties or {}
            existing.updated_at = now
            self.updated_at = now
            return existing

        node = GraphNode(
            uid=uid,
            node_type=node_type,
            title=title,
            description=description,
            tags=sorted(set(tags or [])),
            source_references=sorted(set(source_references or [])),
            properties=properties or {},
            created_at=now,
            updated_at=now,
        )
        self.nodes[uid] = node
        self.updated_at = now
        return node

    def add_evidence(
        self,
        uid: str,
        evidence_type: str = "quote",
        snippet: str = "",
        locator: dict[str, Any] | None = None,
        artifact_uid: str | None = None,
        confidence: float = 1.0,
        source_url: str | None = None,
    ) -> GraphEvidence:
        now = utc_now()
        evidence = GraphEvidence(
            uid=uid,
            evidence_type=evidence_type,
            snippet=snippet,
            locator=locator or {},
            artifact_uid=artifact_uid,
            confidence=confidence,
            source_url=source_url,
        )
        self.evidence[uid] = evidence
        self.updated_at = now
        return evidence

    def add_dependency(
        self,
        uid: str,
        source_uid: str,
        target_uid: str,
        dependency_type: str = "foundational",
        dimensions: list[str] | None = None,
        confidence: float = 1.0,
        status: str = "proposed",
        justification: str = "",
        evidence_uids: list[str] | None = None,
    ) -> DependencyEdge:
        if source_uid not in self.nodes:
            raise ValueError(f"Unknown source node: {source_uid}")
        if target_uid not in self.nodes:
            raise ValueError(f"Unknown target node: {target_uid}")

        now = utc_now()
        edge = DependencyEdge(
            uid=uid,
            source_uid=source_uid,
            target_uid=target_uid,
            dependency_type=dependency_type,
            dimensions=sorted(set(dimensions or [])),
            confidence=confidence,
            status=status,
            justification=justification,
            citation_count=len(evidence_uids or []),
            evidence_uids=sorted(set(evidence_uids or [])),
            created_at=now,
            updated_at=now,
        )
        self.dependencies[uid] = edge
        self.updated_at = now
        return edge

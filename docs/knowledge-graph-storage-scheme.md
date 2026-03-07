# Knowledge Graph Storage Scheme for Idea-Dependency Citations

This document proposes a **data-centric, extensible, and future-upgradable** storage scheme for a knowledge graph where:

- nodes represent ideas/concepts and research artifacts,
- edges represent **directional dependence** ("idea A is founded on idea B"),
- edge objects carry rich citation metadata,
- multiple edge dimensionality (methodological, empirical, mathematical, etc.) is modeled natively,
- graph data remains resilient to external changes in research workflows and tooling.

The design is compatible with both **Memgraph** and **FalkorDB** using Cypher-like query patterns.

---

## 1) Design Principles

1. **Data-centric first**
   - Encode facts and provenance in the graph itself, not hidden in application logic.
   - Treat dependencies and citations as durable data entities.

2. **Edge semantics as first-class entities**
   - A plain relationship alone is often too limited for multi-dimensional dependency evidence.
   - Represent each meaningful dependency as a reusable entity with typed dimensions and evidence.

3. **Forward-compatible schema evolution**
   - Include explicit schema and ontology versions.
   - Use additive evolution and deprecation windows rather than destructive migration.

4. **Resilience to external system changes**
   - Keep source-system references as adapters (`source_system`, `external_id`, `ingest_job_id`).
   - Preserve provenance snapshots so re-indexing or source mutations do not break historical truth.

5. **Operational performance with analytical depth**
   - Maintain performant direct edges for traversal.
   - Also keep richer edge entities for provenance, weighting, and explainability.

---

## 2) Core Entity Model

## 2.1 Node labels

- `:Concept`
  - Stable conceptual units (e.g., “contrastive pretraining”, “cold-start regularization”).
- `:Idea`
  - Concrete instantiations/compositions of concepts in a research context.
- `:Artifact`
  - Source item: paper, notebook, code repo, experiment run, issue, wiki page, benchmark report.
- `:Claim`
  - Normalized claim extracted from an artifact (“method X improves NDCG@10 by 2.1% on dataset Y”).
- `:Agent`
  - Person, model, or pipeline that produced/validated data.
- `:Dimension`
  - Dependency category taxonomy entry (methodological, theoretical, empirical, implementation, dataset, metric, assumption, etc.).
- `:DependencyEdge`
  - First-class edge entity describing one dependency assertion between two ideas/concepts.
- `:Evidence`
  - Evidence unit supporting a dependency (text span, table row, code link, experiment record).

### Minimal shared properties on all node types

```text
uid: string                 // immutable global ID (ULID/UUIDv7 recommended)
tenant_id: string           // optional multi-tenant boundary
created_at: datetime
updated_at: datetime
valid_from: datetime        // business validity start
valid_to: datetime|null     // business validity end (null = active)
schema_version: string      // e.g., "kg.schema.v1"
source_system: string       // e.g., "semantic-scholar", "local-rag", "manual"
external_ref: map           // {id, url, revision, hash}
```

---

## 3) Modeling Multi-Dimensional Directional Dependencies

A directional dependency from `IdeaA` to `IdeaB` means:

> `IdeaA` **depends on / is founded on** `IdeaB`.

### 3.1 Dual-representation pattern (recommended)

Use both:

1. **Direct operational relationship** for fast traversal:
   - `(a:Idea)-[:DEPENDS_ON {edge_uid, strength, status}]->(b:Idea)`

2. **Rich first-class edge object** for explainability and extensibility:
   - `(a)-[:ASSERTS_DEPENDENCY]->(d:DependencyEdge)-[:TARGET]->(b)`

This keeps graph traversal fast while enabling rich metadata and versioning.

### 3.2 DependencyEdge properties (rich semantics)

```text
uid: string
source_uid: string          // denormalized for quick lookup
target_uid: string          // denormalized for quick lookup
direction: "OUTBOUND"       // fixed semantics: source depends on target
dependency_type: string     // e.g., "foundational", "extends", "implements", "contradicts"
dimensions: [string]        // e.g., ["methodological", "empirical", "dataset"]
weight_vector: map          // e.g., {methodological:0.9, empirical:0.6, theoretical:0.2}
confidence: float           // confidence in extracted/asserted dependency [0,1]
polarity: string            // "supports" | "neutral" | "challenges"
status: string              // "proposed" | "validated" | "deprecated"
justification: string       // short natural-language summary
citation_count: int
created_by_uid: string      // Agent uid
```

### 3.3 Citation metadata on dependency edges

Attach citation details to the `DependencyEdge` via evidence links:

- `(d:DependencyEdge)-[:SUPPORTED_BY]->(e:Evidence)-[:FROM_ARTIFACT]->(p:Artifact)`

`Evidence` properties:

```text
uid: string
evidence_type: string       // "quote", "table", "equation", "code", "experiment"
locator: map                // {page, section, paragraph, figure, table, line_start, line_end}
snippet: string             // optional excerpt
doi: string|null
url: string|null
publication_year: int|null
authors: [string]|null
source_hash: string         // content digest to detect source drift
confidence: float
```

This gives paper-like citations, but at **idea-to-idea dependency granularity**.

---

## 4) Suggested Taxonomy for Edge Dimensions

Start with a controlled vocabulary in `:Dimension` nodes:

- `methodological`
- `theoretical`
- `empirical`
- `implementation`
- `dataset`
- `metric`
- `assumption`
- `domain-transfer`
- `negative-dependency` (idea depends on disproving/challenging another)

Store dimensions by stable code, not display labels:

```text
code: "empirical"
label: "Empirical Evidence"
ontology_version: "depdims.v1"
parent_code: "evidence"
```

Future dimensions are additive; old ones remain queryable.

---

## 5) Versioning and Evolution Strategy

1. **Schema version fields** on all nodes/edges.
2. **Ontology versioning** for `dependency_type` and `dimensions`.
3. **Bitemporal-ready fields** (`valid_from`, `valid_to`, event timestamps).
4. **Soft deprecation**:
   - `status="deprecated"` on edge entities,
   - preserve historical evidence.
5. **Migration adapters**:
   - maintain a `:SchemaMap` node/table mapping old keys to new keys.

This allows graceful upgrades without rewriting historical graph facts.

---

## 6) Memgraph / FalkorDB Implementation Notes

Both systems support graph traversals and Cypher-like querying.

## 6.1 Recommended indexes/constraints

- Unique on `uid` for all major labels.
- Index on `Idea.slug`, `Concept.slug` if used.
- Composite index on dependency lookup:
  - `DependencyEdge(source_uid, target_uid, status)`
- Index `Evidence(source_hash)` for drift detection.

## 6.2 Example Cypher skeleton

```cypher
// Ideas
MERGE (a:Idea {uid: $idea_a_uid})
  ON CREATE SET a.title = $idea_a_title, a.created_at = datetime()
MERGE (b:Idea {uid: $idea_b_uid})
  ON CREATE SET b.title = $idea_b_title, b.created_at = datetime()

// Fast direct edge
MERGE (a)-[r:DEPENDS_ON {edge_uid: $dep_uid}]->(b)
SET r.strength = $strength,
    r.status = $status,
    r.updated_at = datetime()

// Rich edge entity
MERGE (d:DependencyEdge {uid: $dep_uid})
SET d.source_uid = $idea_a_uid,
    d.target_uid = $idea_b_uid,
    d.dependency_type = $dependency_type,
    d.dimensions = $dimensions,
    d.weight_vector = $weight_vector,
    d.confidence = $confidence,
    d.status = $status,
    d.updated_at = datetime()

MERGE (a)-[:ASSERTS_DEPENDENCY]->(d)
MERGE (d)-[:TARGET]->(b)

// Evidence and citation metadata
MERGE (e:Evidence {uid: $evidence_uid})
SET e.evidence_type = $evidence_type,
    e.locator = $locator,
    e.snippet = $snippet,
    e.url = $url,
    e.publication_year = $publication_year,
    e.source_hash = $source_hash,
    e.confidence = $evidence_confidence

MERGE (p:Artifact {uid: $artifact_uid})
SET p.title = $artifact_title,
    p.artifact_type = $artifact_type,
    p.external_ref = $artifact_external_ref

MERGE (d)-[:SUPPORTED_BY]->(e)
MERGE (e)-[:FROM_ARTIFACT]->(p)
```

---

## 7) Query Patterns You Will Need

1. **Upstream foundations for an idea**
   - Traverse outgoing `DEPENDS_ON` recursively.
2. **Most evidence-backed foundations**
   - Rank by `citation_count`, number of `SUPPORTED_BY`, and confidence.
3. **Dimension-specific dependency graph**
   - Filter where `"empirical" IN d.dimensions`.
4. **Conflict map**
   - `polarity="challenges"` to identify contradictory foundations.
5. **Temporal replay**
   - filter by `valid_from/valid_to` to reconstruct graph state at time T.

---

## 8) Ingestion and Drift-Resilience

Build ingestion as append-friendly events:

- `ExtractedDependencyEvent`
- `ValidatedDependencyEvent`
- `DeprecatedDependencyEvent`
- `EvidenceLinkedEvent`

Each event writes/updates graph facts while preserving prior state references.

For external drift:

- keep `source_hash`, `source_system`, `external_ref.revision`,
- if a source changes, add new `Evidence` and close old validity interval (`valid_to`).

---

## 9) Integration with an Existing RAG KG Repository

Given you already have a deeper RAG KG in another Falkor-oriented repo, use this **interoperability boundary**:

1. Define canonical IDs in this repo (`uid`) and store cross-system IDs in `external_ref`.
2. Treat your existing RAG KG as an evidence provider:
   - retrieved chunks become `Evidence` nodes with chunk locator metadata.
3. Keep a lightweight synchronization job:
   - pull new/changed dependencies,
   - upsert nodes/edges,
   - write `ingest_job_id` and timestamps.
4. Do not force schema parity initially; bridge with an adapter layer that maps fields into this canonical model.

---

## 10) Minimal Viable Rollout Plan

1. **Phase 1**: Implement `Idea`, `DependencyEdge`, `Evidence`, `Artifact` with dual-edge representation.
2. **Phase 2**: Add dimension taxonomy and confidence/weight vectors.
3. **Phase 3**: Add temporal validity + drift handling (`source_hash`, revision).
4. **Phase 4**: Add automated extraction/validation loops and conflict analytics.

This phased approach gets immediate value while preserving long-term extensibility.

---

## 11) Why this fits your requirement

- Supports **multiple edge dimensionality** with typed dimensions and weight vectors.
- Enforces **directionality of dependence** (`A -> B` where A depends on B).
- Captures **citation-like metadata on edges** through `Evidence` + `Artifact` links.
- Remains **data-centric and extensible** with explicit schema/ontology versioning.
- Is **resilient to external process/tooling changes** via provenance adapters and immutable IDs.
- Works natively with **Memgraph and FalkorDB** query patterns.

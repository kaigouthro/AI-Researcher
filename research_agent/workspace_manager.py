"""Workspace manager for project/topic-oriented research workflows."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


DEFAULT_WORKSPACE_ROOT = Path("research_workspace")
DEFAULT_TAXONOMY = {
    "category_tags": [
        "gnn",
        "diffusion",
        "recommendation",
        "reasoning",
        "optimization",
        "multimodal",
    ],
    "method_tags": [
        "transformer",
        "contrastive_learning",
        "graph_neural_network",
        "retrieval_augmented_generation",
        "reinforcement_learning",
    ],
    "task_tags": [
        "survey",
        "reproduction",
        "benchmark",
        "ideation",
        "implementation",
        "analysis",
        "writing",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    if not normalized:
        raise ValueError("Value cannot be converted to a valid slug")
    return normalized


class ProjectMetadata(BaseModel):
    schema_version: str = "1.0"
    id: str
    slug: str
    title: str
    description: str = ""
    owner: str
    contributors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class TopicMetadata(BaseModel):
    schema_version: str = "1.0"
    id: str
    slug: str
    project_id: str
    title: str
    summary: str = ""
    status: str = "draft"
    priority: str = "medium"
    category_tags: list[str] = Field(default_factory=list)
    method_tags: list[str] = Field(default_factory=list)
    task_tags: list[str] = Field(default_factory=list)
    linked_topics: list[str] = Field(default_factory=list)
    linked_projects: list[str] = Field(default_factory=list)
    source_references: list[str] = Field(default_factory=list)
    owner: str
    contributors: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class BacklogTask(BaseModel):
    id: str
    title: str
    task_id: str
    status: str = "queued"
    priority: str = "medium"
    depends_on: list[str] = Field(default_factory=list)
    rationale: str = ""
    created_at: str


class TopicBacklog(BaseModel):
    schema_version: str = "1.0"
    topic_id: str
    tasks: list[BacklogTask] = Field(default_factory=list)


@dataclass
class WorkspaceManager:
    root: Path = DEFAULT_WORKSPACE_ROOT

    @property
    def projects_dir(self) -> Path:
        return self.root / "projects"

    def ensure_workspace(self) -> None:
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        taxonomy_path = self.root / "taxonomy.yaml"
        if not taxonomy_path.exists():
            self._write_yaml(taxonomy_path, DEFAULT_TAXONOMY)

    def create_project(
        self,
        name: str,
        owner: str,
        slug: str | None = None,
        description: str = "",
        tags: list[str] | None = None,
    ) -> Path:
        self.ensure_workspace()
        slug = slugify(slug or name)
        project_dir = self.projects_dir / slug
        if project_dir.exists():
            raise FileExistsError(f"Project already exists: {slug}")

        now = utc_now()
        metadata = ProjectMetadata(
            id=slug,
            slug=slug,
            title=name,
            description=description,
            owner=owner,
            tags=sorted(set(tags or [])),
            created_at=now,
            updated_at=now,
        )

        (project_dir / "topics").mkdir(parents=True)
        self._write_yaml(project_dir / "project.yaml", metadata.model_dump())
        return project_dir

    def create_topic(
        self,
        project_slug: str,
        title: str,
        owner: str,
        slug: str | None = None,
        summary: str = "",
        category_tags: list[str] | None = None,
        method_tags: list[str] | None = None,
        task_tags: list[str] | None = None,
        priority: str = "medium",
    ) -> Path:
        project_dir = self.projects_dir / project_slug
        if not project_dir.exists():
            raise FileNotFoundError(f"Project not found: {project_slug}")

        topic_slug = slugify(slug or title)
        topic_dir = project_dir / "topics" / topic_slug
        if topic_dir.exists():
            raise FileExistsError(f"Topic already exists: {topic_slug}")

        now = utc_now()
        topic_meta = TopicMetadata(
            id=f"{project_slug}:{topic_slug}",
            slug=topic_slug,
            project_id=project_slug,
            title=title,
            summary=summary,
            priority=priority,
            category_tags=sorted(set(category_tags or [])),
            method_tags=sorted(set(method_tags or [])),
            task_tags=sorted(set(task_tags or [])),
            owner=owner,
            created_at=now,
            updated_at=now,
        )

        (topic_dir / "runs").mkdir(parents=True)
        (topic_dir / "tasks" / "templates").mkdir(parents=True)
        (topic_dir / "notes").mkdir(parents=True)
        (topic_dir / "references").mkdir(parents=True)
        (topic_dir / "vectors" / "embeddings").mkdir(parents=True)

        backlog = TopicBacklog(topic_id=topic_meta.id)
        index_manifest = {
            "schema_version": "1.0",
            "topic_id": topic_meta.id,
            "embedding_provider": None,
            "embedding_model": None,
            "last_indexed_at": None,
            "chunk_count": 0,
            "content_checksum": None,
        }

        self._write_yaml(topic_dir / "topic.yaml", topic_meta.model_dump())
        self._write_yaml(topic_dir / "tasks" / "backlog.yaml", backlog.model_dump())
        self._write_json(topic_dir / "vectors" / "index_manifest.json", index_manifest)
        return topic_dir

    def list_topics(self, project_slug: str, status: str | None = None) -> list[dict[str, Any]]:
        project_topics = self.projects_dir / project_slug / "topics"
        if not project_topics.exists():
            raise FileNotFoundError(f"Project not found: {project_slug}")

        results: list[dict[str, Any]] = []
        for topic_dir in sorted([p for p in project_topics.iterdir() if p.is_dir()]):
            topic_meta_path = topic_dir / "topic.yaml"
            if not topic_meta_path.exists():
                raise FileNotFoundError(
                    f"Missing topic metadata file for topic '{topic_dir.name}' in project '{project_slug}': {topic_meta_path}"
                )
            meta = self._read_yaml(topic_meta_path)
            topic = TopicMetadata.model_validate(meta)
            if status and topic.status != status:
                continue
            results.append(topic.model_dump())
        return results

    def add_backlog_task(
        self,
        project_slug: str,
        topic_slug: str,
        task_id: str,
        title: str,
        status: str = "queued",
        priority: str = "medium",
        depends_on: list[str] | None = None,
        rationale: str = "",
    ) -> dict[str, Any]:
        backlog_path = self._topic_dir(project_slug, topic_slug) / "tasks" / "backlog.yaml"
        backlog_payload = self._read_yaml(backlog_path)
        backlog = TopicBacklog.model_validate(backlog_payload)
        task_key = slugify(f"{task_id}-{title}")
        new_task = BacklogTask(
            id=task_key,
            title=title,
            task_id=task_id,
            status=status,
            priority=priority,
            depends_on=sorted(set(depends_on or [])),
            rationale=rationale,
            created_at=utc_now(),
        )
        backlog.tasks.append(new_task)
        self._write_yaml(backlog_path, backlog.model_dump())
        return new_task.model_dump()

    def recommend_next_tasks(self, project_slug: str, topic_slug: str) -> list[dict[str, str]]:
        topic_dir = self._topic_dir(project_slug, topic_slug)
        topic = TopicMetadata.model_validate(self._read_yaml(topic_dir / "topic.yaml"))
        backlog = TopicBacklog.model_validate(self._read_yaml(topic_dir / "tasks" / "backlog.yaml"))
        queued_task_ids = {task.task_id for task in backlog.tasks if task.status in {"queued", "ready", "running"}}

        recommendations: list[dict[str, str]] = []
        if "literature_discovery" not in queued_task_ids:
            recommendations.append({
                "task_id": "literature_discovery",
                "title": "Expand recent literature coverage",
                "reason": "No active literature discovery task found.",
            })
        if "experiment_plan" not in queued_task_ids and "reproduction" in topic.task_tags:
            recommendations.append({
                "task_id": "experiment_plan",
                "title": "Create reproducible experiment matrix",
                "reason": "Topic is tagged for reproduction but has no explicit experiment plan.",
            })
        if "next_task_recommendation" not in queued_task_ids:
            recommendations.append({
                "task_id": "next_task_recommendation",
                "title": "Run follow-up task suggestion pass",
                "reason": "Keeps backlog refreshed based on latest outputs.",
            })
        return recommendations

    def _topic_dir(self, project_slug: str, topic_slug: str) -> Path:
        path = self.projects_dir / project_slug / "topics" / topic_slug
        if not path.exists():
            raise FileNotFoundError(f"Topic not found: {project_slug}/{topic_slug}")
        return path

    @staticmethod
    def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False)

    @staticmethod
    def _read_yaml(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise ValueError(f"YAML root must be a mapping in {path}")
        return loaded

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")

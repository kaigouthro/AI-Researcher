from pathlib import Path

import yaml
from click.testing import CliRunner

from research_agent.cli import cli
from research_agent.workspace_manager import WorkspaceManager


def test_workspace_manager_topic_structure(tmp_path: Path):
    manager = WorkspaceManager(tmp_path / "workspace")
    project_dir = manager.create_project(name="Graph RAG", owner="alex")
    topic_dir = manager.create_topic(
        project_slug=project_dir.name,
        title="Hybrid Retrieval",
        owner="alex",
        category_tags=["gnn"],
        method_tags=["retrieval_augmented_generation"],
        task_tags=["reproduction"],
    )

    assert (manager.root / "taxonomy.yaml").exists()
    assert (topic_dir / "topic.yaml").exists()
    assert (topic_dir / "tasks" / "backlog.yaml").exists()
    assert (topic_dir / "vectors" / "index_manifest.json").exists()

    topic_payload = yaml.safe_load((topic_dir / "topic.yaml").read_text())
    assert topic_payload["project_id"] == project_dir.name
    assert topic_payload["category_tags"] == ["gnn"]


def test_cli_workspace_flow(tmp_path: Path):
    runner = CliRunner()
    root = tmp_path / "workspace_cli"

    # Test workspace init
    result = runner.invoke(
        cli,
        [
            "workspace",
            "init",
            "--root",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (root / "projects").exists()
    assert (root / "taxonomy.yaml").exists()

    result = runner.invoke(
        cli,
        [
            "workspace",
            "create-project",
            "--name",
            "Research Platform",
            "--owner",
            "alex",
            "--root",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.output

    result = runner.invoke(
        cli,
        [
            "workspace",
            "create-topic",
            "--project",
            "research-platform",
            "--title",
            "Task Planning",
            "--owner",
            "alex",
            "--task-tag",
            "reproduction",
            "--root",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.output

    # Test workspace list-topics
    result = runner.invoke(
        cli,
        [
            "workspace",
            "list-topics",
            "--project",
            "research-platform",
            "--root",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "task-planning" in result.output
    assert "Task Planning" in result.output

    result = runner.invoke(
        cli,
        [
            "workspace",
            "add-task",
            "--project",
            "research-platform",
            "--topic",
            "task-planning",
            "--task-id",
            "literature_discovery",
            "--title",
            "Survey related methods",
            "--root",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "literature_discovery" in result.output

    result = runner.invoke(
        cli,
        [
            "workspace",
            "recommend-tasks",
            "--project",
            "research-platform",
            "--topic",
            "task-planning",
            "--root",
            str(root),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "next_task_recommendation" in result.output

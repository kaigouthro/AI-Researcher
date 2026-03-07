"""
AI-Researcher CLI - Main entry point for autonomous research tasks.
"""
import click
import sys
import json
import shutil
from pathlib import Path

# Load environment variables from .env
from dotenv import load_dotenv
from research_agent.validation import load_and_validate_instance, validate_benchmark_instance_payload
from research_agent.run_metadata import resolve_run_metadata_path
from research_agent.artifacts import create_artifact_bundle, create_artifact_folder

PROJECT_ROOT = Path(__file__).parent.parent
env_path = PROJECT_ROOT / '.env'
load_dotenv(env_path)

# Available research categories
RESEARCH_CATEGORIES = ['vq', 'gnn', 'reasoning', 'recommendation', 'diffu_flow']
BENCHMARK_DIR = PROJECT_ROOT / 'benchmark' / 'final'


@click.group()
@click.version_option(version='0.2.0', prog_name='ai-researcher')
def cli():
    """AI-Researcher - Autonomous Scientific Innovation System.

    A system that automates the entire research lifecycle from literature
    review to paper writing.
    """
    pass


def run_task(category: str, instance_id: str, model: str, task_level: str,
             port: int, max_iter: int, no_docker: bool, dry_run: bool):
    import argparse
    import os
    from research_agent.constant import COMPLETION_MODEL

    model = model or COMPLETION_MODEL
    instance_path = BENCHMARK_DIR / category / f'{instance_id}.json'

    if not instance_path.exists():
        raise click.ClickException(f"Task not found: {instance_path}")

    click.echo(f"Starting AI-Researcher task:")
    click.echo(f"  Category: {category}")
    click.echo(f"  Instance: {instance_id}")
    click.echo(f"  Level: {task_level}")
    click.echo(f"  Model: {model}")
    click.echo(f"  Docker: {'disabled' if no_docker else 'enabled'}")
    click.echo("")

    if no_docker:
        os.environ['USE_DOCKER'] = 'false'

    if not dry_run:
        api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise click.ClickException(
                "No API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY, or use --dry-run."
            )

    args = argparse.Namespace(
        instance_path=str(instance_path),
        container_name='ai_researcher',
        task_level=task_level,
        model=model,
        workplace_name='workplace',
        cache_path='cache',
        port=port,
        max_iter_times=max_iter,
        category=category,
        dry_run=dry_run,
    )

    if task_level == 'task1':
        from research_agent.run_infer_plan import main
        main(args)
    else:
        from research_agent.run_infer_idea import main
        main(args)


@cli.command()
@click.option('--category', '-c', required=True,
              type=click.Choice(RESEARCH_CATEGORIES),
              help='Research category')
@click.option('--instance-id', '-i', required=True,
              help='Instance ID of the benchmark task')
@click.option('--model', '-m', default=None,
              help='LLM model to use (default: from COMPLETION_MODEL env var)')
@click.option('--task-level', '-l', default='task1',
              type=click.Choice(['task1', 'task2']),
              help='Task level: task1 (detailed idea) or task2 (reference-based)')
@click.option('--port', '-p', default=12380,
              help='Port for Docker communication')
@click.option('--max-iter', default=0,
              help='Maximum iteration times (0 for unlimited)')
@click.option('--no-docker', is_flag=True,
              help='Run without Docker container')
@click.option('--dry-run', is_flag=True,
              help='Validate inputs and exit without running agents')
def run(category: str, instance_id: str, model: str, task_level: str,
        port: int, max_iter: int, no_docker: bool, dry_run: bool):
    """Run an autonomous research task.

    Example:
        ai-researcher run -c vq -i one_layer_vq -l task1
    """
    run_task(category, instance_id, model, task_level, port, max_iter, no_docker, dry_run)


@cli.command()
@click.option('--category', '-c', default=None,
              type=click.Choice(RESEARCH_CATEGORIES),
              help='Filter by category')
def list(category: str):
    """List available benchmark tasks."""
    if not BENCHMARK_DIR.exists():
        click.echo("Benchmark directory not found.")
        return

    categories = [category] if category else [d.name for d in BENCHMARK_DIR.iterdir() if d.is_dir()]

    for cat in categories:
        cat_path = BENCHMARK_DIR / cat
        if not cat_path.is_dir():
            continue

        tasks = [f.stem for f in cat_path.glob('*.json')]
        click.echo(f"\n{cat}/ ({len(tasks)} tasks)")
        for task in sorted(tasks):
            click.echo(f"  - {task}")


@cli.command()
@click.option('--category', '-c', required=True,
              type=click.Choice(RESEARCH_CATEGORIES),
              help='Research category')
@click.option('--instance-id', '-i', required=True,
              help='Instance ID of the benchmark task')
def preview(category: str, instance_id: str):
    """Preview a benchmark task without running it."""
    instance_path = BENCHMARK_DIR / category / f'{instance_id}.json'
    payload = load_and_validate_instance(instance_path)

    click.echo(f"Instance: {payload.get('instance_id')}")
    click.echo(f"Target: {payload.get('target')}")
    click.echo(f"Year: {payload.get('year')}")
    click.echo(f"URL: {payload.get('url')}")
    source_papers = payload.get("source_papers", [])
    click.echo(f"Source papers: {len(source_papers)}")
    if source_papers:
        click.echo("Sources:")
        for paper in source_papers:
            click.echo(f"  - {paper.get('reference')}")
    click.echo("")
    click.echo("Task1:")
    click.echo(str(payload.get("task1", "")).strip())
    click.echo("")
    click.echo("Task2:")
    click.echo(str(payload.get("task2", "")).strip())


@cli.command()
def wizard():
    """Interactive wizard to configure and run a task."""
    category = click.prompt("Category", type=click.Choice(RESEARCH_CATEGORIES))
    tasks = sorted((BENCHMARK_DIR / category).glob("*.json"))
    if not tasks:
        raise click.ClickException(f"No tasks found for category {category}")
    task_names = [task.stem for task in tasks]
    instance_id = click.prompt("Instance ID", type=click.Choice(task_names))
    task_level = click.prompt("Task level", type=click.Choice(["task1", "task2"]), default="task1")
    model = click.prompt("Model (leave blank for default)", default="", show_default=False)
    port = click.prompt("Docker port", default=12380, type=int)
    max_iter = click.prompt("Max iterations (0 for unlimited)", default=0, type=int)
    no_docker = click.confirm("Run without Docker?", default=False)
    dry_run = click.confirm("Dry run only?", default=False)

    run_task(
        category=category,
        instance_id=instance_id,
        model=model or None,
        task_level=task_level,
        port=port,
        max_iter=max_iter,
        no_docker=no_docker,
        dry_run=dry_run,
    )


@cli.command()
@click.option('--category', '-c', default=None,
              type=click.Choice(RESEARCH_CATEGORIES),
              help='Research category')
@click.option('--instance-id', '-i', default=None,
              help='Instance ID of the benchmark task')
@click.option('--task-level', '-l', default='task1',
              type=click.Choice(['task1', 'task2']),
              help='Task level: task1 (detailed idea) or task2 (reference-based)')
@click.option('--model', '-m', default=None,
              help='Model name used for the run (default: COMPLETION_MODEL env var)')
@click.option('--show', is_flag=True,
              help='Print the metadata JSON to stdout')
@click.option('--latest', is_flag=True,
              help='Return the most recent run metadata in workplace_paper')
@click.option('--open', 'open_file', is_flag=True,
              help='Open the metadata file in the default viewer')
def metadata(category: str, instance_id: str, task_level: str, model: str, show: bool, latest: bool, open_file: bool):
    """Locate and optionally print run metadata."""
    import os
    import json
    import subprocess
    from pathlib import Path
    from research_agent.constant import COMPLETION_MODEL

    if latest:
        root = Path.cwd() / "workplace_paper"
        candidates = list(root.rglob("run_metadata.json"))
        if not candidates:
            raise click.ClickException("No run metadata found under workplace_paper")
        candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        metadata_path = candidates[0]
    else:
        if not category or not instance_id:
            raise click.ClickException("Provide --category and --instance-id, or use --latest")
        model = model or os.getenv("COMPLETION_MODEL") or COMPLETION_MODEL
        metadata_path = resolve_run_metadata_path(instance_id, task_level, model)

    if not metadata_path.exists():
        raise click.ClickException(f"Run metadata not found: {metadata_path}")

    click.echo(str(metadata_path))
    if show:
        with metadata_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        click.echo(json.dumps(payload, indent=2, ensure_ascii=True))
    if open_file:
        if sys.platform.startswith("darwin"):
            command = ["open", str(metadata_path)]
        elif sys.platform.startswith("win"):
            command = ["cmd", "/c", "start", "", str(metadata_path)]
        else:
            command = ["xdg-open", str(metadata_path)]
        subprocess.run(command, check=False)


@cli.command()
@click.option('--category', '-c', default=None,
              type=click.Choice(RESEARCH_CATEGORIES),
              help='Research category')
@click.option('--instance-id', '-i', default=None,
              help='Instance ID of the benchmark task')
@click.option('--task-level', '-l', default='task1',
              type=click.Choice(['task1', 'task2']),
              help='Task level: task1 (detailed idea) or task2 (reference-based)')
@click.option('--model', '-m', default=None,
              help='Model name used for the run (default: COMPLETION_MODEL env var)')
@click.option('--latest', is_flag=True,
              help='Use the most recent run metadata in workplace_paper')
@click.option('--output-dir', default=None,
              help='Optional output directory for the bundle')
@click.option('--folder', 'as_folder', is_flag=True,
              help='Create a folder instead of a zip bundle')
def bundle(category: str, instance_id: str, task_level: str, model: str, latest: bool, output_dir: str | None, as_folder: bool):
    """Create an artifact bundle (logs + metadata + prompts) for a run."""
    import os
    from pathlib import Path
    from research_agent.constant import COMPLETION_MODEL

    if latest:
        root = Path.cwd() / "workplace_paper"
        candidates = list(root.rglob("run_metadata.json"))
        if not candidates:
            raise click.ClickException("No run metadata found under workplace_paper")
        candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        metadata_path = candidates[0]
    else:
        if not category or not instance_id:
            raise click.ClickException("Provide --category and --instance-id, or use --latest")
        model = model or os.getenv("COMPLETION_MODEL") or COMPLETION_MODEL
        metadata_path = resolve_run_metadata_path(instance_id, task_level, model)
        if not metadata_path.exists():
            raise click.ClickException(f"Run metadata not found: {metadata_path}")

    if as_folder:
        bundle_path = create_artifact_folder(metadata_path, output_dir=output_dir)
    else:
        bundle_path = create_artifact_bundle(metadata_path, output_dir=output_dir)
    click.echo(str(bundle_path))


@cli.command()
@click.option('--category', '-c', default=None,
              type=click.Choice(RESEARCH_CATEGORIES),
              help='Filter by category')
@click.option('--instance-id', '-i', default=None,
              help='Filter by instance ID')
@click.option('--limit', '-n', default=20,
              help='Limit number of rows shown')
def registry(category: str | None, instance_id: str | None, limit: int):
    """Show recent run registry entries."""
    registry_path = Path.cwd() / "workplace_paper" / "run_registry.jsonl"
    if not registry_path.exists():
        raise click.ClickException("Run registry not found: workplace_paper/run_registry.jsonl")
    rows = []
    with registry_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            instance = payload.get("instance", {})
            if category and instance.get("category") != category:
                continue
            if instance_id and instance.get("id") != instance_id:
                continue
            rows.append({
                "timestamp": payload.get("timestamp"),
                "instance_id": instance.get("id"),
                "category": instance.get("category"),
                "task_level": instance.get("task_level"),
                "model": payload.get("models", {}).get("completion_model"),
            })
    rows = list(reversed(rows))[-limit:]
    if not rows:
        click.echo("No matching entries.")
        return
    header = f"{'timestamp':24}  {'instance_id':16}  {'category':12}  {'task':6}  {'model'}"
    click.echo(header)
    click.echo("-" * len(header))
    for row in rows:
        click.echo(
            f"{str(row.get('timestamp', '')):24}  "
            f"{str(row.get('instance_id', '')):16}  "
            f"{str(row.get('category', '')):12}  "
            f"{str(row.get('task_level', '')):6}  "
            f"{str(row.get('model', ''))}"
        )


@cli.command()
@click.option('--apply', is_flag=True,
              help='Delete files instead of dry run')
def clean(apply: bool):
    """Clean runtime artifacts (logs, caches, workspaces)."""
    targets = [
        "logs",
        "terminal_tmp",
        "cache",
        "cache_*",
        "workplace",
        "workplace_paper",
        "paper_db",
        "research_agent/cache",
        "research_agent/cache_*",
        "research_agent/*_tmp",
        "research_agent/workplace_*",
        "research_agent/workspace_*",
    ]
    paths = []
    for target in targets:
        paths.extend(Path.cwd().glob(target))
    if not paths:
        click.echo("No cleanup targets found.")
        return
    for path in paths:
        click.echo(f"{'DELETE' if apply else 'DRY RUN'} {path}")
        if apply:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)


@cli.command("bench-validate")
@click.option('--category', '-c', default=None,
              type=click.Choice(RESEARCH_CATEGORIES),
              help='Filter by category')
@click.option('--json', 'as_json', is_flag=True,
              help='Output results as JSON')
def bench_validate(category: str | None, as_json: bool):
    """Validate benchmark instances and report pass/fail."""
    results = []
    categories = [category] if category else [d.name for d in BENCHMARK_DIR.iterdir() if d.is_dir()]
    for cat in categories:
        cat_path = BENCHMARK_DIR / cat
        if not cat_path.is_dir():
            continue
        for instance_path in cat_path.glob("*.json"):
            with instance_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            errors = validate_benchmark_instance_payload(payload)
            results.append({
                "category": cat,
                "instance": instance_path.stem,
                "ok": not errors,
                "errors": errors,
            })

    if as_json:
        click.echo(json.dumps(results, indent=2, ensure_ascii=True))
        return

    for item in results:
        status = "PASS" if item["ok"] else "FAIL"
        click.echo(f"[{status}] {item['category']}/{item['instance']}")
        if item["errors"]:
            for err in item["errors"]:
                click.echo(f"  - {err}")




@cli.group()
def workspace():
    """Manage project/topic research workspaces."""
    pass


@workspace.command('init')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_init(root: str):
    """Initialize a topic-oriented research workspace."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    manager.ensure_workspace()
    click.echo(f"Initialized workspace at {manager.root}")


@workspace.command('create-project')
@click.option('--name', required=True, help='Project title')
@click.option('--owner', required=True, help='Project owner')
@click.option('--slug', default=None, help='Optional project slug')
@click.option('--description', default='', help='Project description')
@click.option('--tag', 'tags', multiple=True, help='Project tags (repeatable)')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_create_project(name: str, owner: str, slug: str | None, description: str, tags: tuple[str, ...], root: str):
    """Create a project in the research workspace."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        project_dir = manager.create_project(name=name, owner=owner, slug=slug, description=description, tags=[*tags])
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(project_dir))


@workspace.command('create-topic')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--title', required=True, help='Topic title')
@click.option('--owner', required=True, help='Topic owner')
@click.option('--slug', default=None, help='Optional topic slug')
@click.option('--summary', default='', help='Topic summary')
@click.option('--category-tag', 'category_tags', multiple=True, help='Category tag (repeatable)')
@click.option('--method-tag', 'method_tags', multiple=True, help='Method tag (repeatable)')
@click.option('--task-tag', 'task_tags', multiple=True, help='Task tag (repeatable)')
@click.option('--priority', default='medium', show_default=True, type=click.Choice(['low', 'medium', 'high', 'critical']))
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_create_topic(project_slug: str, title: str, owner: str, slug: str | None, summary: str, category_tags: tuple[str, ...], method_tags: tuple[str, ...], task_tags: tuple[str, ...], priority: str, root: str):
    """Create a topic folder with metadata, tasks, and vector manifests."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        topic_dir = manager.create_topic(
            project_slug=project_slug,
            title=title,
            owner=owner,
            slug=slug,
            summary=summary,
            category_tags=[*category_tags],
            method_tags=[*method_tags],
            task_tags=[*task_tags],
            priority=priority,
        )
    except (FileNotFoundError, FileExistsError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(topic_dir))




@workspace.command('init-kg')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--topic', 'topic_slug', required=True, help='Topic slug')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_init_kg(project_slug: str, topic_slug: str, root: str):
    """Initialize a topic knowledge graph file."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        path = manager.initialize_topic_knowledge_graph(project_slug=project_slug, topic_slug=topic_slug)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(path))


@workspace.command('add-kg-node')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--topic', 'topic_slug', required=True, help='Topic slug')
@click.option('--uid', required=True, help='Node UID')
@click.option('--node-type', required=True, type=click.Choice(['Idea', 'Concept', 'Artifact', 'Claim', 'Agent', 'Dimension', 'Evidence']))
@click.option('--title', required=True, help='Node title')
@click.option('--description', default='', help='Node description')
@click.option('--tag', 'tags', multiple=True, help='Node tag (repeatable)')
@click.option('--source-ref', 'source_refs', multiple=True, help='Source reference (repeatable)')
@click.option('--properties', default='{}', help='JSON properties object')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_add_kg_node(project_slug: str, topic_slug: str, uid: str, node_type: str, title: str, description: str, tags: tuple[str, ...], source_refs: tuple[str, ...], properties: str, root: str):
    """Upsert a node in a topic knowledge graph."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        props = json.loads(properties)
        if not isinstance(props, dict):
            raise ValueError('properties must decode to a JSON object')
    except (json.JSONDecodeError, ValueError) as exc:
        raise click.ClickException(f'Invalid --properties payload: {exc}') from exc

    try:
        node = manager.upsert_knowledge_node(
            project_slug=project_slug,
            topic_slug=topic_slug,
            uid=uid,
            node_type=node_type,
            title=title,
            description=description,
            tags=[*tags],
            source_references=[*source_refs],
            properties=props,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps(node, indent=2))


@workspace.command('add-kg-dependency')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--topic', 'topic_slug', required=True, help='Topic slug')
@click.option('--uid', required=True, help='Dependency edge UID')
@click.option('--source-uid', required=True, help='Source node UID (depends on target)')
@click.option('--target-uid', required=True, help='Target node UID')
@click.option('--dependency-type', default='foundational', show_default=True, help='Dependency type')
@click.option('--dimension', 'dimensions', multiple=True, help='Dependency dimension (repeatable)')
@click.option('--confidence', default=1.0, show_default=True, type=float, help='Dependency confidence [0,1]')
@click.option('--status', default='proposed', show_default=True, help='Dependency status')
@click.option('--justification', default='', help='Natural language justification')
@click.option('--evidence-uid', 'evidence_uids', multiple=True, help='Evidence UID (repeatable)')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_add_kg_dependency(project_slug: str, topic_slug: str, uid: str, source_uid: str, target_uid: str, dependency_type: str, dimensions: tuple[str, ...], confidence: float, status: str, justification: str, evidence_uids: tuple[str, ...], root: str):
    """Add a dependency edge in a topic knowledge graph."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        edge = manager.add_knowledge_dependency(
            project_slug=project_slug,
            topic_slug=topic_slug,
            uid=uid,
            source_uid=source_uid,
            target_uid=target_uid,
            dependency_type=dependency_type,
            dimensions=[*dimensions],
            confidence=confidence,
            status=status,
            justification=justification,
            evidence_uids=[*evidence_uids],
        )
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps(edge, indent=2))


@workspace.command('show-kg')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--topic', 'topic_slug', required=True, help='Topic slug')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_show_kg(project_slug: str, topic_slug: str, root: str):
    """Print a topic knowledge graph JSON payload."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        graph = manager.get_topic_knowledge_graph(project_slug=project_slug, topic_slug=topic_slug)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps(graph, indent=2))
@workspace.command('list-topics')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--status', default=None, help='Optional status filter')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_list_topics(project_slug: str, status: str | None, root: str):
    """List topics for a project."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        topics = manager.list_topics(project_slug=project_slug, status=status)
    except (FileNotFoundError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    if not topics:
        click.echo('No topics found.')
        return

    for topic in topics:
        slug = topic.get('slug', '<missing-slug>')
        title = topic.get('title', '<missing-title>')
        status_value = topic.get('status', '<missing-status>')
        priority_value = topic.get('priority', '<missing-priority>')
        click.echo(f"{slug}: {title} [{status_value}, priority={priority_value}]")


@workspace.command('add-task')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--topic', 'topic_slug', required=True, help='Topic slug')
@click.option('--task-id', required=True, help='Task identifier (e.g. literature_discovery)')
@click.option('--title', required=True, help='Task title')
@click.option('--status', default='queued', show_default=True, type=click.Choice(['queued', 'ready', 'running', 'blocked', 'done']))
@click.option('--priority', default='medium', show_default=True, type=click.Choice(['low', 'medium', 'high', 'critical']))
@click.option('--depends-on', multiple=True, help='Task IDs this task depends on')
@click.option('--rationale', default='', help='Why this task was added')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_add_task(project_slug: str, topic_slug: str, task_id: str, title: str, status: str, priority: str, depends_on: tuple[str, ...], rationale: str, root: str):
    """Add a task to a topic backlog."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        task = manager.add_backlog_task(
            project_slug=project_slug,
            topic_slug=topic_slug,
            task_id=task_id,
            title=title,
            status=status,
            priority=priority,
            depends_on=[*depends_on],
            rationale=rationale,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps(task, indent=2))


@workspace.command('recommend-tasks')
@click.option('--project', 'project_slug', required=True, help='Project slug')
@click.option('--topic', 'topic_slug', required=True, help='Topic slug')
@click.option('--root', default='research_workspace', show_default=True, help='Workspace root directory')
def workspace_recommend_tasks(project_slug: str, topic_slug: str, root: str):
    """Suggest next tasks for a topic backlog."""
    from research_agent.workspace_manager import WorkspaceManager

    manager = WorkspaceManager(Path(root))
    try:
        tasks = manager.recommend_next_tasks(project_slug=project_slug, topic_slug=topic_slug)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc

    if not tasks:
        click.echo('No recommendations.')
        return

    click.echo(json.dumps(tasks, indent=2))


@cli.command()
def config():
    """Show current configuration."""
    from research_agent.constant import (
        COMPLETION_MODEL, CHEEP_MODEL, EMBEDDING_MODEL,
        API_BASE_URL, BASE_IMAGES, GPUS
    )
    import os

    click.echo("Current AI-Researcher Configuration:")
    click.echo(f"  Completion Model: {COMPLETION_MODEL}")
    click.echo(f"  Cheap Model: {CHEEP_MODEL}")
    click.echo(f"  Embedding Model: {EMBEDDING_MODEL}")
    click.echo(f"  API Base URL: {API_BASE_URL or 'default'}")
    click.echo(f"  Docker Image: {BASE_IMAGES}")
    click.echo(f"  GPUs: {GPUS}")

    # Check API key status
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    click.echo(f"  API Key: {'configured' if api_key else 'NOT SET'}")

    ollama = os.getenv('OLLAMA_BASE_URL')
    click.echo(f"  Ollama: {ollama or 'not configured'}")


@cli.command()
def doctor():
    """Check system requirements and configuration."""
    import shutil
    import os

    click.echo("AI-Researcher System Check")
    click.echo("=" * 40)

    # Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    click.echo(f"Python: {py_version} {'OK' if py_ok else 'WARNING (3.11+ recommended)'}")

    # Docker
    docker = shutil.which('docker')
    click.echo(f"Docker: {'found' if docker else 'NOT FOUND'}")

    # API Keys
    openrouter = bool(os.getenv('OPENROUTER_API_KEY'))
    openai = bool(os.getenv('OPENAI_API_KEY'))
    click.echo(f"OpenRouter API Key: {'configured' if openrouter else 'not set'}")
    click.echo(f"OpenAI API Key: {'configured' if openai else 'not set'}")

    # Ollama
    ollama_url = os.getenv('OLLAMA_BASE_URL')
    if ollama_url:
        import requests
        try:
            resp = requests.get(f"{ollama_url}/api/version", timeout=2)
            click.echo(f"Ollama: running (v{resp.json().get('version', 'unknown')})")
        except requests.exceptions.RequestException:
            click.echo(f"Ollama: configured but not responding at {ollama_url}")
    else:
        click.echo("Ollama: not configured")

    # Key dependencies
    click.echo("\nKey Dependencies:")
    deps = ['litellm', 'chromadb', 'playwright', 'gradio']
    for dep in deps:
        try:
            __import__(dep)
            click.echo(f"  {dep}: OK")
        except ImportError:
            click.echo(f"  {dep}: NOT INSTALLED")

    click.echo("\n" + "=" * 40)
    if (openrouter or openai) and py_ok:
        click.echo("System is ready to run AI-Researcher!")
    else:
        click.echo("Please address the issues above before running.")


if __name__ == '__main__':
    cli()

"""Command-line interface for Task Queue System"""

import click
from pathlib import Path
from .core import TaskQueueManager


@click.group()
def cli():
    """Task Queue System - Standalone file-based task queue"""
    pass


@cli.command()
@click.option("--path", default="agent-task", help="Queue root directory")
def init(path):
    """Initialize queue directories"""
    queue = TaskQueueManager(queue_root=path)
    click.echo(f"✓ Queue initialized at {path}")
    click.echo(f"  - {queue.queue_dir}")
    click.echo(f"  - {queue.completed_dir}")
    click.echo(f"  - {queue.later_dir}")


@cli.command()
@click.option("--path", default="agent-task", help="Queue root directory")
def status(path):
    """Show queue status"""
    queue = TaskQueueManager(queue_root=path)
    stat = queue.status()

    click.echo("\n📋 Queue Status")
    click.echo(f"  Queued: {len(stat.queue)}")
    click.echo(f"  Completed: {len(stat.completed)}")
    click.echo(f"  Deferred: {len(stat.later)}")
    click.echo(f"  Total: {stat.total_tasks}")
    click.echo(f"  Success Rate: {stat.success_rate:.1f}%")

    if stat.queue:
        click.echo("\n📌 Pending Tasks:")
        for task in stat.queue[:5]:
            click.echo(f"  - {task}")
        if len(stat.queue) > 5:
            click.echo(f"  ... and {len(stat.queue) - 5} more")


@cli.command()
@click.option("--path", default="agent-task", help="Queue root directory")
@click.option("--timeout", default=60, help="Timeout in seconds")
@click.option("--limit", default=None, type=int, help="Max tasks to run")
def run(path, timeout, limit):
    """Run all queued tasks"""
    queue = TaskQueueManager(queue_root=path)
    results = queue.run_queue(limit=limit, timeout_seconds=timeout)

    click.echo(f"\n✓ Processed {len(results)} tasks\n")

    success_count = sum(1 for r in results if r.status == "executed")
    failed_count = sum(1 for r in results if r.status == "failed")

    for result in results:
        status_icon = "✓" if result.status == "executed" else "✗"
        click.echo(f"{status_icon} {result.name} ({result.status})")
        if result.duration_ms:
            click.echo(f"  Duration: {result.duration_ms}ms")

    click.echo(f"\nSummary: {success_count} succeeded, {failed_count} failed")


@cli.command()
@click.option("--path", default="agent-task", help="Queue root directory")
def promote(path):
    """Promote tasks from later/ to queue/"""
    queue = TaskQueueManager(queue_root=path)
    moved = queue.promote_later_to_queue()

    if moved:
        click.echo(f"✓ Promoted {len(moved)} tasks:")
        for task in moved:
            click.echo(f"  - {task}")
    else:
        click.echo("ℹ No deferred tasks to promote")


@cli.command()
@click.option("--path", default="agent-task", help="Queue root directory")
def metrics(path):
    """Show queue metrics"""
    queue = TaskQueueManager(queue_root=path)
    stats = queue.get_metrics()

    click.echo("\n📊 Queue Metrics")
    click.echo(f"  Total Tasks: {stats.total_tasks}")
    click.echo(f"  Completed: {stats.completed_tasks}")
    click.echo(f"  Failed: {stats.failed_tasks}")
    click.echo(f"  Success Rate: {stats.success_rate:.1f}%")
    click.echo(f"  Queue Depth: {stats.queue_depth}")


@cli.command()
@click.option("--path", default="agent-task", help="Queue root directory")
@click.option("--older-than", default=30, help="Days to keep")
def cleanup(path, older_than):
    """Clean old completed tasks"""
    queue = TaskQueueManager(queue_root=path)
    removed = queue.cleanup_old_completed(days=older_than)
    click.echo(f"✓ Removed {removed} old tasks")


@cli.command()
@click.option("--path", default="agent-task", help="Queue root directory")
def archive(path):
    """Archive completed tasks"""
    queue = TaskQueueManager(queue_root=path)
    archive_path = queue.archive_completed()
    click.echo(f"✓ Archive created: {archive_path}")


if __name__ == "__main__":
    cli()

import click
import json
from collections import Counter
from queuectl.core.storage import RedisStorage
from queuectl.core.queue_manager import get_active_workers

storage = RedisStorage()

@click.command()
def status():
    """
    Show a summary of job statuses and active workers.
    """
    click.echo("📋 QueueCTL Status")
    click.echo("──────────────────────────────")

    # === JOB STATUS SUMMARY ===
    click.echo("\n🧱 Jobs Summary:")
    try:
        job_keys = storage.r.keys("queuectl:job:*")
        if not job_keys:
            click.echo("No jobs found.")
        else:
            status_counts = Counter()
            for key in job_keys:
                job = storage.r.hgetall(key)
                status = job.get("status", "unknown")
                status_counts[status] += 1

            total_jobs = sum(status_counts.values())
            for state, count in sorted(status_counts.items()):
                click.echo(f"  {state}: {count}")
            click.echo(f"  total: {total_jobs}")

    except Exception as e:
        click.echo(f"⚠️ Error fetching job status: {e}")

    # === WORKER STATUS ===
    click.echo("\n⚙️ Workers:")
    try:
        active_workers = get_active_workers()
        if not active_workers:
            click.echo("No active workers running.")
        else:
            for worker_name, info in active_workers.items():
                status = info.get("status", "unknown")
                current_job = info.get("current_job", "—")
                click.echo(f"  {worker_name} → {status} (job: {current_job})")
    except Exception as e:
        click.echo(f"⚠️ Unable to retrieve worker status: {e}")

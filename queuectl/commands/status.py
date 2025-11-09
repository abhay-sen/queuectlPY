import click
import json
from queuectl.core.storage import RedisStorage
from queuectl.core.queue_manager import get_active_workers

storage = RedisStorage()

@click.command()
def status():
    """
    Show the current status of all jobs and active workers.
    """
    click.echo("📋 QueueCTL Status")
    click.echo("──────────────────────────────")

    # === JOB STATUS ===
    click.echo("\n🧱 Jobs:")
    try:
        job_keys = storage.r.keys("queuectl:job:*")
        if not job_keys:
            click.echo("No jobs found.")
        else:
            for key in job_keys:
                job = storage.r.hgetall(key)
                job_id = key.split(":")[-1]
                status = job.get("status", "unknown")
                date_added = job.get("date_added", "-")
                data = job.get("data", "{}")
                try:
                    data = json.loads(data)
                except Exception:
                    pass
                command = data.get("command") if isinstance(data, dict) else str(data)
                click.echo(f"[{job_id}] {command} - {status} ({date_added})")

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
                click.echo(f"{worker_name} → {status} (job: {current_job})")

    except Exception:
        click.echo("Unable to retrieve worker status.")

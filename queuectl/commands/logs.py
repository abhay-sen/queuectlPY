import os
import click
from queuectl.core.storage import RedisStorage

storage = RedisStorage()

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")


@click.command("logs")
@click.argument("job_id")
def view_logs(job_id):
    """
    View the logs for a specific job.
    Usage: queuectl logs <job_id>
    """
    log_path = os.path.join(LOG_DIR, f"{job_id}.log")

    # Check Redis if file path is stored (optional fallback)
    redis_log_path = storage.r.hget(f"queuectl:jobs:{job_id}", "log_file")
    if redis_log_path and os.path.exists(redis_log_path):
        log_path = redis_log_path

    if not os.path.exists(log_path):
        click.echo(f"❌ No logs found for job {job_id}")
        return

    click.echo(f"📄 Logs for job {job_id}:\n" + "-" * 50)
    with open(log_path, "r") as f:
        click.echo(f.read())

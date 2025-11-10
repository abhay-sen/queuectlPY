import click
import json
from queuectl.core.storage import RedisStorage

storage = RedisStorage()

@click.group(help="Manage the Dead Letter Queue (DLQ)")
def dlq():
    pass


# -----------------------------------------------------------
# 🪦 LIST DLQ JOBS (uses job_keys pattern)
# -----------------------------------------------------------
@dlq.command("list", help="List all jobs in the Dead Letter Queue")
def list_dlq():
    dlq_job_ids = storage.r.lrange("queuectl:dead_letter", 0, -1)

    if not dlq_job_ids:
        click.echo("✅ DLQ is empty.")
        return

    click.echo("🪦 Dead Letter Queue Jobs:")
    click.echo("=" * 60)

    count = 0
    for job_id in dlq_job_ids:
        job_key = f"queuectl:jobs:{job_id}"
        job = storage.r.hgetall(job_key)

        if not job:
            continue

        status = job.get("status", "dead")
        reason = job.get("reason", "No reason provided")
        failed_at = job.get("failed_at", "?")
        date_added = job.get("date_added", "-")
        data_raw = job.get("data", "{}")

        # Try to extract command
        try:
            data = json.loads(data_raw)
            command = data.get("command", str(data_raw))
        except Exception:
            command = str(data_raw)

        click.echo(f"[{job_id}] {command} - {status} ({date_added})")
        click.echo(f"   └─ Reason: {reason}")
        click.echo(f"   └─ Failed at: {failed_at}")
        click.echo("-" * 60)
        count += 1

    click.echo(f"Total: {count} DLQ jobs.")


# -----------------------------------------------------------
# ♻️ RETRY SPECIFIC DLQ JOB (also uses job_id pattern)
# -----------------------------------------------------------
@dlq.command("retry", help="Retry a specific DLQ job by ID")
@click.argument("job_id")
def retry_dlq(job_id):
    job_key = f"queuectl:jobs:{job_id}"
    job = storage.r.hgetall(job_key)

    if not job:
        click.echo(f"❌ Job {job_id} not found.")
        return

    if job.get("status") != "dead":
        click.echo(f"⚠️ Job {job_id} is not in DLQ (status: {job.get('status')}).")
        return

    # Remove from DLQ list
    storage.r.lrem("queuectl:dead_letter", 0, job_id)

    # Reset job metadata
    storage.r.hset(job_key, mapping={
        "status": "pending",
        "reason": "",
        "failed_at": "",
        "attempts": 0,
        "last_error": "",
        "next_retry_at": ""
    })

    # Push back to main queue
    storage.r.lpush("queuectl:jobs", job_id)

    click.echo(f"♻️ Job {job_id} requeued successfully from DLQ → main queue.")


if __name__ == "__main__":
    dlq()

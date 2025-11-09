import subprocess
from queuectl.core.storage import RedisStorage
import click
import json
storage = RedisStorage()

def should_stop():
    """Check if stop signal is active."""
    return storage.r.get("queuectl:stop_signal") == "true"

def set_stop_signal():
    """Activate the stop signal for all workers."""
    storage.r.set("queuectl:stop_signal", "true")

def clear_stop_signal():
    """Deactivate the stop signal before starting workers."""
    storage.r.delete("queuectl:stop_signal")
    
def enqueue_job(data):
    job_id = storage.enqueue_job(data)
    print(f"✅ Job added: {job_id}")
    return job_id

def list_jobs(state_filter=None):
    """
    Lists jobs, optionally filtering by a specific state.
    """
    
    # --- Handle specific list-based states first ---
    
    if state_filter == 'dead':
        click.echo("📋 Inspecting 'dead' jobs...")
        click.echo("🪦 Jobs in Dead Letter Queue (DLQ):")

        dlq_jobs = storage.list_dlq()
        if not dlq_jobs:
            click.echo("DLQ is empty.")
            return

        count = 0
        for job in dlq_jobs:
            status = job.get("status", "dead")
            date_added = job.get("date_added", "?")
            data = job.get("data", {})
            error = job.get("error", "No error info")

            # Extract command (from dict or str)
            if isinstance(data, dict):
                command = data.get("command", "N/A")
            else:
                command = str(data)

            click.echo(f"[{status}][{date_added}] {command} ❌ {error}")
            count += 1

        click.echo(f"Total: {count} jobs")
        return


    if state_filter == 'pending':
        click.echo("Pending jobs in main queue:")
        # This assumes your pending queue is a list named 'queuectl:queue'
        pending_jobs = storage.list_pending()
        if not pending_jobs:
            click.echo("Pending queue is empty.")
            return
        for j in pending_jobs:
            print(f"[{j.get('status', '?')}][{j.get('date_added','?')}] {j.get('data', '{}')}")
        print(f"Total: {len(pending_jobs)} jobs")
        return
    
    if state_filter == 'failed':
        click.echo("Failed jobs:")
        list_failed_jobs()
        return
    
    if state_filter == 'processing':
        click.echo("Processing jobs:")
        list_processing_jobs()
        return
    
    if state_filter == 'completed':
        click.echo("Completed jobs:")
        list_completed_jobs()
        return

    # --- Handle hash-based states (or all jobs) ---
    
    click.echo("Inspecting all job records...")
    job_keys = storage.r.keys("queuectl:job:*")
    
    if not job_keys:
        click.echo("No jobs found in database.")
        return

    count = 0
    for key in job_keys:
        job = storage.r.hgetall(key)
        status = job.get("status", "unknown")
        
        # If a filter is active, skip non-matching statuses
        if state_filter and status != state_filter:
            continue
            
        # Passed filter (or no filter), so print it
        job_id = key.split(":")[-1]
        command = job.get("data", "{}")
        date_added = job.get("date_added", "-")
        
        click.echo(f"[{job_id}] {command} - {status} ({date_added})")
        count += 1
        
    if count == 0 and state_filter:
        click.echo(f"No jobs found with state '{state_filter}'.")

def list_failed_jobs():
    jobs = storage.list_failed()
    for j in jobs:
        print(f"[FAILED] {j.get('data', '{}')} → attempts: {j.get('attempts', 0)}")
    print(f"Total Failed: {len(jobs)} jobs")


def list_processing_jobs():
    jobs = storage.list_processing()
    for j in jobs:
        print(f"[PROCESSING] {j.get('data', '{}')} → started_at: {j.get('started_at')}")
    print(f"Total Processing: {len(jobs)} jobs")


def list_completed_jobs():
    jobs = storage.list_completed()
    for j in jobs:
        print(f"[COMPLETED] {j.get('data', '{}')} → completed_at: {j.get('completed_at')}")
    print(f"Total Completed: {len(jobs)} jobs")


def list_all_jobs():
    jobs = storage.list_jobs()
    for j in jobs:
        print(f"[{j.get('status', '?')}][{j.get('date_added','?')}] {j.get('data', '{}')}")
    print(f"Total: {len(jobs)} jobs")


def list_dlq_jobs():
    jobs = storage.list_dlq()
    for j in jobs:
        print(f"[DLQ] {j.get('data', '{}')} → reason: {j.get('reason')}")
    print(f"Total DLQ: {len(jobs)} jobs")

def get_active_workers():
    import redis
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    workers = {}
    for key in r.keys("queuectl:worker:*"):
        workers[key.split(":")[-1]] = r.hgetall(key)
    return workers


def process_next_job(worker_name="Worker"):
    job_id, data = storage.get_next_job()
    if not job_id:
        # Less noisy output
        return

    print(f"👷 {worker_name} picked job {job_id}: {data}")

    try:
        command = data.get("command")
        if not command:
            raise ValueError("No command found in job data")

        # === FIX 1: Mark job as processing ===
        storage.r.hset(f"queuectl:job:{job_id}", mapping={
            "status": "processing",
        })

        # === FIX 2: Update worker state ===
        storage.r.hset(
            f"queuectl:worker:{worker_name}",
            "current_job",
            f"Job-{job_id} ({command})"
        )

        # Execute the shell command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        # Job completed
        if result.returncode == 0:
            output = result.stdout.strip() or "(no output)"
            storage.mark_completed(job_id, output)
            print(f"✅ Job {job_id} completed successfully:\n{output}")
        else:
            error_msg = result.stderr.strip() or f"Command failed with code {result.returncode}"
            raise Exception(error_msg)

    except Exception as e:
        storage.mark_failed(job_id, str(e))

    finally:
        # === FIX 3: Reset worker to idle ===
        storage.r.hset(
            f"queuectl:worker:{worker_name}",
            "current_job",
            "idle"
        )
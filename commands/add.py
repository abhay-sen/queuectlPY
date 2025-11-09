import click
import time
from core.storage import load_jobs, save_jobs
from core.queue_manager import get_queue
import json, uuid, redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
@click.command()
@click.argument("command")
def add(command):
    """Add a job to the queue."""
    jobs = load_jobs()
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "command": command,
        "status": "queued",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    jobs.append(job)
    save_jobs(jobs)
    
    # Also add to the live in-memory queue in case workers are already running
    get_queue().put(job)
    
    click.echo(f"✅ Job {job_id} added: {command}")
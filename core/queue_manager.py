import queue
from core.storage import load_jobs

# This is the single, shared in-memory queue
_job_queue = queue.Queue()

def get_queue():
    """Returns the singleton job queue instance."""
    return _job_queue

def populate_queue():
    """
    Loads all 'queued' jobs from persistent storage
    into the in-memory queue for workers to process.
    """
    print("Loading pending jobs into queue...")
    jobs = load_jobs()
    count = 0
    for job in jobs:
        if job["status"] == "queued":
            _job_queue.put(job)
            count += 1
    print(f"Loaded {count} jobs.")
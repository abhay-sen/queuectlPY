import json
import os
import threading

JOBS_FILE = "jobs.json"
# The lock is now part of the storage module to protect all file access
lock = threading.Lock()

def load_jobs():
    """Safely loads the job list from the JSON file."""
    with lock:
        if not os.path.exists(JOBS_FILE):
            return []
        try:
            with open(JOBS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Handle case where file is empty or corrupt
            return []

def save_jobs(jobs):
    """Safely saves the job list to the JSON file."""
    with lock:
        with open(JOBS_FILE, "w") as f:
            json.dump(jobs, f, indent=4)

def update_job_status(job_id, status):
    """Finds a single job by ID and updates its status."""
    jobs = load_jobs()
    job_found = False
    for job in jobs:
        if job["id"] == job_id:
            job["status"] = status
            job_found = True
            break
    
    if job_found:
        save_jobs(jobs)
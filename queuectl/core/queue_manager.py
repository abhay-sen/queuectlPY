import subprocess
from queuectl.core.storage import RedisStorage

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

def process_next_job(worker_name="Worker"):
    job_id, data = storage.get_next_job()
    if not job_id:
        print("No jobs available.")
        return

    print(f"👷 {worker_name} picked job {job_id}: {data}")

    try:
        command = data.get("command")
        if not command:
            raise ValueError("No command found in job data")

        # Execute the shell command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        # Check if it succeeded
        if result.returncode == 0:
            output = result.stdout.strip() or "(no output)"
            storage.mark_completed(job_id, output)
            print(f"✅ Job {job_id} completed successfully:\n{output}")
        else:
            error_msg = result.stderr.strip() or f"Command failed with code {result.returncode}"
            raise Exception(error_msg)

    except Exception as e:
        # 🔄 Instead of immediately moving to DLQ,
        # use mark_failed() to handle retries with exponential backoff
        storage.mark_failed(job_id, str(e))

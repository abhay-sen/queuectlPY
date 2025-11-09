import subprocess
from core.storage import RedisStorage

storage = RedisStorage()

def add_job(data):
    job_id = storage.add_job(data)
    print(f"✅ Job added: {job_id}")
    return job_id


def list_all_jobs():
    jobs = storage.list_jobs()
    for j in jobs:
        print(f"[{j.get('status', '?')}] {j.get('data', '{}')}")
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

        # ✅ Actually execute the command (shell command)
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
        storage.move_to_dlq(job_id, str(e))
        print(f"❌ Job {job_id} failed → moved to DLQ\nReason: {e}")

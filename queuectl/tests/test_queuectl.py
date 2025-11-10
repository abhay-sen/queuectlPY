import time
import pytest
import subprocess
from click.testing import CliRunner
from queuectl.cli import cli
from queuectl.core.storage import RedisStorage

storage = RedisStorage()


@pytest.fixture(autouse=True)
def clean_redis():
    """Clean Redis before and after each test."""
    storage.r.flushdb()
    yield
    storage.r.flushdb()


def run_in_new_terminal(command: list[str]):
    """
    Simulates running a CLI command in a new terminal window.
    Runs it as a subprocess so it doesn't block the test process.
    """
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_and_wait(command: list[str]):
    """Runs a command and waits for it to finish."""
    proc = subprocess.run(command, capture_output=True, text=True)
    return proc


def test_enqueue_and_list_jobs():
    runner = CliRunner()

    # Enqueue a new job
    result = runner.invoke(cli, ["enqueue", "echo Hello Queue"])
    assert result.exit_code == 0
    time.sleep(1)  # give time for Redis to update
    # List jobs
    list_result = runner.invoke(cli, ["list", "--state", "pending"])
    assert "Hello Queue" in list_result.output


def test_worker_processes_job():
    runner = CliRunner()

    # Enqueue a job
    runner.invoke(cli, ["enqueue", "echo Hello Worker"])
    time.sleep(1)  # give time for Redis to update
    # Start worker in a new terminal (subprocess)
    worker_proc = run_in_new_terminal(["queuectl", "worker", "start"])
    time.sleep(3)  # give the worker time to start and process the job

    # Verify job completion
    job_keys = storage.r.keys("queuectl:jobs:*")
    assert job_keys, "No job keys found in Redis!"
    job_data = storage.r.hgetall(job_keys[0])
    assert job_data["status"] == "completed"

    # Stop worker gracefully
    runner.invoke(cli, ["worker", "stop"])
    worker_proc.terminate()


def test_failed_job_goes_to_dlq():
    runner = CliRunner()

    # Configure system to retry once before sending to DLQ
    result = runner.invoke(cli, ["config", "set", "--max-retries", "1"])
    assert result.exit_code == 0

    # Enqueue a failing job
    result = runner.invoke(cli, ["enqueue","invalid_command_xyz"])
    assert result.exit_code == 0

    # Start worker in background (simulating a new terminal)
    worker_proc = run_in_new_terminal(["queuectl", "worker", "start"])
    time.sleep(10)  # Give time for retries + DLQ movement

    # ✅ Use the storage.list_dlq() abstraction
    dlq_jobs = storage.list_dlq()

    # Assertions
    assert isinstance(dlq_jobs, list)
    assert len(dlq_jobs) == 1, f"Expected 1 job in DLQ, found {len(dlq_jobs)}"

    job = dlq_jobs[0]
    assert job.get("status") == "dead", f"DLQ job status mismatch: {job}"

    # Stop the worker
    runner.invoke(cli, ["worker", "stop"])
    worker_proc.terminate()



def test_retry_and_backoff_logic():
    runner = CliRunner()

    # Enqueue with retry configuration
    runner.invoke(cli, ["config","set",
        "--max-retries", "3",
        "--backoff-base", "1",
        "--backoff-factor", "2"])
    runner.invoke(cli, [
        "enqueue","invalid_command_xyz"
    ])

    # Start worker in background
    worker_proc = run_in_new_terminal(["queuectl", "worker", "start"])
    time.sleep(2.5)  # give time for retries and DLQ processing

    failed_jobs = storage.list_failed()
    assert len(failed_jobs) == 1
    assert int(failed_jobs[0]["attempts"]) == 2
    assert failed_jobs[0]["status"] == "failed"

    runner.invoke(cli, ["worker", "stop"])
    worker_proc.terminate()


def test_stop_and_resume_workers():
    runner = CliRunner()

    # Start worker in background
    worker_proc = run_in_new_terminal(["queuectl", "worker", "start"])
    time.sleep(2)

    # Send stop signal from a different "terminal"
    runner.invoke(cli, ["worker", "stop"])
    assert storage.r.get("queuectl:stop_signal") == "true"

    # Resume workers again
    runner.invoke(cli, ["worker", "resume"])
    assert not storage.r.get("queuectl:stop_signal")

    worker_proc.terminate()


def test_clear_queues():
    runner = CliRunner()

    runner.invoke(cli, ["enqueue", "echo", "Test Job"])
    runner.invoke(cli, ["queue", "clear"])

    assert storage.r.llen("queuectl:queue") == 0

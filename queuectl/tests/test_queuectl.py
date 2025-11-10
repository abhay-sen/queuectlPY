import time
import pytest
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


def test_enqueue_and_list_jobs():
    runner = CliRunner()
    result = runner.invoke(cli, ["enqueue", "echo Hello Queue"])
    assert result.exit_code == 0

    # If your CLI uses `list` to show jobs
    list_result = runner.invoke(cli, ["list", "--state", "pending"])
    assert result.exit_code == 0
    assert "Hello Queue" in list_result.output


def test_worker_processes_job():
    runner = CliRunner()

    # 1️⃣ Enqueue a job
    result = runner.invoke(cli, ["enqueue", "echo Hello Worker"])
    assert result.exit_code == 0

    # 2️⃣ Run one worker in test mode
    result = runner.invoke(cli, ["worker", "start", "--once"])
    assert result.exit_code == 0
    assert "✅ One job processed" in result.output

    # 3️⃣ Verify job completion
    job_keys = storage.r.keys("queuectl:job:*")
    assert job_keys, "No job keys found in Redis!"
    job_data = storage.r.hgetall(job_keys[0])
    assert job_data["status"] == "completed"

    runner.invoke(cli, ["worker", "stop"])


def test_failed_job_goes_to_dlq():
    runner = CliRunner()

    runner.invoke(cli, ["enqueue", "invalid_command_xyz"])
    runner.invoke(cli, ["worker", "start"])

    dlq_jobs = storage.r.lrange("queuectl:dlq", 0, -1)
    assert len(dlq_jobs) == 1


def test_retry_and_backoff_logic():
    runner = CliRunner()

    # enqueue with retries
    runner.invoke(cli, [
        "enqueue", "invalid_command_xyz",
        "--max-retries", "3",
        "--backoff-base", "1",
        "--backoff-factor", "2"
    ])

    # process multiple times
    for _ in range(4):
        runner.invoke(cli, ["worker", "start", "--once"])
        time.sleep(0.5)

    job_keys = storage.r.keys("queuectl:job:*")
    job_data = storage.r.hgetall(job_keys[0])
    assert int(job_data.get("retries", 0)) == 3
    assert job_data["status"] == "failed"


def test_stop_and_resume_workers():
    runner = CliRunner()

    runner.invoke(cli, ["worker", "start", "--once"])
    runner.invoke(cli, ["worker", "stop"])
    assert storage.r.get("queuectl:stop_signal") == "true"

    runner.invoke(cli, ["worker", "resume"])
    assert not storage.r.get("queuectl:stop_signal")


def test_clear_queues():
    runner = CliRunner()

    runner.invoke(cli, ["enqueue", "echo Test Job"])
    runner.invoke(cli, ["queue", "clear"])
    assert storage.r.llen("queuectl:queue") == 0

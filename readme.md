## usage video
https://drive.google.com/file/d/15AchhUu048CvUcMg2L1v5vHQTSa3jP27/view?usp=sharing


## 🧩 Installation

You can install QueueCTL directly from the GitHub repository to start using the CLI tool on your system.

### 1. Clone the Repository

```bash
git clone [https://github.com/abhay-sen/queuectlPY.git](https://github.com/abhay-sen/queuectlPY.git)
cd queuectlPY
````

### 2\. (Optional but Recommended) Create a Virtual Environment

It’s best practice to isolate dependencies for your project.

```bash
python -m venv venv
source venv/bin/activate     # On macOS/Linux
venv\Scripts\activate        # On Windows
```

### 3\. Install Dependencies

Use pip to install all required packages.

```bash
pip install -r requirements.txt
```

### 4\. Install the CLI Tool Locally

Once dependencies are installed, install the package in editable mode so the `queuectl` command becomes available on your system.

```bash
pip install -e .
```

### 5\. Verify Installation

Run the following command to confirm everything is working:

```bash
queuectl --help
```

If you see the help menu, your installation was successful ✅

```
```


## 🧾 Command Reference

Here’s a list of all available `queuectl` commands with their purpose and example usage.

---

### ⚙️ Configuration Management

Manage global retry and backoff settings for your job queue.

| Command                                                                         | Description                                                      | Example                                                                   |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `queuectl config show`                                                          | Show the current configuration (max retries, backoff base, etc.) | `queuectl config show`                                                    |
| `queuectl config set --max-retries <n> --backoff-base <b> --backoff-factor <f>` | Update retry/backoff configuration                               | `queuectl config set --max-retries 5 --backoff-base 2 --backoff-factor 3` |
| `queuectl config reset`                                                         | Reset configuration to default values                            | `queuectl config reset`                                                   |

---

### 🧱 Job Management

| Command                                            | Description                                                                                 | Example                                  |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `queuectl enqueue "<command>"`                     | Add a new job to the queue                                                                  | `queuectl enqueue "echo 'Hello world'"`  |
| `queuectl enqueue --timeout <seconds> "<command>"` | Add a job with a custom timeout                                                             | `queuectl enqueue --timeout 30 "ls -la"` |
| `queuectl list [--state <status>]`            | List all jobs, or filter by status (`pending`, `processing`, `completed`, `failed`, `dead`) | `queuectl list --state failed`      |

---

### 🧵 Worker Management

| Command                               | Description                                      | Example                           |
| ------------------------------------- | ------------------------------------------------ | --------------------------------- |
| `queuectl worker start [--count <n>]` | Start one or more worker threads to process jobs | `queuectl worker start --count 2` |
| `queuectl worker stop`                | Stop all workers gracefully                      | `queuectl worker stop`            |


---

### 🪦 Dead Letter Queue (DLQ)

Handle jobs that permanently failed after exceeding retry limits.

| Command                       | Description                                     | Example                    |
| ----------------------------- | ----------------------------------------------- | -------------------------- |
| `queuectl dlq list`           | View all jobs in the DLQ                        | `queuectl dlq list`        |
| `queuectl dlq retry <job_id>` | Requeue a failed job from DLQ to the main queue | `queuectl dlq retry 9fa21` |

---

### 🪵 Logging & Monitoring

| Command                  | Description                               | Example               |
| ------------------------ | ----------------------------------------- | --------------------- |
| `queuectl logs <job_id>` | View log output for a specific job        | `queuectl logs 8b3f4` |
| `queuectl status`        | Show system-wide summary (jobs + workers) | `queuectl status`     |

---


---

---

## 🚀 Usage

Once installed, `queuectl` lets you manage background jobs, workers, and queues — all through simple CLI commands.

### 🧱 Enqueue Jobs

Add a new command to the job queue for background processing:

```bash
queuectl enqueue "echo Hello, QueueCTL!"
```

Enqueue with timeout support:

```bash
queuectl enqueue --timeout 30 "python run_report.py"
```

---

### ⚙️ Manage Configuration

You can view or modify retry and backoff settings globally.

```bash
# Show current configuration
queuectl config show

# Update retry and backoff settings
queuectl config set --max-retries 3 --backoff-base 2 --backoff-factor 2

# Reset to defaults
queuectl config reset
```

---

### 🧵 Start and Manage Workers

Start background worker(s) to process queued jobs continuously:

```bash
queuectl worker start --count 2
```

Stop all workers gracefully:

```bash
queuectl worker stop
```

Resume workers after a stop:

```

---

### 🪦 Handle Failed Jobs (DLQ)

Jobs that exceed the retry limit move to the Dead Letter Queue (DLQ).

```bash
# List failed jobs
queuectl dlq list

# Retry a specific failed job
queuectl dlq retry <job_id>

# Clear DLQ completely
queuectl dlq clear
```

---

### 🪵 View Logs and System Status

Check logs or see the system overview:

```bash
queuectl logs <job_id>
queuectl status
```

---

### 🧹 Clear Queue

If needed, clear all pending jobs:

```bash
queuectl queue clear
```

---


## 🧪 Testing

QueueCTL includes a full suite of **integration tests** written using **`pytest`** to ensure all CLI commands and queue operations work correctly — from job enqueueing to worker execution, retries, and DLQ handling.

---

### ⚙️ 1. Prerequisites

Before running the tests, make sure you have:

* **Python 3.10+**
* **Redis Server** running locally on port `6379`
* All dependencies installed:

  ```bash
  pip install -r requirements.txt
  pip install pytest
  ```

> 🧠 The tests rely on a running Redis instance to store job data, so ensure Redis is active before executing the test suite:
>
> ```bash
> redis-server
> ```

---

### 🧩 2. Running Tests

Run all tests from the project root directory:

```bash
pytest -v
```

Or run a specific test file:

```bash
pytest tests/test_queuectl.py -v
```

To see live print/log output during test runs:

```bash
pytest -s -v
```

---

### 🧼 3. Test Environment Isolation

Every test automatically clears Redis before and after execution:

```python
@pytest.fixture(autouse=True)
def clean_redis():
    storage.r.flushdb()
    yield
    storage.r.flushdb()
```

This ensures tests don’t interfere with each other and run in a clean environment.

---

### 🧪 4. Test Breakdown

Here’s what each test validates:

| Test Function                  | Purpose                                                                                                |
| ------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `test_enqueue_and_list_jobs`   | Verifies that a job can be enqueued and then listed as pending in Redis.                               |
| `test_worker_processes_job`    | Ensures a running worker successfully picks up and completes a job.                                    |
| `test_failed_job_goes_to_dlq`  | Confirms that invalid jobs are retried according to config, then moved to the Dead Letter Queue (DLQ). |
| `test_retry_and_backoff_logic` | Tests exponential backoff behavior for retries and ensures failed jobs are tracked correctly.          |
| `test_stop_and_resume_workers` | Validates stop/resume signaling for worker threads via Redis flags.                                    |
| `test_clear_queues`            | Ensures the queue-clearing command removes all pending jobs.                                           |

---

### 🧰 5. Running Tests in Isolation

To debug a single test:

```bash
pytest -v -k "test_worker_processes_job"
```

To stop on the first failure:

```bash
pytest -x -v
```

---

### 🧱 6. Notes on Worker Simulation

* The tests use **subprocess calls** to simulate running workers and CLI commands in new terminals:

  ```python
  def run_in_new_terminal(command: list[str]):
      return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  ```

  This allows true concurrency testing without blocking the pytest process.

* Background workers are always terminated gracefully at the end of each test:

  ```python
  runner.invoke(cli, ["worker", "stop"])
  worker_proc.terminate()
  ```

---

### 🧩 7. Expected Behavior Summary

| Scenario           | Expected Outcome                             |
| ------------------ | -------------------------------------------- |
| Valid job          | Status → `completed`                         |
| Invalid job        | Retries → DLQ after max retries              |
| Stop signal active | All workers stop after current job           |
| Resume signal      | Workers continue processing jobs             |
| Queue clear        | Main Redis queue becomes empty (`llen == 0`) |



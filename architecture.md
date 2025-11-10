
## 🏗️ Architecture Overview

The **QueueCTL** system is built to simulate a lightweight background job queue — similar in spirit to tools like Celery or RQ — but designed as a **self-contained CLI-driven system** using **Redis** as the backbone.

---

### ⚙️ Core Components

| Layer                              | Description                                                                                                                                                      |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **CLI (Click Commands)**           | Provides user interface to enqueue jobs, manage workers, and inspect queue states. Each subcommand (e.g., `worker`, `dlq`, `config`) is a modular Click command. |
| **Storage Layer (`RedisStorage`)** | Handles job persistence using Redis. Jobs, metadata, configuration, and worker states are stored under `queuectl:*` keys.                                        |
| **Queue Manager**                  | Core logic responsible for pulling jobs from Redis, processing them, retrying failed ones with exponential backoff, and moving dead jobs to DLQ.                 |
| **Worker Threads**                 | Concurrent background threads that continuously fetch and process jobs until a stop signal is received.                                                          |
| **Dead Letter Queue (DLQ)**        | Separate Redis list for permanently failed jobs. Allows inspection and retry of dead jobs manually.                                                              |
| **Logging System**                 | Each job’s output (stdout/stderr) is written to a dedicated log file inside the `logs/` directory and can be viewed via `queuectl logs <job_id>`.                |

---

### 🔄 Job Lifecycle

```
┌────────────┐
│ Enqueue Job│
└──────┬─────┘
       │
       ▼
┌──────────────┐
│ Pending Queue│ (Redis list: queuectl:jobs)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Worker Thread│ → Executes job command
└──────┬───────┘
       │
 ┌─────┴────────────────────────────────┐
 │ Success → Mark “completed”           │
 │ Failure → Retry (exponential delay)  │
 │ Exceeded retries → Move to DLQ       │
 └──────────────────────────────────────┘
```

---

### 🧠 Retry & Backoff Strategy

Retry delay is computed exponentially as:

```
delay = backoff_base * (backoff_factor ** attempt)
```

For example, with `base=2`, `factor=2`:

* 1st retry: 2s
* 2nd retry: 4s
* 3rd retry: 8s

After exceeding `max_retries`, the job is moved to the **Dead Letter Queue**.

---

### 🧩 Redis Key Structure

| Key                    | Type       | Purpose                                        |
| ---------------------- | ---------- | ---------------------------------------------- |
| `queuectl:jobs`        | List       | Main queue storing job IDs                     |
| `queuectl:jobs:<id>`   | Hash       | Job metadata (status, attempts, command, etc.) |
| `queuectl:config`      | Hash       | Global configuration for retries/backoff       |
| `queuectl:retry_queue` | Sorted Set | Scheduled retries with next retry timestamps   |
| `queuectl:dead_letter` | List       | Failed jobs exceeding retry limit              |
| `queuectl:worker:*`    | Hash       | Active worker status information               |

---

### 🧰 Technology Stack

| Component     | Description                                |
| ------------- | ------------------------------------------ |
| **Python**    | Core programming language                  |
| **Click**     | CLI command framework                      |
| **Redis**     | In-memory data store for queue persistence |
| **Threading** | Enables concurrent worker processing       |
| **Logging**   | Job output tracking per process            |




---
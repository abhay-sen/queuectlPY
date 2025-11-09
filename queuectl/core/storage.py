# core/storage.py
import redis
import json
import uuid
import time

class RedisStorage:
    def __init__(self, host="localhost", port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    # -----------------------------
    # Job Enqueue
    # -----------------------------
    def enqueue_job(self, data, max_retries=3, backoff_base=2, backoff_factor=2):
        job_id = str(uuid.uuid4())
        job_key = f"queuectl:job:{job_id}"

        # Store job metadata
        self.r.hset(job_key, mapping={
            "date_added": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "status": "pending",
            "attempts": 0,
            "max_retries": max_retries,
            "backoff_base": backoff_base,
            "backoff_factor": backoff_factor,
            "data": json.dumps(data)
        })

        # Push to main queue (FIFO)
        self.r.lpush("queuectl:jobs", job_id)
        return job_id

    # -----------------------------
    # Job Fetch / Complete / Fail
    # -----------------------------
    def get_next_job(self):
        """Fetch next available job (FIFO)."""
        item = self.r.brpop("queuectl:jobs")
        if item is None:
            return None, None
        _, job_id = item
        job_key = f"queuectl:job:{job_id}"

        self.r.hset(job_key, "status", "processing")
        data = json.loads(self.r.hget(job_key, "data"))
        return job_id, data

    def mark_completed(self, job_id, result):
        job_key = f"queuectl:job:{job_id}"
        self.r.hset(job_key, mapping={
            "status": "completed",
            "result": json.dumps(result),
            "completed_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })

    # -----------------------------
    # Retry Handling
    # -----------------------------
    def mark_failed(self, job_id, reason):
        """Handle failed jobs: either retry or move to DLQ."""
        job_key = f"queuectl:job:{job_id}"
        attempts = int(self.r.hincrby(job_key, "attempts", 1))
        max_retries = int(self.r.hget(job_key, "max_retries"))
        base = int(self.r.hget(job_key, "backoff_base"))
        factor = int(self.r.hget(job_key, "backoff_factor"))

        if attempts > max_retries:
            self.move_to_dlq(job_id, reason)
            return

        # Calculate exponential backoff delay
        delay = base * (factor ** (attempts - 1))
        retry_time = time.time() + delay

        # Move to retry queue (sorted set with timestamp)
        self.r.zadd("queuectl:retry", {job_id: retry_time})
        self.r.hset(job_key, mapping={
            "status": "failed",
            "last_error": reason,
            "next_retry_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(retry_time))
        })
        print(f"⏳ Job {job_id} failed (attempt {attempts}), retrying in {delay:.1f}s")

    # -----------------------------
    # DLQ
    # -----------------------------
    def move_to_dlq(self, job_id, reason):
        job_key = f"queuectl:job:{job_id}"
        self.r.hset(job_key, mapping={
            "status": "dead",
            "reason": reason,
            "failed_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        })
        self.r.lpush("queuectl:dead_letter", job_id)
        print(f"💀 Job {job_id} moved to DLQ: {reason}")

    # -----------------------------
    # Retry Processor
    # -----------------------------
    def process_retry_queue(self):
        """Move ready-to-retry jobs back to main queue."""
        now = time.time()
        ready_jobs = self.r.zrangebyscore("queuectl:retry", 0, now)

        for job_id in ready_jobs:
            # Remove from retry set
            self.r.zrem("queuectl:retry", job_id)
            # Push back to active queue
            self.r.lpush("queuectl:jobs", job_id)
            self.r.hset(f"queuectl:job:{job_id}", "status", "pending")
            print(f"♻️ Job {job_id} requeued from retry queue")

    # -----------------------------
    # Listing Functions
    # -----------------------------
    def list_jobs(self):
        keys = self.r.keys("queuectl:job:*")
        jobs = []
        for k in keys:
            jobs.append(self.r.hgetall(k))
        return jobs

    def list_dlq(self):
        ids = self.r.lrange("queuectl:dead_letter", 0, -1)
        jobs = []
        for job_id in ids:
            jobs.append(self.r.hgetall(f"queuectl:job:{job_id}"))
        return jobs
    
    def list_failed(self):
        keys = self.r.keys("queuectl:job:*")
        jobs = []
        for k in keys:
            job = self.r.hgetall(k)
            if job.get("status") == "failed":
                jobs.append(job)
        return jobs
    
    def list_processing(self):
        keys = self.r.keys("queuectl:job:*")
        jobs = []
        for k in keys:
            job = self.r.hgetall(k)
            if job.get("status") == "processing":
                jobs.append(job)
        return jobs
    
    def list_completed(self):
        keys = self.r.keys("queuectl:job:*")
        jobs = []
        for k in keys:
            job = self.r.hgetall(k)
            if job.get("status") == "completed":
                jobs.append(job)
        return jobs
    
    def list_pending(self):
        pending_jobs = []
        job_keys = self.r.keys("queuectl:job:*")
        for job_key in job_keys:
            job = self.r.hgetall(job_key)
            if job.get("status") == "pending":
                job_id = job_key.split(":")[-1]
                job["id"] = job_id  # add job ID for convenience
                pending_jobs.append(job)
        return pending_jobs


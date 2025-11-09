# core/storage.py
import redis
import json
import uuid
import time

class RedisStorage:
    def __init__(self, host="localhost", port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def enqueue_job(self, data):
        job_id = str(uuid.uuid4())
        job_key = f"queuectl:job:{job_id}"

        # Store job metadata
        self.r.hset(job_key, mapping={
            "date_added": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "status": "pending",
            "data": json.dumps(data)
        })

        # Add to active queue (FIFO)
        self.r.lpush("queuectl:jobs", job_id)
        return job_id

    def get_next_job(self):
        # Block until a job is available
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
            "result": json.dumps(result)
        })

    def move_to_dlq(self, job_id, reason):
        job_key = f"queuectl:job:{job_id}"
        self.r.hset(job_key, mapping={
            "status": "failed",
            "reason": reason
        })
        self.r.lpush("queuectl:dead_letter", job_id)

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

import time
import random

class Worker:
    def __init__(self, worker_id, job_queue, update_status_callback):
        self.worker_id = worker_id
        self.job_queue = job_queue
        self.update_status_callback = update_status_callback

    def run(self):
        while not self.job_queue.empty():
            job = self.job_queue.get()
            job_id = job["id"]

            self.update_status_callback(job_id, "running")
            print(f"👷 Worker {self.worker_id} started job {job_id}: {job['command']}")

            # Simulate job execution
            time.sleep(random.randint(2, 5))

            self.update_status_callback(job_id, "completed")
            print(f"✅ Worker {self.worker_id} finished job {job_id}")

            self.job_queue.task_done()

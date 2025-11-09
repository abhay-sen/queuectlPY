# #!/usr/bin/env python3
# import click
# import json
# import threading
# import queue
# import time
# import os
# from worker import Worker

# JOBS_FILE = "jobs.json"
# job_queue = queue.Queue()
# lock = threading.Lock()

# # Initialize or load jobs
# def load_jobs():
#     if not os.path.exists(JOBS_FILE):
#         return []
#     with open(JOBS_FILE, "r") as f:
#         return json.load(f)

# def save_jobs(jobs):
#     with lock:
#         with open(JOBS_FILE, "w") as f:
#             json.dump(jobs, f, indent=4)

# def update_job_status(job_id, status):
#     jobs = load_jobs()
#     for job in jobs:
#         if job["id"] == job_id:
#             job["status"] = status
#             break
#     save_jobs(jobs)

# @click.group()
# def cli():
#     """A simple CLI job queue system."""
#     pass

# @cli.command()
# @click.argument("command")
# def add(command):
#     """Add a job to the queue."""
#     jobs = load_jobs()
#     job_id = len(jobs) + 1
#     job = {
#         "id": job_id,
#         "command": command,
#         "status": "queued",
#         "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
#     }
#     jobs.append(job)
#     save_jobs(jobs)
#     job_queue.put(job)
#     click.echo(f"✅ Job {job_id} added: {command}")

# @cli.command()
# def list():
#     """List all jobs."""
#     jobs = load_jobs()
#     if not jobs:
#         click.echo("No jobs yet.")
#         return

#     click.echo("\nJOB QUEUE STATUS:\n----------------------")
#     for job in jobs:
#         click.echo(f"[{job['id']}] {job['command']} - {job['status']}")

# @cli.command()
# @click.option("--workers", default=2, help="Number of concurrent workers.")
# def start(workers):
#     """Start worker threads to process jobs."""
#     jobs = load_jobs()
#     for job in jobs:
#         if job["status"] == "queued":
#             job_queue.put(job)

#     threads = []
#     for i in range(workers):
#         worker = Worker(i + 1, job_queue, update_job_status)
#         t = threading.Thread(target=worker.run)
#         t.start()
#         threads.append(t)

#     for t in threads:
#         t.join()

# if __name__ == "__main__":
#     cli()
#!/usr/bin/env python3
import click
import os
import importlib

# Path to the commands folder, calculated relative to this file
CMD_FOLDER = os.path.join(os.path.dirname(__file__), "commands")

class CLIGroup(click.Group):
    """
    A custom click.Group that dynamically loads commands
    from .py files in the 'commands' directory.
    """
    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(CMD_FOLDER):
            if filename.endswith(".py") and filename != "__init__.py":
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, cmd_name):
        try:
            # Adjusted for package import
            mod_path = f"queuectl.commands.{cmd_name}"
            mod = importlib.import_module(mod_path)
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, click.Command):
                    return obj
            return None
        except ImportError as e:
            click.echo(f"⚠️ Error loading command '{cmd_name}': {e}")
            return None


@click.command(cls=CLIGroup)
def cli():
    """QueueCTL — Background Job Queue CLI."""
    pass


if __name__ == "__main__":
    cli()

import click
import threading
from worker import Worker  # Assumes worker.py is in the root
from core.storage import update_job_status
from core.queue_manager import get_queue, populate_queue

@click.command()
@click.option("--workers", default=2, help="Number of concurrent workers.")
def start(workers):
    """Start worker threads to process jobs."""
    
    # 1. Load pending jobs from file into the in-memory queue
    populate_queue()
    
    job_queue = get_queue()

    if job_queue.empty():
        click.echo("No 'queued' jobs to process.")
        return

    click.echo(f"Starting {workers} worker(s) to process {job_queue.qsize()} jobs...")
    threads = []
    for i in range(workers):
        # Pass the update_job_status function from storage as the callback
        worker = Worker(i + 1, job_queue, update_job_status)
        t = threading.Thread(target=worker.run)
        t.start()
        threads.append(t)

    # Wait for all worker threads to finish
    for t in threads:
        t.join()
        
    click.echo("All pending jobs processed. Workers have shut down.")
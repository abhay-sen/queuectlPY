# commands/start.py
import click
import threading
import time
from core.queue_manager import process_next_job

def run_worker(worker_name):
    """
    Target function for a worker thread.
    Runs an infinite loop, blocking until a job is available.
    """
    click.echo(f"🚀 Worker {worker_name} started and waiting for jobs...")
    while True:
        try:
            # This function blocks until a job is available,
            # processes it, and prints all status messages.
            process_next_job(worker_name=worker_name)
        except Exception as e:
            # Catch exceptions (like Redis connection error)
            # and wait a bit before retrying.
            click.echo(f"Error in {worker_name}: {e}. Retrying in 5s...", err=True)
            time.sleep(5)

@click.command()
@click.option("--workers", "-w", default=1, help="Number of concurrent workers.")
def start(workers):
    """
    Start worker(s) to process jobs from the queue.
    
    Workers run continuously and will block, waiting for new jobs.
    Press Ctrl+C to stop.
    """
    click.echo(f"Starting {workers} worker thread(s)...")
    click.echo("Press Ctrl+C to stop workers.")
    
    threads = []
    for i in range(workers):
        worker_name = f"Worker-{i+1}"
        # Start daemon threads so they exit when the main program is killed
        t = threading.Thread(target=run_worker, args=(worker_name,), daemon=True)
        t.start()
        threads.append(t)

    # Keep the main thread alive, waiting for a KeyboardInterrupt
    try:
        while True:
            # Sleep for a long time to keep main thread alive
            # without consuming CPU.
            time.sleep(3600)
    except KeyboardInterrupt:
        click.echo("\n🛑 Shutting down workers... (Received Ctrl+C)")
        # Daemon threads will exit automatically
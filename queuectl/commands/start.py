import click
import threading
import time
from queuectl.core.queue_manager import process_next_job, should_stop, clear_stop_signal

def run_worker(worker_name):
    """
    Worker thread: runs continuously until a stop signal is received.
    """
    click.echo(f"🚀 {worker_name} started and waiting for jobs...")
    while True:
        if should_stop():
            click.echo(f"🛑 {worker_name} stopping gracefully (received stop signal).")
            break

        try:
            process_next_job(worker_name=worker_name)
        except Exception as e:
            click.echo(f"⚠️ Error in {worker_name}: {e}. Retrying in 5s...", err=True)
            time.sleep(5)
        
        # Short pause between iterations to prevent tight looping
        time.sleep(1)


@click.command()
@click.option("--workers", "-w", default=1, help="Number of concurrent workers.")
def start(workers):
    """
    Start worker(s) to process jobs from the queue.
    Use 'python cli.py stop' to stop them gracefully.
    """
    click.echo(f"Starting {workers} worker thread(s)...")
    click.echo("Press Ctrl+C to stop manually, or run 'python cli.py stop' in another terminal.")
    
    # Clear any previous stop signal before starting
    clear_stop_signal()

    threads = []
    for i in range(workers):
        worker_name = f"Worker-{i+1}"
        t = threading.Thread(target=run_worker, args=(worker_name,), daemon=True)
        t.start()
        threads.append(t)

    try:
        # Keep main thread alive
        while not should_stop():
            time.sleep(2)
    except KeyboardInterrupt:
        click.echo("\n🛑 KeyboardInterrupt received, shutting down workers...")
    finally:
        click.echo("✅ All workers stopped.")

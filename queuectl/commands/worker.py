import click
import threading
import time
from queuectl.core.queue_manager import (
    process_next_job,
    should_stop,
    clear_stop_signal,
    set_stop_signal,
)
from queuectl.core.storage import RedisStorage

storage = RedisStorage()


def run_worker(worker_name):
    """
    Worker thread: runs continuously until a stop signal is received.
    """
    worker_key = f"queuectl:worker:{worker_name}"

    storage.r.hset(worker_key, mapping={
        "status": "active",
        "current_job": "idle"
    })

    click.echo(f"🚀 {worker_name} started and waiting for jobs...")

    try:
        while True:
            if should_stop():
                storage.r.hset(worker_key, mapping={
                    "status": "stopped",
                    "current_job": "-"
                })
                click.echo(f"🛑 {worker_name} stopping gracefully (received stop signal).")
                break

            try:
                storage.process_retry_queue()
                process_next_job(worker_name=worker_name)
            except Exception as e:
                click.echo(f"⚠️ Error in {worker_name}: {e}. Retrying in 5s...", err=True)
                time.sleep(5)

            time.sleep(1)

    finally:
        storage.r.delete(worker_key)
        click.echo(f"🧹 {worker_name} removed from worker registry.")


@click.group()
def worker():
    """Manage background worker(s)."""
    pass

@worker.command()
@click.option("--count", "-c", default=1, help="Number of concurrent workers.")
def start(count):
    """
    Start worker(s) to process jobs from the queue continuously
    until a stop signal or keyboard interrupt is received.
    """
    clear_stop_signal()

    click.echo(f"🚀 Starting {count} worker thread(s)...")
    click.echo("Press Ctrl+C to stop manually, or run 'queuectl worker stop' in another terminal.")

    # Launch the specified number of worker threads
    for i in range(count):
        worker_name = f"Worker-{i+1}"
        t = threading.Thread(target=run_worker, args=(worker_name,), daemon=True)
        t.start()

    try:
        # The main process continuously monitors retry queues
        while not should_stop():
            storage.process_retry_queue()
            time.sleep(2)

    except KeyboardInterrupt:
        click.echo("\n🛑 KeyboardInterrupt received, shutting down.")

    finally:
        click.echo("✅ All workers stopped and cleaned up.")


@worker.command()
def stop():
    """Stop all running workers gracefully and clear their records."""
    set_stop_signal()
    click.echo("🛑 Stop signal sent. Workers will exit after finishing current job.")

    time.sleep(1)
    worker_keys = storage.r.keys("queuectl:worker:*")
    for key in worker_keys:
        storage.r.delete(key)
    click.echo(f"🧹 Cleared {len(worker_keys)} worker record(s) from Redis.")


@worker.command()
def resume():
    """Resume worker processing after stop."""
    clear_stop_signal()
    click.echo("▶️ Workers resumed.")

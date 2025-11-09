# commands/list.py
import click
from core.queue_manager import list_all_jobs, list_dlq_jobs

@click.command()
@click.option("--dlq", is_flag=True, help="List jobs in the Dead Letter Queue.")
def list(dlq):
    """
    List jobs in the queue.
    
    By default, lists all known jobs (pending, processing, completed).
    Use --dlq to see only jobs in the Dead Letter Queue.
    """
    try:
        if dlq:
            click.echo("Inspecting Dead Letter Queue (DLQ)...")
            list_dlq_jobs()
        else:
            click.echo("Inspecting all jobs...")
            list_all_jobs()
    except Exception as e:
        click.echo(f"Error connecting to Redis: {e}", err=True)
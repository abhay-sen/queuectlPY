# commands/add.py
import click
from core.queue_manager import add_job

@click.command()
@click.argument("data", nargs=-1)
def add(data):
    """
    Add a new job to the queue.
    
    Provide data as space-separated key=value pairs.
    
    Example:
    
    queuectl add command=send_report user_id=42 type=monthly
    
    queuectl add command=fail_this_job
    """
    if not data:
        click.echo("Error: No job data provided.", err=True)
        click.echo("Usage: queuectl add key1=value1 key2=value2 ...")
        return

    job_data = {}
    try:
        for item in data:
            # Split only on the first '='
            key, value = item.split("=", 1)
            job_data[key] = value
    except ValueError:
        click.echo("Error: Data must be in key=value format.", err=True)
        return
    
    # The add_job function from queue_manager already prints
    # a success message, so we just call it.
    try:
        add_job(job_data)
    except Exception as e:
        click.echo(f"Error connecting to Redis: {e}", err=True)
import click
from queuectl.core.queue_manager import enqueue_job

@click.command()
@click.argument("command")
def enqueue(command):
    """
    enqueue a new shell command as a job to the queue.

    Example:
      python cli.py enqueue "echo hello world"
      python cli.py enqueue "ls -la"
      python cli.py enqueue "cat missingfile.txt"
    """
    job_data = {"command": command}

    try:
        enqueue_job(job_data)
    except Exception as e:
        click.echo(f"❌ Error enqueueing job: {e}", err=True)

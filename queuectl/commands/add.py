import click
from queuectl.core.queue_manager import add_job

@click.command()
@click.argument("command")
def add(command):
    """
    Add a new shell command as a job to the queue.

    Example:
      python cli.py add "echo hello world"
      python cli.py add "ls -la"
      python cli.py add "cat missingfile.txt"
    """
    job_data = {"command": command}

    try:
        add_job(job_data)
    except Exception as e:
        click.echo(f"❌ Error adding job: {e}", err=True)

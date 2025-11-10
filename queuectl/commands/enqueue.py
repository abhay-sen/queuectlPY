import click
# Assuming 'queuectl.core.queue_manager' is in your project's PYTHONPATH
from queuectl.core.queue_manager import enqueue_job

@click.command()
@click.argument("command")
@click.option(
    "--timeout",
    default=None,
    type=int,
    help="Job execution timeout in seconds. (Default: No limit)",
)
def enqueue(command, timeout):
    """
    Enqueue a new shell command as a job to the queue.

    Example:
      python cli.py enqueue "echo hello world"
      python cli.py enqueue --timeout 30 "ls -la"
      python cli.py enqueue "cat missingfile.txt"
    """
    # Pass the timeout to your job data dictionary
    job_data = {"command": command, "timeout": timeout}

    try:
        # Assuming enqueue_job now accepts this new structure
        enqueue_job(job_data)
        timeout_msg = f"with timeout {timeout}s" if timeout is not None else "with no timeout"
        click.echo(f"✅ Job enqueued {timeout_msg}: {command}")
    except Exception as e:
        click.echo(f"❌ Error enqueueing job: {e}", err=True)

# Note: This file only contains the modified 'enqueue' command.
# You will need to integrate this back into your main CLI file
# and ensure 'enqueue_job' handles the new 'timeout' key in job_data.

if __name__ == "__main__":
    # This is just for demonstration if you wanted to run this file directly
    # In your project, you'd likely have a main entry point that groups commands.
    enqueue()
import click
from queuectl.core.queue_manager import list_jobs  # <-- We'll rename this

@click.command()
@click.option(
    "--state",
    type=click.Choice(
        ['pending', 'processing', 'completed', 'failed', 'dead'], 
        case_sensitive=False
    ),
    default=None,  # This will be None if the option is not used
    help="Filter by job state. Lists all jobs if omitted."
)
def list(state):
    """
    List jobs in the queue.
    
    By default, lists all known jobs.
    Use --state to filter by a specific status:
    - 'pending': Jobs waiting to be run.
    - 'processing': Jobs currently being run.
    - 'completed': Jobs that finished successfully.
    - 'failed': Jobs in the retry queue.
    - 'dead': Jobs in the Dead Letter Queue (DLQ).
    """
    try:
        if state:
            click.echo(f"📋 Inspecting '{state}' jobs...")
        else:
            click.echo("📋 Inspecting all jobs...")

        # We pass the state filter (e.g., 'pending' or None) 
        # to the backend function.
        list_jobs(state_filter=state)

    except Exception as e:
        click.echo(f"Error connecting to Redis: {e}", err=True)
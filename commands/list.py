import click
from core.storage import load_jobs

@click.command()
def list():
    """List all jobs."""
    jobs = load_jobs()
    if not jobs:
        click.echo("No jobs yet.")
        return

    click.echo("\nJOB QUEUE STATUS:\n----------------------")
    for job in jobs:
        # Simple formatting
        status_color = "green"
        if job['status'] == 'queued':
            status_color = 'yellow'
        elif job['status'] in ['failed', 'error']:
            status_color = 'red'
            
        click.echo(
            f"[{job['id']}] " +
            click.style(f"({job['status']})", fg=status_color) +
            f" - {job['command']}"
        )
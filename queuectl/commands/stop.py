import click
from queuectl.core.queue_manager import set_stop_signal

@click.command()
def stop():
    """Stop all running workers gracefully."""
    set_stop_signal()
    click.echo("🛑 Stop signal sent. Workers will finish their current job and exit.")

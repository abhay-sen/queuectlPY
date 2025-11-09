import click
from queuectl.core.storage import RedisStorage

storage = RedisStorage()
CONFIG_KEY = "queuectl:config"

@click.group(help="Manage global queue configuration")
def config():
    pass

@config.command("show", help="Show current configuration")
def show_config():
    config_data = storage.r.hgetall(CONFIG_KEY)
    if not config_data:
        click.echo("⚠️ No configuration found. Using defaults:")
        click.echo("   max_retries=3, backoff_base=2, backoff_factor=2")
        return

    click.echo("⚙️ Current Queue Configuration:")
    click.echo("-" * 40)
    for k, v in config_data.items():
        # ✅ REMOVED .decode() from k and v
        click.echo(f"{k} = {v}")
    click.echo("-" * 40)

@config.command("set", help="Set global retry/backoff settings")
@click.option("--max-retries", type=int)
@click.option("--backoff-base", type=int)
@click.option("--backoff-factor", type=int)
@click.pass_context  # <-- 1. Add this decorator
def set_config(ctx, max_retries, backoff_base, backoff_factor): # <-- 2. Add ctx
    updates = {}
    if max_retries is not None:
        updates["max_retries"] = max_retries
    if backoff_base is not None:
        updates["backoff_base"] = backoff_base
    if backoff_factor is not None:
        updates["backoff_factor"] = backoff_factor

    if not updates:
        click.echo("⚠️ No options provided.")
        return

    storage.r.hset(CONFIG_KEY, mapping=updates)
    click.echo("✅ Configuration updated successfully.")
    ctx.invoke(show_config)  # <-- 3. Use ctx.invoke()

@config.command("reset", help="Reset configuration to defaults")
@click.pass_context  # <-- 1. Add this decorator
def reset_config(ctx):  # <-- 2. Add ctx
    default = {"max_retries": 3, "backoff_base": 2, "backoff_factor": 2}
    storage.r.hset(CONFIG_KEY, mapping=default)
    click.echo("♻️ Configuration reset to defaults:")
    ctx.invoke(show_config)  # <-- 3. Use ctx.invoke()

if __name__ == "__main__":
    config()
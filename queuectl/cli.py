#!/usr/bin/env python3
import click
import os
import importlib

CMD_FOLDER = os.path.join(os.path.dirname(__file__), "commands")

class CLIGroup(click.Group):
    """Dynamically loads subcommands from the 'commands' folder."""

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(CMD_FOLDER):
            if filename.endswith(".py") and filename != "__init__.py":
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, cmd_name):
        try:
            mod_path = f"queuectl.commands.{cmd_name}"
            mod = importlib.import_module(mod_path)
            
            # ✅ Prefer click.Group instances (e.g., worker)
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, click.Group):
                    return obj

            # Fallback: any click.Command
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, click.Command):
                    return obj

            return None
        except ImportError as e:
            click.echo(f"⚠️ Error loading command '{cmd_name}': {e}")
            return None


@click.command(cls=CLIGroup)
def cli():
    """QueueCTL — Background Job Queue CLI."""
    pass


if __name__ == "__main__":
    cli()

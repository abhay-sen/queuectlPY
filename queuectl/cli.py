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

            # ✅ Try to get a Click Group or Command named exactly as the file
            cmd_obj = getattr(mod, cmd_name, None)
            if isinstance(cmd_obj, (click.Group, click.Command)):
                return cmd_obj

            # ✅ Fallback: first Click object found
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, (click.Group, click.Command)):
                    return obj

            click.echo(f"⚠️ No valid click command found in {mod_path}")
            return None

        except ImportError as e:
            click.echo(f"⚠️ Error loading command '{cmd_name}': {e}")
            return None


@click.group(cls=CLIGroup)
def cli():
    """QueueCTL — Background Job Queue CLI."""
    pass


if __name__ == "__main__":
    cli()

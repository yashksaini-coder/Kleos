import click

@click.group('setup')
def setup_group():
    """Commands for initial setup and configuration."""
    pass

@setup_group.command('hackernews')
@click.option('--name', default='hackernews', show_default=True, help="Name for the HackerNews datasource.")
@click.pass_context
def setup_hackernews(ctx, name):
    """
    Creates the HackerNews datasource in MindsDB.
    """
    handler = ctx.obj
    if not handler or not handler.project: # Check if connection was successful
        click.echo(click.style("MindsDB connection not available. Please check connection in main entry point.", fg='red'))
        return

    click.echo(f"Attempting to create HackerNews datasource named '{name}'...")
    if handler.create_hackernews_datasource(ds_name=name):
        click.echo(click.style(f"HackerNews datasource '{name}' is ready.", fg='green'))
    else:
        click.echo(click.style(f"Failed to create HackerNews datasource '{name}'. Check logs for details.", fg='red'))

# To make this command group available, it needs to be added to the main cli object in main.py
# Example in main.py:
# from .commands import setup_commands
# cli.add_command(setup_commands.setup_group)

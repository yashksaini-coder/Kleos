import click
from src.core.mindsdb_handler import MindsDBHandler
from config import config

from src.commands import setup_commands
from src.commands import kb_commands
from src.commands import job_commands
from src.commands import ai_commands # ADD THIS IMPORT
# from .commands import report_commands

@click.group()
@click.pass_context
def cli(ctx):
    """
    MindsDB CLI - A tool to interact with MindsDB, manage Knowledge Bases,
    run AI tasks, and generate reports.
    """
    ctx.ensure_object(dict)
    handler = MindsDBHandler()
    if handler.connect():
        ctx.obj = handler
        click.echo(click.style("Successfully connected to MindsDB.", fg='green'))
    else:
        ctx.obj = None
        click.echo(click.style("Failed to connect to MindsDB. Some commands may not work.", fg='red'))

cli.add_command(setup_commands.setup_group)
cli.add_command(kb_commands.kb_group)
cli.add_command(job_commands.job_group)
cli.add_command(ai_commands.ai_group) # ADD THIS LINE
# ... and so on

if __name__ == '__main__':
    cli()

import click
from rich.status import Status
from .utils import get_handler_and_console, CONTEXT_SETTINGS, RichHelpFormatter # Import RichHelpFormatter

@click.group('setup', context_settings=CONTEXT_SETTINGS)
def setup_group():
    """Commands for initial setup and project configuration.

    This includes setting up necessary datasources or other initial configurations
    required for Kleos to interact effectively with MindsDB.
    """
    pass

setup_group.formatter_class = RichHelpFormatter # Set formatter for this group

@setup_group.command('hackernews')
@click.option('--name', default='hackernews', show_default=True,
              help="Specify the name for the HackerNews datasource in MindsDB. Default: 'hackernews'.")
@click.pass_context
def setup_hackernews(ctx, name):
    """
    Creates or verifies the HackerNews datasource in MindsDB.

    The HackerNews datasource provides access to stories, comments, and other data
    from Hacker News (news.ycombinator.com). This is often used as a sample
    dataset for examples and testing Knowledge Bases or AI Models.

    If a datasource with the specified name already exists, its presence will be confirmed.
    Otherwise, a new datasource connection will be created.

    Example:
    `kleos setup hackernews --name my_hn_data`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler:
        return

    with Status(f"Attempting to create HackerNews datasource named '[cyan]{name}[/cyan]'...", console=console, spinner="earth"):
        if handler.create_hackernews_datasource(ds_name=name):
            console.print(f"[green]:heavy_check_mark: HackerNews datasource '[cyan]{name}[/cyan]' is ready.[/green]")
        else:
            console.print(f"[red]:x: Failed to create HackerNews datasource '[cyan]{name}[/cyan]'. Check logs for details.[/red]")
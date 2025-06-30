import click
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
import importlib.metadata
import sys
import os
from rich.table import Table as RichTable # Alias to avoid conflict
from rich.padding import Padding

from .core.mindsdb_handler import MindsDBHandler
# from config import config # Config is used by MindsDBHandler, not directly here

from .commands import setup_commands
from .commands import kb_commands
from .commands import job_commands
from .commands import ai_commands
from .commands.utils import CONTEXT_SETTINGS, RichHelpFormatter


# Initialize Rich Console
console = Console()

_BANNER_ART = """
██╗  ██╗██╗     ███████╗ ██████╗ ███████╗
██║ ██╔╝██║     ██╔════╝██╔═══██╗██╔════╝
█████╔╝ ██║     █████╗  ██║   ██║███████╗
██╔═██╗ ██║     ██╔══╝  ██║   ██║╚════██║
██║  ██╗███████╗███████╗╚██████╔╝███████║
╚═╝  ╚═╝╚══════╝╚══════╝ ╚═════╝ ╚══════╝
    """
_BANNER_COLOR = "purple4"  # Color for the banner art

def get_banner_art() -> Text:
    """Returns the styled ASCII banner art."""
    return Text(_BANNER_ART, style=f"bold {_BANNER_COLOR}")

def display_banner():
    """Displays an ASCII art banner and project information."""
    try:
        version = importlib.metadata.version("kleos")
    except importlib.metadata.PackageNotFoundError:
        version = "0.1.0 (local)" # Fallback for local development

    # banner_text is now in _BANNER_ART via get_banner_art()
    # banner_color is _BANNER_COLOR
    link_color = "deep_sky_blue4"
    info_color = "indian_red"
    desc_color = "italic grey82" # For concise description
    value_color = "sea_green3"
    telos_style = "italic #E76F51"


    # Condensed CLI Info
    cli_version_text = Text.assemble((f"Kleos CLI v{version}", f"bold {info_color}"))
    concise_cli_description = Text("Seek, structure, and serve insight with MindsDB Knowledge Bases & AI Agents.", style=desc_color)
    head_desc = "Every system has its `telos´ — its final cause."
    full_desc = """
This CLI fulfills the purpose of MindsDB's Knowledge Base:-
    ● To seek
    ● To structure
    ● To serve insight through intelligent agents.
"""
    kleos_repo_url = "https://github.com/yashksaini-coder/Kleos"
    cli_repo_text = Text.assemble(("Project Repo: ", info_color), (kleos_repo_url, f"link {kleos_repo_url} {link_color}"))

    # Condensed Author Info
    author_name = "Yash K. Saini"
    author_profile_url = "https://github.com/yashksaini-coder"
    sponsor_url = "https://github.com/sponsors/yashksaini-coder"
    author_text = Text.assemble(("Author: ", info_color), (author_name, value_color)) # value_color defined in show_cli_info, reuse or define here
    author_profile_text = Text.assemble(("Profile: ", info_color), (author_profile_url, f"link {author_profile_url} {link_color}"))
    sponsor_text = Text.assemble(("Sponsor: ", info_color), (sponsor_url, f"link {sponsor_url} {link_color}"))

    powered_by_text = Text("Powered by MindsDB's Knowledge Base", style="bright_magenta")

    # Assemble all parts for the main welcome panel
    description_text = Text.from_markup(head_desc.replace('`telos´', f"[{telos_style}]`telos´[/{telos_style}]"))
    welcome_content = Text.assemble(
        get_banner_art(), "\n\n",
        cli_version_text, "\n",
        description_text, "\n",
        full_desc, "\n",
        Text("---"*26, style="dim " + info_color), "\n", # Divider
        cli_repo_text, "\n",
        "\n", 
        Text("---"*26, style="dim " + info_color), "\n", # Divider
        author_text, "\n",
        author_profile_text, "\n",
        sponsor_text, "\n",
        Text("---"*26, style="dim " + info_color), "\n", # Divider
        "\n",
        powered_by_text
    )

    console.print(Panel(
        welcome_content,
        title=f"[bold {info_color}]Welcome to Kleos CLI[/bold {info_color}]",
        border_style=f"dim {_BANNER_COLOR}",
        padding=(1, 2),
        expand=False
    ))

@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.version_option(None, "-v", "--version", message="%(prog)s CLI version %(version)s", package_name="kleos")
@click.pass_context
def cli(ctx):
    """
    Kleos CLI - A powerful toolkit to interact with MindsDB.

    Every system has its `telos´ — its final cause. This CLI fulfills the purpose of MindsDB's Knowledge Base: to seek, structure, and serve insight through intelligent agents.

    Manage Knowledge Bases, AI Agents, AI Models, run AI tasks, and generate reports.
    """
    ctx.ensure_object(dict)
    ctx.obj = {'handler': MindsDBHandler(rich_console=console), 'console': console}

    if ctx.invoked_subcommand is None:
        is_direct_command_or_help = False
        if len(sys.argv) > 1:
            if any(arg in ['--help', '-h', '--version', '-v'] for arg in sys.argv[1:]) or \
               (len(sys.argv) > 1 and sys.argv[1] in cli.commands): # Check if first arg is a command
                is_direct_command_or_help = True

        if not is_direct_command_or_help and len(sys.argv) == 1:
            display_banner()
            console.print(ctx.get_help())
            console.print("\nStarting interactive mode. Type 'exit' or 'quit' to leave.", style="bold #F4A261")

            while True:
                try:
                    command_line = console.input("[bold #6495ED]kleos>[/] ")
                    if command_line.lower() in ['exit', 'quit']:
                        console.print("Exiting Kleos CLI.", style="bold #F4A261")
                        break
                    if not command_line.strip():
                        continue

                    import shlex
                    args = shlex.split(command_line)

                    if len(args) == 1 and args[0] in cli.commands and isinstance(cli.commands[args[0]], click.Group):
                        group_name = args[0]
                        try:
                            with cli.commands[group_name].make_context(info_name=group_name, args=['--help'], parent=ctx) as group_ctx:
                                cli.commands[group_name].invoke(group_ctx)
                        except click.exceptions.Exit:
                            pass
                        except Exception as e_group_help:
                            console.print(f"[red]Error showing help for group '{group_name}': {e_group_help}[/red]")
                    else:
                        try:
                            with cli.make_context(info_name="kleos", args=args, parent=ctx) as loop_ctx:
                                cli.invoke(loop_ctx)
                        except click.exceptions.Exit:
                            pass
                        except click.exceptions.MissingParameter as e:
                            console.print(f"[bold red]Usage Error:[/bold red] Missing parameter: [bold cyan]{e.param_hint}[/bold cyan]")
                        except click.exceptions.BadParameter as e:
                            console.print(f"[bold red]Usage Error:[/bold red] Invalid parameter for [bold cyan]{e.param_hint}[/bold cyan]: {e.message}")
                        except click.exceptions.NoSuchOption as e:
                            console.print(f"[bold red]Usage Error:[/bold red] No such option: [bold cyan]{e.option_name}[/bold cyan]")
                        except click.exceptions.UsageError as e:
                            console.print(f"[bold yellow]Usage Error:[/bold yellow]\n{e.format_message()}")
                        except click.exceptions.ClickException as e:
                            console.print(f"[red]CLI Error: {e.format_message()}[/red]")
                        except ConnectionError as e:
                             console.print(f"[red]:x: Connection Error: {str(e)}[/red]")
                        except Exception as e:
                            console.print(f"[bold red]An unexpected error occurred: {str(e)}[/bold red]")
                    console.print("")
                except KeyboardInterrupt:
                    console.print("\nExiting Kleos CLI (Ctrl+C).", style="bold #F4A261")
                    break
                except EOFError:
                    console.print("\nExiting Kleos CLI (EOF).", style="bold #F4A261")
                    break

cli.formatter_class = RichHelpFormatter

@cli.command('cls', help="Clears the terminal screen.")
def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

@cli.command('about', help="Displays information about the author of Kleos CLI.")
def show_about():
    """Displays detailed information about the author of the Kleos CLI."""
    banner_art = get_banner_art() # Get the banner art
    console.print() # Add a newline for spacing before the panel

    author_name = "Yash K. Saini"
    bio = "👋 Hi there! I'm Yash K. Saini, an open source contributor, self-taught developer.\nBuilding applications and CLI products."
    author_github_username = "yashksaini-coder"
    author_profile_url = f"https://github.com/{author_github_username}"
    sponsor_url = f"https://github.com/sponsors/{author_github_username}"

    title_color = "bold white"
    field_color = "bold deep_sky_blue4"
    value_color = "sea_green3"
    link_color = "hot_pink3"
    bio_color = "italic grey82"

    author_details_table = RichTable(box=None, show_header=False, padding=(0, 1, 0, 1), expand=False)
    author_details_table.add_column(style=field_color, justify="right", width=18)
    author_details_table.add_column(style=value_color, overflow="fold")

    author_details_table.add_row("Author:", Text(author_name, style="sky_blue2"), style=title_color)
    author_details_table.add_row("About:", Text(bio, style=value_color), style=title_color)
    author_details_table.add_row("GitHub Profile:", Text(author_profile_url, style=f"link {author_profile_url} {link_color}"), style=title_color)
    author_details_table.add_row("Sponsor Link:", Text(sponsor_url, style=f"link {sponsor_url} {link_color}"), style=title_color)

    from rich.console import Group # Import Group
    # Assemble content for the panel: banner + table
    render_group = Group(
        banner_art,
        "\n", # Single newline might be enough if panel has padding
        author_details_table
    )

    console.print(Panel(
        render_group,
        title=f"[{title_color}]About the Author[/{title_color}]",
        border_style="dim medium_purple1",
        padding=(1,2),
        expand=False
    ))

@cli.command('info', help="Displays information about the Kleos CLI tool.")
def show_cli_info():
    """Displays version, description, and project information for the Kleos CLI."""
    banner_art = get_banner_art() # Get just the Text object for the art
    console.print() # Add a newline for spacing before the panel

    try:
        version = importlib.metadata.version("kleos")
    except importlib.metadata.PackageNotFoundError:
        version = "0.1.0 (local)"

    head_desc = "Every system has its `telos´ — its final cause."
    full_desc = """
This CLI fulfills the purpose of MindsDB's Knowledge Base:-
    ● To seek
    ● To structure
    ● To serve insight through intelligent agents.
"""

    github_repo_url = "https://github.com/yashksaini-coder/Kleos"

    title_color = "bold white"
    field_color = "bold deep_sky_blue4"
    value_color = "sea_green3"
    link_color = "hot_pink3"
    desc_cli_color = "italic grey82"
    telos_style = "italic #E76F51"

    description_text = Text.from_markup(head_desc.replace('`telos´', f"[{telos_style}]`telos´[/{telos_style}]"))

    info_details_table = RichTable(box=None, show_header=False, padding=(0,1,0,1), expand=False)
    info_details_table.add_column(style=field_color, justify="right", width=18)
    info_details_table.add_column(style=value_color, overflow="fold")

    info_details_table.add_row("Version:", version)
    info_details_table.add_row("Description:", description_text)
    info_details_table.add_row("Full Description:", Text(full_desc, style="sky_blue2"))
    info_details_table.add_row("Repository:", Text(github_repo_url, style=f"link {github_repo_url} {link_color}"))
    info_details_table.add_row("Powered by:", Text("MindsDB", style="bright_magenta"))

    from rich.console import Group # Ensure Group is available
    # Assemble content for the panel: banner + table
    render_group = Group(
        banner_art,
        "\n", # Single newline might be enough if panel has padding
        info_details_table
    )

    console.print(Panel(
        render_group,
        title=f"[{title_color}]Kleos CLI Information[/{title_color}]",
        border_style="dim deep_sky_blue1",
        padding=(1,2),
        expand=False
    ))

cli.add_command(setup_commands.setup_group)
cli.add_command(kb_commands.kb_group)
cli.add_command(job_commands.job_group)
cli.add_command(ai_commands.ai_group)

if __name__ == '__main__':
    cli(prog_name="kleos")

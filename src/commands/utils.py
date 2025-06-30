import click
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.panel import Panel
from rich.status import Status # Added for get_handler_and_console if it uses it directly

# Custom Rich Help Formatter
class RichHelpFormatter(click.HelpFormatter):
    def __init__(self, indent_increment=2, width=None, max_width=None):
        super().__init__(indent_increment, width, max_width if width is None else width)
        self.console = Console() # Use a local console for help formatting

    def write_usage(self, prog, args, prefix="[bold #F4A261]Usage:[/bold #F4A261] "):
        usage_text = f"{prog} {args}"
        self.console.print(Text.assemble(prefix, (usage_text, "italic #E0E0E0")))
        self.write_full_line("")

    def write_heading(self, heading):
        self.console.print(f"\n[bold underline #E9C46A]{heading}[/bold underline #E9C46A]")

    def write_text(self, text):
        processed_text = text.replace('`telos´', '[italic #E76F51]`telos´[/italic #E76F51]')
        if "Kleos CLI - A powerful toolkit" in processed_text:
             self.console.print(Panel(Text(processed_text, style="#S_LIGHT_GREY"), border_style="#2A9D8F", padding=(0,1), expand=False))
        else:
            self.console.print(Text(processed_text, style="#S_LIGHT_GREY"))
        self.write_full_line("")

    def write_dl(self, rows, col_max=30, col_spacing=2):
        table = Table(box=None, show_header=False, padding=0, expand=True)
        table.add_column(min_width=20, max_width=col_max, overflow="fold", style="bold #26A9D0")
        table.add_column(style="#D0D0D0")

        for cmd_opt, description in rows:
            description_text = Text.from_markup(description.replace('`telos´', '[italic #E76F51]`telos´[/italic #E76F51]'))
            table.add_row(cmd_opt, description_text)
        self.console.print(table)
        self.write_full_line("")

# CONTEXT_SETTINGS should only contain settings directly passed to Context.__init__
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
# RichHelpFormatter class itself is defined above and will be assigned to commands/groups directly.

# Helper function to get handler and console, and ensure connection
def get_handler_and_console(ctx):
    obj = ctx.obj
    # Ensure obj is a dict, which should be guaranteed by main.py's ctx.ensure_object(dict)
    # However, direct calls or testing might not have it.
    if not isinstance(obj, dict):
        # This case should ideally not happen in normal CLI flow.
        # Consider raising an error or initializing a default console/handler for robustness if needed.
        # For now, assume obj is dict as per CLI design.
        # Fallback console if not found in context for some reason.
        fallback_console = Console()
        fallback_console.print("[bold red]Critical Error: Context object not found or not a dict in get_handler_and_console.[/bold red]")
        # Depending on strictness, could raise an exception here.
        return None, None


    handler = obj.get('handler')
    console = obj.get('console')

    if not handler or not console:
        # This indicates a programming error if ctx.obj was not set up correctly in main.py
        local_console = console if console else Console() # Use provided console or a new one
        local_console.print("[bold red]Critical Error: Handler or Console not found in context object.[/bold red]")
        return None, None


    if not handler.project: # Check if already connected
        with Status("Connecting to MindsDB...", console=console, spinner="dots"):
            if not handler.connect(): # connect method now uses handler.console
                # Error message is printed by handler.connect() itself using Rich
                return None, None # Indicate failure
    return handler, console

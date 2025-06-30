import click
import pandas as pd
from rich.table import Table
from rich.status import Status
from rich.syntax import Syntax
from rich.text import Text
from .utils import get_handler_and_console, CONTEXT_SETTINGS, RichHelpFormatter # Import RichHelpFormatter

@click.group('job', context_settings=CONTEXT_SETTINGS)
def job_group():
    """Commands for managing and monitoring MindsDB Jobs.

    MindsDB Jobs are used to automate SQL-based tasks, such as periodic data
    ingestion, model retraining, or any sequence of SQL commands that need to
    be executed on a schedule or triggered by certain conditions.
    """
    pass

job_group.formatter_class = RichHelpFormatter # Set formatter for this group

def _display_df_as_table(console, df, title=""):
    if df is None:
        console.print("[yellow]No data to display.[/yellow]")
        return
    if df.empty:
        console.print(f"[yellow]{title if title else 'Result'} is empty.[/yellow]")
        return

    table = Table(title=title if title else None, show_header=True, header_style="bold magenta", show_lines=True)
    for col in df.columns:
        table.add_column(str(col))
    for _, row in df.iterrows():
        table.add_row(*(str(x) for x in row))
    console.print(table)

@job_group.command('update-hn-refresh')
@click.argument('job_name') # Removed help
@click.option('--hn-datasource', default='hackernews', show_default=True, help="The name of the HackerNews datasource in MindsDB that this job will refresh.")
@click.option('--schedule', default='EVERY 1 day', show_default=True, help="Schedule interval for the job, using MindsDB's `SCHEDULE` syntax (e.g., 'EVERY 1 hour', 'EVERY 1 day at 03:00').")
@click.option('--project', help="MindsDB project where the job should be created. Defaults to the currently connected project.")
@click.pass_context
def job_update_hackernews_db(ctx, job_name, hn_datasource, schedule, project):
    """
    Creates a specific MindsDB Job to periodically refresh the HackerNews database.

    This job automates the process of dropping the existing HackerNews datasource
    (specified by --hn-datasource) and recreating it, ensuring the data is kept up-to-date
    according to the defined --schedule.

    Example:
    `kleos job update-hn-refresh daily_hackernews_refresh --hn-datasource my_hndb --schedule "EVERY 1 day at 04:00"`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    console.print(f"Creating job '[cyan]{job_name}[/cyan]' to refresh HackerNews datasource '[cyan]{hn_datasource}[/cyan]'...")
    console.print(f"  Schedule: [yellow]{schedule}[/yellow]")

    with Status(f"Submitting job '[cyan]{job_name}[/cyan]'...", console=console):
        success = handler.update_hackernews_db(
            job_name=job_name, hn_datasource=hn_datasource,
            schedule_interval=schedule, project_name=project
        )
    if success:
        console.print(f"[green]:heavy_check_mark: Job '[cyan]{job_name}[/cyan]' created successfully.[/green]")
        console.print(f"  Check status with: [bold]kleos job status {job_name}{f' --project {project}' if project else ''}[/bold]")
    else:
        console.print(f"[red]:x: Failed to create job '[cyan]{job_name}[/cyan]'. Check logs for details.[/red]")

@job_group.command('list')
@click.option('--project', help="Filter jobs by a specific MindsDB project name. If omitted, lists jobs from the currently connected project.")
@click.pass_context
def job_list(ctx, project):
    """
    Lists all MindsDB jobs in a specified project or the current project.

    Displays information such as job name, creation date, schedule, status, and the next run time.
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project = project if project else handler.project.name if handler.project else "current"
    with Status(f"Fetching jobs from project '[cyan]{effective_project}[/cyan]'...", console=console):
        jobs_df = handler.list_jobs(project_name=project)

    if jobs_df is not None and not jobs_df.empty:
        _display_df_as_table(console, jobs_df, title=f"Jobs in Project: {effective_project}")
    elif jobs_df is not None: # Empty DataFrame
        console.print(f"[yellow]No jobs found in project '[cyan]{effective_project}[/cyan]'.[/yellow]")
    # Error already printed by handler if jobs_df is None

@job_group.command('status')
@click.argument('job_name') # Removed help
@click.option('--project', default=None, help="MindsDB project where the job is located. Defaults to the currently connected project.")
@click.pass_context
def job_status(ctx, job_name, project):
    """
    Get the current status and details of a specific MindsDB job.

    This includes information like the last execution time, next run time, and current status (e.g., active, inactive, error).
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project = project if project else handler.project.name if handler.project else "current"
    with Status(f"Getting status for job '[cyan]{job_name}[/cyan]' in project '[cyan]{effective_project}[/cyan]'...", console=console):
        status_df = handler.get_job_status(job_name=job_name, project_name=effective_project)

    if status_df is not None and not status_df.empty:
        _display_df_as_table(console, status_df, title=f"Status for Job: {effective_project}.{job_name}")
    elif status_df is not None: # Empty DataFrame
        console.print(f"[yellow]Job '[cyan]{job_name}[/cyan]' not found in project '[cyan]{effective_project}[/cyan]'.[/yellow]")
    # Error already printed by handler if status_df is None

@job_group.command('history')
@click.argument('job_name') # Removed help
@click.option('--project', default=None, help="MindsDB project where the job is located. Defaults to the currently connected project. History is typically in the 'log' database.")
@click.pass_context
def job_history(ctx, job_name, project):
    """
    Get the execution history of a specific MindsDB job.

    Shows records of past job runs, including start time, end time, status, and any error messages.
    Note: Job history is often stored in a 'log.jobs_history' table which might require specific permissions or configuration in MindsDB to access.
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project = project if project else handler.project.name if handler.project else "current"
    with Status(f"Getting history for job '[cyan]{job_name}[/cyan]' in project '[cyan]{effective_project}[/cyan]'...", console=console):
        history_df = handler.get_job_history(job_name=job_name, project_name=effective_project)

    if history_df is not None and not history_df.empty:
        _display_df_as_table(console, history_df, title=f"Execution History for Job: {effective_project}.{job_name}")
    elif history_df is not None: # Empty DataFrame
        console.print(f"[yellow]No execution history found for job '[cyan]{job_name}[/cyan]' in project '[cyan]{effective_project}[/cyan]'.[/yellow]")
    # Error/warning already printed by handler if history_df is None or log table inaccessible

@job_group.command('create')
@click.argument('job_name') # Removed help
@click.argument('sql_statements') # Removed help
@click.option('--project', help="MindsDB project where the job should be created. Defaults to the currently connected project.")
@click.option('--schedule', help="Schedule interval for the job, using MindsDB's `SCHEDULE` syntax (e.g., 'EVERY 1 hour', 'EVERY MONDAY AT 09:00').")
@click.option('--start-date', help="Job start date/time. Format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.")
@click.option('--end-date', help="Job end date/time. Format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.")
@click.option('--if-condition', help="A SQL query that must return rows for the job to execute. E.g., \"SELECT 1 FROM my_table WHERE new_data_flag = TRUE\".")
@click.pass_context
def job_create_generic(ctx, job_name, sql_statements, project, schedule, start_date, end_date, if_condition):
    """
    Create a generic MindsDB job with one or more custom SQL statements.

    Allows for flexible automation of tasks using SQL.
    SQL_STATEMENTS should be a string containing one or more SQL commands,
    separated by semicolons.

    Example:
    `kleos job create my_nightly_ingest "INSERT INTO main_table SELECT * FROM staging_table WHERE date = CURRENT_DATE; DELETE FROM staging_table;" --schedule "EVERY 1 day at 01:00"`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    statements = [stmt.strip() for stmt in sql_statements.split(';') if stmt.strip()]
    if not statements:
        console.print("[red]Error: No SQL statements provided.[/red]")
        return

    console.print(f"Creating job '[cyan]{job_name}[/cyan]' with {len(statements)} SQL statement(s):")
    console.print(Syntax(";\n".join(statements), "sql", theme="dracula", line_numbers=True))
    if schedule: console.print(f"  Schedule: [yellow]{schedule}[/yellow]")
    if start_date: console.print(f"  Start Date: [yellow]{start_date}[/yellow]")
    if end_date: console.print(f"  End Date: [yellow]{end_date}[/yellow]")
    if if_condition: console.print(f"  Condition: [yellow]{if_condition}[/yellow]")
    
    with Status(f"Submitting job '[cyan]{job_name}[/cyan]'...", console=console):
        success = handler.create_job(
            job_name=job_name, statements=statements, project_name=project,
            start_date=start_date, end_date=end_date,
            schedule_interval=schedule, if_condition=if_condition
        )
    if success:
        console.print(f"[green]:heavy_check_mark: Job '[cyan]{job_name}[/cyan]' created successfully.[/green]")
        console.print(f"  Check status with: [bold]kleos job status {job_name}{f' --project {project}' if project else ''}[/bold]")
    else:
        console.print(f"[red]:x: Failed to create job '[cyan]{job_name}[/cyan]'.[/red]")

@job_group.command('logs') # Note: get_job_logs in handler currently returns status
@click.argument('job_name')
@click.option('--project', default=None, help="Project name (defaults to connected project).")
@click.pass_context
def job_logs(ctx, job_name, project):
    """Get the logs/details of a specific MindsDB job (currently shows status)."""
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project = project if project else handler.project.name if handler.project else "current"
    with Status(f"Getting logs/status for job '[cyan]{job_name}[/cyan]' in project '[cyan]{effective_project}[/cyan]'...", console=console):
        logs_df = handler.get_job_logs(job_name=job_name, project_name=effective_project) # This calls get_job_status

    if logs_df is not None and not logs_df.empty:
        _display_df_as_table(console, logs_df, title=f"Details/Status for Job: {effective_project}.{job_name}")
        console.print("[dim]Note: For detailed execution logs, query 'log.jobs_history' or specific log tables if available in your MindsDB setup.[/dim]")
    elif logs_df is not None: # Empty DataFrame
        console.print(f"[yellow]No logs/status found for job '[cyan]{job_name}[/cyan]' in project '[cyan]{effective_project}[/cyan]'.[/yellow]")
    # Error already printed by handler if logs_df is None

@job_group.command('drop')
@click.argument('job_name') # Removed help, already good in docstring
@click.option('--project', help="Project name for the job.")
@click.confirmation_option(prompt='Are you sure you want to drop this job?')
@click.pass_context
def job_drop(ctx, job_name, project):
    """Drop/delete a MindsDB job."""
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project = project if project else handler.project.name if handler.project else "current"
    with Status(f"Dropping job '[cyan]{job_name}[/cyan]' from project '[cyan]{effective_project}[/cyan]'...", console=console):
        success = handler.drop_job(job_name=job_name, project_name=project)

    if success:
        console.print(f"[green]:heavy_check_mark: Job '[cyan]{job_name}[/cyan]' (from project '[cyan]{effective_project}[/cyan]') dropped successfully.[/green]")
    else:
        console.print(f"[red]:x: Failed to drop job '[cyan]{job_name}[/cyan]' (from project '[cyan]{effective_project}[/cyan]').[/red]")

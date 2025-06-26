import click

@click.group('job')
def job_group():
    """Commands for managing MindsDB Jobs."""
    pass

@job_group.command('update-hn-refresh')
@click.argument('job_name')
@click.option('--hn-datasource', default='hackernews', show_default=True, help="Name of the HackerNews datasource to refresh.")
@click.option('--schedule', default='EVERY 1 day', show_default=True, help="Schedule interval for the job (e.g., 'EVERY 1 hour', 'EVERY 1 day').")
@click.option('--project', help="Project name where the job should be created.")
@click.pass_context
def job_update_hackernews_db(ctx, job_name, hn_datasource, schedule, project):
    """
    Creates a MindsDB Job to periodically refresh the HackerNews database by dropping and recreating it.
    
    This job will drop the existing HackerNews database and recreate it to get fresh data.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Creating job '{job_name}' to refresh HackerNews database '{hn_datasource}'...")
    click.echo(f"Schedule: {schedule}")

    if handler.update_hackernews_db(
        job_name=job_name,
        hn_datasource=hn_datasource,
        schedule_interval=schedule,
        project_name=project
    ):
        click.echo(click.style(f"Job '{job_name}' created successfully.", fg='green'))
        click.echo(f"You can check its status with: python main.py job status {job_name}")
    else:
        click.echo(click.style(f"Failed to create job '{job_name}'. Check logs for details.", fg='red'))

@job_group.command('list')
@click.option('--project', help="Filter jobs by project name.")
@click.pass_context
def job_list(ctx, project):
    """
    List all MindsDB jobs.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo("Listing MindsDB jobs...")
    result = handler.list_jobs(project_name=project)
    if result is None:
        click.echo(click.style("Failed to list jobs or no jobs found.", fg='yellow'))

@job_group.command('status')
@click.argument('job_name')
@click.option('--project', default='mindsdb', show_default=True, help="Project name where the job is located.")
@click.pass_context
def job_status(ctx, job_name, project):
    """
    Get the status of a specific MindsDB job.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Getting status for job '{job_name}'...")
    result = handler.get_job_status(job_name=job_name, project_name=project)
    if result is None:
        click.echo(click.style(f"Failed to get status for job '{job_name}' or job not found.", fg='yellow'))

@job_group.command('history')
@click.argument('job_name')
@click.option('--project', default='mindsdb', show_default=True, help="Project name where the job is located.")
@click.pass_context
def job_history(ctx, job_name, project):
    """
    Get the execution history of a specific MindsDB job.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Getting execution history for job '{job_name}'...")
    result = handler.get_job_history(job_name=job_name, project_name=project)
    if result is None:
        click.echo(click.style(f"Failed to get history for job '{job_name}' or no history found.", fg='yellow'))

@job_group.command('create')
@click.argument('job_name')
@click.argument('sql_statements')
@click.option('--project', help="Project name where the job should be created.")
@click.option('--schedule', help="Schedule interval (e.g., 'EVERY 1 hour', 'EVERY 2 days').")
@click.option('--start-date', help="Start date in format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.")
@click.option('--end-date', help="End date in format 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.")
@click.option('--if-condition', help="Conditional statement - job only runs if this returns rows.")
@click.pass_context
def job_create_generic(ctx, job_name, sql_statements, project, schedule, start_date, end_date, if_condition):
    """
    Create a generic MindsDB job with custom SQL statements.
    
    JOB_NAME: Name of the job to create
    SQL_STATEMENTS: SQL statements to execute (use semicolon to separate multiple statements)
    
    Examples:
    python main.py job create my_job "INSERT INTO my_table SELECT * FROM source_table" --schedule "EVERY 1 hour"
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    # Split SQL statements by semicolon
    statements = [stmt.strip() for stmt in sql_statements.split(';') if stmt.strip()]
    
    click.echo(f"Creating job '{job_name}' with {len(statements)} SQL statement(s)...")
    if schedule:
        click.echo(f"Schedule: {schedule}")
    if start_date:
        click.echo(f"Start date: {start_date}")
    if end_date:
        click.echo(f"End date: {end_date}")
    
    if handler.create_job(
        job_name=job_name,
        statements=statements,
        project_name=project,
        start_date=start_date,
        end_date=end_date,
        schedule_interval=schedule,
        if_condition=if_condition
    ):
        click.echo(click.style(f"Job '{job_name}' created successfully.", fg='green'))
        click.echo(f"You can check its status with: python main.py job status {job_name}")
    else:
        click.echo(click.style(f"Failed to create job '{job_name}'. Check logs for details.", fg='red'))

@job_group.command('logs')
@click.argument('job_name')
@click.option('--project', default='mindsdb', show_default=True, help="Project name where the job is located.")
@click.pass_context
def job_logs(ctx, job_name, project):
    """
    Get the logs/details of a specific MindsDB job.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Getting logs for job '{job_name}'...")
    result = handler.get_job_logs(job_name=job_name, project_name=project)
    if result is None:
        click.echo(click.style(f"Failed to get logs for job '{job_name}' or no logs found.", fg='yellow'))

@job_group.command('drop')
@click.argument('job_name')
@click.option('--project', help="Project name where the job is located.")
@click.confirmation_option(prompt='Are you sure you want to drop this job?')
@click.pass_context
def job_drop(ctx, job_name, project):
    """
    Drop/delete a MindsDB job.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Dropping job '{job_name}'...")
    if handler.drop_job(job_name=job_name, project_name=project):
        click.echo(click.style(f"Job '{job_name}' dropped successfully.", fg='green'))
    else:
        click.echo(click.style(f"Failed to drop job '{job_name}'.", fg='red'))

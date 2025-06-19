import click

@click.group('job')
def job_group():
    """Commands for managing MindsDB Jobs."""
    pass

@job_group.command('create-hn-ingest')
@click.argument('job_name')
@click.argument('kb_name')
@click.argument('hn_table_name', type=click.Choice(['stories', 'comments', 'polls', 'users'])) # Add other valid HN tables if needed
@click.option('--hn-datasource', default='hackernews', show_default=True, help="Name of the HackerNews datasource in MindsDB.")
@click.option('--interval', default='every 1 day', show_default=True, help="Schedule interval for the job (e.g., 'every 1 hour', 'every 15 minutes').")
# Add more options if needed to customize the job's SELECT query (e.g., specific columns to map)
# For now, the handler method has some defaults.
@click.pass_context
def job_create_hn_ingest(ctx, job_name, kb_name, hn_table_name, hn_datasource, interval):
    """
    Creates a MindsDB Job to periodically ingest new data from a HackerNews
    table (e.g., stories, comments) into a specified Knowledge Base.

    The job uses the LATEST keyword to fetch only new data since the last run.
    Default column mappings are used in the handler (e.g., 'title' or 'text' to content).
    Ensure the target Knowledge Base is structured to accept these columns.
    For 'stories': content (from title), story_id (from id), author (from by).
    For 'comments': content (from text), comment_id (from id), author (from by).
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Creating job '{job_name}' to ingest from '{hn_datasource}.{hn_table_name}' into '{kb_name}' scheduled '{interval}'...")

    if handler.create_mindsdb_job(
        job_name=job_name,
        kb_name=kb_name,
        hn_datasource=hn_datasource,
        hn_table_name=hn_table_name,
        schedule_interval=interval
    ):
        click.echo(click.style(f"Job '{job_name}' created successfully or already exists.", fg='green'))
        click.echo(f"You can check its status with: SELECT * FROM mindsdb.jobs WHERE name = '{job_name}';")
    else:
        click.echo(click.style(f"Failed to create job '{job_name}'. Check logs for details.", fg='red'))

# Add other job commands here if needed (e.g., job list, job delete, job status)

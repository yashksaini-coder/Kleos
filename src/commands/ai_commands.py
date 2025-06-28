import click
from config import config as app_config # To get GOOGLE_GEMINI_API_KEY

@click.group('ai')
def ai_group():
    """Commands for managing and querying AI Models (trained on data)."""
    pass

@ai_group.command('create-model') # Reverted from create-table
@click.argument('model_name') # Reverted from table_name
@click.option('--project-name', default=None, help="MindsDB project name. Defaults to the connected project.")
@click.option('--select-data-query', required=True, help="SQL SELECT query to fetch training data. E.g., 'SELECT text, category FROM my_integration.training_data'")
@click.option('--predict-column', required=True, help="Name of the column the AI Model should predict/generate.")
@click.option('--engine', default='openai', show_default=True, help="AI engine to use (e.g., 'openai', 'google_gemini', 'anthropic').")
@click.option('--prompt-template', default=None, help="Prompt template for the AI Model. E.g., 'Summarize this: {{text_column}}'")
@click.option('--param', 'additional_params', multiple=True, type=(str, str), help="Additional USING parameters as key-value pairs. E.g., --param model_name gpt-3.5-turbo --param api_key YOUR_KEY")
@click.pass_context
def ai_create_model(ctx, model_name, project_name, select_data_query, predict_column, engine, prompt_template, additional_params): # Reverted function name
    """
    Creates an AI Model that learns from input data specified by a SELECT query.
    The MODEL_NAME will be created in the specified --project-name or the default project.
    --select-data-query specifies the source of training data.
    --predict-column is the target variable the AI Model will learn to predict/generate.
    --engine specifies the underlying LLM engine.
    --prompt-template can be used to guide the AI Model's generation process.
    Additional engine-specific parameters can be passed using multiple --param options.
    Example:
    mdcli ai create-model my_summarizer_model --select-data-query "SELECT title, text FROM hackernews.stories WHERE score > 10" \\
    --predict-column summary --engine openai --prompt-template "Generate a concise summary for the following text: {{text}}. The title is {{title}}." \\
    --param api_key YOUR_OPENAI_KEY
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        click.echo(click.style("Could not determine MindsDB project. Please connect or specify --project-name.", fg='red'))
        return

    using_params = {'engine': engine}
    if prompt_template:
        using_params['prompt_template'] = prompt_template

    if engine == 'google_gemini' and 'api_key' not in dict(additional_params):
        gemini_api_key = app_config.GOOGLE_GEMINI_API_KEY
        if gemini_api_key:
            using_params['api_key'] = gemini_api_key
        else:
            click.echo(click.style(f"Warning: Engine is '{engine}' but GOOGLE_GEMINI_API_KEY not found in app config and not provided via --param api_key.", fg='yellow'))

    for key, value in additional_params:
        using_params[key] = value

    if engine in ['openai', 'anthropic', 'google_gemini'] and 'api_key' not in using_params:
         click.echo(click.style(f"Warning: Engine '{engine}' typically requires an 'api_key' in USING clause. Please provide it via --param api_key YOUR_KEY or ensure it's in app config for supported engines.", fg='yellow'))

    click.echo(f"Creating AI Model '{model_name}' in project '{effective_project_name}'...")
    click.echo(f"  Training data query: {select_data_query}")
    click.echo(f"  Predicting column: {predict_column}")
    click.echo(f"  Using parameters: {using_params}")

    if handler.create_model_from_query( # Updated to call renamed handler method
        model_name=model_name,
        project_name=effective_project_name,
        select_data_query=select_data_query,
        predict_column=predict_column,
        using_params=using_params
    ):
        click.echo(click.style(f"AI Model '{model_name}' creation process initiated or model already exists.", fg='green'))
        click.echo(f"Training/generation may take some time. Use 'ai list-models --project-name {effective_project_name}' and 'ai describe-model {model_name} --project-name {effective_project_name}' to check status.")
    else:
        click.echo(click.style(f"Failed to initiate creation for AI Model '{model_name}'.", fg='red'))

@ai_group.command('list-models') # Reverted from list-tables
@click.option('--project-name', default=None, help="MindsDB project name. Defaults to the connected project.")
@click.pass_context
def ai_list_models(ctx, project_name): # Reverted from ai_list_tables
    """Lists all AI Models in the specified project (or default project)."""
    handler = ctx.obj
    if not handler or (not handler.project and not project_name):
        click.echo(click.style("MindsDB connection not available or project not specified.", fg='red'))
        return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        click.echo(click.style("Could not determine MindsDB project. Please connect or specify --project-name.", fg='red'))
        return

    click.echo(f"Listing AI Models in project '{effective_project_name}'...")
    models_df = handler.list_models(project_name=effective_project_name)

    if models_df is not None and not models_df.empty:
        display_columns = ['name', 'status', 'engine', 'version', 'active', 'predict']
        available_display_columns = [col for col in display_columns if col in models_df.columns]

        if not available_display_columns:
             click.echo(models_df.to_string(index=False))
        else:
             click.echo(models_df[available_display_columns].to_string(index=False))
    elif models_df is not None:
        click.echo(click.style(f"No AI Models found in project '{effective_project_name}'.", fg='yellow'))
    else:
        click.echo(click.style(f"Failed to list AI Models from project '{effective_project_name}'.", fg='red'))

@ai_group.command('describe-model') # Reverted from describe-table
@click.argument('model_name') # Reverted from table_name
@click.option('--project-name', default=None, help="MindsDB project name. Defaults to the connected project.")
@click.pass_context
def ai_describe_model(ctx, model_name, project_name): # Reverted from ai_describe_table
    """Describes an AI Model, showing its details, schema, and status."""
    handler = ctx.obj
    if not handler or (not handler.project and not project_name):
        click.echo(click.style("MindsDB connection not available or project not specified.", fg='red'))
        return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        click.echo(click.style("Could not determine MindsDB project. Please connect or specify --project-name.", fg='red'))
        return

    click.echo(f"Describing AI Model '{model_name}' in project '{effective_project_name}'...")
    description_df = handler.describe_model(model_name=model_name, project_name=effective_project_name)

    if description_df is not None and not description_df.empty:
        click.echo(click.style(f"Details for AI Model '{model_name}':", fg='green'))
        if 'column' in description_df.columns and 'value' in description_df.columns:
            for _, row in description_df.iterrows():
                click.echo(f"  {row['column']}: {row['value']}")
        elif 'Type' in description_df.columns and 'Value' in description_df.columns:
             for _, row in description_df.iterrows():
                click.echo(f"  {row['Type']}: {row['Value']}")
        else:
            click.echo(description_df.to_string(index=False))

        status_row = description_df[description_df.apply(lambda row: str(row.iloc[0]).upper() == 'STATUS', axis=1)]
        if not status_row.empty:
            status_value = status_row.iloc[0,1]
            click.echo(click.style(f"AI Model Status: {status_value}", fg='blue'))
            if status_value.lower() == 'error':
                error_row = description_df[description_df.apply(lambda row: str(row.iloc[0]).upper() == 'ERROR', axis=1)]
                if not error_row.empty:
                     click.echo(click.style(f"Error Details: {error_row.iloc[0,1]}", fg='red'))
    elif description_df is not None:
        click.echo(click.style(f"No description found for AI Model '{model_name}' in project '{effective_project_name}'. It might not exist or is still processing.", fg='yellow'))
    else:
        click.echo(click.style(f"Failed to describe AI Model '{model_name}' from project '{effective_project_name}'.", fg='red'))

@ai_group.command('drop-model') # Reverted from drop-table
@click.argument('model_name') # Reverted from table_name
@click.option('--project-name', default=None, help="MindsDB project name. Defaults to the connected project.")
@click.confirmation_option(prompt='Are you sure you want to drop this AI Model? This action cannot be undone.')
@click.pass_context
def ai_drop_model(ctx, model_name, project_name): # Reverted from ai_drop_table
    """Drops (deletes) an AI Model from the specified project."""
    handler = ctx.obj
    if not handler or (not handler.project and not project_name):
        click.echo(click.style("MindsDB connection not available or project not specified.", fg='red'))
        return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        click.echo(click.style("Could not determine MindsDB project. Please connect or specify --project-name.", fg='red'))
        return

    click.echo(f"Attempting to drop AI Model '{model_name}' from project '{effective_project_name}'...")
    if handler.drop_model(model_name=model_name, project_name=effective_project_name):
        click.echo(click.style(f"AI Model '{model_name}' (or '{effective_project_name}.{model_name}') dropped successfully or did not exist.", fg='green'))
    else:
        click.echo(click.style(f"Failed to drop AI Model '{model_name}' from project '{effective_project_name}'.", fg='red'))

@ai_group.command('refresh-model') # Reverted from refresh-table
@click.argument('model_name') # Reverted from table_name
@click.option('--project-name', default=None, help="MindsDB project name. Defaults to the connected project.")
@click.pass_context
def ai_refresh_model(ctx, model_name, project_name): # Reverted from ai_refresh_table
    """
    Refreshes an AI Model, typically by retraining it with the latest data
    from its original data source.
    """
    handler = ctx.obj
    if not handler or (not handler.project and not project_name):
        click.echo(click.style("MindsDB connection not available or project not specified.", fg='red'))
        return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        click.echo(click.style("Could not determine MindsDB project. Please connect or specify --project-name.", fg='red'))
        return

    click.echo(f"Attempting to refresh AI Model '{model_name}' in project '{effective_project_name}'...")
    if handler.refresh_model(model_name=model_name, project_name=effective_project_name):
        click.echo(click.style(f"AI Model '{model_name}' (or '{effective_project_name}.{model_name}') refresh process initiated successfully.", fg='green'))
        click.echo(f"Retraining may take some time. Use 'ai describe-model {model_name} --project-name {effective_project_name}' to check status.")
    else:
        click.echo(click.style(f"Failed to initiate refresh for AI Model '{model_name}' from project '{effective_project_name}'.", fg='red'))

# @ai_group.command('retrain-model') # Reverted from retrain-table
# @click.argument('model_name') # Reverted from table_name
# @click.option('--project-name', default=None, help="MindsDB project name. Defaults to the connected project.")
# @click.option('--select-data-query', default=None, help="Optional new SQL SELECT query to fetch training data. If not provided, AI model retrains with original query/data source.")
# @click.option('--param', 'additional_params', multiple=True, type=(str, str), help="Optional new USING parameters as key-value pairs for retraining.")
# @click.pass_context
# def ai_retrain_model(ctx, model_name, project_name, select_data_query, additional_params): # Reverted from ai_retrain_table
#     """
#     Retrains an AI Model, optionally with a new data query or new USING parameters.
#     If --select-data-query is omitted, it behaves like 'refresh-model'.
#     """
#     handler = ctx.obj
#     if not handler or (not handler.project and not project_name):
#         click.echo(click.style("MindsDB connection not available or project not specified.", fg='red'))
#         return

#     effective_project_name = project_name if project_name else handler.project.name
#     if not effective_project_name:
#         click.echo(click.style("Could not determine MindsDB project. Please connect or specify --project-name.", fg='red'))
#         return

#     using_params = {}
#     if additional_params:
#         for key, value in additional_params:
#             using_params[key] = value

#     click.echo(f"Attempting to retrain AI Model '{model_name}' in project '{effective_project_name}'...")
#     if select_data_query:
#         click.echo(f"  Using new training data query: {select_data_query}")
#     if using_params:
#         click.echo(f"  Using new parameters: {using_params}")

#     if handler.retrain_model_custom(
#         model_name=model_name,
#         project_name=effective_project_name,
#         select_data_query=select_data_query,
#         using_params=using_params if using_params else None
#     ):
#         click.echo(click.style(f"AI Model '{model_name}' (or '{effective_project_name}.{model_name}') retrain process initiated successfully.", fg='green'))
#         click.echo(f"Retraining may take some time. Use 'ai describe-model {model_name} --project-name {effective_project_name}' to check status.")
#     else:
#         click.echo(click.style(f"Failed to initiate retrain for AI Model '{model_name}' from project '{effective_project_name}'.", fg='red'))

@ai_group.command('query')
@click.argument('query_string', type=str)
@click.option('--project-name', default=None, help="MindsDB project name to run the query against. Defaults to the connected project.")
@click.pass_context
def ai_query(ctx, query_string, project_name):
    """
    Executes a SQL query against the MindsDB project, typically to query an AI Model.
    The MODEL_NAME should be referenced appropriately within your QUERY_STRING.

    Example for an AI Model 'my_summarizer_model':
    mdcli ai query "SELECT hn.title, hn.text, ai.summary FROM hackernews.hnstories AS hn JOIN my_summarizer_model AS ai WHERE hn.title IS NOT NULL LIMIT 3"
    """
    handler = ctx.obj
    if not handler or (not handler.project and not project_name):
        click.echo(click.style("MindsDB connection not available or project not specified.", fg='red'))
        return

    if project_name and handler.project and project_name != handler.project.name:
        click.echo(click.style(f"Warning: Query will be executed in the context of the currently connected project ('{handler.project.name}'). "
                               f"Ensure your query string correctly references objects if they are in '{project_name}'.", fg='yellow'))
    elif not handler.project and project_name:
         click.echo(click.style(f"Warning: No active connection to a default project. Ensure your query string fully qualifies table and model names with their respective projects if needed.", fg='yellow'))

    click.echo(f"Executing query: {query_string}")
    try:
        result_df = handler.execute_sql(query_string)
        if result_df is not None:
            if not result_df.empty:
                click.echo(click.style("Query Result:", fg='green'))
                click.echo(result_df.to_string(index=False))
            else:
                click.echo(click.style("Query executed successfully but returned no data.", fg='yellow'))
        else:
            click.echo(click.style("Query execution failed to return results.", fg='red'))
    except Exception as e:
        click.echo(click.style(f"Error executing query: {str(e)}", fg='red'))

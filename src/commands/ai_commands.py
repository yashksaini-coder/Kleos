import click
import pandas as pd
from rich.table import Table
from rich.status import Status
from rich.syntax import Syntax
from rich.text import Text
from config import config as app_config # To get GOOGLE_GEMINI_API_KEY
from .utils import get_handler_and_console, CONTEXT_SETTINGS, RichHelpFormatter # Import RichHelpFormatter

@click.group('ai', context_settings=CONTEXT_SETTINGS)
def ai_group():
    """Commands for managing AI Models, often called 'Generative AI Tables' in MindsDB.

    These models are created from your data using a `CREATE MODEL ... FROM (SELECT ...)`
    SQL statement. They can be used for various tasks such as text classification,
    summarization, translation, or other generative AI tasks, depending on the
    chosen engine and prompt template.
    """
    pass

ai_group.formatter_class = RichHelpFormatter # Set formatter for this group

@ai_group.command('create-model')
@click.argument('model_name')
@click.option('--project-name', default=None, help="MindsDB project where the model will be created. Defaults to the currently connected project.")
@click.option('--select-data-query', required=True, help="SQL SELECT query to fetch training data. Must be a complete query. E.g., 'SELECT text_column, label_column FROM my_datasource.my_table'.")
@click.option('--predict-column', required=True, help="Name of the column the AI Model should learn to predict or generate.")
@click.option('--engine', default='openai', show_default=True, help="AI engine to use (e.g., 'openai', 'google_gemini', 'anthropic', 'ollama'). Check MindsDB docs for available engines.")
@click.option('--prompt-template', default=None, help="Prompt template for the AI Model. Use {{column_name}} for placeholders from your --select-data-query. E.g., 'Summarize: {{text_column}}'.")
@click.option('--param', 'additional_params', multiple=True, type=(str, str), help="Additional `USING` parameters as key-value pairs. Can be specified multiple times. E.g., --param model_name gpt-3.5-turbo --param api_key YOUR_API_KEY.")
@click.pass_context
def ai_create_model(ctx, model_name, project_name, select_data_query, predict_column, engine, prompt_template, additional_params):
    """
    Creates an AI Model (Generative AI Table) by training it on data from a SELECT query.

    This command constructs a `CREATE MODEL ... FROM (SELECT ...) PREDICT ... USING ...` SQL statement.
    The MODEL_NAME will be created in the specified --project-name or the default connected project.

    --select-data-query: Provides the training data. Ensure columns referenced in the
                         prompt template are selected in this query.
    --predict-column: The target variable the AI Model will learn to generate.
    --engine: Specifies the underlying LLM or ML engine.
    --prompt-template: Guides the model's generation process. Use {{column_name}} for features.
    --param: Allows passing engine-specific parameters like API keys, model variants (e.g., 'gpt-4'), temperature, etc.

    Examples:

      Create a text summarizer using OpenAI:
      `kleos ai create-model news_summarizer --select-data-query "SELECT article_text FROM news_data.articles" --predict-column summary --engine openai --prompt-template "Summarize this article: {{article_text}}" --param api_key YOUR_OPENAI_KEY --param model_name gpt-3.5-turbo`

      Create a sentiment classifier using Google Gemini:
      `kleos ai create-model review_sentiment --select-data-query "SELECT review, sentiment FROM my_reviews.data" --predict-column sentiment --engine google_gemini --prompt-template "Classify sentiment: {{review}}" --param api_key YOUR_GOOGLE_KEY`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        console.print("[red]:x: Could not determine MindsDB project. Please connect or specify --project-name.[/red]")
        return

    using_params = {'engine': engine}
    if prompt_template: using_params['prompt_template'] = prompt_template
    if engine == 'google_gemini' and 'api_key' not in dict(additional_params):
        gemini_api_key = app_config.GOOGLE_GEMINI_API_KEY
        if gemini_api_key: using_params['api_key'] = gemini_api_key
        else: console.print(f"[yellow]Warning: Engine is '{engine}' but GOOGLE_GEMINI_API_KEY not found in config and not provided via --param api_key.[/yellow]")
    for key, value in additional_params: using_params[key] = value
    if engine in ['openai', 'anthropic', 'google_gemini'] and 'api_key' not in using_params:
         console.print(f"[yellow]Warning: Engine '{engine}' typically requires an 'api_key'. Provide via --param api_key or ensure in config.[/yellow]")

    console.print(f"Creating AI Model '[cyan]{model_name}[/cyan]' in project '[cyan]{effective_project_name}[/cyan]'...")
    console.print(Text.assemble(("  Training data query: ", "dim"), (select_data_query, "italic")))
    console.print(Text.assemble(("  Predicting column: ", "dim"), (predict_column, "italic")))
    console.print(Text.assemble(("  Using parameters: ", "dim"), (str(using_params), "italic")))

    with Status(f"Initiating AI Model '[cyan]{model_name}[/cyan]' creation...", console=console, spinner="dots"):
        success = handler.create_model_from_query(
            model_name=model_name, project_name=effective_project_name,
            select_data_query=select_data_query, predict_column=predict_column, using_params=using_params
        )
    if success:
        console.print(f"[green]:heavy_check_mark: AI Model '[cyan]{model_name}[/cyan]' creation process initiated or model already exists.[/green]")
        console.print(f"[dim]Training/generation may take time. Use 'kleos ai list-models --project-name {effective_project_name}' and 'kleos ai describe-model {model_name} --project-name {effective_project_name}' to check status.[/dim]")
    else:
        console.print(f"[red]:x: Failed to initiate creation for AI Model '[cyan]{model_name}[/cyan]'.[/red]")

@ai_group.command('list-models')
@click.option('--project-name', default=None, help="MindsDB project from which to list models. Defaults to the currently connected project.")
@click.pass_context
def ai_list_models(ctx, project_name):
    """
    Lists all AI Models within a specified MindsDB project.

    Displays key information: NAME, ENGINE, PROJECT, ACTIVE, STATUS, PREDICT,
    UPDATE_STATUS, and TRAINING_OPTIONS.
    The table will use the full console width.
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        console.print("[red]:x: Could not determine MindsDB project. Please connect or specify --project-name.[/red]")
        return

    with Status(f"Fetching AI Models from project '[cyan]{effective_project_name}[/cyan]'...", console=console):
        # Assuming handler.list_models() returns a DataFrame with columns like:
        # 'name', 'engine', 'project_name', 'active', 'status', 'predict' (target column),
        # 'update_status', 'training_options_json' (or similar for training_options)
        models_df = handler.list_models(project_name=effective_project_name)

    if models_df is not None and not models_df.empty:
        console.print(f"\n[bold green]AI Models in Project '[cyan]{effective_project_name}[/cyan]':[/bold green]")

        # Define the exact columns to display and their user-friendly headers.
        # The keys are the expected column names from models_df (adjust if handler.list_models() returns different names).
        # The values are the headers to display in the table.
        # Example: 'name' from df becomes 'NAME' in table.
        # These are based on the user request: NAME, ENGINE, PROJECT, ACTIVE, STATUS, PREDICT, UPDATE_STATUS, TRAINING_OPTIONS
        # Assuming MindsDB `SHOW MODELS` output columns are lowercase with underscores.
        display_columns_map = {
            'NAME': 'NAME',
            'ENGINE': 'ENGINE',
            'PROJECT': 'PROJECT',
            'ACTIVE': 'ACTIVE',
            'STATUS': 'STATUS',
            'PREDICT': 'PREDICT',
            'STATUS': 'STATUS',
            'TRAINING_OPTIONS': 'TRAINING_OPTIONS'
        }

        # Create table. `expand=True` helps in utilizing full width when possible.
        # `box=box.ROUNDED` for a nicer look.
        table = Table(show_header=True, header_style="bold magenta", show_lines=True,
                      title=f"AI Models in Project '[cyan]{effective_project_name}[/cyan]'",
                      expand=True)

        actual_df_columns_to_render = []

        for df_col, display_header in display_columns_map.items():
            if df_col in models_df.columns:
                col_options = {}
                if df_col == 'training_options': # Keep training_options potentially truncated as it can be very long
                    col_options['max_width'] = 50
                    col_options['overflow'] = 'ellipsis'

                # For other columns, let Rich manage width by not setting max_width, allowing them to expand.
                # Rich's `expand=True` on Table and no width on Column helps.
                table.add_column(display_header, **col_options)
                actual_df_columns_to_render.append(df_col)
            else:
                # If a specifically requested column is missing in the DataFrame,
                # we could add it with a note or skip. For now, skipping.
                console.print(f"[yellow]Note: Column '{df_col}' (for '{display_header}') not found in model data. It will not be displayed.[/yellow]")

        if not actual_df_columns_to_render:
            console.print("[red]Error: None of the requested columns were found in the model data. Cannot display table.[/red]")
            # Fallback to showing all available columns if none of the desired ones are present.
            if not models_df.empty:
                console.print("[yellow]Displaying all available columns instead:[/yellow]")
                for df_col_name in models_df.columns:
                    table.add_column(df_col_name.replace('_', ' ').title(), max_width=30, overflow="ellipsis") # Basic fallback
                    actual_df_columns_to_render.append(df_col_name)
            else: # models_df is empty
                console.print(f"[yellow]No AI Models found in project '[cyan]{effective_project_name}[/cyan]'.[/yellow]")
                return


        # Only proceed to add rows if there are columns to render
        if actual_df_columns_to_render:
            for _, row in models_df.iterrows():
                row_data = []
                for df_col_name in actual_df_columns_to_render:
                    cell_value = row.get(df_col_name)
                    # Ensure training_options (or any complex object) is nicely stringified for the table
                    if df_col_name == 'training_options' and not isinstance(cell_value, str):
                        cell_value = str(cell_value)
                    else:
                        cell_value = str(cell_value) if cell_value is not None else ""
                    row_data.append(cell_value)
                table.add_row(*row_data)

            if table.columns:
                console.print(table)
            else:
                 console.print(f"[red]Error: Could not prepare table for display even though model data exists for project '{effective_project_name}'.[/red]")
        # If actual_columns_to_render was empty and models_df was also empty, it's handled above.

    elif models_df is not None: # models_df is empty
        console.print(f"[yellow]No AI Models found in project '[cyan]{effective_project_name}[/cyan]'.[/yellow]")
    else: # models_df is None (error fetching)
        console.print(f"[red]:x: Failed to list AI Models from project '[cyan]{effective_project_name}[/cyan]'.[/red]")

@ai_group.command('describe-model')
@click.argument('model_name')
@click.option('--project-name', default=None, help="MindsDB project where the model resides. Defaults to the currently connected project.")
@click.pass_context
def ai_describe_model(ctx, model_name, project_name):
    """
    Shows detailed information for a specific AI Model in a table format.

    Displays: NAME, ENGINE, PROJECT, ACTIVE, STATUS, PREDICT, UPDATE_STATUS,
    and TRAINING_OPTIONS. The table uses the full console width.
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        console.print("[red]:x: Could not determine MindsDB project. Please connect or specify --project-name.[/red]")
        return

    with Status(f"Fetching details for AI Model '[cyan]{model_name}[/cyan]' in project '[cyan]{effective_project_name}[/cyan]'...", console=console):
        # We expect handler.describe_model to return a DataFrame for the single model,
        # containing the necessary columns, similar to a filtered `list_models` result.
        # If handler.describe_model returns the old format (key-value pairs), this will need adjustment
        # in the handler itself, or here by fetching all models and filtering.
        # For now, proceeding with the assumption it returns a one-row DataFrame with relevant columns.
        model_df = handler.describe_model(model_name=model_name, project_name=effective_project_name)

    if model_df is not None and not model_df.empty:
        # Ensure we're dealing with a single model's data, possibly by taking the first row
        # if describe_model by chance returns more (e.g. if it internally used list_models without exact name filter)
        if len(model_df) > 1:
            # If more than one model is returned by describe_model for a specific name, it's unexpected.
            # We'll take the first one that matches the name, or just the first one.
            # A more robust handler.describe_model should ensure only one model's data is returned.
            console.print(f"[yellow]Warning: describe-model returned multiple entries for '{model_name}'. Displaying the first one.[/yellow]")
            # Attempt to find an exact name match if multiple rows are returned
            exact_match_df = model_df[model_df['name'].str.lower() == model_name.lower()]
            if not exact_match_df.empty:
                model_df = exact_match_df.head(1)
            else:
                model_df = model_df.head(1) # Fallback to first row if no exact name match (e.g. due to case)

        console.print(f"\n[bold green]Details for AI Model '[cyan]{effective_project_name}.{model_name}[/cyan]':[/bold green]")

        display_columns_map = {
            'NAME': 'NAME',
            'ENGINE': 'ENGINE',
            'PROJECT': 'PROJECT',
            'ACTIVE': 'ACTIVE',
            'STATUS': 'STATUS',
            'PREDICT': 'PREDICT',
            'STATUS': 'STATUS',
            'TRAINING_OPTIONS': 'TRAINING_OPTIONS'
        }

        table = Table(show_header=True, header_style="bold magenta", show_lines=True,
                      title=f"Details for AI Model '[cyan]{effective_project_name}.{model_name}[/cyan]'",
                      expand=True)

        actual_df_columns_to_render = []
        for df_col, display_header in display_columns_map.items():
            if df_col in model_df.columns:
                col_options = {}
                if df_col == 'training_options':
                    col_options['max_width'] = 50
                    col_options['overflow'] = 'ellipsis'
                table.add_column(display_header, **col_options)
                actual_df_columns_to_render.append(df_col)
            else:
                console.print(f"[yellow]Note: Detail '{df_col}' (for '{display_header}') not found for this model. It will not be displayed.[/yellow]")

        if not actual_df_columns_to_render:
            console.print(f"[red]Error: None of the requested details were found for model '{model_name}'.[/red]")
            # Fallback to showing all available columns from the first row if any.
            if not model_df.empty:
                console.print("[yellow]Displaying all available raw details instead (key-value format):[/yellow]")
                # Revert to a simple key-value display if the structured table fails
                kv_table = Table(show_header=False, box=None)
                kv_table.add_column("Property", style="dim")
                kv_table.add_column("Value")
                first_row = model_df.iloc[0]
                for col_name, value in first_row.items():
                    kv_table.add_row(str(col_name), str(value))
                console.print(kv_table)
            return

        # Add the single row of model data
        if actual_df_columns_to_render and not model_df.empty:
            # model_df should contain one row after the logic above
            row_data_series = model_df.iloc[0]
            row_values = []
            for df_col_name in actual_df_columns_to_render:
                cell_value = row_data_series.get(df_col_name)
                if df_col_name == 'training_options' and not isinstance(cell_value, str):
                    cell_value = str(cell_value)
                else:
                    cell_value = str(cell_value) if cell_value is not None else ""
                row_values.append(cell_value)
            table.add_row(*row_values)

            if table.columns:
                console.print(table)
            else: # Should be rare
                 console.print(f"[red]Error: Could not prepare table for display for model '{model_name}'.[/red]")
        elif model_df.empty : # Handles case where model_df became empty after filtering
             console.print(f"[yellow]No data found for AI Model '[cyan]{model_name}[/cyan]' in project '[cyan]{effective_project_name}[/cyan]' after filtering.[/yellow]")

    elif model_df is not None: # model_df is empty initially
        console.print(f"[yellow]No description found for AI Model '[cyan]{model_name}[/cyan]' in project '[cyan]{effective_project_name}[/cyan]'. It might not exist.[/yellow]")
    else: # model_df is None (error fetching)
        console.print(f"[red]:x: Failed to describe AI Model '[cyan]{model_name}[/cyan]' from project '[cyan]{effective_project_name}[/cyan]'. Check connection and model name.[/red]")

@ai_group.command('drop-model')
@click.argument('model_name')
@click.option('--project-name', default=None, help="MindsDB project where the model resides. Defaults to the currently connected project.")
@click.confirmation_option(prompt='Are you sure you want to drop this AI Model? This action is irreversible.')
@click.pass_context
def ai_drop_model(ctx, model_name, project_name):
    """
    Drops (deletes) a specified AI Model from a MindsDB project.

    This action is irreversible and will remove the model and its associated training artifacts.
    You will be prompted for confirmation before deletion.
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        console.print("[red]:x: Could not determine MindsDB project. Please connect or specify --project-name.[/red]")
        return

    with Status(f"Attempting to drop AI Model '[cyan]{model_name}[/cyan]' from project '[cyan]{effective_project_name}[/cyan]'...", console=console):
        success = handler.drop_model(model_name=model_name, project_name=effective_project_name)

    if success:
        console.print(f"[green]:heavy_check_mark: AI Model '[cyan]{effective_project_name}.{model_name}[/cyan]' dropped successfully or did not exist.[/green]")
    else:
        console.print(f"[red]:x: Failed to drop AI Model '[cyan]{effective_project_name}.{model_name}[/cyan]'.[/red]")

@ai_group.command('refresh-model')
@click.argument('model_name')
@click.option('--project-name', default=None, help="MindsDB project where the model resides. Defaults to the currently connected project.")
@click.pass_context
def ai_refresh_model(ctx, model_name, project_name):
    """
    Refreshes an existing AI Model.

    This typically involves retraining the model with the latest data from its
    original data source, using its original training parameters (`RETRAIN model_name;`).
    The model status will change to 'training' or 'generating' during this process.
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project_name = project_name if project_name else handler.project.name
    if not effective_project_name:
        console.print("[red]:x: Could not determine MindsDB project. Please connect or specify --project-name.[/red]")
        return

    with Status(f"Attempting to refresh AI Model '[cyan]{model_name}[/cyan]' in project '[cyan]{effective_project_name}[/cyan]'...", console=console):
        success = handler.refresh_model(model_name=model_name, project_name=effective_project_name)

    if success:
        console.print(f"[green]:heavy_check_mark: AI Model '[cyan]{effective_project_name}.{model_name}[/cyan]' refresh process initiated successfully.[/green]")
        console.print(f"[dim]Retraining may take time. Use 'kleos ai describe-model {model_name} --project-name {effective_project_name}' to check status.[/dim]")
    else:
        console.print(f"[red]:x: Failed to initiate refresh for AI Model '[cyan]{effective_project_name}.{model_name}[/cyan]'.[/red]")

@ai_group.command('query')
@click.argument('query_string', type=str) # Removed help, will be in docstring
@click.option('--project-name', default=None, help="MindsDB project context for the query. Defaults to the currently connected project.")
@click.pass_context
def ai_query(ctx, query_string, project_name):
    """
    Executes an arbitrary SQL query against the MindsDB project.

    This is commonly used to query AI Models by joining them with data tables
    or selecting from them with a `WHERE` clause that provides input to the model.
    Ensure your query string correctly references table and model names, including
    project and datasource prefixes if necessary (e.g., `mindsdb.my_model`, `my_datasource.input_data`).

    Example for an AI Model 'my_summarizer_model':
    `kleos ai query "SELECT t.text_content, m.summary FROM news.articles AS t JOIN mindsdb.my_summarizer_model AS m WHERE t.id = 123"`

    Directly querying a model that takes input via WHERE clause:
    `kleos ai query "SELECT * FROM mindsdb.my_translator_model WHERE text_to_translate = 'Hello world' AND target_language = 'Spanish'"`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    effective_project_name = project_name if project_name else handler.project.name if handler.project else "default"

    if project_name and handler.project and project_name != handler.project.name:
        console.print(f"[yellow]Warning: Query will be executed in the context of the connected project ('{handler.project.name}'). "
                      f"Ensure your query string correctly references objects if they are in '{project_name}'.[/yellow]")

    console.print(f"Executing query in project '[cyan]{effective_project_name}[/cyan]':")
    console.print(Syntax(query_string, "sql", theme="dracula", line_numbers=True))

    with Status("Executing query...", console=console, spinner="aesthetic"):
        try:
            result_df = handler.execute_sql(query_string)
        except Exception as e:
            console.print(f"[red]:x: Error executing query: {str(e)}[/red]")
            return

    if result_df is not None:
        if not result_df.empty:
            console.print("\n[bold green]Query Result:[/bold green]")
            table = Table(show_header=True, header_style="bold magenta", show_lines=True)
            for col in result_df.columns: table.add_column(col)
            for _, row in result_df.iterrows():
                table.add_row(*(str(x) for x in row))
            console.print(table)
        else:
            console.print("[yellow]Query executed successfully but returned no data.[/yellow]")
    else: # Should not happen if execute_sql raises on failure, but as a safeguard
        console.print("[red]:x: Query execution failed to return results.[/red]")

# Full content for src/commands/kb_commands.py

import click
import json
from config import config as app_config # Used for default OLLAMA_BASE_URL in kb create

@click.group('kb')
def kb_group():
    """Commands for managing Knowledge Bases and associated AI Agents."""
    pass

# --- Existing KB Commands (from previous steps) ---

@kb_group.command('create')
@click.argument('kb_name')
@click.option('--embedding-provider', default='ollama', show_default=True, help="Provider for embedding model (e.g., ollama, openai, google).")
@click.option('--embedding-model', default='nomic-embed-text', show_default=True, help="Name of the embedding model.")
@click.option('--embedding-base-url', default=None, help="Base URL for the embedding model provider (e.g., for ollama).")
@click.option('--embedding-api-key', default=None, help="API key for the embedding model provider (e.g., for google, openai).")
@click.option('--reranking-provider', default=None, help="Provider for reranking model (optional, e.g., ollama, google, cohere).")
@click.option('--reranking-model', default=None, help="Name of the reranking model (optional, e.g., llama3, gemini-pro).")
@click.option('--reranking-base-url', default=None, help="Base URL for the reranking model provider (if needed, optional).")
@click.option('--reranking-api-key', default=None, help="API key for the reranking model provider (if needed, optional).")
@click.option('--content-columns', help="Comma-separated list of content columns (e.g., 'title,text').")
@click.option('--metadata-columns', help="Comma-separated list of metadata columns (e.g., 'id,time,score').")
@click.option('--id-column', help="Name of the ID column (e.g., 'id').")
@click.pass_context
def kb_create(ctx, kb_name, embedding_provider, embedding_model, embedding_base_url, embedding_api_key,
              reranking_provider, reranking_model, reranking_base_url, reranking_api_key,
              content_columns, metadata_columns, id_column):
    """Creates a new Knowledge Base with specified embedding and reranking models."""
    handler = ctx.obj
    if not handler or not handler.project:
        # Attempt to connect if not already connected or if connection failed previously
        if not handler.connect():
            click.echo(click.style("MindsDB connection failed. Please ensure MindsDB is running and accessible.", fg='red'))
            return
        # If connect() was called, handler.project should now be set if successful.
        # If it's still None, then the connection truly failed.
        if not handler.project:
            click.echo(click.style("MindsDB connection not available even after retry.", fg='red'))
            return


    # Auto-use app_config.OLLAMA_BASE_URL if provider is ollama and URL not specified for embedding
    if embedding_provider == 'ollama' and not embedding_base_url:
        embedding_base_url = getattr(app_config, 'OLLAMA_BASE_URL', None)
        if not embedding_base_url:
            click.echo(click.style("Warning: Embedding provider is ollama, but OLLAMA_BASE_URL is not configured and --embedding-base-url not provided.", fg='yellow'))

    # Auto-use app_config.OLLAMA_BASE_URL if provider is ollama and URL not specified for reranking
    if reranking_provider == 'ollama' and not reranking_base_url and reranking_model:
        reranking_base_url = getattr(app_config, 'OLLAMA_BASE_URL', None)
        if not reranking_base_url:
            click.echo(click.style("Warning: Reranking provider is ollama, but OLLAMA_BASE_URL is not configured and --reranking-base-url not provided.", fg='yellow'))

    # Ensure reranking provider/URL/key are None if model is not specified
    if not reranking_model:
        reranking_provider = None
        reranking_base_url = None
        reranking_api_key = None

    # Parse content and metadata columns
    content_columns_list = [col.strip() for col in content_columns.split(',')] if content_columns else None
    metadata_columns_list = [col.strip() for col in metadata_columns.split(',')] if metadata_columns else None

    click.echo(f"Creating Knowledge Base '{kb_name}' with embedding model '{embedding_provider}/{embedding_model}'...")
    if reranking_model:
        click.echo(f"Using reranking model '{reranking_provider}/{reranking_model}'.")
    if content_columns_list:
        click.echo(f"Content columns: {content_columns_list}")
    if metadata_columns_list:
        click.echo(f"Metadata columns: {metadata_columns_list}")
    if id_column:
        click.echo(f"ID column: {id_column}")

    if handler.create_knowledge_base(
        kb_name=kb_name,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        embedding_base_url=embedding_base_url,
        embedding_api_key=embedding_api_key,
        reranking_provider=reranking_provider,
        reranking_model=reranking_model,
        reranking_base_url=reranking_base_url,
        reranking_api_key=reranking_api_key,
        content_columns=content_columns_list,
        metadata_columns=metadata_columns_list,
        id_column=id_column
    ):
        click.echo(click.style(f"Knowledge Base '{kb_name}' creation command sent successfully.", fg='green'))
        click.echo(click.style(f"Note: KB creation is asynchronous. Check MindsDB logs or list KBs to confirm.", fg='bright_black'))
    else:
        click.echo(click.style(f"Failed to send command to create Knowledge Base '{kb_name}'.", fg='red'))

@kb_group.command('index')
@click.argument('kb_name')
@click.pass_context
def kb_index(ctx, kb_name):
    """Creates/refreshes the index for a Knowledge Base (typically the content vector index)."""
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return
    click.echo(f"Initiating index creation/refresh for Knowledge Base '{kb_name}'...")
    if handler.create_index_on_knowledge_base(kb_name):
        click.echo(click.style(f"Index operation for '{kb_name}' initiated successfully.", fg='green'))
    else:
        click.echo(click.style(f"Failed to initiate index operation for '{kb_name}'.", fg='red'))

@kb_group.command('ingest')
@click.argument('kb_name')
@click.option('--from-hackernews', 'from_hackernews_table', help="Name of the HackerNews table to ingest from (e.g., 'stories', 'comments').")
@click.option('--hn-datasource', default='hackernews', show_default=True, help="Name of the HackerNews datasource in MindsDB.")
@click.option('--limit', type=int, default=100, show_default=True, help="Number of records to ingest from HackerNews table.")
@click.option('--content-column', help="Source column for KB content. Auto-detects: 'title' for stories, 'text' for comments.")
@click.option('--metadata-map', help="JSON string mapping KB metadata_cols to source_cols. Auto-detects for HackerNews tables if not specified.")
@click.pass_context
def kb_ingest(ctx, kb_name, from_hackernews_table, hn_datasource, limit, content_column, metadata_map):
    """Ingests data into a Knowledge Base from a HackerNews table with smart defaults."""
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red')); return
    if not from_hackernews_table:
        click.echo(click.style("Please specify --from-hackernews <table_name>.", fg='red')); return
    
    # Smart defaults for HackerNews tables
    if not content_column:
        if from_hackernews_table == 'stories':
            content_column = 'title'
        elif from_hackernews_table == 'comments':
            content_column = 'text'
        else:
            click.echo(click.style("Please specify --content-column for this table.", fg='red')); return
    
    # Smart defaults for metadata mapping
    parsed_metadata_map = None
    if metadata_map:
        try:
            parsed_metadata_map = json.loads(metadata_map)
            if not isinstance(parsed_metadata_map, dict): 
                click.echo(click.style("metadata-map must be a JSON dictionary.", fg='red')); return
            # Validate that all values are strings (column names)
            for kb_col, source_col in parsed_metadata_map.items():
                if not isinstance(source_col, str):
                    raise ValueError(f"All metadata map values must be source column names (strings). Got: {source_col}")
        except Exception as e: 
            click.echo(click.style(f"Invalid JSON in --metadata-map: {e}", fg='red')); return
    else:
        # Provide smart defaults based on HackerNews table structure
        if from_hackernews_table == 'stories':
            parsed_metadata_map = {
                "story_id": "id",
                "time": "time", 
                "score": "score",
                "descendants": "descendants"
            }
        elif from_hackernews_table == 'comments':
            parsed_metadata_map = {
                "comment_id": "id",
                "time": "time",
                "parent": "parent"
            }
        elif from_hackernews_table == 'hnstories':
            parsed_metadata_map = {
                "story_id": "id"
            }
        click.echo(f"Using smart defaults for {from_hackernews_table}: content='{content_column}', metadata={list(parsed_metadata_map.keys())}")

    click.echo(f"Ingesting data from '{hn_datasource}.{from_hackernews_table}' into '{kb_name}'...")
    
    # Check if the HackerNews datasource exists, create it if it doesn't
    if not handler.get_database_custom_check(hn_datasource):
        click.echo(f"HackerNews datasource '{hn_datasource}' not found. Creating it...")
        if not handler.create_hackernews_datasource(ds_name=hn_datasource):
            click.echo(click.style(f"Failed to create HackerNews datasource '{hn_datasource}'.", fg='red'))
            return
        click.echo(click.style(f"HackerNews datasource '{hn_datasource}' created successfully.", fg='green'))
    
    # Build the source table name
    source_table = f"{hn_datasource}.{from_hackernews_table}"
    
    # Use the new direct insertion method which follows MindsDB's recommended syntax
    try:
        if handler.insert_into_knowledge_base_direct(
            kb_name=kb_name, 
            source_table=source_table,
            content_column=content_column, 
            metadata_columns=parsed_metadata_map,
            limit=limit,
            order_by="id DESC"
        ):
            click.echo(click.style(f"Data ingestion into '{kb_name}' initiated successfully.", fg='green'))
        else:
            click.echo(click.style(f"Data ingestion into '{kb_name}' failed.", fg='red'))
    except Exception as e:
        click.echo(click.style(f"Error during ingestion: {e}", fg='red'))

@kb_group.command('query')
@click.argument('kb_name')
@click.argument('query_text')
@click.option('--metadata-filter', 'metadata_filters_str', help="JSON string for metadata filters. E.g., '{\"author\":\"John Doe\", \"year\":2023}'.")
@click.option('--limit', type=int, default=5, show_default=True, help="Max number of results.")
@click.pass_context
def kb_query(ctx, kb_name, query_text, metadata_filters_str, limit):
    """Queries a Knowledge Base using semantic search and optional metadata filters."""
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red')); return
    metadata_filters = None
    if metadata_filters_str:
        try:
            metadata_filters = json.loads(metadata_filters_str)
            if not isinstance(metadata_filters, dict): raise ValueError("metadata-filter must be a JSON dictionary.")
        except Exception as e: click.echo(click.style(f"Invalid JSON in --metadata-filter: {e}", fg='red')); return

    click.echo(f"Querying KB '{kb_name}' for: '{query_text}' with filters: {metadata_filters}")
    results_df = handler.select_from_knowledge_base(kb_name, query_text, metadata_filters=metadata_filters, limit=limit)
    if results_df is not None:
        if not results_df.empty:
            click.echo(click.style("Query results:", fg='green')); click.echo(results_df.to_string())
        else:
            click.echo(click.style("No results found.", fg='yellow'))
    else:
        click.echo(click.style("Failed to query Knowledge Base.", fg='red'))

@kb_group.command('list-databases')
@click.pass_context
def kb_list_databases(ctx):
    """Lists all available databases/datasources in MindsDB."""
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return
    
    try:
        databases_df = handler.execute_sql('SHOW DATABASES;')
        if databases_df is not None and not databases_df.empty:
            click.echo(click.style("Available databases/datasources:", fg='green'))
            click.echo(databases_df.to_string(index=False))
        else:
            click.echo(click.style("No databases found or query failed.", fg='yellow'))
    except Exception as e:
        click.echo(click.style(f"Error listing databases: {e}", fg='red'))

# --- New AI Agent Commands ---

@kb_group.command('create-agent')
@click.argument('agent_name')
@click.option('--model-name', required=True, help="LLM model name for the agent (e.g., 'gemini-1.5-flash', 'llama3').")
@click.option('--include-knowledge-bases', required=True, help="Comma-separated list of Knowledge Base names to include.")
@click.option('--google-api-key', default=None, help="Google API key, if required by the model.")
@click.option('--include-tables', default=None, help="Comma-separated list of table names to include (e.g., 'datasource.table1,ds.table2').")
@click.option('--prompt-template', default=None, help="Custom prompt template for the agent. Use triple quotes for multi-line.")
@click.option('--other-params', 'other_params_str', default=None, help="JSON string of other parameters for the agent's USING clause (e.g., '{\"temperature\": 0.7}').")
@click.pass_context
def kb_create_agent(ctx, agent_name, model_name, include_knowledge_bases,
                    google_api_key, include_tables, prompt_template, other_params_str):
    """
    Creates an AI Agent with specified model, knowledge bases, and other configurations.
    """
    handler = ctx.obj
    # Ensure connection
    if not handler or not handler.project:
        if not handler.connect() or not handler.project:
            click.echo(click.style("MindsDB connection failed. Please ensure MindsDB is running and accessible.", fg='red'))
            return

    # Parse comma-separated strings into lists
    include_kb_list = [kb.strip() for kb in include_knowledge_bases.split(',')] if include_knowledge_bases else []
    if not include_kb_list:
        click.echo(click.style("Error: --include-knowledge-bases cannot be empty.", fg='red'))
        return

    include_tables_list = [table.strip() for table in include_tables.split(',')] if include_tables else None

    parsed_other_params = {}
    if other_params_str:
        try:
            parsed_other_params = json.loads(other_params_str)
            if not isinstance(parsed_other_params, dict):
                raise ValueError("--other-params must be a valid JSON dictionary string.")
        except json.JSONDecodeError as e:
            click.echo(click.style(f"Invalid JSON in --other-params: {e}", fg='red'))
            return
        except ValueError as e: # Catches custom error
            click.echo(click.style(str(e), fg='red'))
            return

    click.echo(f"Attempting to create agent '{agent_name}' using model '{model_name}'...")
    click.echo(f"Including knowledge bases: {include_kb_list}")
    if include_tables_list:
        click.echo(f"Including tables: {include_tables_list}")
    if google_api_key:
        click.echo("Using provided Google API Key.")
    if prompt_template:
        click.echo(f"Using custom prompt template (first 50 chars): {prompt_template[:50]}...")
    if parsed_other_params:
        click.echo(f"Other parameters: {parsed_other_params}")

    if handler.create_kb_agent(
        agent_name=agent_name,
        model_name=model_name,
        include_knowledge_bases=include_kb_list,
        google_api_key=google_api_key,
        include_tables=include_tables_list,
        prompt_template=prompt_template,
        other_params=parsed_other_params
    ):
        click.echo(click.style(f"Agent '{agent_name}' creation command sent successfully.", fg='green'))
        click.echo(click.style("Note: Agent creation is asynchronous. Check MindsDB logs or status to confirm.", fg='bright_black'))

    else:
        click.echo(click.style(f"Failed to send command to create agent '{agent_name}'. Check logs for details.", fg='red'))

@kb_group.command('query-agent')
@click.argument('agent_name')
@click.argument('question')
@click.pass_context
def kb_query_agent(ctx, agent_name, question):
    """
    Queries an AI Agent linked to a Knowledge Base with a natural language question.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Querying agent '{agent_name}' with question: \"{question}\"")
    response = handler.query_kb_agent(agent_name=agent_name, question=question)

    if response is not None:
        click.echo(click.style("Agent Response:", fg='green'))
        if isinstance(response, dict): # If handler returned full row due to missing 'response' col
            click.echo(json.dumps(response, indent=2))
        else:
            click.echo(response) # Expecting a string response
    else:
        click.echo(click.style(f"Failed to get a response from agent '{agent_name}' or agent returned no data.", fg='yellow'))

@kb_group.command('evaluate')
@click.argument('kb_name')
@click.option('--test-table', required=True, help="Test table name in 'datasource.table' format.")
@click.option('--version', type=click.Choice(['doc_id', 'llm_relevancy'], case_sensitive=False), help="Evaluator version.")
@click.option('--generate-data', 'generate_data_flag', is_flag=True, help="Generate test data using defaults (sets generate_data=true).")
@click.option('--generate-data-from-sql', help="SQL query to fetch data for test data generation.")
@click.option('--generate-data-count', type=int, help="Number of test data items to generate.")
@click.option('--no-evaluate', 'run_evaluation_flag', is_flag=True, default=True, help="Set to only generate data without running evaluation (sets evaluate=false).") # default is True for run_evaluation
@click.option('--llm-provider', help="LLM provider for evaluation (if version='llm_relevancy').")
@click.option('--llm-api-key', help="API key for the LLM provider.")
@click.option('--llm-model-name', help="LLM model name for evaluation.")
@click.option('--llm-base-url', help="Base URL for the LLM provider.")
@click.option('--llm-other-params', help="JSON string for other LLM parameters (e.g., '{\"method\":\"multi-class\"}').")
@click.option('--save-to-table', help="Table to save evaluation results in 'datasource.table' format.")
@click.pass_context
def kb_evaluate(ctx, kb_name, test_table, version,
                generate_data_flag, generate_data_from_sql, generate_data_count,
                run_evaluation_flag, # This flag comes from --no-evaluate, so its presence means run_evaluation=False
                llm_provider, llm_api_key, llm_model_name, llm_base_url, llm_other_params,
                save_to_table):
    """Evaluates a Knowledge Base using a test table and specified parameters."""
    handler = ctx.obj
    if not handler or not handler.project:
        if not handler.connect() or not handler.project: # Try to connect
            click.echo(click.style("MindsDB connection failed. Please ensure MindsDB is running and accessible.", fg='red'))
            return

    parsed_llm_other_params = None
    if llm_other_params:
        try:
            parsed_llm_other_params = json.loads(llm_other_params)
            if not isinstance(parsed_llm_other_params, dict):
                raise ValueError("--llm-other-params must be a valid JSON dictionary.")
        except json.JSONDecodeError as e:
            click.echo(click.style(f"Invalid JSON in --llm-other-params: {e}", fg='red'))
            return
        except ValueError as e:
            click.echo(click.style(str(e), fg='red'))
            return

    # --no-evaluate flag means run_evaluation should be False.
    # Click sets run_evaluation_flag to True if --no-evaluate is present.
    # So, we invert it for the handler.
    actual_run_evaluation = not run_evaluation_flag if ctx.params.get('no_evaluate') else True
    # A bit confusing: click's is_flag sets the param to True if present.
    # If --no-evaluate is NOT given, run_evaluation_flag is False (its default from is_flag behavior if not set).
    # We want run_evaluation to be True if --no-evaluate is NOT given.
    # Correct logic: if --no-evaluate is passed, run_evaluation_flag becomes True. We want actual_run_evaluation = False.
    # If --no-evaluate is NOT passed, run_evaluation_flag is False. We want actual_run_evaluation = True.
    # The parameter name for is_flag is 'run_evaluation_flag', but the option is '--no-evaluate'.
    # Let's rename the click option parameter to make it clearer.

    # Re-evaluating the logic for --no-evaluate:
    # If --no-evaluate is passed, the internal variable `run_evaluation_flag` (as named in @click.option)
    # will be True. In this case, we want `actual_run_evaluation` to be False.
    # If --no-evaluate is NOT passed, `run_evaluation_flag` will be False (its default).
    # In this case, we want `actual_run_evaluation` to be True.
    # So, actual_run_evaluation = not run_evaluation_flag (where run_evaluation_flag is the value from click)
    # The default for the flag is False. If --no-evaluate is specified, it becomes True.
    # So: actual_run_evaluation = not run_evaluation_flag (default True)
    # Let's adjust the click option to be more direct.
    # Let's use a new variable for the actual flag from click:
    no_evaluate_is_set = ctx.params.get('run_evaluation_flag', False) # run_evaluation_flag is True if --no-evaluate is set
    actual_run_evaluation_param = not no_evaluate_is_set


    click.echo(f"Initiating evaluation for Knowledge Base '{kb_name}'...")
    results_df = handler.evaluate_knowledge_base(
        kb_name=kb_name,
        test_table=test_table,
        version=version,
        generate_data_flag=generate_data_flag,
        generate_data_from_sql=generate_data_from_sql,
        generate_data_count=generate_data_count,
        run_evaluation=actual_run_evaluation_param, # Correctly use the inverted flag
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_model_name=llm_model_name,
        llm_base_url=llm_base_url,
        llm_other_params=parsed_llm_other_params,
        save_to_table=save_to_table
    )

    if results_df is not None:
        click.echo(click.style("Evaluation completed.", fg='green'))
        if not results_df.empty:
            click.echo("Results:")
            click.echo(results_df.to_string())
        else:
            click.echo(click.style("Evaluation returned no data or results were saved to table.", fg='yellow'))
    else:
        click.echo(click.style("Failed to evaluate Knowledge Base or evaluation was set not to run explicitly.", fg='red'))

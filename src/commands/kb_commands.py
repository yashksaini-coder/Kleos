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
@click.option('--embedding-provider', default='ollama', show_default=True, help="Provider for embedding model (e.g., ollama, openai).")
@click.option('--embedding-model', default='nomic-embed-text', show_default=True, help="Name of the embedding model.")
@click.option('--embedding-base-url', default=None, help="Base URL for the embedding model provider (if needed).")
@click.option('--reranking-provider', default='ollama', show_default=True, help="Provider for reranking model (optional).") # Default should be None or allow empty
@click.option('--reranking-model', default=None, help="Name of the reranking model (optional, e.g., llama3).") # Default should be None
@click.option('--reranking-base-url', default=None, help="Base URL for the reranking model provider (if needed, optional).")
@click.pass_context
def kb_create(ctx, kb_name, embedding_provider, embedding_model, embedding_base_url, reranking_provider, reranking_model, reranking_base_url):
    """Creates a new Knowledge Base."""
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    # Auto-use app_config.OLLAMA_BASE_URL if provider is ollama and URL not specified
    if embedding_provider == 'ollama' and not embedding_base_url:
        embedding_base_url = app_config.OLLAMA_BASE_URL
    if reranking_provider == 'ollama' and not reranking_base_url and reranking_model: # Only if reranking_model is specified
        reranking_base_url = app_config.OLLAMA_BASE_URL

    # Ensure reranking provider/URL are None if model is not specified
    if not reranking_model:
        reranking_provider = None
        reranking_base_url = None # Explicitly set to None if no model

    click.echo(f"Creating Knowledge Base '{kb_name}'...")
    if handler.create_knowledge_base(
        kb_name,
        embedding_model_provider=embedding_provider,
        embedding_model_name=embedding_model,
        embedding_model_base_url=embedding_base_url,
        reranking_model_provider=reranking_provider,
        reranking_model_name=reranking_model,
        reranking_model_base_url=reranking_base_url
    ):
        click.echo(click.style(f"Knowledge Base '{kb_name}' created successfully or already exists.", fg='green'))
    else:
        click.echo(click.style(f"Failed to create Knowledge Base '{kb_name}'.", fg='red'))

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
@click.option('--content-column', help="Source column for KB content (e.g., 'title' for stories, 'text' for comments). Required if --from-hackernews.")
@click.option('--metadata-map', help="JSON string mapping KB metadata_cols to source_cols. E.g., '{\"story_id\":\"id\", \"author\":\"by\"}'.")
@click.pass_context
def kb_ingest(ctx, kb_name, from_hackernews_table, hn_datasource, limit, content_column, metadata_map):
    """Ingests data into a Knowledge Base from a HackerNews table."""
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red')); return
    if not from_hackernews_table:
        click.echo(click.style("Please specify --from-hackernews <table_name>.", fg='red')); return
    if not content_column:
        click.echo(click.style("Please specify --content-column from the source table.", fg='red')); return
    parsed_metadata_map = None
    if metadata_map:
        try:
            parsed_metadata_map = json.loads(metadata_map)
            if not isinstance(parsed_metadata_map, dict): raise ValueError("metadata-map must be a JSON dictionary.")
        except Exception as e: click.echo(click.style(f"Invalid JSON in --metadata-map: {e}", fg='red')); return

    click.echo(f"Ingesting data from '{hn_datasource}.{from_hackernews_table}' into '{kb_name}'...")
    try:
        select_cols_list = [content_column]
        if parsed_metadata_map: select_cols_list.extend(parsed_metadata_map.values())
        select_cols_str = ", ".join(sorted(list(set(select_cols_list))))
        query_fetch_data = f"SELECT {select_cols_str} FROM {hn_datasource}.{from_hackernews_table} ORDER BY id DESC LIMIT {limit}"

        source_data_df = handler.execute_sql(query_fetch_data)
        if source_data_df is None or source_data_df.empty:
            click.echo(click.style(f"No data fetched from '{hn_datasource}.{from_hackernews_table}'.", fg='yellow')); return

        source_data_list = source_data_df.to_dict('records')
        if handler.insert_into_knowledge_base(kb_name, source_data_list, content_column=content_column, metadata_columns=parsed_metadata_map):
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

# --- New AI Agent Commands ---

@kb_group.command('create-agent')
@click.argument('agent_name')
@click.argument('kb_name')
@click.option('--model-provider', default='google', show_default=True, help="LLM provider for the agent (e.g., 'google', 'ollama', 'openai').")
@click.option('--model-name', default='gemini-pro', show_default=True, help="LLM model name for the agent (e.g., 'gemini-pro', 'llama3').")
@click.option('--agent-params', 'agent_params_str', default=None, help="JSON string of additional parameters for the agent's USING clause. E.g., '{\"temperature\": 0.5, \"api_key\": \"your_google_api_key\"}'.")
@click.pass_context
def kb_create_agent(ctx, agent_name, kb_name, model_provider, model_name, agent_params_str):
    """
    Creates an AI Agent linked to a Knowledge Base.
    The agent uses a specified LLM (defaults to Google Gemini-Pro).
    If using Google Gemini, ensure GOOGLE_GEMINI_API_KEY is in config/env or pass 'api_key' in --agent-params.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    parsed_agent_params = {} # Default to empty dict
    if agent_params_str:
        try:
            parsed_agent_params = json.loads(agent_params_str)
            if not isinstance(parsed_agent_params, dict):
                raise ValueError("Agent params must be a valid JSON dictionary string.")
        except json.JSONDecodeError as e:
            click.echo(click.style(f"Invalid JSON in --agent-params: {e}", fg='red'))
            return
        except ValueError as e:
            click.echo(click.style(str(e), fg='red'))
            return

    click.echo(f"Attempting to create agent '{agent_name}' linked to KB '{kb_name}' using model '{model_provider}/{model_name}'...")

    if handler.create_kb_agent(
        agent_name=agent_name,
        kb_name=kb_name,
        model_provider=model_provider,
        model_name=model_name,
        agent_params=parsed_agent_params
    ):
        click.echo(click.style(f"Agent '{agent_name}' created successfully or already exists.", fg='green'))
    else:
        click.echo(click.style(f"Failed to create agent '{agent_name}'. Check logs for details.", fg='red'))

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

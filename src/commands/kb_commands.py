import click
import json
import pandas as pd
from rich.table import Table
from rich.status import Status
from rich.syntax import Syntax
from rich.text import Text
try:
    from config import config as app_config
except ImportError:
    # When installed as package, config might be at different location
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from config import config as app_config
from .utils import get_handler_and_console, CONTEXT_SETTINGS # Import from local utils

@click.group('kb', context_settings=CONTEXT_SETTINGS)
def kb_group():
    """Commands for managing Knowledge Bases (KBs) and associated AI Agents.

    Knowledge Bases in MindsDB enable semantic search over large text datasets.
    They typically use an embedding model to convert text into vectors and may
    optionally use a reranking model to refine search relevance. AI Agents can
    leverage these KBs to answer questions based on the stored knowledge.
    """
    pass

@kb_group.command('create')
@click.argument('kb_name')
@click.option('--embedding-provider', default='ollama', show_default=True, help="Provider for the embedding model (e.g., 'ollama', 'openai', 'google').")
@click.option('--embedding-model', default='nomic-embed-text', show_default=True, help="Name of the embedding model (e.g., 'nomic-embed-text', 'text-embedding-ada-002').")
@click.option('--embedding-base-url', default=None, help="Base URL for embedding provider if self-hosted (e.g., Ollama URL 'http://localhost:11434').")
@click.option('--embedding-api-key', default=None, help="API key if required by the embedding provider (e.g., Google, OpenAI).")
@click.option('--reranking-provider', default=None, help="Provider for the reranking model (optional; e.g., 'ollama', 'google', 'cohere').")
@click.option('--reranking-model', default=None, help="Name of the reranking model (optional; e.g., 'llama3', 'gemini-1.5-flash').")
@click.option('--reranking-base-url', default=None, help="Base URL for reranking provider if self-hosted (optional).")
@click.option('--reranking-api-key', default=None, help="API key if required by the reranking provider (optional).")
@click.option('--content-columns', help="Comma-separated list of source column names to embed as content. E.g., 'title,text'.")
@click.option('--metadata-columns', help="Comma-separated list of source column names to store as filterable metadata. E.g., 'id,author,timestamp'.")
@click.option('--id-column', help="Name of the source column to use as a unique identifier for records within the KB.")
@click.pass_context
def kb_create(ctx, kb_name, embedding_provider, embedding_model, embedding_base_url, embedding_api_key,
              reranking_provider, reranking_model, reranking_base_url, reranking_api_key,
              content_columns, metadata_columns, id_column):
    """
    Creates a new Knowledge Base (KB) in MindsDB.

    KBs are designed for storing and querying textual data using semantic search.
    You must specify an EMBEDDING_MODEL to convert text into vector embeddings.
    A RERANKING_MODEL is optional but can be used to improve the relevance of
    search results by re-processing the initial set of documents found by the
    embedding model.

    The --content-columns option specifies which columns from your source data
    will be combined and embedded. --metadata-columns are stored alongside the
    embeddings and can be used for filtering queries. --id-column sets a unique
    key for each record.

    Examples:

      Create a KB using default Ollama embedder (nomic-embed-text):
      `kleos kb create my_documents_kb --content-columns "title,body_text" --metadata-columns "doc_id,category,created_at" --id-column doc_id`

      Create a KB with Google's text-embedding-004 and an Ollama Llama3 reranker:
      `kleos kb create gemini_ollama_kb --embedding-provider google --embedding-model text-embedding-004 --embedding-api-key YOUR_GOOGLE_KEY --reranking-provider ollama --reranking-model llama3 --content-columns "question,answer"`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    if embedding_provider == 'ollama' and not embedding_base_url:
        embedding_base_url = getattr(app_config, 'OLLAMA_BASE_URL', None)
        if not embedding_base_url:
            console.print("[yellow]Warning: Embedding provider is ollama, but OLLAMA_BASE_URL is not configured and --embedding-base-url not provided.[/yellow]")
    # Set reranking provider default if reranking model is provided but provider is not
    if reranking_model and not reranking_provider:
        reranking_provider = 'ollama'  # Default to ollama if model is provided but provider is not
        console.print(f"[yellow]Info: Reranking model '{reranking_model}' provided without provider. Defaulting to 'ollama'.[/yellow]")
    
    if reranking_provider == 'ollama' and not reranking_base_url and reranking_model:
        reranking_base_url = getattr(app_config, 'OLLAMA_BASE_URL', None)
        if not reranking_base_url:
            console.print("[yellow]Warning: Reranking provider is ollama, but OLLAMA_BASE_URL is not configured and --reranking-base-url not provided.[/yellow]")

    # Clear reranking settings if no model is provided
    if not reranking_model: 
        reranking_provider, reranking_base_url, reranking_api_key = None, None, None
    content_columns_list = [col.strip() for col in content_columns.split(',')] if content_columns else None
    metadata_columns_list = [col.strip() for col in metadata_columns.split(',')] if metadata_columns else None

    details = Text.assemble(
        ("KB Name: ", "bold"), (f"{kb_name}\n", "cyan"),
        ("Embedding: ", "bold"), (f"{embedding_provider}/{embedding_model}\n", "cyan"),
        ("Reranking: ", "bold"), (f"{reranking_provider}/{reranking_model}\n" if reranking_model else "Not configured\n", "cyan"),
        ("Content Cols: ", "bold"), (f"{content_columns_list}\n" if content_columns_list else "Default\n", "cyan"),
        ("Metadata Cols: ", "bold"), (f"{metadata_columns_list}\n" if metadata_columns_list else "Default\n", "cyan"),
        ("ID Col: ", "bold"), (f"{id_column}\n" if id_column else "Default", "cyan")
    )
    console.print(details)

    with Status(f"Creating Knowledge Base '[cyan]{kb_name}[/cyan]'...", console=console, spinner="dots2"):
        success = handler.create_knowledge_base(
            kb_name=kb_name, embedding_provider=embedding_provider, embedding_model=embedding_model,
            embedding_base_url=embedding_base_url, embedding_api_key=embedding_api_key,
            reranking_provider=reranking_provider, reranking_model=reranking_model,
            reranking_base_url=reranking_base_url, reranking_api_key=reranking_api_key,
            content_columns=content_columns_list, metadata_columns=metadata_columns_list, id_column=id_column
        )
    if success:
        console.print(f"[green]:heavy_check_mark: Knowledge Base '[cyan]{kb_name}[/cyan]' creation command sent.[/green]")
        console.print("[dim]Note: KB creation is asynchronous. Check MindsDB logs or list KBs to confirm.[/dim]")
    else:
        console.print(f"[red]:x: Failed to send command to create Knowledge Base '[cyan]{kb_name}[/cyan]'.[/red]")

@kb_group.command('index')
@click.argument('kb_name')
@click.pass_context
def kb_index(ctx, kb_name):
    """
    Creates or refreshes the vector index for a specified Knowledge Base.

    After ingesting data into a KB, an index must be built (or updated) to enable
    efficient semantic search. This command triggers that process.
    MindsDB typically uses a vector database (like ChromaDB by default) under the hood,
    and this command ensures its index is up-to-date with the KB's content.

    Example:
    `kleos kb index my_docs_kb`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    with Status(f"Initiating index creation/refresh for KB '[cyan]{kb_name}[/cyan]'...", console=console, spinner="earth"):
        success = handler.create_index_on_knowledge_base(kb_name)
    if success:
        console.print(f"[green]:heavy_check_mark: Index operation for '[cyan]{kb_name}[/cyan]' initiated successfully.[/green]")
    else:
        console.print(f"[red]:x: Failed to initiate index operation for '[cyan]{kb_name}[/cyan]'.[/red]")

@kb_group.command('ingest')
@click.argument('kb_name')
@click.option('--from-hackernews', 'from_hackernews_table', required=True, help="Name of the HackerNews table to ingest from (e.g., 'stories', 'comments').")
@click.option('--hn-datasource', default='hackernews', show_default=True, help="Name of the HackerNews datasource in MindsDB.")
@click.option('--limit', type=int, default=100, show_default=True, help="Maximum number of records to ingest from the HackerNews table.")
@click.option('--content-column', help="Source column(s) for KB content, comma-separated. Auto-detects for HN tables (e.g., 'title,text' for stories, 'text' for comments).")
@click.option('--metadata-map', help="JSON string mapping your desired KB metadata column names to source table column names. E.g., '{\"doc_id\":\"id\", \"author\":\"by\"}'. Auto-detects for HN tables if not specified.")
@click.pass_context
def kb_ingest(ctx, kb_name, from_hackernews_table, hn_datasource, limit, content_column, metadata_map):
    """
    Ingests data into an existing Knowledge Base from a HackerNews table.

    This command uses MindsDB's `INSERT INTO ... SELECT ...` syntax for efficient ingestion.
    It includes smart defaults for HackerNews tables ('stories', 'comments') regarding
    which columns are used for content embedding and which for metadata.
    The HackerNews datasource will be automatically created if it doesn't exist using the name provided by `--hn-datasource`.

    Examples:
    `kleos kb ingest my_hn_kb --from-hackernews stories --limit 500`

    Custom mapping for 'stories' table:
    `kleos kb ingest my_hn_kb --from-hackernews stories --content-column "title" --metadata-map '{\"id_in_kb\":\"id\", \"user\":\"by\", \"points\":\"score\"}' --limit 100`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return
    if not from_hackernews_table: console.print("[red]Error: Please specify --from-hackernews <table_name>.[/red]"); return

    if not content_column:
        if from_hackernews_table == 'stories': content_column = 'title'
        elif from_hackernews_table == 'comments': content_column = 'text'
        else: console.print("[red]Error: Please specify --content-column for this table.[/red]"); return
    
    parsed_metadata_map = None
    if metadata_map:
        try:
            parsed_metadata_map = json.loads(metadata_map)
            if not isinstance(parsed_metadata_map, dict) or not all(isinstance(v, str) for v in parsed_metadata_map.values()):
                console.print("[red]Error: --metadata-map must be a JSON dictionary with string values (column names).[/red]"); return
        except Exception as e: console.print(f"[red]Invalid JSON in --metadata-map: {e}[/red]"); return
    else:
        if from_hackernews_table == 'stories': parsed_metadata_map = {"story_id": "id", "time": "time", "score": "score", "descendants": "descendants"}
        elif from_hackernews_table == 'comments': parsed_metadata_map = {"comment_id": "id", "time": "time", "parent": "parent"}
        elif from_hackernews_table == 'hnstories': parsed_metadata_map = {"story_id": "id"}
        console.print(f"Using smart defaults for [cyan]{from_hackernews_table}[/cyan]: content='[cyan]{content_column}[/cyan]', metadata=[cyan]{list(parsed_metadata_map.keys()) if parsed_metadata_map else 'None'}[/cyan]")

    if not handler.get_database_custom_check(hn_datasource):
        console.print(f"HackerNews datasource '[cyan]{hn_datasource}[/cyan]' not found. Creating it...")
        with Status(f"Creating datasource '{hn_datasource}'...", console=console):
            if not handler.create_hackernews_datasource(ds_name=hn_datasource):
                console.print(f"[red]:x: Failed to create HackerNews datasource '[cyan]{hn_datasource}[/cyan]'.[/red]")
                return
        console.print(f"[green]:heavy_check_mark: Datasource '[cyan]{hn_datasource}[/cyan]' created.[/green]")
    
    source_table_full_name = f"{hn_datasource}.{from_hackernews_table}"
    ingest_msg = f"Ingesting [bold yellow]{limit}[/bold yellow] records from '[cyan]{source_table_full_name}[/cyan]' into KB '[cyan]{kb_name}[/cyan]'..."
    
    with Status(ingest_msg, console=console, spinner="moon"):
        success = handler.insert_into_knowledge_base_direct(
            kb_name=kb_name, source_table=source_table_full_name,
            content_column=content_column, metadata_columns=parsed_metadata_map,
            limit=limit, order_by="id DESC" # Assuming 'id' exists and is sortable
        )
    if success:
        console.print(f"[green]:heavy_check_mark: Data ingestion into '[cyan]{kb_name}[/cyan]' initiated successfully.[/green]")
    else:
        console.print(f"[red]:x: Data ingestion into '[cyan]{kb_name}[/cyan]' failed.[/red]")

@kb_group.command('query')
@click.argument('kb_name')
@click.argument('query_text') # Removed help, it's in the docstring
@click.option('--metadata-filter', 'metadata_filters_str', help="JSON string for filtering results based on metadata. Supports operators like '$gt', '$gte', '$lt', '$lte'. Example: '{\"author\":\"JohnDoe\", \"year\":{\"$gt\":2022}}'.")
@click.option('--limit', type=int, default=5, show_default=True, help="Maximum number of search results to return.")
@click.pass_context
def kb_query(ctx, kb_name, query_text, metadata_filters_str, limit):
    """
    Queries a Knowledge Base using semantic search and optional metadata filters.

    The command searches for content similar to the <query_text>.
    You can further refine results using --metadata-filter with a JSON string.
    The filter supports simple key-value equality and comparison operators
    like `$gt` (greater than), `$gte` (greater than or equal),
    `$lt` (less than), `$lte` (less than or equal) nested within the JSON.

    Examples:
    `kleos kb query my_docs_kb "latest advancements in AI"`
    `kleos kb query my_hn_kb "python programming tips" --limit 10`
    `kleos kb query product_faq "warranty information" --metadata-filter '{\"product_line\":\"X Series\", \"year\":{\"$gte\": 2023}}'`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    metadata_filters = None
    if metadata_filters_str:
        try:
            metadata_filters = json.loads(metadata_filters_str)
            if not isinstance(metadata_filters, dict): raise ValueError("metadata-filter must be a JSON dictionary.")
        except Exception as e: console.print(f"[red]Invalid JSON in --metadata-filter: {e}[/red]"); return

    query_info = f"Querying KB '[cyan]{kb_name}[/cyan]' for: \"[italic]{query_text}[/italic]\""
    if metadata_filters: query_info += f" with filters: [yellow]{metadata_filters}[/yellow]"

    with Status(query_info + "...", console=console, spinner="simpleDotsScrolling"):
        results_df = handler.select_from_knowledge_base(kb_name, query_text, metadata_filters=metadata_filters, limit=limit)

    if results_df is not None:
        if not results_df.empty:
            console.print("\n[bold green]Query Results:[/bold green]")
            table = Table(show_header=True, header_style="bold magenta", show_lines=True)
            for col in results_df.columns: table.add_column(col)
            for _, row in results_df.iterrows():
                table.add_row(*(str(x) for x in row))
            console.print(table)
        else:
            console.print("[yellow]No results found.[/yellow]")
    else:
        console.print("[red]:x: Failed to query Knowledge Base.[/red]")

@kb_group.command('list-databases')
@click.pass_context
def kb_list_databases(ctx):
    """
    Lists all available databases and datasources connected to your MindsDB instance.

    This can be useful to verify datasource creation (like HackerNews) or to see
    all available data sources you can potentially ingest from or use with models.
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return
    
    with Status("Fetching databases...", console=console):
        try:
            databases_df = handler.execute_sql('SHOW DATABASES;')
        except Exception as e:
            console.print(f"[red]:x: Error listing databases: {e}[/red]")
            return

    if databases_df is not None and not databases_df.empty:
        console.print("\n[bold green]Available Databases/Datasources:[/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        # Determine column name, common ones are 'Database', 'name', 'NAME'
        db_col_name = 'name' # Default from newer MindsDB versions
        if 'Database' in databases_df.columns: db_col_name = 'Database'
        elif 'NAME' in databases_df.columns: db_col_name = 'NAME'

        table.add_column(db_col_name)
        for db_name in databases_df[db_col_name]: table.add_row(db_name)
        console.print(table)
    else:
        console.print("[yellow]No databases found or query failed.[/yellow]")


@kb_group.command('create-agent')
@click.argument('agent_name')
@click.option('--model-name', required=True, help="LLM model to power the agent (e.g., 'gemini-1.5-flash', 'llama3', 'openai/gpt-4'). This is the `model` parameter in `CREATE AGENT`.")
@click.option('--include-knowledge-bases', required=True, help="Comma-separated list of Knowledge Base names for the agent to use as its knowledge source.")
@click.option('--google-api-key', default=None, help="Your Google API key. Required if using a Google LLM (e.g., Gemini) and not globally configured in MindsDB.")
@click.option('--include-tables', default=None, help="Comma-separated list of additional table names (format: 'datasource.tablename') to provide context to the agent.")
@click.option('--prompt-template', default=None, help="A custom prompt template guiding the agent's behavior and response format. Use {{question}} and {{context}} placeholders.")
@click.option('--other-params', 'other_params_str', default=None, help="JSON string for other parameters to pass to the agent's `USING` clause (e.g., '{\"temperature\": 0.7, \"max_tokens\": 300}'). Refer to MindsDB docs for model-specific params.")
@click.pass_context
def kb_create_agent(ctx, agent_name, model_name, include_knowledge_bases,
                    google_api_key, include_tables, prompt_template, other_params_str):
    """
    Creates an AI Agent in MindsDB, linking it to Knowledge Bases and/or tables.

    Agents use an LLM (specified by --model-name) to answer questions or perform tasks
    based on the data provided from the included KBs and tables.
    The `model` parameter in the `USING` clause of `CREATE AGENT` refers to the LLM itself.

    Examples:
    `kleos kb create-agent my_kb_assistant --model-name gemini-1.5-flash --include-knowledge-bases "product_docs_kb,faq_kb" --prompt-template "Answer based on provided documents: {{question}}"`

    Using Ollama Llama3 (ensure Ollama integration is set up in MindsDB):
    `kleos kb create-agent ollama_chat --model-name llama3 --include-knowledge-bases my_local_kb --other-params '{\"provider\":\"ollama\"}'`
    (Note: provider might be needed in `other-params` if not inferred by MindsDB from model name for some setups)
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    include_kb_list = [kb.strip() for kb in include_knowledge_bases.split(',')] if include_knowledge_bases else []
    if not include_kb_list: console.print("[red]Error: --include-knowledge-bases cannot be empty.[/red]"); return
    include_tables_list = [table.strip() for table in include_tables.split(',')] if include_tables else None
    parsed_other_params = {}
    if other_params_str:
        try:
            parsed_other_params = json.loads(other_params_str)
            if not isinstance(parsed_other_params, dict): raise ValueError("--other-params must be a JSON dictionary.")
        except Exception as e: console.print(f"[red]Invalid JSON in --other-params: {e}[/red]"); return

    console.print(f"Attempting to create agent '[cyan]{agent_name}[/cyan]' using model '[cyan]{model_name}[/cyan]'...")
    # Further details can be printed here if needed

    with Status(f"Creating agent '[cyan]{agent_name}[/cyan]'...", console=console, spinner="material"):
        success = handler.create_kb_agent(
            agent_name=agent_name, model_name=model_name, include_knowledge_bases=include_kb_list,
            google_api_key=google_api_key, include_tables=include_tables_list,
            prompt_template=prompt_template, other_params=parsed_other_params
        )
    if success:
        console.print(f"[green]:heavy_check_mark: Agent '[cyan]{agent_name}[/cyan]' creation command sent.[/green]")
        console.print("[dim]Note: Agent creation is asynchronous. Check MindsDB logs or status to confirm.[/dim]")
    else:
        console.print(f"[red]:x: Failed to send command to create agent '[cyan]{agent_name}[/cyan]'.[/red]")

@kb_group.command('query-agent')
@click.argument('agent_name')
@click.argument('question') # Removed help, it's in the docstring
@click.pass_context
def kb_query_agent(ctx, agent_name, question):
    """
    Queries an existing AI Agent with a natural language question.

    The agent will use its configured LLM and linked Knowledge Bases/tables
    to generate an answer.

    Example:
    `kleos kb query-agent my_kb_assistant "How do I reset my password?"`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    with Status(f"Querying agent '[cyan]{agent_name}[/cyan]' with: \"[italic]{question[:70]}...[/italic]\"", console=console, spinner="dots"):
        response = handler.query_kb_agent(agent_name=agent_name, question=question)

    if response is not None:
        console.print("\n[bold green]Agent Response:[/bold green]")
        if isinstance(response, dict):
            console.print(Syntax(json.dumps(response, indent=2), "json", theme="dracula", line_numbers=True))
        elif isinstance(response, str):
             console.print(response)
        else: # Should ideally be string or dict from handler
            console.print(str(response))
    else:
        console.print(f"[yellow]:warning: Failed to get a response from agent '[cyan]{agent_name}[/cyan]' or agent returned no data.[/yellow]")

@kb_group.command('evaluate')
@click.argument('kb_name')
@click.option('--test-table', required=True, help="Test table for evaluation in 'datasource.table_name' format. Its structure depends on the chosen --version.")
@click.option('--version', type=click.Choice(['doc_id', 'llm_relevancy'], case_sensitive=False), default='doc_id', show_default=True, help="Evaluation version: 'doc_id' (checks if correct document ID is returned) or 'llm_relevancy' (uses an LLM to rank/evaluate responses).")
@click.option('--generate-data', 'generate_data_flag', is_flag=True, help="Flag to enable automatic test data generation using default settings (fetches from the KB being evaluated).")
@click.option('--generate-data-from-sql', help="SQL query string to fetch data for test data generation. E.g., \"SELECT question, expected_doc_id FROM my_source.manual_tests\".")
@click.option('--generate-data-count', type=int, default=20, show_default=True, help="Number of test data items to generate if --generate-data or --generate-data-from-sql is used.")
@click.option('--no-evaluate', 'no_evaluate_flag', is_flag=True, help="If set, only generates test data (if generation options active) and saves it to --test-table without running evaluation.")
@click.option('--llm-provider', help="LLM provider for evaluation (e.g., 'google', 'openai', 'ollama'), required if version='llm_relevancy'.")
@click.option('--llm-api-key', help="API key for the LLM provider, if required.")
@click.option('--llm-model-name', help="Name of the LLM model to use for evaluation (e.g., 'gemini-1.5-flash'), required if version='llm_relevancy'.")
@click.option('--llm-base-url', help="Base URL for the LLM provider (e.g., for local Ollama).")
@click.option('--llm-other-params', help="JSON string for other LLM parameters (e.g., '{\"method\":\"multi-class\"}'). Example for JSON: '{\"key\":\"value\"}'")
@click.option('--save-to-table', help="Table to save evaluation results, in 'datasource.table_name' format. If not provided, results are printed to console.")
@click.pass_context
def kb_evaluate(ctx, kb_name, test_table, version,
                generate_data_flag, generate_data_from_sql, generate_data_count,
                no_evaluate_flag,
                llm_provider, llm_api_key, llm_model_name, llm_base_url, llm_other_params,
                save_to_table):
    """
    Evaluates a Knowledge Base's retrieval accuracy and relevance.

    This command can operate in two main modes specified by --version:
    1.  `doc_id`: Checks if the KB returns the expected document ID for given questions.
        The --test-table should contain 'question' and 'expected_doc_id' columns.
    2.  `llm_relevancy`: Uses a specified LLM to evaluate the relevance of the content
        returned by the KB for given questions. The --test-table should contain 'question'
        and optionally 'expected_content' or 'expected_answer' columns.

    Test data can be automatically generated from the KB itself or from a custom SQL query.
    Results can be printed to the console or saved to a MindsDB table.

    Examples:
    `kleos kb evaluate my_docs_kb --test-table my_project.eval_questions --version doc_id`

    Generate test data and evaluate using LLM relevancy:
    `kleos kb evaluate sales_kb --test-table my_project.generated_sales_eval --generate-data --generate-data-count 30 --version llm_relevancy --llm-provider google --llm-model-name gemini-pro --llm-api-key YOUR_KEY --save-to-table my_project.sales_eval_results`

    Only generate test data from SQL and save to a table:
    `kleos kb evaluate main_kb --test-table tests.custom_data --generate-data-from-sql "SELECT query as question, answer as expected_answer FROM source_db.qa_pairs" --no-evaluate`
    """
    handler, console = get_handler_and_console(ctx)
    if not handler: return

    parsed_llm_other_params = None
    if llm_other_params:
        try:
            parsed_llm_other_params = json.loads(llm_other_params)
            if not isinstance(parsed_llm_other_params, dict):
                raise ValueError("--llm-other-params must be a valid JSON dictionary.")
        except Exception as e: console.print(f"[red]Invalid JSON in --llm-other-params: {e}[/red]"); return

    run_evaluation_param = not no_evaluate_flag

    eval_msg = f"Initiating evaluation for KB '[cyan]{kb_name}[/cyan]'"
    if not run_evaluation_param and (generate_data_flag or generate_data_from_sql):
        eval_msg = f"Generating test data for KB '[cyan]{kb_name}[/cyan]' into table '[cyan]{test_table}[/cyan]'. Evaluation will NOT run."
    elif not run_evaluation_param:
        console.print("[yellow]Warning: --no-evaluate specified without data generation options. Nothing will be done.[/yellow]")
        return

    with Status(eval_msg + "...", console=console, spinner="bouncingBar"):
        results_df = handler.evaluate_knowledge_base(
            kb_name=kb_name, test_table=test_table, version=version,
            generate_data_flag=generate_data_flag, generate_data_from_sql=generate_data_from_sql,
            generate_data_count=generate_data_count, run_evaluation=run_evaluation_param,
            llm_provider=llm_provider, llm_api_key=llm_api_key, llm_model_name=llm_model_name,
            llm_base_url=llm_base_url, llm_other_params=parsed_llm_other_params,
            save_to_table=save_to_table
        )

    if results_df is not None:
        action_verb = "Evaluation" if run_evaluation_param else "Data generation"
        console.print(f"[green]:heavy_check_mark: {action_verb} for KB '[cyan]{kb_name}[/cyan]' completed.[/green]")
        if not results_df.empty:
            console.print("\n[bold green]Results:[/bold green]")
            table = Table(show_header=True, header_style="bold magenta", show_lines=True)
            for col in results_df.columns: table.add_column(str(col)) # Ensure col names are strings
            for _, row in results_df.iterrows():
                table.add_row(*(str(x) for x in row))
            console.print(table)
        elif run_evaluation_param: # Only say this if evaluation was supposed to run
            console.print(f"[yellow]{action_verb} returned no data or results were saved to table '[cyan]{save_to_table}[/cyan]'.[/yellow]")
    else:
        console.print(f"[red]:x: Failed to evaluate Knowledge Base '[cyan]{kb_name}[/cyan]'.[/red]")

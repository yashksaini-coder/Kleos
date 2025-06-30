import mindsdb_sdk
from config import config
import pandas as pd
import time
import json # Ensure json is imported for create_kb_agent
from rich.console import Console

# Use a global console for handler's own print statements, or pass one if preferred
console = Console()

class MindsDBHandler:
    def __init__(self, rich_console: Console = None):
        self.server = None
        self.project = None
        self.mindsdb_host = config.MINDSDB_HOST
        self.mindsdb_port = config.MINDSDB_PORT
        self.mindsdb_user = config.MINDSDB_USER
        self.mindsdb_password = config.MINDSDB_PASSWORD
        self.console = rich_console if rich_console else console # Use passed console or global
        # self.console.print(f"MindsDBHandler initialized for [cyan]{self.mindsdb_host}:{self.mindsdb_port}[/cyan]")

    def connect(self, suppress_messages: bool = False) -> bool:
        if not suppress_messages:
            self.console.print(f"Attempting to connect to MindsDB: [cyan]{self.mindsdb_host}:{self.mindsdb_port}[/cyan]")
        try:
            if self.mindsdb_user and self.mindsdb_password:
                self.server = mindsdb_sdk.connect(
                    url=f'{self.mindsdb_host}:{self.mindsdb_port}',
                    login=self.mindsdb_user,
                    password=self.mindsdb_password
                )
            else:
                self.server = mindsdb_sdk.connect(f'{self.mindsdb_host}:{self.mindsdb_port}')

            if not self.server:
                raise ConnectionError("SDK connect returned None server object.")

            self.project = self.server.get_project()
            if not self.project:
                raise ConnectionError("Failed to get default project from MindsDB server.")

            if not suppress_messages:
                self.console.print(f"[green]:heavy_check_mark: Successfully connected to MindsDB. Project: '{self.project.name}'[/green]")
            return True
        except Exception as e:
            if not suppress_messages:
                self.console.print(f"[red]:x: Error connecting to MindsDB: {str(e)}[/red]")
            self.server = None
            self.project = None
            return False

    def execute_sql(self, query: str, suppress_messages: bool = False):
        if not self.project:
            if not suppress_messages:
                self.console.print("[yellow]No active MindsDB project. Attempting to reconnect...[/yellow]")
            if not self.connect(suppress_messages=True) or not self.project: # Suppress connect messages on auto-reconnect
                raise ConnectionError("MindsDB connection not established. Cannot execute query.")

        if not suppress_messages:
            self.console.print(f"Executing SQL: [dim]{query[:200]}{'...' if len(query) > 200 else ''}[/dim]")
        try:
            query_result = self.project.query(query)
            # self.console.print("Query executed successfully via SDK.") # Often too verbose
            return query_result.fetch()
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                if not suppress_messages:
                    self.console.print("[yellow]Event loop closed, retrying query...[/yellow]")
                try:
                    query_result = self.project.query(query)
                    # self.console.print("Query executed successfully via SDK on retry.")
                    return query_result.fetch()
                except Exception as retry_e:
                    if not suppress_messages:
                        self.console.print(f"[red]MindsDB API Error on retry '{query[:50]}...': {str(retry_e)}[/red]")
                    raise
            else:
                raise
        except Exception as e:
            error_details = str(e)
            if not suppress_messages:
                self.console.print(f"[red]MindsDB API Error executing query '{query[:50]}...': {error_details}[/red]")
            raise

    def get_database_custom_check(self, ds_name: str) -> bool:
        if not self.project:
            self.console.print("[yellow]Cannot perform custom database check: No active MindsDB project.[/yellow]")
            return False
        # self.console.print(f"Custom check: Verifying existence of database '{ds_name}' using SHOW DATABASES.")
        try:
            res_df = self.execute_sql('SHOW DATABASES;', suppress_messages=True)
            if res_df is None or res_df.empty:
                # self.console.print("Custom check: 'SHOW DATABASES' returned no results or failed.")
                return False
            db_column_name = None
            if 'Database' in res_df.columns: db_column_name = 'Database'
            elif 'name' in res_df.columns: db_column_name = 'name'
            elif 'NAME' in res_df.columns: db_column_name = 'NAME'
            else:
                # self.console.print(f"Custom check: Could not find a known database name column. Columns: {res_df.columns.tolist()}")
                return False
            databases = res_df[db_column_name].values
            if ds_name in databases:
                # self.console.print(f"Custom check: Database '{ds_name}' found.");
                return True
            else:
                # self.console.print(f"Custom check: Database '{ds_name}' not found.");
                return False
        except Exception as e:
            self.console.print(f"[yellow]Custom check: Error during 'SHOW DATABASES' for '{ds_name}': {str(e)}[/yellow]")
            return False

    def create_hackernews_datasource(self, ds_name: str = "hackernews"):
        if not self.project:
            self.console.print("[red]Error: MindsDB connection not established for create_hackernews_datasource.[/red]")
            return False
        if self.get_database_custom_check(ds_name):
            self.console.print(f"Datasource '[cyan]{ds_name}[/cyan]' (HackerNews) already exists.")
            return True
        query = f"CREATE DATABASE {ds_name} WITH ENGINE = 'hackernews';"
        try:
            self.execute_sql(query)
            # self.console.print(f"HackerNews datasource '{ds_name}' creation command executed.")
            time.sleep(1) # Give it a moment
            if self.get_database_custom_check(ds_name):
                # self.console.print(f"Datasource '{ds_name}' successfully verified after creation.")
                return True
            else:
                self.console.print(f"[red]Error: Datasource '{ds_name}' creation command executed, but verification check failed.[/red]")
                try: # Fallback SDK check
                    if self.project and hasattr(self.project, 'get_database') and self.project.get_database(ds_name):
                        # self.console.print(f"Fallback SDK check: Datasource '{ds_name}' found after creation.")
                        return True
                except Exception as sdk_e:
                    self.console.print(f"[red]Fallback SDK check also failed for '{ds_name}': {str(sdk_e)}[/red]")
                return False
        except Exception as e:
            self.console.print(f"[red]Error executing create HackerNews datasource query for '{ds_name}': {str(e)}[/red]")
            return False

    def create_knowledge_base(self, kb_name: str,
                             embedding_provider: str, embedding_model: str,
                             embedding_base_url: str = None, embedding_api_key: str = None,
                             reranking_provider: str = None, reranking_model: str = None,
                             reranking_base_url: str = None, reranking_api_key: str = None,
                             content_columns: list = None, metadata_columns: list = None, id_column: str = None):
        if not self.project:
            self.console.print("[red]Error: MindsDB connection not established.[/red]")
            return False

        using_clauses = []
        emb_config = {"provider": embedding_provider, "model_name": embedding_model}
        if embedding_base_url: emb_config["base_url"] = embedding_base_url.rstrip('/')
        if embedding_api_key: emb_config["api_key"] = embedding_api_key
        emb_config_str = ", ".join([f'"{k}": "{str(v).replace("\"", "\\\"")}"' for k, v in emb_config.items()])
        using_clauses.append(f"embedding_model = {{ {emb_config_str} }}")

        if reranking_provider and reranking_model:
            rerank_config = {"provider": reranking_provider, "model_name": reranking_model}
            if reranking_base_url: rerank_config["base_url"] = reranking_base_url.rstrip('/')
            if reranking_api_key: rerank_config["api_key"] = reranking_api_key
            rerank_config_str = ", ".join([f'"{k}": "{str(v).replace("\"", "\\\"")}"' for k, v in rerank_config.items()])
            using_clauses.append(f"reranking_model = {{ {rerank_config_str} }}")

        if content_columns:
            if isinstance(content_columns, list) and all(isinstance(col, str) for col in content_columns):
                if len(content_columns) == 1:
                    using_clauses.append(f"content_columns = '{content_columns[0]}'")
                else:
                    columns_str = ', '.join([f"'{col}'" for col in content_columns])
                    using_clauses.append(f"content_columns = [{columns_str}]")
            else: 
                self.console.print("[yellow]Warning: content_columns should be a list of strings. Skipping.[/yellow]")
        
        if metadata_columns:
            if isinstance(metadata_columns, list) and all(isinstance(col, str) for col in metadata_columns):
                if len(metadata_columns) == 1:
                    using_clauses.append(f"metadata_columns = '{metadata_columns[0]}'")
                else:
                    columns_str = ', '.join([f"'{col}'" for col in metadata_columns])
                    using_clauses.append(f"metadata_columns = [{columns_str}]")
            else: 
                self.console.print("[yellow]Warning: metadata_columns should be a list of strings. Skipping.[/yellow]")
        
        if id_column: using_clauses.append(f"id_column = '{id_column}'")

        query = f"CREATE KNOWLEDGE_BASE {kb_name} USING {', '.join(using_clauses)};"
        
        try:
            self.execute_sql(query)
            # self.console.print(f"Knowledge Base '{kb_name}' creation command executed.")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                self.console.print(f"Knowledge Base '[cyan]{kb_name}[/cyan]' already exists.")
                return True # Or False if strict creation is needed
            self.console.print(f"[red]Error creating Knowledge Base '{kb_name}': {str(e)}[/red]")
            return False

    def create_index_on_knowledge_base(self, kb_name: str):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return False
        query = f"CREATE INDEX ON KNOWLEDGE_BASE {kb_name};"
        try:
            self.execute_sql(query)
            # self.console.print(f"Index creation/rebuild initiated for KB '{kb_name}'.")
            return True
        except Exception as e:
            self.console.print(f"[red]Error creating index for KB '{kb_name}': {str(e)}[/red]")
            return False

    def insert_into_knowledge_base_direct(self, kb_name: str, source_table: str, content_column: str, metadata_columns: dict = None, limit: int = None, order_by: str = None):
        if not self.project: 
            self.console.print("[red]Error: MindsDB connection not established.[/red]")
            return False
        
        select_columns = [content_column]
        if metadata_columns: select_columns.extend(metadata_columns.values())
        select_columns_str = ", ".join(list(dict.fromkeys(select_columns))) # Ensure unique and keep order
        
        query = f"INSERT INTO {kb_name} ({select_columns_str}) SELECT {select_columns_str} FROM {source_table}" # Ensure INSERT columns match SELECT
        
        if order_by: query += f" ORDER BY {order_by}"
        if limit and limit > 0: query += f" LIMIT {limit}"
        query += ";"
        
        try:
            self.execute_sql(query)
            # self.console.print(f"Data inserted into KB '{kb_name}' successfully from '{source_table}'.")
            return True
        except Exception as e:
            error_msg = str(e)
            if "Can't select from" in error_msg and "unknown" in error_msg:
                self.console.print(f"[red]Error: The datasource '{source_table}' was not found. Please create it first.[/red]")
            self.console.print(f"[red]Error inserting data into KB '{kb_name}' from '{source_table}': {error_msg}[/red]")
            return False

    def select_from_knowledge_base(self, kb_name: str, query_text: str, metadata_filters: dict = None, limit: int = 5):
        if not self.project: 
            self.console.print("[red]Error: MindsDB connection not established.[/red]")
            return None

        # self.console.print(f"Querying KB '{self.project.name}.{kb_name}' for: '{query_text}' with filters: {metadata_filters}")
        sanitized_query_text = query_text.replace("'", "''")
        where_clauses = [f"content = '{sanitized_query_text}'"]
        
        if metadata_filters:
            for col, val in metadata_filters.items():
                if isinstance(val, dict):
                    for op, op_val in val.items(): # MongoDB-style operators
                        sql_op = {"$gt": ">", "$gte": ">=", "$lt": "<", "$lte": "<="}.get(op)
                        if sql_op: where_clauses.append(f"{col} {sql_op} {op_val if isinstance(op_val, (int, float)) else f'{str(op_val).replace("'", "''")}'}")
                        else: self.console.print(f"[yellow]Warning: Unsupported operator '{op}' for column '{col}'. Skipping.[/yellow]")
                else:
                    sanitized_val = str(val).replace("'", "''") if isinstance(val, str) else val
                    where_clauses.append(f"{col} = '{sanitized_val}'" if isinstance(val, str) else f"{col} = {val}")
        
        query = f"SELECT * FROM {kb_name} WHERE {' AND '.join(where_clauses)}"
        if limit > 0: query += f" LIMIT {limit}"
        query += ";"
        
        try: 
            results_df = self.execute_sql(query)
            # self.console.print(f"Semantic search on KB '{kb_name}' executed successfully.")
            return results_df
        except Exception as e: 
            self.console.print(f"[red]Error performing semantic search on KB '{kb_name}': {str(e)}[/red]")
            return None

    def create_mindsdb_job(self, job_name: str, kb_name: str, hn_datasource: str, hn_table_name: str, schedule_interval: str = "every 1 day"):
        # This specific job creation method might be too specific if we have a generic one.
        # Consider deprecating or ensuring it uses the generic `create_job` if that's more flexible.
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return False

        if hn_table_name == 'stories': insert_cols, select_cols = "(content, story_id, author)", "title, id, by"
        elif hn_table_name == 'comments': insert_cols, select_cols = "(content, comment_id, author)", "text, id, by"
        else:
            insert_cols, select_cols = "(content, original_id)", "text, id"
            self.console.print(f"[yellow]Warning: Using generic column mapping for job on table {hn_table_name}[/yellow]")

        job_query_insert = f"INSERT INTO {kb_name} {insert_cols} SELECT {select_cols} FROM {hn_datasource}.{hn_table_name} LATEST"
        full_job_query = f"CREATE JOB {job_name} AS ({job_query_insert}) SCHEDULE {schedule_interval};"

        try:
            self.execute_sql(full_job_query)
            # self.console.print(f"Job '{job_name}' creation command executed.")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                self.console.print(f"Job '[cyan]{job_name}[/cyan]' already exists.")
                return True
            self.console.print(f"[red]Error creating job '{job_name}': {str(e)}[/red]")
            return False

    def list_models(self, project_name: str = None):
        if not self.project and not project_name:
            self.console.print("[red]Error: MindsDB connection not established and no project specified.[/red]")
            return None
        target_project = project_name if project_name else self.project.name
        if not target_project: self.console.print("[red]Error: Target project name could not be determined.[/red]"); return None

        query = f"SHOW MODELS FROM {target_project};"
        try:
            models_df = self.execute_sql(query, suppress_messages=True)
            if models_df is not None and not models_df.empty:
                return models_df
            # else: self.console.print(f"No models found in project '{target_project}'.") # Handled by command
            return pd.DataFrame()
        except Exception as e:
            self.console.print(f"[red]Error listing models from project '{target_project}': {str(e)}[/red]")
            return None

    def describe_model(self, model_name: str, project_name: str = None):
        if not self.project and not project_name:
            self.console.print("[red]Error: MindsDB connection not established and no project specified.[/red]")
            return None
        target_project = project_name if project_name else self.project.name
        if not target_project: self.console.print("[red]Error: Target project name could not be determined.[/red]"); return None

        qualified_model_name = f"{target_project}.{model_name}"
        query = f"DESCRIBE {qualified_model_name};"
        try:
            description_df = self.execute_sql(query, suppress_messages=True)
            if description_df is not None and not description_df.empty: return description_df

            query_fallback = f"DESCRIBE {model_name};" # Try without project qualification if first fails
            # self.console.print(f"First describe attempt for '{qualified_model_name}' returned empty. Trying fallback: {query_fallback}", style="dim")
            description_df_fallback = self.execute_sql(query_fallback, suppress_messages=True)
            if description_df_fallback is not None and not description_df_fallback.empty: return description_df_fallback

            # self.console.print(f"Model '{model_name}' not found or no description available in project '{target_project}'.") # Handled by command
            return pd.DataFrame()
        except Exception as e:
            self.console.print(f"[red]Error describing model '{qualified_model_name}': {str(e)}[/red]")
            return None # Fallback already tried implicitly if first exception was "not found" type

    def drop_model(self, model_name: str, project_name: str = None):
        if not self.project and not project_name:
            self.console.print("[red]Error: MindsDB connection not established and no project specified.[/red]")
            return False
        target_project = project_name if project_name else self.project.name
        if not target_project: self.console.print("[red]Error: Target project name could not be determined.[/red]"); return False

        qualified_model_name = f"{target_project}.{model_name}"
        query = f"DROP MODEL {qualified_model_name};"
        try:
            self.execute_sql(query)
            # self.console.print(f"Model '{qualified_model_name}' dropped successfully.")
            return True
        except Exception as e:
            err_str = str(e).lower()
            if "not found" in err_str or "doesn't exist" in err_str:
                # self.console.print(f"Model '{qualified_model_name}' not found, so it's already considered dropped.")
                return True # Consider it success
            self.console.print(f"[red]Error dropping model '{qualified_model_name}': {str(e)}[/red]")
            return False

    def refresh_model(self, model_name: str, project_name: str = None):
        if not self.project and not project_name:
            self.console.print("[red]Error: MindsDB connection not established and no project specified.[/red]")
            return False
        target_project = project_name if project_name else self.project.name
        if not target_project: self.console.print("[red]Error: Target project name could not be determined.[/red]"); return False

        qualified_model_name = f"{target_project}.{model_name}"
        query = f"RETRAIN {qualified_model_name};"
        try:
            self.execute_sql(query)
            # self.console.print(f"Model '{qualified_model_name}' refresh (retrain) process initiated.")
            time.sleep(0.5) # Short pause
            # Status check can be done by describe-model command separately
            return True
        except Exception as e:
            self.console.print(f"[red]Error refreshing model '{qualified_model_name}': {str(e)}[/red]")
            return False

    def create_model_from_query(self, model_name: str, project_name: str, select_data_query: str, predict_column: str, using_params: dict):
        if not self.project:
            self.console.print("[red]Error: MindsDB connection not established.[/red]")
            return False

        using_clause_parts = []
        for key, value in using_params.items():
            if isinstance(value, str): escaped_value = value.replace("'", "''"); using_clause_parts.append(f"{key} = '{escaped_value}'")
            elif isinstance(value, (int, float, bool)): using_clause_parts.append(f"{key} = {value}")
            else: using_clause_parts.append(f"{key} = {str(value)}") # May need more care for complex types
        using_statement = f"USING {', '.join(using_clause_parts)}" if using_clause_parts else ""

        query = f"CREATE MODEL {model_name} FROM {project_name} ({select_data_query}) PREDICT {predict_column} {using_statement};"
        try:
            self.execute_sql(query)
            # Verification can be done by describe-model command separately
            return True
        except Exception as e:
            err_str = str(e).lower()
            if "already exists" in err_str or "already created" in err_str:
                self.console.print(f"AI Model '[cyan]{model_name}[/cyan]' already exists.")
                return True # Or False if strict
            self.console.print(f"[red]Error during AI Model '{model_name}' creation process: {str(e)}[/red]")
            return False

    def create_kb_agent(self, agent_name: str, model_name: str, include_knowledge_bases: list[str],
                        google_api_key: str = None, include_tables: list[str] = None,
                        prompt_template: str = None, other_params: dict = None):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return False

        using_clauses = [f"model = '{model_name}'"]
        if google_api_key: using_clauses.append(f"google_api_key = '{google_api_key}'")
        elif 'google' in model_name.lower() or (other_params and other_params.get('provider', '').lower() == 'google'):
            config_google_key = getattr(config, 'GOOGLE_GEMINI_API_KEY', None)
            if config_google_key: using_clauses.append(f"google_api_key = '{config_google_key}'")
            else: self.console.print("[yellow]Warning: Google model specified, but google_api_key not provided/configured.[/yellow]")

        if not include_knowledge_bases or not isinstance(include_knowledge_bases, list) or not all(isinstance(kb, str) for kb in include_knowledge_bases):
            self.console.print("[red]Error: 'include_knowledge_bases' must be a non-empty list of strings.[/red]"); return False
        kb_list_str = "[" + ", ".join([f"'{kb.replace("'", "''")}'" for kb in include_knowledge_bases]) + "]"
        using_clauses.append(f"include_knowledge_bases = {kb_list_str}")

        if include_tables:
            if isinstance(include_tables, list) and all(isinstance(tbl, str) for tbl in include_tables):
                table_list_str = "[" + ", ".join([f"'{tbl.replace("'", "''")}'" for tbl in include_tables]) + "]"
                using_clauses.append(f"include_tables = {table_list_str}")
            else: self.console.print("[yellow]Warning: 'include_tables' provided but not a list of strings. Skipping.[/yellow]")
        if prompt_template:
            escaped_prompt = prompt_template.replace("'", "''")
            using_clauses.append(f"prompt_template = '''{escaped_prompt}'''")
        if other_params:
            for key, value in other_params.items():
                if key.lower() in ['model', 'google_api_key', 'include_knowledge_bases', 'include_tables', 'prompt_template', 'provider', 'api_key', 'knowledge_base']: continue
                if isinstance(value, str): using_clauses.append(f"{key} = '{str(value).replace("'", "''")}'")
                elif isinstance(value, (int, float, bool)): using_clauses.append(f"{key} = {value}")
                else:
                    try: json_val = json.dumps(value); using_clauses.append(f"{key} = '{json_val.replace("'", "''")}'")
                    except TypeError: self.console.print(f"[yellow]Warning: Parameter '{key}' for agent '{agent_name}' could not be serialized. Skipping.[/yellow]")

        query = f"CREATE AGENT {agent_name} USING {', '.join(using_clauses)};"
        try:
            self.execute_sql(query)
            return True
        except Exception as e:
            err_str = str(e).lower()
            if "already exists" in err_str or "already created" in err_str:
                self.console.print(f"Agent '[cyan]{agent_name}[/cyan]' already exists.")
                return True
            self.console.print(f"[red]Error creating agent '{agent_name}': {str(e)}[/red]")
            return False

    def query_kb_agent(self, agent_name: str, question: str):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return None
        sanitized_question = question.replace("'", "''")
        query = f"SELECT answer FROM {agent_name} WHERE question = '{sanitized_question}';"
        # self.console.print(f"Querying agent '{agent_name}' with question: '{question[:100]}...'")
        try:
            results_df = self.execute_sql(query)
            if results_df is not None and not results_df.empty:
                if 'answer' in results_df.columns and len(results_df['answer']) > 0:
                    return results_df['answer'].iloc[0]
                # self.console.print(f"[yellow]Warning: 'answer' column not found in agent output. Columns: {results_df.columns.tolist()}.[/yellow]")
                return results_df.iloc[0].to_dict() # Return full dict if 'answer' is missing
            # elif results_df is not None: self.console.print(f"Agent '{agent_name}' returned no results.") # Handled by command
            return "Agent returned no results or an empty DataFrame." if results_df is not None else None
        except Exception as e:
            self.console.print(f"[red]Error querying agent '{agent_name}': {str(e)}[/red]")
            return None
        
    def create_job(self, job_name: str, statements: list, project_name: str = None,
                   start_date: str = None, end_date: str = None,
                   schedule_interval: str = None, if_condition: str = None):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return False
        
        job_full_name = f"{project_name}.{job_name}" if project_name else job_name
        statements_str = ";\n    ".join(statements)
        query_parts = [f"CREATE JOB IF NOT EXISTS {job_full_name} (", f"    {statements_str}", ")"]
        
        if start_date: query_parts.append(f"START '{start_date}'")
        if end_date: query_parts.append(f"END '{end_date}'")
        if schedule_interval:
            if not schedule_interval.upper().startswith('EVERY '): schedule_interval = f"EVERY {schedule_interval}"
            query_parts.append(schedule_interval)
        if if_condition: query_parts.append(f"IF ({if_condition})")
        
        query = "\n".join(query_parts) + ";"
        try:
            # self.console.print(f"Creating job '{job_name}' with query:\n{query}", style="dim")
            self.execute_sql(query)
            return True
        except Exception as e:
            self.console.print(f"[red]Error creating job '{job_name}': {str(e)}[/red]")
            return False

    def update_hackernews_db(self, job_name: str, hn_datasource: str = "hackernews",
                           schedule_interval: str = 'EVERY 1 day', project_name: str = None):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return False
        statements = [f"DROP DATABASE IF EXISTS {hn_datasource}", f"CREATE DATABASE {hn_datasource} WITH ENGINE = 'hackernews'"]
        return self.create_job(job_name=job_name, statements=statements, project_name=project_name, schedule_interval=schedule_interval)

    def list_jobs(self, project_name: str = None):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return None
        try:
            query = f"SELECT * FROM {project_name}.jobs;" if project_name else "SHOW JOBS;"
            result = self.execute_sql(query, suppress_messages=True)
            # if result is not None and not result.empty: self.console.print("Available jobs:") # Handled by command
            # elif result is not None: self.console.print("No jobs found.") # Handled by command
            return result
        except Exception as e:
            self.console.print(f"[red]Error listing jobs: {str(e)}[/red]")
            return None

    def get_job_status(self, job_name: str, project_name: str = 'mindsdb'):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return None
        try:
            query = f"SELECT * FROM {project_name}.jobs WHERE name = '{job_name}';"
            result = self.execute_sql(query, suppress_messages=True)
            # if result is not None and not result.empty: self.console.print(f"Job '{job_name}' status:") # Handled by command
            # elif result is not None: self.console.print(f"Job '{job_name}' not found.") # Handled by command
            return result
        except Exception as e:
            self.console.print(f"[red]Error getting job status for '{job_name}': {str(e)}[/red]")
            return None

    def get_job_history(self, job_name: str, project_name: str = 'mindsdb'):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return None
        try:
            query = f"SELECT * FROM log.jobs_history WHERE project = '{project_name}' AND name = '{job_name}'" # Ensure log DB is accessible
            result = self.execute_sql(query, suppress_messages=True)
            # if result is not None and not result.empty: self.console.print(f"Job '{job_name}' execution history:") # Handled by command
            # elif result is not None: self.console.print(f"No execution history found for job '{job_name}'.") # Handled by command
            return result
        except Exception as e:
            # It's common for log.jobs_history to not exist or not be queryable by all users.
            self.console.print(f"[yellow]Could not get job history for '{job_name}' (table 'log.jobs_history' might be inaccessible or empty): {str(e)}[/yellow]")
            return None # Return None on specific error or empty

    def get_job_logs(self, job_name: str, project_name: str = 'mindsdb'):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return None
        # This method is tricky as log tables vary and might not be directly queryable
        # For now, defer detailed log fetching to direct SQL via `kleos ai query`
        # self.console.print(f"[yellow]Fetching detailed job logs for '{job_name}' is best done via direct SQL query to information_schema or log tables if available.[/yellow]")
        # self.console.print(f"Try: `kleos ai query \"SELECT * FROM {project_name}.jobs WHERE name = '{job_name}';\"` for basic info.")
        return self.get_job_status(job_name, project_name) # Return status as a proxy for "logs" for now

    def drop_job(self, job_name: str, project_name: str = None):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return False
        job_full_name = f"{project_name}.{job_name}" if project_name else job_name
        query = f"DROP JOB IF EXISTS {job_full_name};"
        try:
            self.execute_sql(query)
            return True
        except Exception as e:
            self.console.print(f"[red]Error deleting job '{job_name}': {str(e)}[/red]")
            return False

    def evaluate_knowledge_base(self, kb_name: str, test_table: str, version: str = None,
                                generate_data_from_sql: str = None, generate_data_count: int = None,
                                generate_data_flag: bool = False, run_evaluation: bool = True,
                                llm_provider: str = None, llm_api_key: str = None, llm_model_name: str = None,
                                llm_base_url: str = None, llm_other_params: dict = None,
                                save_to_table: str = None):
        if not self.project: self.console.print("[red]Error: MindsDB connection not established.[/red]"); return None

        using_clauses = [f"test_table = {test_table}"]
        if version: using_clauses.append(f"version = '{version}'")
        if generate_data_flag: using_clauses.append("generate_data = true")
        elif generate_data_from_sql or generate_data_count is not None:
            gen_data_dict_parts = []
            if generate_data_from_sql: escaped_sql = generate_data_from_sql.replace("'", "''"); gen_data_dict_parts.append(f"'from_sql': '''{escaped_sql}'''")
            if generate_data_count is not None: gen_data_dict_parts.append(f"'count': {generate_data_count}")
            if gen_data_dict_parts: using_clauses.append(f"generate_data = {{ {', '.join(gen_data_dict_parts)} }}")
        if not run_evaluation: using_clauses.append("evaluate = false")
        if llm_model_name:
            llm_config_parts = [f"'model_name': '{llm_model_name}'"]
            if llm_provider: llm_config_parts.append(f"'provider': '{llm_provider}'")
            if llm_api_key: llm_config_parts.append(f"'api_key': '{llm_api_key}'")
            if llm_base_url: llm_config_parts.append(f"'base_url': '{llm_base_url.rstrip('/')}'")
            if llm_other_params:
                for key, value in llm_other_params.items():
                    if isinstance(value, str): llm_config_parts.append(f"'{key}': '{str(value).replace("'", "''")}'")
                    elif isinstance(value, (int, float, bool)): llm_config_parts.append(f"'{key}': {value}")
                    else:
                        try: json_val = json.dumps(value); llm_config_parts.append(f"'{key}': '{json_val.replace("'", "''")}'")
                        except TypeError: self.console.print(f"[yellow]Warning: LLM parameter '{key}' could not be serialized. Skipping.[/yellow]")
            using_clauses.append(f"llm = {{ {', '.join(llm_config_parts)} }}")
        if save_to_table: using_clauses.append(f"save_to = {save_to_table}")

        query = f"EVALUATE KNOWLEDGE_BASE {kb_name} USING {', '.join(using_clauses)};"
        try:
            # self.console.print(f"Executing evaluation for KB '{kb_name}'...")
            result_df = self.execute_sql(query)
            # self.console.print(f"Evaluation for KB '{kb_name}' completed.")
            return result_df
        except Exception as e:
            self.console.print(f"[red]Error evaluating Knowledge Base '{kb_name}': {str(e)}[/red]")
            return None

# Keep the __main__ block for direct testing (will use standard print)
if __name__ == '__main__':
    print("Testing MindsDBHandler directly (using standard print)...")
    # Use a default console for direct testing if not passed
    test_console = Console()
    handler = MindsDBHandler(rich_console=test_console) # Pass the console
    if handler.connect():
        test_console.print("\n--- Connected successfully ---", style="bold green")

        hn_test_name = f"test_hn_ds_final_{int(time.time())%10000}"
        test_console.print(f"\n--- Testing Create HackerNews DS: {hn_test_name} ---")
        handler.create_hackernews_datasource(hn_test_name)

        kb_test_name = f"test_kb_final_{int(time.time())%10000}"
        test_console.print(f"\n--- Testing Create KB: {kb_test_name} ---")
        ollama_base = getattr(config, 'OLLAMA_BASE_URL', "http://127.0.0.1:11434")
        ollama_embed = getattr(config, 'OLLAMA_EMBEDDING_MODEL', "nomic-embed-text")
        ollama_rerank = getattr(config, 'OLLAMA_RERANKING_MODEL', "llama3")

        if handler.create_knowledge_base(
            kb_test_name, "ollama", ollama_embed, ollama_base, None, # No API key for local Ollama
            "ollama", ollama_rerank, ollama_base, None # No API key for local Ollama
            ):
            test_console.print(f"KB {kb_test_name} created/exists.")

            # Agent creation in MindsDB has evolved. The old 'model_provider' might not be standard.
            # The current CLI uses 'model_name' and infers provider or expects it in other_params.
            # For direct testing, we'll adapt to something closer to the new CLI's agent creation logic.
            # Example: Create agent with Ollama Llama3 (assuming it's set up in MindsDB)
            agent_ollama_test_name = f"test_agent_o_{int(time.time())%10000}"
            test_console.print(f"\n--- Testing Create Ollama Agent: {agent_ollama_test_name} for KB {kb_test_name} ---")

            # Correct agent creation for Ollama: specify model name directly
            # The `model_name` for an agent is the LLM used by the agent, not the KB's embedding model.
            if handler.create_kb_agent(agent_name=agent_ollama_test_name,
                                       model_name=ollama_rerank, # e.g., 'llama3'
                                       include_knowledge_bases=[kb_test_name],
                                       other_params={'provider': 'ollama', 'base_url': ollama_base.rstrip('/')} # provider might be needed by older MDB versions
                                      ):
                test_console.print(f"Agent {agent_ollama_test_name} created.")
                test_console.print(f"\n--- Testing Query Ollama Agent: {agent_ollama_test_name} ---")
                response = handler.query_kb_agent(agent_ollama_test_name, "Explain knowledge bases simply.")
                test_console.print(f"Ollama Agent Response: {response}")
            else:
                test_console.print(f"Failed to create Ollama agent {agent_ollama_test_name}")

            if config.GOOGLE_GEMINI_API_KEY and getattr(config, 'GOOGLE_MODEL', None):
                agent_google_test_name = f"test_agent_g_{int(time.time())%10000}"
                google_model_for_agent = getattr(config, 'GOOGLE_MODEL') # e.g., 'gemini-1.5-flash'
                test_console.print(f"\n--- Testing Create Google Agent: {agent_google_test_name} for KB {kb_test_name} using {google_model_for_agent} ---")
                if handler.create_kb_agent(agent_name=agent_google_test_name,
                                           model_name=google_model_for_agent,
                                           include_knowledge_bases=[kb_test_name],
                                           google_api_key=config.GOOGLE_GEMINI_API_KEY # Pass explicitly
                                           # other_params={'provider': 'google'} # Provider might be needed
                                           ):
                    test_console.print(f"Agent {agent_google_test_name} created.")
                    test_console.print(f"\n--- Testing Query Google Agent: {agent_google_test_name} ---")
                    response = handler.query_kb_agent(agent_google_test_name, "What is a knowledge base?")
                    test_console.print(f"Google Agent Response: {response}")
                else:
                    test_console.print(f"Failed to create Google agent {agent_google_test_name}")
            else:
                test_console.print("\n--- Skipping Google Agent tests (GOOGLE_GEMINI_API_KEY or GOOGLE_MODEL not set in config) ---", style="yellow")
        else:
            test_console.print(f"KB {kb_test_name} creation failed, skipping agent tests for it.", style="red")
    else:
        test_console.print("\n--- Failed to connect to MindsDB. Handler tests aborted. ---", style="bold red")

import mindsdb_sdk
from config import config
import pandas as pd
import time
import json # Ensure json is imported for create_kb_agent

class MindsDBHandler:
    def __init__(self):
        self.server = None
        self.project = None
        self.mindsdb_host = config.MINDSDB_HOST
        self.mindsdb_port = config.MINDSDB_PORT
        self.mindsdb_user = config.MINDSDB_USER
        self.mindsdb_password = config.MINDSDB_PASSWORD
        print(f"MindsDBHandler initialized for {self.mindsdb_host}:{self.mindsdb_port}")

    def connect(self):
        print(f"Attempting to connect to MindsDB: {self.mindsdb_host}:{self.mindsdb_port}")
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

            print(f"Successfully connected to MindsDB and got project '{self.project.name}'.")
            return True
        except Exception as e:
            print(f"Error connecting to MindsDB: {str(e)}")
            self.server = None
            self.project = None
            return False

    def execute_sql(self, query: str):
        if not self.project:
            print("No active MindsDB project. Attempting to reconnect...")
            if not self.connect() or not self.project:
                raise ConnectionError("MindsDB connection not established. Cannot execute query.")

        print(f"Executing SQL: {query}")
        try:
            query_result = self.project.query(query)
            print("Query executed successfully via SDK.")
            return query_result.fetch()
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                # Retry once if event loop is closed
                print("Event loop closed, retrying query...")
                try:
                    query_result = self.project.query(query)
                    print("Query executed successfully via SDK on retry.")
                    return query_result.fetch()
                except Exception as retry_e:
                    print(f"MindsDB API Error on retry '{query}': {str(retry_e)}")
                    raise
            else:
                raise
        except Exception as e:
            error_details = str(e)
            print(f"MindsDB API Error executing query '{query}': {error_details}")
            raise

    def get_database_custom_check(self, ds_name: str) -> bool:
        if not self.project:
            print("Cannot perform custom database check: No active MindsDB project.")
            return False
        print(f"Custom check: Verifying existence of database '{ds_name}' using SHOW DATABASES.")
        try:
            res_df = self.execute_sql('SHOW DATABASES;')
            if res_df is None or res_df.empty:
                print("Custom check: 'SHOW DATABASES' returned no results or failed.")
                return False
            db_column_name = None
            if 'Database' in res_df.columns: db_column_name = 'Database'
            elif 'name' in res_df.columns: db_column_name = 'name'
            elif 'NAME' in res_df.columns: db_column_name = 'NAME'
            else:
                print(f"Custom check: Could not find a known database name column. Columns: {res_df.columns.tolist()}")
                return False
            databases = res_df[db_column_name].values
            if ds_name in databases:
                print(f"Custom check: Database '{ds_name}' found."); return True
            else:
                print(f"Custom check: Database '{ds_name}' not found."); return False
        except Exception as e:
            print(f"Custom check: Error during 'SHOW DATABASES' for '{ds_name}': {str(e)}")
            return False

    def create_hackernews_datasource(self, ds_name: str = "hackernews"):
        if not self.project:
            print("Error: MindsDB connection not established for create_hackernews_datasource.")
            return False
        if self.get_database_custom_check(ds_name):
            print(f"Datasource '{ds_name}' (HackerNews) already exists (verified by custom check).")
            return True
        query = f"CREATE DATABASE {ds_name} WITH ENGINE = 'hackernews';"
        try:
            self.execute_sql(query)
            print(f"HackerNews datasource '{ds_name}' creation command executed.")
            time.sleep(1)
            if self.get_database_custom_check(ds_name):
                print(f"Datasource '{ds_name}' successfully verified after creation (custom check).")
                return True
            else:
                print(f"Error: Datasource '{ds_name}' creation command executed, but custom verification check failed.")
                try:
                    if self.project and hasattr(self.project, 'get_database') and self.project.get_database(ds_name):
                        print(f"Fallback SDK check: Datasource '{ds_name}' found after creation.")
                        return True
                except Exception as sdk_e:
                    print(f"Fallback SDK check also failed for '{ds_name}': {str(sdk_e)}")
                return False
        except Exception as e:
            print(f"Error executing create HackerNews datasource query for '{ds_name}': {str(e)}")
            return False

    def create_knowledge_base(self, kb_name: str,
                             embedding_provider: str, embedding_model: str,
                             embedding_base_url: str = None, embedding_api_key: str = None,
                             reranking_provider: str = None, reranking_model: str = None,
                             reranking_base_url: str = None, reranking_api_key: str = None,
                             content_columns: list = None, metadata_columns: list = None, id_column: str = None):
        if not self.project:
            print("Error: MindsDB connection not established.")
            return False

        using_clauses = []

        # Embedding model configuration
        emb_config = {
            "provider": embedding_provider,
            "model_name": embedding_model
        }
        if embedding_base_url:
            emb_config["base_url"] = embedding_base_url.rstrip('/')
        if embedding_api_key:
            emb_config["api_key"] = embedding_api_key
        
        # Correctly escape special characters in JSON string values
        emb_config_str = ", ".join([f'"{k}": "{str(v).replace("\"", "\\\"")}"' for k, v in emb_config.items()])
        using_clauses.append(f"embedding_model = {{ {emb_config_str} }}")

        # Reranking model configuration (if specified)
        if reranking_provider and reranking_model:
            rerank_config = {
                "provider": reranking_provider,
                "model_name": reranking_model
            }
            if reranking_base_url:
                rerank_config["base_url"] = reranking_base_url.rstrip('/')
            if reranking_api_key:
                rerank_config["api_key"] = reranking_api_key

            rerank_config_str = ", ".join([f'"{k}": "{str(v).replace("\"", "\\\"")}"' for k, v in rerank_config.items()])
            using_clauses.append(f"reranking_model = {{ {rerank_config_str} }}")

        # Add content_columns, metadata_columns, and id_column if specified
        if content_columns:
            # Ensure content_columns is a list of strings, then format for SQL
            if isinstance(content_columns, list) and all(isinstance(col, str) for col in content_columns):
                 # MindsDB expects content_columns = ['col1', 'col2'] or content_columns = 'col1'
                if len(content_columns) == 1:
                    using_clauses.append(f"content_columns = '{content_columns[0]}'")
                else:
                    content_columns_sql_array = "[" + ", ".join([f"'{col}'" for col in content_columns]) + "]"
                    using_clauses.append(f"content_columns = {content_columns_sql_array}")
            else:
                print("Warning: content_columns should be a list of strings. Skipping.")
        
        if metadata_columns:
            if isinstance(metadata_columns, list) and all(isinstance(col, str) for col in metadata_columns):
                if len(metadata_columns) == 1:
                    using_clauses.append(f"metadata_columns = '{metadata_columns[0]}'")
                else:
                    metadata_columns_sql_array = "[" + ", ".join([f"'{col}'" for col in metadata_columns]) + "]"
                    using_clauses.append(f"metadata_columns = {metadata_columns_sql_array}")
            else:
                print("Warning: metadata_columns should be a list of strings. Skipping.")
        
        if id_column:
            using_clauses.append(f"id_column = '{id_column}'")

        query = f"CREATE KNOWLEDGE_BASE {kb_name} USING {', '.join(using_clauses)};"
        
        try:
            self.execute_sql(query)
            print(f"Knowledge Base '{kb_name}' creation command executed.")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Knowledge Base '{kb_name}' already exists.")
                return True
            print(f"Error creating Knowledge Base '{kb_name}': {str(e)}")
            return False

    def create_index_on_knowledge_base(self, kb_name: str):
        if not self.project: print("Error: MindsDB connection not established."); return False
        query = f"CREATE INDEX ON KNOWLEDGE_BASE {kb_name};"
        try: self.execute_sql(query); print(f"Index creation/rebuild initiated for KB '{kb_name}'."); return True
        except Exception as e: print(f"Error creating index for KB '{kb_name}': {str(e)}"); return False

    def insert_into_knowledge_base_direct(self, kb_name: str, source_table: str, content_column: str, metadata_columns: dict = None, limit: int = None, order_by: str = None):
        """Insert data directly from a source table into knowledge base using MindsDB's recommended syntax."""
        if not self.project: 
            print("Error: MindsDB connection not established.")
            return False
        
        # Build SELECT columns list - content column first, then metadata columns
        select_columns = [content_column]
        if metadata_columns:
            # metadata_columns maps kb_column_name -> source_column_name
            select_columns.extend(metadata_columns.values())
        
        # Remove duplicates and join
        select_columns_str = ", ".join(select_columns)  # Keep order: content first, then metadata
        
        # Build the query using MindsDB's recommended INSERT INTO ... SELECT syntax
        query = f"INSERT INTO {kb_name} SELECT {select_columns_str} FROM {source_table}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit and limit > 0:
            query += f" LIMIT {limit}"
        query += ";"
        
        try:
            self.execute_sql(query)
            print(f"Data inserted into KB '{kb_name}' successfully from '{source_table}'.")
            return True
        except Exception as e:
            error_msg = str(e)
            if "Can't select from" in error_msg and "unknown" in error_msg:
                print(f"Error: The datasource '{source_table}' was not found. Please create the datasource first.")
                print(f"You can create a HackerNews datasource using: CREATE DATABASE {source_table.split('.')[0]} WITH ENGINE = 'hackernews';")
            print(f"Error inserting data into KB '{kb_name}' from '{source_table}': {error_msg}")
            return False

    # def insert_into_knowledge_base(self, kb_name: str, data: list[dict], content_column: str, metadata_columns: dict = None):
    #     if not self.project: print("Error: MindsDB connection not established."); return False
    #     if not data: print("No data provided for insertion."); return True
    #     column_names_for_sql = [content_column];
    #     if metadata_columns: column_names_for_sql.extend(metadata_columns.keys())
    #     values_list_str = []
    #     for record in data:
    #         if content_column not in record: print(f"Warning: Record missing content_column ('{content_column}'). Skipping: {record}"); continue
    #         value_tuple_parts = [f"'{str(record[content_column]).replace("'", "''")}'"]
    #         if metadata_columns:
    #             for kb_meta_col, data_key in metadata_columns.items():
    #                 val = record.get(data_key)
    #                 if val is None: value_tuple_parts.append("NULL")
    #                 elif isinstance(val, (int, float, bool)): value_tuple_parts.append(str(val))
    #                 else: value_tuple_parts.append(f"'{str(val).replace("'", "''")}'")
    #         values_list_str.append(f"({', '.join(value_tuple_parts)})")
    #     if not values_list_str: print("No valid data to insert after processing."); return False
    #     query = f"INSERT INTO {self.project.name}.{kb_name} ({', '.join(column_names_for_sql)}) VALUES {', '.join(values_list_str)};"
    #     try: self.execute_sql(query); print(f"Data inserted into KB '{kb_name}' successfully."); return True
    #     except Exception as e: print(f"Error inserting data into KB '{kb_name}': {str(e)}"); return False

    def select_from_knowledge_base(self, kb_name: str, query_text: str, metadata_filters: dict = None, limit: int = 5):
        """Select data from a knowledge base using semantic search and optional metadata filters."""
        if not self.project: 
            print("Error: MindsDB connection not established.")
            return None

        print(f"Querying KB '{self.project.name}.{kb_name}' for: '{query_text}' with filters: {metadata_filters}")

        # For MindsDB knowledge bases, use the correct 'content' parameter in WHERE clause
        # According to MindsDB docs: WHERE content = 'search text' for semantic search
        sanitized_query_text = query_text.replace("'", "''")
        where_clauses = [f"content = '{sanitized_query_text}'"]
        
        if metadata_filters:
            for col, val in metadata_filters.items():
                if isinstance(val, dict):
                    # Handle MongoDB-style operators like {"$gt": 50}
                    for op, op_val in val.items():
                        if op == "$gt":
                            where_clauses.append(f"{col} > {op_val}")
                        elif op == "$gte":
                            where_clauses.append(f"{col} >= {op_val}")
                        elif op == "$lt":
                            where_clauses.append(f"{col} < {op_val}")
                        elif op == "$lte":
                            where_clauses.append(f"{col} <= {op_val}")
                        else:
                            print(f"Warning: Unsupported operator '{op}' for column '{col}'. Skipping.")
                else:
                    # Simple equality filter
                    sanitized_val = str(val).replace("'", "''") if isinstance(val, str) else val
                    where_clauses.append(f"{col} = '{sanitized_val}'" if isinstance(val, str) else f"{col} = {val}")
        
        # Use correct MindsDB Knowledge Base syntax: WHERE content = 'search text'
        query = f"SELECT * FROM {kb_name} WHERE {' AND '.join(where_clauses)}"
        if limit > 0: 
            query += f" LIMIT {limit}"
        query += ";"
        
        try: 
            results_df = self.execute_sql(query)
            print(f"Semantic search on KB '{kb_name}' executed successfully.")
            return results_df
        except Exception as e: 
            print(f"Error performing semantic search on KB '{kb_name}': {str(e)}")
            return None

    def create_mindsdb_job(self, job_name: str, kb_name: str, hn_datasource: str, hn_table_name: str, schedule_interval: str = "every 1 day"):
        if not self.project: print("Error: MindsDB connection not established."); return False
        if hn_table_name == 'stories': insert_cols, select_cols = "(content, story_id, author)", "title, id, by"
        elif hn_table_name == 'comments': insert_cols, select_cols = "(content, comment_id, author)", "text, id, by"
        else: insert_cols, select_cols = "(content, original_id)", "text, id"; print(f"Warning: Using generic column mapping for job on table {hn_table_name}")
        job_query_insert = f"INSERT INTO {kb_name} {insert_cols} SELECT {select_cols} FROM {hn_datasource}.{hn_table_name} LATEST"
        full_job_query = f"CREATE JOB {job_name} AS ({job_query_insert}) SCHEDULE {schedule_interval};"
        try: self.execute_sql(full_job_query); print(f"Job '{job_name}' creation command executed."); return True
        except Exception as e:
            if "already exists" in str(e).lower(): print(f"Job '{job_name}' already exists."); return True
            print(f"Error creating job '{job_name}': {str(e)}"); return False

    def create_ai_table(self, model_name: str, gemini_api_key: str = None, additional_using_params: dict = None):
        if not self.project: print("Error: MindsDB connection not established."); return False
        engine = additional_using_params.get('engine', 'google_gemini') if additional_using_params else 'google_gemini'
        actual_api_key = None
        if engine == 'google_gemini':
            actual_api_key = additional_using_params.get('api_key', gemini_api_key) if additional_using_params else gemini_api_key
            if not actual_api_key: print("Error: Google Gemini API key required for google_gemini engine."); return False
        using_clause_parts = [f"engine = '{engine}'"]
        if actual_api_key and engine == 'google_gemini':
             using_clause_parts.append(f"api_key = '{actual_api_key}'")
        if additional_using_params:
            for key, value in additional_using_params.items():
                if key.lower() not in ['engine', 'api_key']:
                    if key == 'base_url' and isinstance(value, str): value = value.rstrip('/')
                    if isinstance(value, str): using_clause_parts.append(f"{key} = '{value.replace("'", "''")}'")
                    else: using_clause_parts.append(f"{key} = {value}")
        query = f"CREATE MODEL {model_name} USING {', '.join(using_clause_parts)};"
        try: self.execute_sql(query); print(f"AI Model '{model_name}' creation command executed."); return True
        except Exception as e:
            err_str = str(e).lower()
            if "already exists" in err_str or "already created" in err_str:
                print(f"AI Model '{model_name}' already exists."); return True
            print(f"Error creating AI Model '{model_name}': {str(e)}"); return False

    def query_ai_table(self, model_name: str, text_to_process: str, classification_prompt: str = None):
        if not self.project: print("Error: MindsDB connection not established."); return None
        final_input_text = text_to_process
        if classification_prompt:
            if "{text}" in classification_prompt: final_input_text = classification_prompt.replace("{text}", text_to_process)
            else: final_input_text = f"{classification_prompt} Text: {text_to_process}"
        sanitized_input = final_input_text.replace("'", "''")
        query = f"SELECT response FROM {model_name} WHERE prompt='{sanitized_input}';"
        try:
            results_df = self.execute_sql(query)
            if results_df is not None and not results_df.empty and 'response' in results_df.columns:
                return results_df['response'].iloc[0] if len(results_df['response']) > 0 else None
            elif results_df is not None: print("AI Model query returned no response."); return None
            else: print("AI Model query failed to return DataFrame."); return None
        except Exception as e: print(f"Error querying AI Model '{model_name}': {str(e)}"); return None

    # --- New AI Agent Methods ---
    def create_kb_agent(self,
                        agent_name: str,
                        model_name: str,
                        include_knowledge_bases: list[str],
                        google_api_key: str = None,
                        include_tables: list[str] = None,
                        prompt_template: str = None,
                        other_params: dict = None):
        if not self.project:
            print("Error: MindsDB connection not established.")
            return False

        using_clauses = [
            f"model = '{model_name}'" # Direct model name
        ]

        # Handle google_api_key
        if google_api_key:
            using_clauses.append(f"google_api_key = '{google_api_key}'")
        elif 'google' in model_name.lower() or (other_params and other_params.get('provider', '').lower() == 'google'): # Heuristic for google model
            # Try to get from config if not provided
            config_google_key = getattr(config, 'GOOGLE_GEMINI_API_KEY', None)
            if config_google_key:
                using_clauses.append(f"google_api_key = '{config_google_key}'")
            else:
                print("Warning: Google model specified or inferred, but google_api_key not provided and not in config. Agent creation might fail.")


        # Handle include_knowledge_bases (must be a list of strings)
        if not include_knowledge_bases or not isinstance(include_knowledge_bases, list) or not all(isinstance(kb, str) for kb in include_knowledge_bases):
            print("Error: 'include_knowledge_bases' must be a non-empty list of strings.")
            return False
        kb_list_str = "[" + ", ".join([f"'{kb.replace("'", "''")}'" for kb in include_knowledge_bases]) + "]"
        using_clauses.append(f"include_knowledge_bases = {kb_list_str}")

        # Handle include_tables (optional list of strings)
        if include_tables:
            if isinstance(include_tables, list) and all(isinstance(tbl, str) for tbl in include_tables):
                table_list_str = "[" + ", ".join([f"'{tbl.replace("'", "''")}'" for tbl in include_tables]) + "]"
                using_clauses.append(f"include_tables = {table_list_str}")
            else:
                print("Warning: 'include_tables' provided but not a list of strings. Skipping.")

        # Handle prompt_template (optional string)
        if prompt_template:
            # Triple single quotes for multi-line SQL strings, escape internal single quotes
            escaped_prompt = prompt_template.replace("'", "''")
            using_clauses.append(f"prompt_template = '''{escaped_prompt}'''")

        # Handle other_params (e.g., temperature)
        if other_params:
            for key, value in other_params.items():
                # Skip keys already handled or not suitable for direct USING clause
                if key.lower() in ['model', 'google_api_key', 'include_knowledge_bases', 'include_tables', 'prompt_template', 'provider', 'api_key', 'knowledge_base']: # 'provider', 'api_key', 'knowledge_base' are from old agent style
                    continue

                if isinstance(value, str):
                    using_clauses.append(f"{key} = '{str(value).replace("'", "''")}'")
                elif isinstance(value, (int, float, bool)):
                    using_clauses.append(f"{key} = {value}")
                else:
                    try:
                        # For complex objects, try to dump as JSON string, then quote it for SQL
                        json_val = json.dumps(value)
                        using_clauses.append(f"{key} = '{json_val.replace("'", "''")}'")
                    except TypeError:
                        print(f"Warning: Parameter '{key}' from other_params for agent '{agent_name}' could not be serialized to a valid SQL literal. Skipping.")

        query = f"CREATE AGENT {agent_name} USING {', '.join(using_clauses)};"

        try:
            self.execute_sql(query)
            print(f"Agent '{agent_name}' creation command executed successfully.")
            return True
        except Exception as e:
            err_str = str(e).lower()
            if "already exists" in err_str or "already created" in err_str:
                print(f"Agent '{agent_name}' already exists.")
                return True
            print(f"Error creating agent '{agent_name}': {str(e)}")
            return False

    def query_kb_agent(self, agent_name: str, question: str):
        if not self.project:
            print("Error: MindsDB connection not established.")
            return None
        sanitized_question = question.replace("'", "''")
        query = f"SELECT answer FROM {agent_name} WHERE question = '{sanitized_question}';"
        print(f"Querying agent '{agent_name}' with question: '{question[:100]}...'")
        try:
            results_df = self.execute_sql(query)
            if results_df is not None and not results_df.empty:
                if 'answer' in results_df.columns and len(results_df['answer']) > 0:
                    return results_df['answer'].iloc[0]
                else:
                    print(f"Warning: 'answer' column not found in agent output. Columns: {results_df.columns.tolist()}. Returning full first row dict.")
                    return results_df.iloc[0].to_dict() if not results_df.empty else "Agent returned data but no 'answer' column or rows."
            elif results_df is not None:
                print(f"Agent '{agent_name}' returned no results for the question.")
                return "Agent returned no results."
            else:
                print(f"Agent query for '{agent_name}' failed to return a DataFrame.")
                return None
        except Exception as e:
            print(f"Error querying agent '{agent_name}': {str(e)}")
            return None
        
    def create_job(self, job_name: str, statements: list, project_name: str = None, start_date: str = None, end_date: str = None, schedule_interval: str = None, if_condition: str = None):
        """
        Create a MindsDB job with custom SQL statements.
        
        Args:
            job_name: Name of the job to create
            statements: List of SQL statements to execute
            project_name: Optional project name
            start_date: Optional start date ('YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS')
            end_date: Optional end date ('YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS')
            schedule_interval: Optional schedule interval (e.g., 'EVERY 1 hour', 'EVERY 2 days')
            if_condition: Optional condition statement
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.project:
            print("Error: MindsDB connection not established.")
            return False
        
        # Build the job name with project if provided
        job_full_name = f"{project_name}.{job_name}" if project_name else job_name
        
        # Build the SQL statements part
        statements_str = ";\n    ".join(statements)
        
        # Build the complete query
        query_parts = [f"CREATE JOB IF NOT EXISTS {job_full_name} ("]
        query_parts.append(f"    {statements_str}")
        query_parts.append(")")
        
        if start_date:
            query_parts.append(f"START '{start_date}'")
        
        if end_date:
            query_parts.append(f"END '{end_date}'")
        
        if schedule_interval:
            # Ensure the interval starts with 'EVERY'
            if not schedule_interval.upper().startswith('EVERY'):
                schedule_interval = f"EVERY {schedule_interval}"
            query_parts.append(schedule_interval)
        
        if if_condition:
            query_parts.append(f"IF ({if_condition})")
        
        query = "\n".join(query_parts) + ";"
        
        try:
            print(f"Creating job '{job_name}' with query:")
            print(query)
            self.execute_sql(query)
            print(f"Job '{job_name}' created successfully.")
            return True
        except Exception as e:
            print(f"Error creating job '{job_name}': {str(e)}")
            return False

    def update_hackernews_db(self, job_name: str, hn_datasource: str = "hackernews",
                           schedule_interval: str = 'EVERY 1 day', project_name: str = None):
        """
        Create a MindsDB job to periodically refresh the HackerNews database by dropping and recreating it.
        
        Args:
            job_name: Name of the job to create
            hn_datasource: Name of the HackerNews datasource to refresh (default: 'hackernews')
            schedule_interval: Schedule interval (e.g., 'EVERY 1 hour', 'EVERY 1 day')
            project_name: Optional project name
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.project:
            print("Error: MindsDB connection not established.")
            return False
        
        # Create statements to drop and recreate the HackerNews database
        statements = [
            f"DROP DATABASE IF EXISTS {hn_datasource}",
            f"CREATE DATABASE {hn_datasource} WITH ENGINE = 'hackernews'"
        ]
        
        return self.create_job(
            job_name=job_name,
            statements=statements,
            project_name=project_name,
            schedule_interval=schedule_interval
        )

    def list_jobs(self, project_name: str = None):
        """
        List all jobs in MindsDB.
        
        Args:
            project_name: Optional project name to filter jobs
        
        Returns:
            DataFrame or None: Job information
        """
        if not self.project:
            print("Error: MindsDB connection not established.")
            return None
        
        try:
            if project_name:
                query = f"SELECT * FROM {project_name}.jobs;"
            else:
                query = "SHOW JOBS;"
            
            result = self.execute_sql(query)
            if result is not None and not result.empty:
                print("Available jobs:")
                print(result.to_string(index=False))
                return result
            else:
                print("No jobs found.")
                return None
        except Exception as e:
            print(f"Error listing jobs: {str(e)}")
            return None

    def get_job_status(self, job_name: str, project_name: str = 'mindsdb'):
        """
        Get the status of a specific job.
        
        Args:
            job_name: Name of the job
            project_name: Project name (defaults to 'mindsdb')
        
        Returns:
            DataFrame or None: Job status information
        """
        if not self.project:
            print("Error: MindsDB connection not established.")
            return None
        
        try:
            query = f"SELECT * FROM {project_name}.jobs WHERE name = '{job_name}';"
            result = self.execute_sql(query)
            
            if result is not None and not result.empty:
                print(f"Job '{job_name}' status:")
                print(result.to_string(index=False))
                return result
            else:
                print(f"Job '{job_name}' not found.")
                return None
        except Exception as e:
            print(f"Error getting job status for '{job_name}': {str(e)}")
            return None

    def get_job_history(self, job_name: str, project_name: str = 'mindsdb'):
        """
        Get the execution history of a specific job.
        
        Args:
            job_name: Name of the job
            project_name: Project name (defaults to 'mindsdb')
        
        Returns:
            DataFrame or None: Job execution history
        """
        if not self.project:
            print("Error: MindsDB connection not established.")
            return None
        
        try:
            query = f"SELECT * FROM log.jobs_history WHERE project = '{project_name}' AND name = '{job_name}'"
            result = self.execute_sql(query)
            
            if result is not None and not result.empty:
                print(f"Job '{job_name}' execution history:")
                print(result.to_string(index=False))
                return result
            else:
                print(f"No execution history found for job '{job_name}'.")
                return None
        except Exception as e:
            print(f"Error getting job history for '{job_name}': {str(e)}")
            return None

    def get_job_logs(self, job_name: str, project_name: str = 'mindsdb'):
        """
        Get the logs of a specific job.
        
        Args:
            job_name: Name of the job
            project_name: Project name (defaults to 'mindsdb')
        
        Returns:
            DataFrame or None: Job logs
        """
        if not self.project:
            print("Error: MindsDB connection not established.")
            return None
        
        try:
            # Try different log table names as they might vary
            queries = [
                f"SELECT * FROM log.jobs WHERE project = '{project_name}' AND name = '{job_name}' ORDER BY created_at DESC;",
                f"SELECT * FROM information_schema.jobs WHERE project = '{project_name}' AND name = '{job_name}';",
                f"SELECT * FROM {project_name}.jobs WHERE name = '{job_name}';"
            ]
            
            for query in queries:
                try:
                    result = self.execute_sql(query)
                    if result is not None and not result.empty:
                        print(f"Job '{job_name}' information:")
                        print(result.to_string(index=False))
                        return result
                except:
                    continue
            
            print(f"No detailed logs found for job '{job_name}'. Try checking job status or history.")
            return None
        except Exception as e:
            print(f"Error getting job logs for '{job_name}': {str(e)}")
            return None

    def drop_job(self, job_name: str, project_name: str = None):
        """
        Drop/delete a MindsDB job.
        
        Args:
            job_name: Name of the job to delete
            project_name: Optional project name
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.project:
            print("Error: MindsDB connection not established.")
            return False
        
        job_full_name = f"{project_name}.{job_name}" if project_name else job_name
        query = f"DROP JOB IF EXISTS {job_full_name};"
        
        try:
            self.execute_sql(query)
            print(f"Job '{job_name}' deleted successfully.")
            return True
        except Exception as e:
            print(f"Error deleting job '{job_name}': {str(e)}")
            return False

    def evaluate_knowledge_base(self, kb_name: str, test_table: str,
                                version: str = None,
                                generate_data_from_sql: str = None,
                                generate_data_count: int = None,
                                generate_data_flag: bool = False,
                                run_evaluation: bool = True,
                                llm_provider: str = None,
                                llm_api_key: str = None,
                                llm_model_name: str = None,
                                llm_base_url: str = None,
                                llm_other_params: dict = None, # For params like 'method'
                                save_to_table: str = None):
        if not self.project:
            print("Error: MindsDB connection not established.")
            return None

        using_clauses = [f"test_table = {test_table}"] # test_table is like 'datasource.table'

        if version:
            using_clauses.append(f"version = '{version}'")

        if generate_data_flag:
            using_clauses.append("generate_data = true")
        elif generate_data_from_sql or generate_data_count is not None:
            gen_data_dict_parts = []
            if generate_data_from_sql:
                # SQL query string needs to be quoted within the JSON-like structure for SQL
                escaped_sql = generate_data_from_sql.replace("'", "''")
                gen_data_dict_parts.append(f"'from_sql': '''{escaped_sql}'''")
            if generate_data_count is not None:
                gen_data_dict_parts.append(f"'count': {generate_data_count}")
            if gen_data_dict_parts:
                using_clauses.append(f"generate_data = {{ {', '.join(gen_data_dict_parts)} }}")

        if not run_evaluation: # if run_evaluation is False, then add 'evaluate = false'
            using_clauses.append("evaluate = false")
        # Otherwise, 'evaluate = true' is default in MindsDB, so we can omit it.

        if llm_model_name: # LLM clause is only added if a model name is specified
            llm_config_parts = [f"'model_name': '{llm_model_name}'"]
            if llm_provider:
                llm_config_parts.append(f"'provider': '{llm_provider}'")
            if llm_api_key:
                llm_config_parts.append(f"'api_key': '{llm_api_key}'")
            if llm_base_url:
                llm_config_parts.append(f"'base_url': '{llm_base_url.rstrip('/')}'")

            if llm_other_params:
                for key, value in llm_other_params.items():
                    if isinstance(value, str):
                        llm_config_parts.append(f"'{key}': '{str(value).replace("'", "''")}'")
                    elif isinstance(value, (int, float, bool)):
                         llm_config_parts.append(f"'{key}': {value}")
                    else: # Attempt to JSON dump for complex types, though less common for LLM params here
                        try:
                            json_val = json.dumps(value)
                            llm_config_parts.append(f"'{key}': '{json_val.replace("'", "''")}'")
                        except TypeError:
                             print(f"Warning: LLM parameter '{key}' could not be serialized. Skipping.")

            using_clauses.append(f"llm = {{ {', '.join(llm_config_parts)} }}")

        if save_to_table:
            using_clauses.append(f"save_to = {save_to_table}") # save_to_table is like 'datasource.table'

        query = f"EVALUATE KNOWLEDGE_BASE {kb_name} USING {', '.join(using_clauses)};"

        try:
            print(f"Executing evaluation for KB '{kb_name}'...")
            result_df = self.execute_sql(query)
            print(f"Evaluation for KB '{kb_name}' completed.")
            return result_df
        except Exception as e:
            print(f"Error evaluating Knowledge Base '{kb_name}': {str(e)}")
            return None

# Keep the __main__ block for direct testing
if __name__ == '__main__':
    print("Testing MindsDBHandler directly...")
    handler = MindsDBHandler()
    if handler.connect():
        print("\n--- Connected successfully ---")

        hn_test_name = f"test_hn_ds_final_{int(time.time())%10000}"
        print(f"\n--- Testing Create HackerNews DS: {hn_test_name} ---")
        handler.create_hackernews_datasource(hn_test_name)

        kb_test_name = f"test_kb_final_{int(time.time())%10000}"
        print(f"\n--- Testing Create KB: {kb_test_name} ---")
        ollama_base = getattr(config, 'OLLAMA_BASE_URL', "http://127.0.0.1:11434")
        ollama_embed = getattr(config, 'OLLAMA_EMBEDDING_MODEL', "nomic-embed-text")
        ollama_rerank = getattr(config, 'OLLAMA_RERANKING_MODEL', "llama3")

        if handler.create_knowledge_base(
            kb_test_name, "ollama", ollama_embed, ollama_base,
            "ollama", ollama_rerank, ollama_base ):
            print(f"KB {kb_test_name} created/exists.")

            if config.GOOGLE_GEMINI_API_KEY:
                agent_google_test_name = f"test_agent_g_{int(time.time())%10000}"
                print(f"\n--- Testing Create Google Agent: {agent_google_test_name} for KB {kb_test_name} ---")
                if handler.create_kb_agent(agent_google_test_name, kb_test_name, model_provider='google', model_name='gemini-pro'):
                    print(f"Agent {agent_google_test_name} created.")
                    print(f"\n--- Testing Query Google Agent: {agent_google_test_name} ---")
                    response = handler.query_kb_agent(agent_google_test_name, "What is a knowledge base?")
                    print(f"Google Agent Response: {response}")
            else:
                print("\n--- Skipping Google Agent tests (GOOGLE_GEMINI_API_KEY not set) ---")

            agent_ollama_test_name = f"test_agent_o_{int(time.time())%10000}"
            print(f"\n--- Testing Create Ollama Agent: {agent_ollama_test_name} for KB {kb_test_name} ---")
            ollama_agent_params = {'base_url': ollama_base.rstrip('/')}
            if handler.create_kb_agent(agent_ollama_test_name, kb_test_name,
                                       model_provider='ollama', model_name=ollama_rerank,
                                       agent_params=ollama_agent_params):
                print(f"Agent {agent_ollama_test_name} created.")
                print(f"\n--- Testing Query Ollama Agent: {agent_ollama_test_name} ---")
                response = handler.query_kb_agent(agent_ollama_test_name, "Explain knowledge bases simply.")
                print(f"Ollama Agent Response: {response}")

        else:
            print(f"KB {kb_test_name} creation failed, skipping agent tests for it.")
    else:
        print("\n--- Failed to connect to MindsDB. Handler tests aborted. ---")

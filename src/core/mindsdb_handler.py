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

    def create_knowledge_base(self, kb_name: str, embedding_model_provider: str, embedding_model_name: str, 
                             embedding_model_base_url: str = None, reranking_model_provider: str = None, 
                             reranking_model_name: str = None, reranking_model_base_url: str = None,
                             content_columns: list = None, metadata_columns: list = None, id_column: str = None):
        if not self.project: print("Error: MindsDB connection not established."); return False

        if embedding_model_base_url: embedding_model_base_url = embedding_model_base_url.rstrip('/')
        if reranking_model_base_url: reranking_model_base_url = reranking_model_base_url.rstrip('/')

        embedding_model_config_parts = [f'"provider": "{embedding_model_provider}"', f'"model_name": "{embedding_model_name}"']
        if embedding_model_base_url: embedding_model_config_parts.append(f'"base_url": "{embedding_model_base_url}"')
        embedding_model_config = ", ".join(embedding_model_config_parts)

        query = f"CREATE KNOWLEDGE_BASE {kb_name} USING embedding_model = {{ {embedding_model_config} }}"

        if reranking_model_provider and reranking_model_name:
            reranking_model_config_parts = [f'"provider": "{reranking_model_provider}"', f'"model_name": "{reranking_model_name}"']
            if reranking_model_base_url: reranking_model_config_parts.append(f'"base_url": "{reranking_model_base_url}"')
            reranking_model_config = ", ".join(reranking_model_config_parts)
            query += f", reranking_model = {{ {reranking_model_config} }}"
        
        # Add content_columns, metadata_columns, and id_column if specified
        if content_columns:
            content_columns_str = str(content_columns).replace("'", '"')  # Convert to JSON format
            query += f", content_columns = {content_columns_str}"
        
        if metadata_columns:
            metadata_columns_str = str(metadata_columns).replace("'", '"')  # Convert to JSON format
            query += f", metadata_columns = {metadata_columns_str}"
        
        if id_column:
            query += f", id_column = '{id_column}'"
        
        query += ";"
        try:
            self.execute_sql(query)
            print(f"Knowledge Base '{kb_name}' creation command executed.")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"Knowledge Base '{kb_name}' already exists."); return True
            print(f"Error creating Knowledge Base '{kb_name}': {str(e)}"); return False

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

    def insert_into_knowledge_base(self, kb_name: str, data: list[dict], content_column: str, metadata_columns: dict = None):
        if not self.project: print("Error: MindsDB connection not established."); return False
        if not data: print("No data provided for insertion."); return True
        column_names_for_sql = [content_column];
        if metadata_columns: column_names_for_sql.extend(metadata_columns.keys())
        values_list_str = []
        for record in data:
            if content_column not in record: print(f"Warning: Record missing content_column ('{content_column}'). Skipping: {record}"); continue
            value_tuple_parts = [f"'{str(record[content_column]).replace("'", "''")}'"]
            if metadata_columns:
                for kb_meta_col, data_key in metadata_columns.items():
                    val = record.get(data_key)
                    if val is None: value_tuple_parts.append("NULL")
                    elif isinstance(val, (int, float, bool)): value_tuple_parts.append(str(val))
                    else: value_tuple_parts.append(f"'{str(val).replace("'", "''")}'")
            values_list_str.append(f"({', '.join(value_tuple_parts)})")
        if not values_list_str: print("No valid data to insert after processing."); return False
        query = f"INSERT INTO {self.project.name}.{kb_name} ({', '.join(column_names_for_sql)}) VALUES {', '.join(values_list_str)};"
        try: self.execute_sql(query); print(f"Data inserted into KB '{kb_name}' successfully."); return True
        except Exception as e: print(f"Error inserting data into KB '{kb_name}': {str(e)}"); return False

    def select_from_knowledge_base(self, kb_name: str, query_text: str, metadata_filters: dict = None, limit: int = 5):
        if not self.project: print("Error: MindsDB connection not established."); return None
        sanitized_query_text = query_text.replace("'", "''")
        where_clauses = [f"content LIKE '{sanitized_query_text}'"]
        if metadata_filters:
            for col, val in metadata_filters.items():
                sanitized_val = str(val).replace("'", "''") if isinstance(val, str) else val
                where_clauses.append(f"{col} = '{sanitized_val}'" if isinstance(val, str) else f"{col} = {val}")
        query = f"SELECT * FROM {kb_name} WHERE {' AND '.join(where_clauses)}"
        if limit > 0: query += f" LIMIT {limit}"
        query += ";";
        try: results_df = self.execute_sql(query); print(f"Query from KB '{kb_name}' executed."); return results_df
        except Exception as e: print(f"Error querying KB '{kb_name}': {str(e)}"); return None

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
    def create_kb_agent(self, agent_name: str, kb_name: str, model_provider: str = 'google', model_name: str = 'gemini-pro', agent_params: dict = None):
        if not self.project:
            print("Error: MindsDB connection not established.")
            return False

        using_clauses = [
            f"knowledge_base = '{kb_name}'",
            f"model_name = '{model_name}'",
            f"provider = '{model_provider}'"
        ]

        processed_params = agent_params.copy() if agent_params else {}

        if model_provider == 'google':
            api_key_val = processed_params.pop('api_key', config.GOOGLE_GEMINI_API_KEY)
            if not api_key_val:
                print("Warning: Google Gemini API key not provided for agent. Creation might fail if not globally set in MindsDB.")
            else:
                 using_clauses.append(f"api_key = '{api_key_val}'")

        if model_provider == 'ollama':
            base_url_val = processed_params.pop('base_url', getattr(config, 'OLLAMA_BASE_URL', None))
            if base_url_val:
                using_clauses.append(f"base_url = '{base_url_val.rstrip('/')}'")
            else:
                print(f"Warning: base_url not provided for ollama agent '{agent_name}'. Defaulting to MindsDB's Ollama setup if any.")

        for key, value in processed_params.items():
            if key == 'base_url' and isinstance(value, str): value = value.rstrip('/')

            if isinstance(value, str):
                using_clauses.append(f"{key} = '{str(value).replace("'", "''")}'")
            elif isinstance(value, (int, float, bool)):
                using_clauses.append(f"{key} = {value}")
            else:
                try:
                    json_val = json.dumps(value)
                    using_clauses.append(f"{key} = '{json_val.replace("'", "''")}'")
                except TypeError:
                    print(f"Warning: Parameter '{key}' for agent '{agent_name}' could not be serialized. Skipping.")

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
        query = f"SELECT response FROM {agent_name} WHERE question = '{sanitized_question}';"
        print(f"Querying agent '{agent_name}' with question: '{question[:100]}...'")
        try:
            results_df = self.execute_sql(query)
            if results_df is not None and not results_df.empty:
                if 'response' in results_df.columns and len(results_df['response']) > 0:
                    return results_df['response'].iloc[0]
                else:
                    print(f"Warning: 'response' column not found in agent output. Columns: {results_df.columns.tolist()}. Returning full first row dict.")
                    return results_df.iloc[0].to_dict() if not results_df.empty else "Agent returned data but no 'response' column or rows."
            elif results_df is not None:
                print(f"Agent '{agent_name}' returned no results for the question.")
                return "Agent returned no results."
            else:
                print(f"Agent query for '{agent_name}' failed to return a DataFrame.")
                return None
        except Exception as e:
            print(f"Error querying agent '{agent_name}': {str(e)}")
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

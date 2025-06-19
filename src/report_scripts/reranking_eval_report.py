import argparse
import time
import datetime
import json
import sys
import os

# Adjust import path
# Calculate project root assuming script is in src/report_scripts/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from src.core.mindsdb_handler import MindsDBHandler
from config import config as app_config

# --- Configuration for the Reranking Evaluation ---
DEFAULT_KB_NO_RERANKER_NAME = "rerank_eval_kb_no_reranker"
DEFAULT_KB_WITH_RERANKER_NAME = "rerank_eval_kb_with_reranker"
DEFAULT_HN_DATASOURCE_RERANK = "hackernews"
DEFAULT_HN_TABLE_RERANK = "stories" # Source of data for KBs
DEFAULT_INGESTION_SIZE_RERANK = 500  # A reasonably sized dataset for evaluation

# Reranker model details (ensure these are sensible, e.g., from config)
RERANKER_PROVIDER = app_config.OLLAMA_RERANKING_MODEL.split('/')[0] if '/' in app_config.OLLAMA_RERANKING_MODEL else 'ollama'
RERANKER_MODEL_NAME = app_config.OLLAMA_RERANKING_MODEL.split('/')[-1] if '/' in app_config.OLLAMA_RERANKING_MODEL else app_config.OLLAMA_RERANKING_MODEL
RERANKER_BASE_URL = app_config.OLLAMA_BASE_URL

# Embedding model details (same for both KBs for fair comparison)
EMBEDDING_PROVIDER = app_config.OLLAMA_EMBEDDING_MODEL.split('/')[0] if '/' in app_config.OLLAMA_EMBEDDING_MODEL else 'ollama'
EMBEDDING_MODEL_NAME = app_config.OLLAMA_EMBEDDING_MODEL.split('/')[-1] if '/' in app_config.OLLAMA_EMBEDDING_MODEL else app_config.OLLAMA_EMBEDDING_MODEL
EMBEDDING_BASE_URL = app_config.OLLAMA_BASE_URL

# Content and metadata for ingestion (consistent with other reports if using same table)
CONTENT_COLUMN_NAME_RERANK = 'title' # From HackerNews 'stories'
METADATA_MAP_RERANK = {
    'story_id': 'id', 'author': 'by', 'submission_time': 'time', 'story_score': 'score', 'url': 'url'
}

# Define nuanced/ambiguous queries for evaluation
# These should be queries where reranking might make a difference.
EVALUATION_QUERIES = [
    {
        "id": "nuanced_query_1",
        "text": "ethical considerations of advanced artificial intelligence",
        "description": "Looking for discussions on AI ethics, not just AI capabilities."
    },
    {
        "id": "nuanced_query_2",
        "text": "impact of remote work on software development team productivity",
        "description": "Focus on productivity changes, not just remote work tools."
    },
    {
        "id": "ambiguous_query_1",
        "text": "apple new products", # Could be about fruit or tech
        "description": "Ambiguous term 'apple', context from HN should imply tech."
    },
    {
        "id": "complex_intent_query_1",
        "text": "startups using machine learning for climate change solutions",
        "description": "Multi-faceted: startups, ML, and climate change."
    }
]
DEFAULT_QUERY_LIMIT = 5 # Number of results per query to compare

class RerankingEvaluator:
    def __init__(self, kb_no_reranker_name, kb_with_reranker_name, hn_datasource, hn_table, ingestion_size):
        self.handler = MindsDBHandler()
        self.kb_no_reranker_name = kb_no_reranker_name
        self.kb_with_reranker_name = kb_with_reranker_name
        self.hn_datasource = hn_datasource
        self.hn_table = hn_table
        self.ingestion_size = ingestion_size

        self.report = {
            "reranking_evaluation_run_at": datetime.datetime.now().isoformat(),
            "environment": {
                "mindsdb_host": app_config.MINDSDB_HOST,
                "mindsdb_port": app_config.MINDSDB_PORT,
                "embedding_model": f"{EMBEDDING_PROVIDER}/{EMBEDDING_MODEL_NAME} (URL: {EMBEDDING_BASE_URL})",
                "reranker_model_used": f"{RERANKER_PROVIDER}/{RERANKER_MODEL_NAME} (URL: {RERANKER_BASE_URL}) for '{kb_with_reranker_name}'"
            },
            "parameters": {
                "kb_no_reranker": kb_no_reranker_name,
                "kb_with_reranker": kb_with_reranker_name,
                "data_source": f"{hn_datasource}.{hn_table}",
                "ingestion_size_per_kb": ingestion_size,
                "content_column": CONTENT_COLUMN_NAME_RERANK,
                "metadata_map": METADATA_MAP_RERANK,
                "evaluation_queries_count": len(EVALUATION_QUERIES),
                "results_limit_per_query": DEFAULT_QUERY_LIMIT
            },
            "evaluation_results": [] # List of comparisons for each query
        }
        self.is_connected = False

    def connect_to_mindsdb(self):
        print("Connecting to MindsDB for reranking evaluation...")
        if self.handler.connect():
            print("Successfully connected to MindsDB.")
            self.is_connected = True
        else:
            print("Failed to connect to MindsDB. Aborting evaluation.")
        return self.is_connected

    def _setup_kb(self, kb_name, use_reranker):
        print(f"Setting up KB: {kb_name} (Reranker: {use_reranker})...")
        # Drop if exists
        try:
            self.handler.execute_sql(f"DROP KNOWLEDGE_BASE IF EXISTS {kb_name};")
            print(f"  Dropped KB '{kb_name}' if it existed.")
            time.sleep(5)
        except Exception as e:
            print(f"  Warning: Failed to drop KB '{kb_name}': {e}")

        rerank_provider_arg = RERANKER_PROVIDER if use_reranker else None
        rerank_model_arg = RERANKER_MODEL_NAME if use_reranker else None
        rerank_url_arg = RERANKER_BASE_URL if use_reranker else None

        created = self.handler.create_knowledge_base(
            kb_name,
            embedding_model_provider=EMBEDDING_PROVIDER, embedding_model_name=EMBEDDING_MODEL_NAME, embedding_model_base_url=EMBEDDING_BASE_URL,
            reranking_model_provider=rerank_provider_arg, reranking_model_name=rerank_model_arg, reranking_model_base_url=rerank_url_arg
        )
        if not created:
            print(f"  ERROR: Failed to create KB '{kb_name}'. Cannot proceed with this KB.")
            return False

        print(f"  KB '{kb_name}' created. Waiting a moment...")
        time.sleep(2)
        indexed = self.handler.create_index_on_knowledge_base(kb_name)
        if not indexed:
            print(f"  Warning: Index creation for '{kb_name}' might have failed or is processing.")

        print(f"  Waiting for potential index building for '{kb_name}' (e.g., 30s)...")
        time.sleep(30) # Adjust as needed
        return True

    def _ingest_data_into_kb(self, kb_name):
        print(f"  Ingesting {self.ingestion_size} records into '{kb_name}' from {self.hn_datasource}.{self.hn_table}...")

        select_cols_list = [CONTENT_COLUMN_NAME_RERANK] + list(METADATA_MAP_RERANK.values())
        select_cols_str = ", ".join(sorted(list(set(select_cols_list)))))
        # Fetch a consistent set of data if possible, e.g., latest N, or specific IDs.
        # For this eval, ORDER BY id ASC (or DESC) then LIMIT is good for consistency.
        fetch_query = f"SELECT {select_cols_str} FROM {self.hn_datasource}.{self.hn_table} ORDER BY id ASC LIMIT {self.ingestion_size}"

        try:
            source_data_df = self.handler.execute_sql(fetch_query)
            if source_data_df is None or source_data_df.empty or len(source_data_df) < self.ingestion_size:
                print(f"  ERROR: Failed to fetch sufficient data ({len(source_data_df) if source_data_df is not None else 0}/{self.ingestion_size} records). Cannot proceed with '{kb_name}'.")
                return False
            source_data_list = source_data_df.to_dict('records')
        except Exception as e:
            print(f"  ERROR: Data fetching error for '{kb_name}': {e}")
            return False

        ingested = self.handler.insert_into_knowledge_base(
            kb_name, source_data_list,
            content_column=CONTENT_COLUMN_NAME_RERANK,
            metadata_columns=METADATA_MAP_RERANK
        )
        if ingested:
            print(f"  Ingestion into '{kb_name}' successful.")
            # Wait for embeddings to process if async
            print(f"  Waiting after ingestion for '{kb_name}' (e.g., 30s)...")
            time.sleep(30)
            return True
        else:
            print(f"  ERROR: Ingestion into '{kb_name}' failed as per handler.")
            return False

    def prepare_kbs(self):
        if not self.is_connected: return False

        print("\n\n--- Preparing Knowledge Bases for Reranking Evaluation ---")
        kb1_ok = self._setup_kb(self.kb_no_reranker_name, use_reranker=False)
        if kb1_ok:
            kb1_ok = self._ingest_data_into_kb(self.kb_no_reranker_name)

        kb2_ok = self._setup_kb(self.kb_with_reranker_name, use_reranker=True)
        if kb2_ok:
            kb2_ok = self._ingest_data_into_kb(self.kb_with_reranker_name)

        if not (kb1_ok and kb2_ok):
            print("ERROR: One or both KBs could not be prepared. Aborting evaluation.")
            return False

        print("Both KBs prepared and ingested with data.")
        return True

    def run_evaluation_queries(self):
        if not self.is_connected: return
        print("\n\n--- Running Evaluation Queries ---")

        for query_info in EVALUATION_QUERIES:
            query_id = query_info["id"]
            query_text = query_info["text"]
            query_desc = query_info["description"]

            print(f"\n\nEvaluating Query ID: {query_id} - \"{query_text}\"")
            print(f"  Description: {query_desc}")

            results_no_reranker_df = self.handler.select_from_knowledge_base(
                self.kb_no_reranker_name, query_text, limit=DEFAULT_QUERY_LIMIT
            )
            results_with_reranker_df = self.handler.select_from_knowledge_base(
                self.kb_with_reranker_name, query_text, limit=DEFAULT_QUERY_LIMIT
            )

            # Convert DataFrames to list of dicts for JSON report
            # Only include relevant columns for easier comparison, e.g., content, score, and key metadata.
            relevant_cols = [CONTENT_COLUMN_NAME_RERANK] + list(METADATA_MAP_RERANK.keys()) + ['score'] # 'score' is often returned by KBs

            def format_results(df):
                if df is None or df.empty: return []
                # Ensure we only try to access columns that exist in the DataFrame
                cols_to_select = [col for col in relevant_cols if col in df.columns]
                return df[cols_to_select].to_dict('records')

            query_comparison = {
                "query_id": query_id,
                "query_text": query_text,
                "query_description": query_desc,
                "results_no_reranker": format_results(results_no_reranker_df),
                "results_with_reranker": format_results(results_with_reranker_df),
                "qualitative_analysis_notes": "TODO: User to fill in - Compare results and explain differences, impact of reranker."
            }
            self.report["evaluation_results"].append(query_comparison)

            # Print side-by-side for immediate review (optional)
            print(f"  Results for '{self.kb_no_reranker_name}' (No Reranker):")
            print(results_no_reranker_df[[col for col in [CONTENT_COLUMN_NAME_RERANK, 'score'] if col in results_no_reranker_df.columns]].head(DEFAULT_QUERY_LIMIT).to_string() if results_no_reranker_df is not None and not results_no_reranker_df.empty else "  No results or error.")
            print(f"  Results for '{self.kb_with_reranker_name}' (With Reranker):")
            print(results_with_reranker_df[[col for col in [CONTENT_COLUMN_NAME_RERANK, 'score'] if col in results_with_reranker_df.columns]].head(DEFAULT_QUERY_LIMIT).to_string() if results_with_reranker_df is not None and not results_with_reranker_df.empty else "  No results or error.")

    def print_evaluation_report(self):
        print("\n\n--- Reranking Evaluation Report ---")
        print(json.dumps(self.report, indent=2))
        report_filename = f"reranking_evaluation_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"\nReranking evaluation report saved to {report_filename}")
        print("\nACTION REQUIRED: Please open the JSON report and fill in the 'qualitative_analysis_notes' for each query.")

    def run_full_evaluation(self):
        if not self.connect_to_mindsdb():
            return

        if not self.prepare_kbs():
            self.print_evaluation_report() # Print partial report if KBs failed
            return

        self.run_evaluation_queries()
        self.print_evaluation_report()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MindsDB Knowledge Base Reranking Evaluation.")
    parser.add_argument("--kb-no-reranker", default=DEFAULT_KB_NO_RERANKER_NAME, help="Name for KB without reranker.")
    parser.add_argument("--kb-with-reranker", default=DEFAULT_KB_WITH_RERANKER_NAME, help="Name for KB with reranker.")
    parser.add_argument("--hn-datasource", default=DEFAULT_HN_DATASOURCE_RERANK, help="HackerNews datasource name.")
    parser.add_argument("--hn-table", default=DEFAULT_HN_TABLE_RERANK, help="HackerNews table for ingestion.")
    parser.add_argument("--ingestion-size", type=int, default=DEFAULT_INGESTION_SIZE_RERANK, help="Number of records to ingest into each KB.")

    args = parser.parse_args()

    print("--- Starting Reranking Evaluation ---")
    print(f"Parameters: {vars(args)}")

    evaluator = RerankingEvaluator(
        kb_no_reranker_name=args.kb_no_reranker,
        kb_with_reranker_name=args.kb_with_reranker,
        hn_datasource=args.hn_datasource,
        hn_table=args.hn_table,
        ingestion_size=args.ingestion_size
    )
    evaluator.run_full_evaluation()
    print("--- Reranking Evaluation Finished ---")

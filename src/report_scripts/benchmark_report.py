import argparse
import time
import datetime
import statistics
import json
import sys
import os

# Adjust import path to access src and config
# This assumes the script is run from the root of the project,
# or PYTHONPATH is set up to find mindsdb_cli and config.
# Calculate project root assuming script is in src/report_scripts/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from src.core.mindsdb_handler import MindsDBHandler
from config import config as app_config # For OLLAMA_BASE_URL etc. if needed for KB creation

# --- Configuration for the Benchmark ---
# These can be overridden by command-line arguments
DEFAULT_KB_NAME = "benchmark_kb"
DEFAULT_HN_DATASOURCE = "hackernews" # Assumes this is created e.g. via 'mindsdb-cli setup hackernews'
DEFAULT_HN_TABLE_FOR_INGESTION = "stories" # Table to fetch data from
DEFAULT_INGESTION_SIZE_INITIAL = 100 # Number of records for initial ingestion test
DEFAULT_INGESTION_SIZE_SCALED = [1000, 5000, 10000] # Number of records for scaled ingestion tests
DEFAULT_NUM_QUERIES = 20 # Number of times to run each test query for latency measurement

# Define content and metadata mapping for ingestion
# This should match the structure of DEFAULT_HN_TABLE_FOR_INGESTION ('stories')
# And how the KB is intended to be used.
# For 'stories': title, id, by, time, score, url, text.
# We'll map 'title' to content, and 'id', 'by', 'time', 'score' as metadata.
CONTENT_COLUMN_NAME = 'title' # From HackerNews 'stories' table
METADATA_MAP_FOR_INGESTION = {
    'story_id': 'id',
    'author': 'by',
    'submission_time': 'time',
    'story_score': 'score'
}
# Ensure the KB is created to accept these fields.
# The insert_into_knowledge_base method in handler will use these keys.

# Example queries for latency testing (semantic and with metadata)
# These queries should be relevant to the ingested data (HackerNews stories)
QUERIES_FOR_LATENCY_TEST = [
    {"type": "semantic_only", "text": "artificial intelligence trends"},
    {"type": "semantic_only", "text": "python programming new libraries"},
    {"type": "semantic_metadata", "text": "database performance", "filters": {"author": "pg"}}, # Assuming 'pg' is a known author
    {"type": "semantic_metadata", "text": "startup funding", "filters": {"story_score_gt": 100}} # Example: score > 100
]
# Note: The filter `story_score_gt` implies the select_from_knowledge_base might need to support `>` operator.
# Current handler's select_from_knowledge_base supports '=', let's simplify filter for now or assume it's handled.
# For simplicity, let's stick to '=' for metadata filters in this benchmark or note the assumption.
# Let's use a filter that works with current handler:
QUERIES_FOR_LATENCY_TEST[2] = {"type": "semantic_metadata", "text": "database performance", "filters": {"author": "pg"}}
QUERIES_FOR_LATENCY_TEST[3] = {"type": "semantic_metadata", "text": "startup funding", "filters": {"story_score": 150}} # Exact match for simplicity


class PerformanceBenchmark:
    def __init__(self, kb_name, hn_datasource, hn_table, ingestion_sizes, num_queries):
        self.handler = MindsDBHandler()
        self.kb_name = kb_name
        self.hn_datasource = hn_datasource
        self.hn_table = hn_table
        self.ingestion_sizes = ingestion_sizes # This should be a list: [initial_size] + scaled_sizes
        self.num_queries_per_type = num_queries
        self.report = {
            "benchmark_run_at": datetime.datetime.now().isoformat(),
            "environment": {
                "mindsdb_host": app_config.MINDSDB_HOST,
                "mindsdb_port": app_config.MINDSDB_PORT,
                # Potentially add MindsDB version here if accessible
            },
            "parameters": {
                "kb_name": kb_name,
                "hn_datasource": hn_datasource,
                "hn_table_for_ingestion": hn_table,
                "content_column": CONTENT_COLUMN_NAME,
                "metadata_map": METADATA_MAP_FOR_INGESTION,
                "ingestion_sizes_tested": self.ingestion_sizes,
                "num_latency_queries_per_type": num_queries
            },
            "results": {
                "kb_setup_time_seconds": None,
                "ingestion_performance": [],
                "query_latency": []
            }
        }
        self.is_connected = False

    def connect_to_mindsdb(self):
        print("Connecting to MindsDB...")
        if self.handler.connect():
            print("Successfully connected to MindsDB.")
            self.is_connected = True
        else:
            print("Failed to connect to MindsDB. Aborting benchmark.")
            self.is_connected = False
        return self.is_connected

    def setup_knowledge_base(self):
        if not self.is_connected: return False
        print(f"Setting up Knowledge Base: {self.kb_name}...")
        start_time = time.time()

        # Using default Ollama models from config for KB creation
        # This assumes the user has Ollama running if these are the defaults
        created = self.handler.create_knowledge_base(
            self.kb_name,
            embedding_model_provider=app_config.OLLAMA_EMBEDDING_MODEL.split('/')[0] if '/' in app_config.OLLAMA_EMBEDDING_MODEL else 'ollama', # simplistic provider parse
            embedding_model_name=app_config.OLLAMA_EMBEDDING_MODEL.split('/')[-1] if '/' in app_config.OLLAMA_EMBEDDING_MODEL else app_config.OLLAMA_EMBEDDING_MODEL,
            embedding_model_base_url=app_config.OLLAMA_BASE_URL,
            reranking_model_provider=app_config.OLLAMA_RERANKING_MODEL.split('/')[0] if '/' in app_config.OLLAMA_RERANKING_MODEL else 'ollama',
            reranking_model_name=app_config.OLLAMA_RERANKING_MODEL.split('/')[-1] if '/' in app_config.OLLAMA_RERANKING_MODEL else app_config.OLLAMA_RERANKING_MODEL,
            reranking_model_base_url=app_config.OLLAMA_BASE_URL
        )
        # A small delay to ensure KB is ready before index creation
        time.sleep(2)

        if created:
            # Explicitly create/refresh index
            indexed = self.handler.create_index_on_knowledge_base(self.kb_name)
            if not indexed:
                print(f"Warning: Index creation for {self.kb_name} might have failed or is processing.")
            # Allow some time for index to build, crucial for KBs
            print("Waiting for potential index building (e.g., 30 seconds)...")
            time.sleep(30) # Adjust as needed
        else:
            print(f"Failed to create Knowledge Base {self.kb_name}. It might already exist or an error occurred.")
            # If it already exists, we can proceed, but the setup time won't be for creation.
            # For a clean benchmark, it's better to drop and recreate, or use a unique name.
            # For simplicity, we assume 'created' means it's ready or was already there and okay.

        end_time = time.time()
        self.report["results"]["kb_setup_time_seconds"] = round(end_time - start_time, 3)
        print(f"KB setup/verification took {self.report['results']['kb_setup_time_seconds']:.3f} seconds.")
        return True # Assume success if no critical failure

    def measure_ingestion_performance(self, num_records_to_ingest):
        if not self.is_connected: return
        print(f"Measuring ingestion performance for {num_records_to_ingest} records from {self.hn_datasource}.{self.hn_table}...")

        # Fetch data from HackerNews
        select_cols_list = [CONTENT_COLUMN_NAME] + list(METADATA_MAP_FOR_INGESTION.values())
        select_cols_str = ", ".join(sorted(list(set(select_cols_list))))

        fetch_query = f"SELECT {select_cols_str} FROM {self.hn_datasource}.{self.hn_table} ORDER BY id DESC LIMIT {num_records_to_ingest}"
        # ORDER BY id DESC (or time DESC) helps get more recent, somewhat consistent data for tests.

        print(f"Fetching {num_records_to_ingest} records using: {fetch_query}")
        try:
            source_data_df = self.handler.execute_sql(fetch_query)
            if source_data_df is None or source_data_df.empty:
                print(f"Failed to fetch data for ingestion ({num_records_to_ingest} records). Skipping this size.")
                return

            actual_fetched_count = len(source_data_df)
            if actual_fetched_count < num_records_to_ingest:
                print(f"Warning: Fetched only {actual_fetched_count} records, requested {num_records_to_ingest}.")
            if actual_fetched_count == 0:
                print("No records fetched. Cannot proceed with ingestion test for this size.")
                return

            source_data_list = source_data_df.to_dict('records')
        except Exception as e:
            print(f"Error fetching data for ingestion: {e}. Skipping this size.")
            return

        start_time = time.time()
        try:
            # content_column here is the key in source_data_list dicts that holds the content.
            # metadata_columns is the map from KB metadata names to keys in source_data_list dicts.
            ingested = self.handler.insert_into_knowledge_base(
                self.kb_name,
                source_data_list,
                content_column=CONTENT_COLUMN_NAME, # This is the key from HackerNews data
                metadata_columns=METADATA_MAP_FOR_INGESTION
            )
            if not ingested:
                print(f"Ingestion of {actual_fetched_count} records reported failure by handler.")
                # Continue to record time, but note failure
        except Exception as e:
            print(f"Error during ingestion process: {e}")
            # Continue to record time, but note failure
            ingested = False

        end_time = time.time()
        duration = round(end_time - start_time, 3)
        time_per_1k = round((duration / actual_fetched_count) * 1000, 3) if actual_fetched_count > 0 else 0

        ingestion_result = {
            "dataset_size_requested": num_records_to_ingest,
            "dataset_size_actual": actual_fetched_count,
            "total_ingestion_time_seconds": duration,
            "time_per_1k_records_seconds": time_per_1k,
            "ingestion_successful": ingested and actual_fetched_count > 0
        }
        self.report["results"]["ingestion_performance"].append(ingestion_result)
        print(f"Ingestion of {actual_fetched_count} records took {duration}s ({time_per_1k}s per 1k). Success: {ingestion_result['ingestion_successful']}")

    def measure_query_latency(self):
        if not self.is_connected: return
        print(f"Measuring query latency ({self.num_queries_per_type} iterations per query type)...")

        for query_template in QUERIES_FOR_LATENCY_TEST:
            latencies = []
            query_text = query_template["text"]
            metadata_filters = query_template.get("filters")
            query_type_label = query_template["type"]

            print(f"  Testing query type '{query_type_label}': "{query_text}" with filters {metadata_filters}")

            for i in range(self.num_queries_per_type):
                start_time = time.time()
                try:
                    results_df = self.handler.select_from_knowledge_base(
                        self.kb_name,
                        query_text,
                        metadata_filters=metadata_filters,
                        limit=5 # Typical limit for latency tests
                    )
                    # We are interested in time, not correctness here, but good to check if results were returned
                    if results_df is None: # Error occurred
                        print(f"    Run {i+1}/{self.num_queries_per_type}: Query failed or returned None.")
                        # Decide how to handle failed queries in latency stats (e.g., exclude or record as high latency)
                        # For now, we'll record the time taken until failure, or skip if it's too disruptive.
                        # If select_from_knowledge_base raises exception, it's caught below.
                        # If it returns None without exception, it's an issue.
                        pass # Latency will be recorded.
                except Exception as e:
                    print(f"    Run {i+1}/{self.num_queries_per_type}: Exception during query: {e}")
                    # Exclude this run from latency stats or assign a penalty? For now, just note and continue.
                    # The time taken will be recorded up to the point of failure.

                end_time = time.time()
                latencies.append(end_time - start_time)
                time.sleep(0.1) # Small delay between queries to avoid overwhelming the server

            if latencies:
                avg_latency = round(statistics.mean(latencies), 4)
                p95_latency = round(sorted(latencies)[int(len(latencies) * 0.95)], 4) if len(latencies) >= 20 else avg_latency # Approx p95
                p99_latency = round(sorted(latencies)[int(len(latencies) * 0.99)], 4) if len(latencies) >= 100 else avg_latency # Approx p99
                min_latency = round(min(latencies), 4)
                max_latency = round(max(latencies), 4)
            else:
                avg_latency = p95_latency = p99_latency = min_latency = max_latency = 0
                print(f"    No successful queries recorded for type '{query_type_label}'.")

            latency_result = {
                "query_type": query_type_label,
                "query_text": query_text,
                "metadata_filters": metadata_filters,
                "iterations": len(latencies), # Could be less than num_queries_per_type if errors
                "avg_latency_seconds": avg_latency,
                "p95_latency_seconds": p95_latency,
                "p99_latency_seconds": p99_latency,
                "min_latency_seconds": min_latency,
                "max_latency_seconds": max_latency,
                "individual_latencies": [round(l, 4) for l in latencies] # Optional: include all latencies
            }
            self.report["results"]["query_latency"].append(latency_result)
            print(f"  Latency for '{query_type_label}': Avg={avg_latency}s, P95={p95_latency}s, P99={p99_latency}s")

    def print_report(self):
        print("\n\n--- Performance Benchmark Report ---")
        # Pretty print JSON for now. Could format as Markdown later.
        print(json.dumps(self.report, indent=2))
        # Optionally, save to a file
        report_filename = f"benchmark_report_{self.kb_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"\nReport saved to {report_filename}")

    def run_benchmark(self):
        if not self.connect_to_mindsdb():
            return

        # 1. Setup KB (Create and Index)
        # Consider dropping KB if it exists for a clean run:
        # print(f"Attempting to drop existing KB '{self.kb_name}' for a clean run...")
        # try: self.handler.execute_sql(f"DROP KNOWLEDGE_BASE {self.kb_name};")
        # except Exception: pass # Ignore if it doesn't exist or fails
        # time.sleep(2) # Give time for drop operation

        if not self.setup_knowledge_base():
            print("Failed to setup Knowledge Base. Aborting benchmark.")
            return

        # 2. Measure Ingestion Performance for various sizes
        for size in self.ingestion_sizes:
            self.measure_ingestion_performance(size)
            # Optional: Re-index or wait after large ingestions if it impacts query performance
            # print("Waiting after ingestion (e.g., 10 seconds) for system to stabilize...")
            # time.sleep(10)

        # 3. Measure Query Latency (after all ingestion is done or after a specific baseline ingestion)
        # If testing query latency vs dataset size, this needs to be in the loop above.
        # For now, query latency is measured after the LAST ingestion size.
        # This means KB contains sum of all ingested records if not cleared.
        # For isolated tests, KB should be cleared & re-populated for each ingestion_size test.
        # Current implementation: KB grows with each ingestion step. Query test is on final state.
        # To test query latency on KB of `size`, clear and ingest `size` records before `measure_query_latency`.
        # For simplicity of this first script, we do one sequence of ingestions, then one query test.
        # Let's refine: Test query latency after the *initial* ingestion size for a baseline.
        # Re-running setup_knowledge_base and measure_ingestion_performance(initial_size)
        # before measure_query_latency would ensure a clean state for query tests.
        # Or, ensure the KB is cleared and populated with a defined number of records before latency tests.

        # Let's adjust: for query latency, ensure KB has a known state, e.g., populated with initial_size records.
        # This requires clearing the KB or re-creating it.
        # For this script, we'll test query latency on the KB state after all ingestion_sizes have been added.
        # This means the KB is at its largest. User should be aware.
        # A better approach would be to parameterize the KB state for query tests.

        # If no records were ingested at all, query latency tests might not be meaningful.
        total_ingested_successfully = sum(
            r['dataset_size_actual'] for r in self.report['results']['ingestion_performance'] if r['ingestion_successful']
        )
        if total_ingested_successfully > 0 :
            self.measure_query_latency()
        else:
            print("Skipping query latency tests as no data was successfully ingested.")

        # 4. Print Report
        self.print_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MindsDB Knowledge Base Performance Benchmark.")
    parser.add_argument("--kb-name", default=DEFAULT_KB_NAME, help="Name of the Knowledge Base to use/create.")
    parser.add_argument("--hn-datasource", default=DEFAULT_HN_DATASOURCE, help="HackerNews datasource name.")
    parser.add_argument("--hn-table", default=DEFAULT_HN_TABLE_FOR_INGESTION, help="HackerNews table for ingestion.")
    parser.add_argument("--ingestion-sizes", nargs='+', type=int, default=[DEFAULT_INGESTION_SIZE_INITIAL] + DEFAULT_INGESTION_SIZE_SCALED, help="List of ingestion sizes to test.")
    parser.add_argument("--num-queries", type=int, default=DEFAULT_NUM_QUERIES, help="Number of iterations for each latency query.")

    args = parser.parse_args()

    print("--- Starting Performance Benchmark ---")
    print(f"Parameters: KB Name='{args.kb_name}', HN Datasource='{args.hn_datasource}', HN Table='{args.hn_table}', Ingestion Sizes={args.ingestion_sizes}, Num Queries/Type={args.num_queries}")

    benchmark = PerformanceBenchmark(
        kb_name=args.kb_name,
        hn_datasource=args.hn_datasource,
        hn_table=args.hn_table,
        ingestion_sizes=sorted(list(set(args.ingestion_sizes))), # Ensure unique and sorted sizes
        num_queries=args.num_queries
    )
    benchmark.run_benchmark()
    print("--- Performance Benchmark Finished ---")

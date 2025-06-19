import argparse
import time
import datetime
import json
import sys
import os
import random
import string

# Adjust import path
# Calculate project root assuming script is in src/report_scripts/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
sys.path.insert(0, project_root)

from src.core.mindsdb_handler import MindsDBHandler
from config import config as app_config

# --- Configuration for the Stress Test ---
DEFAULT_KB_NAME_STRESS = "stress_test_kb"
DEFAULT_HN_DATASOURCE_STRESS = "hackernews"
DEFAULT_HN_TABLE_STRESS = "stories"

# Stress Test Parameters (can be overridden by CLI args)
INITIAL_INGESTION_LOAD = 10000       # Start with a larger base load
INCREMENTAL_INGESTION_STEPS = [20000, 50000, 100000] # Records to add in steps
MAX_RECORDS_TO_ATTEMPT_INGEST = 200000 # A ceiling for ingestion

CONCURRENT_QUERY_SIMULATION_COUNT = 5 # Number of "threads" for sequential simulation
QUERIES_PER_SIMULATED_THREAD = 10     # Queries each simulated thread will run

COMPLEX_QUERY_COUNT = 20 # Number of complex queries to run
COMPLEX_QUERY_MAX_TERMS = 50 # Max terms in a randomly generated complex query

# Content and metadata for ingestion (same as benchmark for consistency if using same table)
CONTENT_COLUMN_NAME_STRESS = 'title'
METADATA_MAP_STRESS = {
    'story_id': 'id', 'author': 'by', 'submission_time': 'time', 'story_score': 'score'
}

# Example base queries for stress testing (will be repeated/modified)
BASE_STRESS_QUERIES = [
    "technology and software development",
    "global economic trends and analysis",
    "artificial intelligence impact on society"
]

class StressTester:
    def __init__(self, kb_name, hn_datasource, hn_table, initial_load, incremental_steps, max_records,
                 concurrent_sim_count, queries_per_thread, complex_query_count, complex_query_terms):
        self.handler = MindsDBHandler()
        self.kb_name = kb_name
        self.hn_datasource = hn_datasource
        self.hn_table = hn_table

        self.initial_ingestion_load = initial_load
        self.incremental_ingestion_steps = incremental_steps
        self.max_records_to_attempt_ingest = max_records

        self.concurrent_query_simulation_count = concurrent_sim_count
        self.queries_per_simulated_thread = queries_per_thread
        self.complex_query_count = complex_query_count
        self.complex_query_max_terms = complex_query_terms

        self.report = {
            "stress_test_run_at": datetime.datetime.now().isoformat(),
            "environment": {
                "mindsdb_host": app_config.MINDSDB_HOST,
                "mindsdb_port": app_config.MINDSDB_PORT,
            },
            "parameters": {
                "kb_name": kb_name,
                "hn_datasource": hn_datasource,
                "hn_table_for_ingestion": hn_table,
                "initial_ingestion_load": self.initial_ingestion_load,
                "incremental_ingestion_steps": self.incremental_ingestion_steps,
                "max_records_to_attempt_ingest": self.max_records_to_attempt_ingest,
                "concurrent_query_simulation_count": self.concurrent_query_simulation_count,
                "queries_per_simulated_thread": self.queries_per_simulated_thread,
                "complex_query_count": self.complex_query_count,
                "complex_query_max_terms": self.complex_query_max_terms,
            },
            "observations": [], # List of dicts detailing each step and outcome
            "summary": {
                "total_records_ingested_successfully": 0,
                "ingestion_failures": 0,
                "query_failures": 0,
                "performance_degradation_points": [], # Describe points where things slowed or failed
                "failure_modes_observed": [] # Describe types of failures
            }
        }
        self.is_connected = False
        self.total_ingested_count = 0

    def connect_to_mindsdb(self):
        print("Connecting to MindsDB for stress test...")
        if self.handler.connect():
            print("Successfully connected to MindsDB.")
            self.is_connected = True
        else:
            print("Failed to connect to MindsDB. Aborting stress test.")
        return self.is_connected

    def _log_observation(self, step_name, status, duration_seconds=None, details=None, error_message=None):
        observation = {
            "step": step_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "status": status, # "success", "failure", "warning"
            "duration_seconds": round(duration_seconds, 3) if duration_seconds is not None else None,
            "details": details or {},
            "error_message": error_message
        }
        self.report["observations"].append(observation)
        print(f"  [{status.upper()}] {step_name} - Details: {details} - Error: {error_message if error_message else 'N/A'}")
        if status == "failure":
            if "ingestion" in step_name.lower():
                self.report["summary"]["ingestion_failures"] += 1
            elif "query" in step_name.lower():
                self.report["summary"]["query_failures"] += 1


    def setup_kb_for_stress_test(self):
        if not self.is_connected: return False
        print(f"Setting up Knowledge Base: {self.kb_name} for stress test...")
        # Drop if exists for a clean start
        try:
            print(f"  Attempting to drop existing KB '{self.kb_name}'...")
            self.handler.execute_sql(f"DROP KNOWLEDGE_BASE IF EXISTS {self.kb_name};")
            time.sleep(5) # Allow time for drop
            self._log_observation("Drop KB (if exists)", "success", details={"kb_name": self.kb_name})
        except Exception as e:
            self._log_observation("Drop KB (if exists)", "warning", details={"kb_name": self.kb_name}, error_message=str(e))

        start_time = time.time()
        created = self.handler.create_knowledge_base(
            self.kb_name,
            embedding_model_provider='ollama', embedding_model_name=app_config.OLLAMA_EMBEDDING_MODEL, embedding_model_base_url=app_config.OLLAMA_BASE_URL,
            reranking_model_provider='ollama', reranking_model_name=app_config.OLLAMA_RERANKING_MODEL, reranking_model_base_url=app_config.OLLAMA_BASE_URL
        )
        duration = time.time() - start_time

        if created:
            self._log_observation("Create KB", "success", duration, {"kb_name": self.kb_name})
            time.sleep(2)
            indexed = self.handler.create_index_on_knowledge_base(self.kb_name) # Assumes default index
            if indexed:
                self._log_observation("Create KB Index", "success", details={"kb_name": self.kb_name})
                print("  Waiting for KB index to build (e.g., 30s initial)...")
                time.sleep(30)
            else:
                self._log_observation("Create KB Index", "warning", details={"kb_name": self.kb_name}, error_message="Index command failed or did not confirm.")
            return True
        else:
            self._log_observation("Create KB", "failure", duration, {"kb_name": self.kb_name}, error_message="KB creation failed.")
            self.report["summary"]["failure_modes_observed"].append("KB_CREATION_FAILURE")
            return False

    def _ingest_data_batch(self, num_records, batch_id):
        step_name = f"Ingest Batch {batch_id} ({num_records} records)"
        print(f"  {step_name} from {self.hn_datasource}.{self.hn_table}...")

        select_cols_list = [CONTENT_COLUMN_NAME_STRESS] + list(METADATA_MAP_STRESS.values())
        select_cols_str = ", ".join(sorted(list(set(select_cols_list)))))
        fetch_query = f"SELECT {select_cols_str} FROM {self.hn_datasource}.{self.hn_table} ORDER BY RANDOM() LIMIT {num_records}"
        # Using ORDER BY RANDOM() to get different data slices, though can be slow on large tables.
        # For very large tables, `OFFSET` with `LIMIT` might be better if `RANDOM()` is too slow,
        # but `OFFSET` can also be slow. Or select by ID ranges if IDs are somewhat sequential.

        try:
            source_data_df = self.handler.execute_sql(fetch_query)
            if source_data_df is None or source_data_df.empty:
                self._log_observation(step_name, "warning", details={"requested": num_records, "fetched": 0}, error_message="No data fetched.")
                return False
            actual_fetched = len(source_data_df)
            source_data_list = source_data_df.to_dict('records')
        except Exception as e:
            self._log_observation(step_name, "failure", details={"requested": num_records}, error_message=f"Data fetching error: {str(e)}")
            self.report["summary"]["failure_modes_observed"].append("DATA_FETCHING_FAILURE")
            return False

        start_time = time.time()
        ingested_successfully = False
        try:
            ingested_successfully = self.handler.insert_into_knowledge_base(
                self.kb_name, source_data_list,
                content_column=CONTENT_COLUMN_NAME_STRESS,
                metadata_columns=METADATA_MAP_STRESS
            )
        except Exception as e:
            duration = time.time() - start_time
            self._log_observation(step_name, "failure", duration, {"requested": num_records, "actual_inserted": 0}, error_message=f"Ingestion error: {str(e)}")
            self.report["summary"]["failure_modes_observed"].append("KB_INSERTION_EXCEPTION")
            # Check if latency is unacceptable
            if duration > 600: # Example: 10 minutes for a batch
                self.report["summary"]["performance_degradation_points"].append(f"High ingestion latency ({duration}s) for batch {batch_id} ({actual_fetched} records)")
            return False

        duration = time.time() - start_time
        if ingested_successfully:
            self.total_ingested_count += actual_fetched
            self.report["summary"]["total_records_ingested_successfully"] = self.total_ingested_count
            self._log_observation(step_name, "success", duration, {"requested": num_records, "actual_inserted": actual_fetched, "total_in_kb": self.total_ingested_count})
            # Check for performance degradation
            time_per_record = duration / actual_fetched if actual_fetched > 0 else float('inf')
            if time_per_record > 1.0: # Example: more than 1 second per record avg
                 self.report["summary"]["performance_degradation_points"].append(f"Ingestion rate degradation: {time_per_record:.2f}s/record for batch {batch_id} ({actual_fetched} records)")
            return True
        else:
            self._log_observation(step_name, "failure", duration, {"requested": num_records, "actual_inserted": 0}, error_message="Handler reported ingestion failure.")
            self.report["summary"]["failure_modes_observed"].append("KB_INSERTION_HANDLER_FAILURE")
            return False

    def run_large_ingestion_stress(self):
        if not self.is_connected: return
        print("\n\n--- Running Large Ingestion Stress Test ---")

        # Initial load
        print(f"Starting with initial ingestion load of {self.initial_ingestion_load} records.")
        if not self._ingest_data_batch(self.initial_ingestion_load, "initial"):
            print("Initial ingestion failed. Stress test may be compromised.")
            # Decide whether to stop or continue

        # Incremental loads
        batch_num = 1
        for increment_size in self.incremental_ingestion_steps:
            if self.total_ingested_count >= self.max_records_to_attempt_ingest:
                print(f"Reached max records to attempt ({self.max_records_to_attempt_ingest}). Stopping ingestion stress.")
                break
            print(f"\nIngesting incremental batch {batch_num} of {increment_size} records...")
            if not self._ingest_data_batch(increment_size, f"incremental_{batch_num}"):
                print(f"Failed to ingest incremental batch {batch_num}. Further ingestion might be affected.")
            batch_num +=1
            # Optional: wait or re-index if needed between large batches
            # print("Waiting briefly after incremental batch...")
            # time.sleep(10)
        print(f"Large ingestion stress test finished. Total records in KB: {self.total_ingested_count}")

    def run_concurrent_query_simulation(self):
        if not self.is_connected or self.total_ingested_count == 0:
            print("\n\nSkipping Concurrent Query Simulation (not connected or no data in KB).")
            return

        print(f"\n\n--- Running Concurrent Query Simulation (Sequential) ---")
        print(f"Simulating {self.concurrent_query_simulation_count} 'threads', each running {self.queries_per_simulated_thread} queries.")

        total_queries_simulated = 0
        failed_queries_simulated = 0

        for i in range(self.concurrent_query_simulation_count):
            print(f"  Simulating 'Thread' {i+1}:")
            for j in range(self.queries_per_simulated_thread):
                query_text = random.choice(BASE_STRESS_QUERIES) + " " + ''.join(random.choices(string.ascii_lowercase, k=5)) # Add randomness
                step_name = f"Concurrent Query Sim (Thread {i+1}, Query {j+1})"
                start_time = time.time()
                try:
                    results = self.handler.select_from_knowledge_base(self.kb_name, query_text, limit=1)
                    duration = time.time() - start_time
                    if results is not None:
                        self._log_observation(step_name, "success", duration, {"query": query_text, "results_count": len(results)})
                        if duration > 10: # Example: query takes > 10s
                            self.report["summary"]["performance_degradation_points"].append(f"High query latency ({duration:.2f}s) during concurrent simulation: {query_text}")
                    else: # Handler returned None, implies an issue
                        failed_queries_simulated += 1
                        self._log_observation(step_name, "failure", duration, {"query": query_text}, error_message="Query returned None (handler error).")
                        self.report["summary"]["failure_modes_observed"].append("QUERY_HANDLER_RETURNS_NONE")

                except Exception as e:
                    duration = time.time() - start_time
                    failed_queries_simulated += 1
                    self._log_observation(step_name, "failure", duration, {"query": query_text}, error_message=str(e))
                    self.report["summary"]["failure_modes_observed"].append("QUERY_EXCEPTION")
                total_queries_simulated += 1
                time.sleep(0.05) # Minimal delay between queries in a "thread"
            # time.sleep(0.2) # Minimal delay between "threads"

        details = {"total_simulated_queries": total_queries_simulated, "failed_simulated_queries": failed_queries_simulated}
        self._log_observation("Concurrent Query Simulation Summary", "completed", details=details)


    def run_complex_query_stress(self):
        if not self.is_connected or self.total_ingested_count == 0:
            print("\n\nSkipping Complex Query Stress Test (not connected or no data in KB).")
            return

        print(f"\n\n--- Running Complex Query Stress Test ---")
        print(f"Running {self.complex_query_count} complex queries.")

        words_for_queries = ["data", "ai", "system", "model", "search", "knowledge", "base", "integration", "performance", "analysis", "hackernews", "story", "comment", "user", "developer"]

        failed_complex_queries = 0
        for i in range(self.complex_query_count):
            num_terms = random.randint(self.complex_query_max_terms // 2, self.complex_query_max_terms)
            query_text = " ".join(random.choices(words_for_queries, k=num_terms))
            step_name = f"Complex Query {i+1} ({num_terms} terms)"

            start_time = time.time()
            try:
                results = self.handler.select_from_knowledge_base(self.kb_name, query_text, limit=1)
                duration = time.time() - start_time
                if results is not None:
                    self._log_observation(step_name, "success", duration, {"terms": num_terms, "results_count": len(results)})
                    if duration > 20: # Example: complex query takes > 20s
                        self.report["summary"]["performance_degradation_points"].append(f"High complex query latency ({duration:.2f}s) for {num_terms} terms.")
                else:
                    failed_complex_queries += 1
                    self._log_observation(step_name, "failure", duration, {"terms": num_terms}, error_message="Query returned None.")
                    self.report["summary"]["failure_modes_observed"].append("COMPLEX_QUERY_HANDLER_RETURNS_NONE")
            except Exception as e:
                duration = time.time() - start_time
                failed_complex_queries += 1
                self._log_observation(step_name, "failure", duration, {"terms": num_terms}, error_message=str(e))
                self.report["summary"]["failure_modes_observed"].append("COMPLEX_QUERY_EXCEPTION")
            time.sleep(0.1)

        details = {"total_complex_queries": self.complex_query_count, "failed_complex_queries": failed_complex_queries}
        self._log_observation("Complex Query Stress Summary", "completed", details=details)

    def print_stress_report(self):
        print("\n\n--- Stress Test Report ---")
        # Deduplicate failure modes and degradation points
        self.report["summary"]["failure_modes_observed"] = sorted(list(set(self.report["summary"]["failure_modes_observed"])))
        self.report["summary"]["performance_degradation_points"] = sorted(list(set(self.report["summary"]["performance_degradation_points"])))

        print(json.dumps(self.report, indent=2))
        report_filename = f"stress_test_report_{self.kb_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.report, f, indent=2)
        print(f"\nStress test report saved to {report_filename}")

    def run_full_stress_test(self):
        if not self.connect_to_mindsdb():
            return

        if not self.setup_kb_for_stress_test():
            print("KB setup failed. Aborting stress test.")
            self.print_stress_report() # Print whatever was logged
            return

        self.run_large_ingestion_stress()
        self.run_concurrent_query_simulation() # Simulation is sequential but tests repeated queries
        self.run_complex_query_stress()

        self.print_stress_report()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MindsDB Knowledge Base Stress Test.")
    parser.add_argument("--kb-name", default=DEFAULT_KB_NAME_STRESS, help="Name of the KB to use/create.")
    parser.add_argument("--hn-datasource", default=DEFAULT_HN_DATASOURCE_STRESS, help="HackerNews datasource.")
    parser.add_argument("--hn-table", default=DEFAULT_HN_TABLE_STRESS, help="HackerNews table for ingestion.")

    parser.add_argument("--initial-load", type=int, default=INITIAL_INGESTION_LOAD, help="Initial number of records to ingest.")
    parser.add_argument("--increment-steps", nargs='+', type=int, default=INCREMENTAL_INGESTION_STEPS, help="List of incremental ingestion sizes.")
    parser.add_argument("--max-records", type=int, default=MAX_RECORDS_TO_ATTEMPT_INGEST, help="Max total records to attempt ingesting.")

    parser.add_argument("--concurrent-sim", type=int, default=CONCURRENT_QUERY_SIMULATION_COUNT, help="Number of simulated concurrent query 'threads'.")
    parser.add_argument("--queries-per-thread", type=int, default=QUERIES_PER_SIMULATED_THREAD, help="Queries per simulated thread.")

    parser.add_argument("--complex-queries", type=int, default=COMPLEX_QUERY_COUNT, help="Number of complex queries to run.")
    parser.add_argument("--complex-query-terms", type=int, default=COMPLEX_QUERY_MAX_TERMS, help="Max terms in auto-generated complex queries.")

    args = parser.parse_args()

    print("--- Starting Stress Test ---")
    print(f"Parameters: {vars(args)}")

    stresser = StressTester(
        kb_name=args.kb_name, hn_datasource=args.hn_datasource, hn_table=args.hn_table,
        initial_load=args.initial_load, incremental_steps=args.increment_steps, max_records=args.max_records,
        concurrent_sim_count=args.concurrent_sim, queries_per_thread=args.queries_per_thread,
        complex_query_count=args.complex_queries, complex_query_terms=args.complex_query_terms
    )
    stresser.run_full_stress_test()
    print("--- Stress Test Finished ---")

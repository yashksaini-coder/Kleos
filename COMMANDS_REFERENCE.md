# Kleos-Quira CLI Commands Reference

This document provides detailed information on all available CLI commands, their options, and platform-specific usage examples.

---

# Setup Commands

## `setup hackernews` - Setup HackerNews Datasource

Creates a HackerNews datasource connection in MindsDB.

**Usage:**
```bash
python main.py setup hackernews --name <datasource_name>
```

**Arguments:**
- `--name`: Name for the datasource (default: hackernews_db)

**Example:**
```bash
python main.py setup hackernews --name my_hackernews_source
```

---

# Knowledge Base Commands

## `kb create` - Create a new Knowledge Base

Creates a new Knowledge Base with specified embedding and (optional) reranking models, allowing for different providers and configurations.

**Usage:**
```bash
python main.py kb create <kb_name> [options]
```

**Required Arguments:**
- `<kb_name>`: Name of the Knowledge Base to create.

**Embedding Model Options:**
- `--embedding-provider <provider>`: Provider for the embedding model (e.g., `ollama`, `openai`, `google`). Default: `ollama`.
- `--embedding-model <model_name>`: Name of the embedding model (e.g., `nomic-embed-text`, `text-embedding-ada-002`, `text-embedding-004`). Default: `nomic-embed-text`.
- `--embedding-base-url <url>`: Base URL for the embedding model provider (e.g., for Ollama: `http://localhost:11434`). Optional, defaults to `OLLAMA_BASE_URL` from config if provider is `ollama`.
- `--embedding-api-key <key>`: API key for the embedding model provider (e.g., for Google, OpenAI). Optional.

**Reranking Model Options (all optional):**
- `--reranking-provider <provider>`: Provider for the reranking model (e.g., `ollama`, `google`, `cohere`).
- `--reranking-model <model_name>`: Name of the reranking model (e.g., `llama3`, `gemini-1.5-flash`).
- `--reranking-base-url <url>`: Base URL for the reranking model provider. Optional, defaults to `OLLAMA_BASE_URL` from config if provider is `ollama`.
- `--reranking-api-key <key>`: API key for the reranking model provider. Optional.

**Data Structure Options:**
- `--content-columns <cols>`: Comma-separated list of column names to be used as content for embeddings (e.g., `"title,text"`).
- `--metadata-columns <cols>`: Comma-separated list of column names to be stored as metadata.
- `--id-column <col_name>`: Name of the column to be used as the unique identifier for records.

**Examples:**

1.  **Basic KB with default Ollama embedder, no reranker:**
    ```bash
    python main.py kb create my_ollama_kb
    ```
    *(Assumes `nomic-embed-text` for embedding and `OLLAMA_BASE_URL` is configured or Ollama runs on default)*

2.  **KB with Ollama embedder and Ollama reranker:**
    ```bash
    python main.py kb create my_advanced_ollama_kb \
        --embedding-model nomic-embed-text \
        --reranking-provider ollama \
        --reranking-model llama3
    ```
    *(Assumes `OLLAMA_BASE_URL` is configured or Ollama runs on default for both)*

3.  **KB with Google Gemini for embeddings and no reranker:**
    ```bash
    python main.py kb create my_gemini_embed_kb \
        --embedding-provider google \
        --embedding-model text-embedding-004 \
        --embedding-api-key "YOUR_GOOGLE_API_KEY"
    ```

4.  **KB with OpenAI embeddings and Google Gemini reranker:**
    ```bash
    # PowerShell/Bash/Zsh
    python main.py kb create my_mixed_provider_kb \
        --embedding-provider openai \
        --embedding-model text-embedding-ada-002 \
        --embedding-api-key "YOUR_OPENAI_API_KEY" \
        --reranking-provider google \
        --reranking-model gemini-1.5-flash \
        --reranking-api-key "YOUR_GOOGLE_API_KEY" \
        --content-columns "document_content" \
        --metadata-columns "source,timestamp" \
        --id-column "doc_id"
    ```
    ```cmd
    REM Windows Command Prompt (ensure correct JSON escaping if any complex params were JSON)
    python main.py kb create my_mixed_provider_kb 
        --embedding-provider openai 
        --embedding-model text-embedding-ada-002 
        --embedding-api-key "YOUR_OPENAI_API_KEY" 
        --reranking-provider google 
        --reranking-model gemini-1.5-flash 
        --reranking-api-key "YOUR_GOOGLE_API_KEY" 
        --content-columns "document_content" 
        --metadata-columns "source,timestamp" 
        --id-column "doc_id"
    ```

5.  **KB with custom content/metadata columns for HackerNews stories (using default Ollama embedder):**
    ```bash
    python main.py kb create hn_stories_custom_kb \
        --content-columns "title,text" \
        --metadata-columns "id,by,score,time" \
        --id-column "id"
    ```

## `kb ingest` - Ingest data into a Knowledge Base

Ingests data from a HackerNews table into an existing Knowledge Base. The command automatically detects sensible defaults for HackerNews tables and can auto-create the datasource if needed.

**Usage:**
```bash
python main.py kb ingest <kb_name> --from-hackernews <table> [options]
```

**Required Arguments:**
- `<kb_name>`: Name of the existing Knowledge Base
- `--from-hackernews`: HackerNews table to ingest from (stories, comments, etc.)

**Optional Arguments:**
- `--limit`: Maximum number of records to ingest (default: 1000)
- `--content-columns`: Comma-separated list of columns to use as content (auto-detected for HN tables if not specified)
- `--metadata-map`: JSON mapping of KB metadata columns to source table columns

**Auto-Detection for HackerNews Tables:**
- **stories**: content = "title,text", metadata = "id,by,score,time,descendants,url"
- **comments**: content = "text", metadata = "id,by,parent,time"
- **Other tables**: content = "text", metadata = "id" (fallback)

**Examples:**

**PowerShell/Bash/Zsh:**
```bash
# Simple ingestion with auto-detected columns
python main.py kb ingest my_documents_kb --from-hackernews stories --limit 50

# Custom content columns only
python main.py kb ingest my_documents_kb --from-hackernews stories --content-columns title --limit 100

# Custom content and metadata mapping
python main.py kb ingest my_documents_kb --from-hackernews stories --content-columns title --metadata-map '{"story_id":"id", "author":"by", "score":"score"}' --limit 100

# Ingest comments with custom mapping
python main.py kb ingest comment_kb --from-hackernews comments --metadata-map '{"comment_id":"id", "author":"by", "parent_story":"parent"}' --limit 200
```

**Windows Command Prompt:**
```cmd
Simple ingestion with auto-detected columns
python main.py kb ingest my_documents_kb --from-hackernews stories --limit 50

RUN Custom content columns only
python main.py kb ingest my_documents_kb --from-hackernews stories --content-columns title --limit 100

RUN Custom content and metadata mapping
python main.py kb ingest my_documents_kb --from-hackernews stories --content-columns title --metadata-map "{\"story_id\":\"id\", \"author\":\"by\", \"score\":\"score\"}" --limit 100

RUN Ingest comments with custom mapping
python main.py kb ingest comment_kb --from-hackernews comments --metadata-map "{\"comment_id\":\"id\", \"author\":\"by\", \"parent_story\":\"parent\"}" --limit 200
```

## `kb query` - Query a Knowledge Base

Queries a Knowledge Base for relevant content using semantic search.

**Usage:**
```bash
python main.py kb query <kb_name> "<query_text>" [options]
```

**Arguments:**
- `<kb_name>`: Name of the Knowledge Base to query
- `<query_text>`: Text to search for (enclose in quotes)
- `--limit`: Maximum number of results to return (default: 10)
- `--metadata-filter`: JSON filter to apply to metadata (optional)

**Examples:**

**PowerShell/Bash/Zsh:**
```bash
# Basic query
python main.py kb query my_documents_kb "latest trends in AI"

# Query with result limit
python main.py kb query my_documents_kb "Python programming tips" --limit 5

# Query with metadata filter
python main.py kb query my_documents_kb "machine learning" --metadata-filter '{"author":"tech_expert", "score":{"$gt":50}}'

# Search specific topics in HackerNews stories
python main.py kb query hn_stories_kb "startups and funding" --metadata-filter '{"score":{"$gte":100}}'
```

**Windows Command Prompt:**
```cmd
RUN Basic query
python main.py kb query my_documents_kb "latest trends in AI"

RUN Query with result limit
python main.py kb query my_documents_kb "Python programming tips" --limit 5

RUN Query with metadata filter
python main.py kb query my_documents_kb "machine learning" --metadata-filter "{\"author\":\"tech_expert\", \"score\":{\"$gt\":50}}"

RUN Search specific topics in HackerNews stories
python main.py kb query hn_stories_kb "startups and funding" --metadata-filter "{\"score\":{\"$gte\":100}}"
```

### `kb list-databases` - List available databases

Lists all databases available in the current MindsDB instance.

**Usage:**
```bash
python main.py kb list-databases
```

**Example Output:**
```
Available databases:
- information_schema
- mindsdb
- hackernews_db
- my_custom_datasource
```

### `kb create-agent` - Create an AI Agent

Creates an AI agent with a specified model, linked to knowledge bases and/or tables, and configured with a prompt template.

**Usage:**
```bash
python main.py kb create-agent <agent_name> [options]
```

**Required Arguments:**
- `<agent_name>`: Name for the new agent.
- `--model-name <model>`: LLM model to use for the agent (e.g., `gemini-1.5-flash`, `llama3`). This is a **required** option.
- `--include-knowledge-bases <kb_names>`: Comma-separated list of Knowledge Base names to include (e.g., `my_kb1,another_kb`). This is a **required** option.

**Optional Arguments:**
- `--google-api-key <key>`: Your Google API key, if using a Google model and not set globally in MindsDB or via environment/config.
- `--include-tables <table_names>`: Comma-separated list of table names to include, in `datasource.tablename` format (e.g., `hackernews.stories,myds.comments`).
- `--prompt-template <template_string>`: Custom prompt template for the agent. Enclose multi-line templates in quotes appropriate for your shell.
- `--other-params <json_string>`: JSON string for other parameters to pass to the agent's `USING` clause (e.g., `'{"temperature": 0.7, "max_tokens": 300}'`). Refer to MindsDB documentation for model-specific parameters.

**Examples:**

1.  **Agent using Google Gemini, one KB, one table, and a custom prompt:**
    ```bash
    # PowerShell/Bash/Zsh
    python main.py kb create-agent my_hn_analyzer \
        --model-name gemini-1.5-flash \
        --include-knowledge-bases "hn_kb_main" \
        --include-tables "hackernews_db.stories" \
        --google-api-key "YOUR_GOOGLE_API_KEY" \
        --prompt-template "You are an expert Hacker News analyst. Based on the story title and text from hackernews_db.stories and relevant info from hn_kb_main, answer the question." \
        --other-params '{"temperature":0.3}'
    ```
    ```cmd
    REM Windows Command Prompt (long commands might need care with line breaks using )
    python main.py kb create-agent my_hn_analyzer 
        --model-name gemini-1.5-flash 
        --include-knowledge-bases "hn_kb_main" 
        --include-tables "hackernews_db.stories" 
        --google-api-key "YOUR_GOOGLE_API_KEY" 
        --prompt-template "You are an expert Hacker News analyst. Based on the story title and text from hackernews_db.stories and relevant info from hn_kb_main, answer the question." 
        --other-params "{\"temperature\":0.3}"
    ```

2.  **Agent using an Ollama model (e.g., Llama3), multiple KBs, no extra tables:**
    *(Assumes Ollama model `llama3` is available to MindsDB)*
    ```bash
    python main.py kb create-agent ollama_kb_chat \
        --model-name llama3 \
        --include-knowledge-bases "product_docs_kb,faq_kb" \
        --prompt-template "Answer questions based on the provided product documentation and FAQs."
    ```

3.  **Simple agent with only required fields (model and KBs):**
    ```bash
    python main.py kb create-agent basic_agent \
        --model-name gemini-pro \
        --include-knowledge-bases "general_kb" \
        --google-api-key "YOUR_GOOGLE_KEY"
        # Assuming GOOGLE_GEMINI_API_KEY is also in config or GOOGLE_API_KEY is globally set in MindsDB if not provided
    ```

**Note on API Keys:**
- For Google models, provide `--google-api-key` or ensure `GOOGLE_GEMINI_API_KEY` is in your `config.py` or environment variables if the agent handler in MindsDB expects it. The current implementation prioritizes the CLI flag, then the config.
- For other models (e.g., OpenAI hosted via MindsDB), API keys might be configured directly in MindsDB when setting up the ML_ENGINE or passed via `--other-params` if the specific model integration supports it in the `USING` clause.

### `kb query-agent` - Query an AI Agent

Queries an AI agent for answers based on its associated Knowledge Base.

**Usage:**
```bash
python main.py kb query-agent <agent_name> "<question>"
```

**Arguments:**
- `<agent_name>`: Name of the agent to query
- `<question>`: Question to ask the agent (enclose in quotes)

**Examples:**
```bash
# Basic agent query
python main.py kb query-agent my_agent "What is the total number of stories ?"
```

---


### `kb evaluate` - Evaluate a Knowledge Base

Evaluates the relevancy and accuracy of documents returned by a Knowledge Base using a test dataset.

**Usage:**
```bash
python main.py kb evaluate <kb_name> --test-table <datasource.table_name> [options]
```

**Required Arguments:**
- `<kb_name>`: Name of the Knowledge Base to evaluate.
- `--test-table <datasource.table_name>`: Name of the table containing test data (e.g., `my_tests.question_answers`). The structure depends on the `--version` chosen.

**Optional Arguments:**

**Evaluation Mode & Data Generation:**
- `--version <version>`: Evaluator version. Choices: `doc_id` (checks if correct document ID is returned) or `llm_relevancy` (uses an LLM to rank/evaluate responses). Default: `doc_id`.
- `--generate-data`: Flag to enable automatic test data generation using default settings (fetches from the KB being evaluated, default count 20).
- `--generate-data-from-sql <sql_query>`: SQL query string to fetch data for test data generation (e.g., `"SELECT question, expected_doc_id FROM my_source.manual_tests"`).
- `--generate-data-count <count>`: Number of test data items to generate if `--generate-data` or `--generate-data-from-sql` is used. Default: 20.
- `--no-evaluate`: If set, only generates test data (if generation options are active) and saves it to `--test-table` without running the evaluation.

**LLM Configuration (for `version = 'llm_relevancy'`):**
- `--llm-provider <provider>`: LLM provider for evaluation (e.g., `gemini`, `openai`, `ollama`).
- `--llm-model-name <model>`: Name of the LLM model to use for evaluation.
- `--llm-api-key <key>`: API key for the LLM provider, if required.
- `--llm-base-url <url>`: Base URL for the LLM provider (e.g., for local Ollama).
- `--llm-other-params <json_string>`: JSON string for other LLM parameters (e.g., `'{"method": "multi-class"}'`).

**Output:**
- `--save-to-table <datasource.table_name>`: Table where evaluation results will be saved (e.g., `my_results.eval_output`). If not provided, results are printed to console but not saved to a table.

**Examples:**

1.  **Basic evaluation using `doc_id` version (test data already in `tests.kb_questions`):**
    ```bash
    python main.py kb evaluate my_knowledge_base --test-table tests.kb_questions
    ```

2.  **Generate test data and then evaluate using `doc_id` version:**
    ```bash
    python main.py kb evaluate my_knowledge_base \
        --test-table tests.generated_eval_data \
        --generate-data \
        --generate-data-count 50
    ```
    *(This will first populate `tests.generated_eval_data` then evaluate against it)*

3.  **Evaluate using `llm_relevancy` with a specific Google Gemini model:**
    ```bash
    # PowerShell/Bash/Zsh
    python main.py kb evaluate my_knowledge_base \
        --test-table tests.relevancy_questions \
        --version llm_relevancy \
        --llm-provider google \
        --llm-model-name gemini-1.5-flash \
        --llm-api-key "YOUR_GOOGLE_API_KEY" \
        --save-to-table results_db.relevancy_eval_output
    ```
    ```cmd
    REM Windows Command Prompt
    python main.py kb evaluate my_knowledge_base 
        --test-table tests.relevancy_questions 
        --version llm_relevancy 
        --llm-provider gemini 
        --llm-model-name gemini-1.5-flash 
        --llm-api-key "YOUR_GOOGLE_API_KEY" 
        --save-to-table results_db.relevancy_eval_output
    ```

4.  **Only generate test data from a custom SQL query, do not evaluate:**
    ```bash
    python main.py kb evaluate my_knowledge_base \
        --test-table tests.custom_questions_for_eval \
        --generate-data-from-sql "SELECT id as question_id, query_text as question FROM source_data.benchmark_queries" \
        --generate-data-count 100 \
        --no-evaluate
    ```

---

# AI Model Commands (`ai`)

Commands for managing and querying AI Models that are trained on your data (often referred to as Generative AI Tables or AI Tables within MindsDB documentation, but presented as "models" in this CLI for broader understanding). These models are created using a `CREATE MODEL ... FROM (SELECT ...) ...` syntax, making them behave like queryable tables that can generate predictions or content.

## `ai create-model` - Create an AI Model from Data

Creates an AI Model by training it on data specified by a SELECT query.

**Usage:**
```bash
python main.py ai create-model <model_name> --select-data-query "<query>" --predict-column <column_name> [options]
```

**Required Arguments:**
- `<model_name>`: Name for the new AI Model.
- `--select-data-query "<query>"`: SQL SELECT query to fetch training data. Enclose in quotes.
  Example: `"SELECT text_content, category FROM my_datasource.training_set"`
- `--predict-column <column_name>`: Name of the column the AI Model should learn to predict/generate.

**Optional Arguments:**
- `--project-name <name>`: MindsDB project where the AI Model will be created. Defaults to the currently connected project.
- `--engine <engine_name>`: AI engine to use (e.g., `openai`, `google_gemini`, `anthropic`). Default: `openai`.
- `--prompt-template "<template>"`: Prompt template for the AI Model. Use `{{column_name}}` for placeholders from your `--select-data-query`.
  Example: `"Summarize the following article: {{text_content}}"`
- `--param <key> <value>`: Additional `USING` parameters as key-value pairs for the model. Can be specified multiple times.
  Example: `--param model_name gpt-3.5-turbo --param api_key YOUR_API_KEY`

**Examples:**

1.  **Create a story summarizer AI Model using OpenAI and HackerNews data:**
    ```bash
    # Ensure hackernews_db datasource exists (e.g., via `setup hackernews --name hackernews_db`)
    # PowerShell/Bash/Zsh
    python main.py ai create-model story_summarizer_model \
        --select-data-query "SELECT title, text FROM hackernews_db.stories WHERE score > 5 AND text IS NOT NULL LIMIT 100" \
        --predict-column summary \
        --engine openai \
        --prompt-template "Generate a concise summary for the following HackerNews story titled '{{title}}': {{text}}" \
        --param api_key "YOUR_OPENAI_API_KEY" \
        --param model_name "gpt-3.5-turbo"
    ```
    ```cmd
    REM Windows Command Prompt
    python main.py ai create-model story_summarizer_model ^
        --select-data-query "SELECT title, text FROM hackernews_db.stories WHERE score > 5 AND text IS NOT NULL LIMIT 100" ^
        --predict-column summary ^
        --engine openai ^
        --prompt-template "Generate a concise summary for the following HackerNews story titled '{{title}}': {{text}}" ^
        --param api_key "YOUR_OPENAI_API_KEY" ^
        --param model_name "gpt-3.5-turbo"
    ```

2.  **Create a sentiment classification AI Model using Google Gemini:**
    ```bash
    # PowerShell/Bash/Zsh
    python main.py ai create-model product_sentiment_model \
        --select-data-query "SELECT review_text, sentiment_label FROM my_data.product_reviews" \
        --predict-column sentiment_label \
        --engine google_gemini \
        --prompt-template "Classify the sentiment of this product review: {{review_text}}. Sentiment should be one of: Positive, Negative, Neutral." \
        --param api_key "YOUR_GOOGLE_API_KEY" \
        --param model_name "gemini-1.5-flash"
    ```
    *(Ensure `GOOGLE_GEMINI_API_KEY` is available in your app config or environment if not passed via `--param api_key`)*

## `ai list-models` - List AI Models

Lists all AI Models in a specified project or the default connected project.

**Usage:**
```bash
python main.py ai list-models [options]
```

**Optional Arguments:**
- `--project-name <name>`: MindsDB project from which to list AI Models. Defaults to the currently connected project.

**Example:**
```bash
python main.py ai list-models --project-name my_mindsdb_project
# Lists AI Models in 'my_mindsdb_project'

python main.py ai list-models
# Lists AI Models in the default connected project
```

## `ai describe-model` - Describe an AI Model

Shows details, schema, and status of a specific AI Model.

**Usage:**
```bash
python main.py ai describe-model <model_name> [options]
```

**Required Arguments:**
- `<model_name>`: Name of the AI Model to describe.

**Optional Arguments:**
- `--project-name <name>`: MindsDB project where the AI Model resides. Defaults to the currently connected project.

**Example:**
```bash
python main.py ai describe-model story_summarizer_model --project-name my_mindsdb_project
```

## `ai drop-model` - Drop (Delete) an AI Model

Deletes an AI Model from the specified project. This action is irreversible.

**Usage:**
```bash
python main.py ai drop-model <model_name> [options]
```

**Required Arguments:**
- `<model_name>`: Name of the AI Model to drop.

**Optional Arguments:**
- `--project-name <name>`: MindsDB project where the AI Model resides. Defaults to the currently connected project.

**Example:**
```bash
python main.py ai drop-model old_text_classifier_model --project-name my_mindsdb_project
# You will be prompted for confirmation.
```

## `ai refresh-model` - Refresh an AI Model

Refreshes an AI Model. This typically involves retraining the model with the latest data from its original data source, using its original parameters (`RETRAIN model_name;` in SQL).

**Usage:**
```bash
python main.py ai refresh-model <model_name> [options]
```

**Required Arguments:**
- `<model_name>`: Name of the AI Model to refresh.

**Optional Arguments:**
- `--project-name <name>`: MindsDB project where the AI Model resides. Defaults to the currently connected project.

**Example:**
```bash
python main.py ai refresh-model story_summarizer_model
# Refreshes 'story_summarizer_model' in the default project
```

<!-- ## `ai retrain-model` - Retrain an AI Model with Options

Retrains an AI Model, optionally allowing you to specify a new data query or new `USING` parameters for the model.

**Usage:**
```bash
python main.py ai retrain-model <model_name> [options]
```

**Required Arguments:**
- `<model_name>`: Name of the AI Model to retrain.

**Optional Arguments:**
- `--project-name <name>`: MindsDB project where the AI Model resides. Defaults to the currently connected project.
- `--select-data-query "<query>"`: Optional new SQL SELECT query to fetch training data. If omitted, uses the model's original training query.
- `--param <key> <value>`: Optional new `USING` parameters for retraining. Can be specified multiple times.

**Examples:**

1.  **Retrain with a new data query:**
    ```bash
    # PowerShell/Bash/Zsh
    python main.py ai retrain-model product_sentiment_model \
        --select-data-query "SELECT review_text, sentiment_label FROM my_data.all_product_reviews_v2"
    ```

2.  **Retrain with new parameters (e.g., change a hyperparameter if supported by the engine):**
    ```bash
    # PowerShell/Bash/Zsh
    python main.py ai retrain-model story_summarizer_model \
        --param temperature 0.85
    ```
    *(Note: Not all models/engines support changing all parameters on retrain. Check MindsDB engine documentation.)* -->


## `ai query` - Execute a SQL Query (Typically for AI Models)

Executes an arbitrary SQL query against the MindsDB project. This is commonly used to query AI Models by joining them with data tables or selecting from them with a `WHERE` clause that provides input to the model.

**Usage:**
```bash
python main.py ai query "<query_string>" [options]
```

**Required Arguments:**
- `<query_string>`: The SQL query to execute. Enclose in quotes.

**Optional Arguments:**
- `--project-name <name>`: MindsDB project context for the query. The query will execute in the context of the default connected project; this option is more for user clarity or if future versions support context switching. Ensure your query string fully qualifies table and model names with project names if they are not in the default project (e.g., `mindsdb.my_model` or `specific_project.my_model`).

**Examples:**

1.  **Query the `story_summarizer_model` AI Model by joining with HackerNews data:**
    ```bash
    # PowerShell/Bash/Zsh
    # Assuming story_summarizer_model is in the 'mindsdb' project (default)
    # and hnstories table is in 'hackernews_db' datasource.
    python main.py ai query "SELECT hn.title, hn.text, hn.score, ai.summary FROM hackernews.hnstories AS hn JOIN mindsdb.story_summarizer AS ai WHERE hn.title IS NOT NULL LIMIT 2"
    ```

2.  **Query a sentiment classification AI Model directly (if it's structured for this pattern):**
    ```bash
    # PowerShell/Bash/Zsh
    # Assuming sentiment_model is in 'my_project'
    python main.py ai query "SELECT input_text, predicted_category FROM my_project.sentiment_model WHERE input_text = 'MindsDB makes AI development much easier!'"
    ```

---

## JSON Parameter Handling

When passing complex parameters as JSON strings via options like `--metadata-map`, `--metadata-filter`, or `--agent-params`, ensure they are correctly quoted and escaped for your specific command-line shell.

### Windows Command Prompt (`cmd.exe`)
- Enclose the entire JSON string in double quotes (`"`)
- Escape all inner double quotes with a backslash (`\"`)
- Example: `--metadata-map "{\"key\":\"value\"}"`

### PowerShell
- Option 1: Use single quotes and escape inner double quotes with backslash
- Example: `--metadata-map '{\"key\":\"value\"}'`
- Option 2: Use double quotes and escape with backticks
- Example: `--metadata-map "{`"key`":`"value`"}"`

### Bash, Zsh (Linux/macOS)
- Enclose the JSON string in single quotes (`'`)
- Example: `--metadata-map '{"key":"value"}'`

---

## Job Commands

### `job create` - Create a job for data processing

Creates a job for processing data with AI models.

**Usage:**
```bash
python main.py job create <job_name> --model <model> --input <input_file> [options]
```

---

## Best Practices

1. **Always test with small limits first**: When ingesting data, start with `--limit 10` to verify the configuration works correctly.

2. **Use descriptive names**: Choose clear, descriptive names for KBs and agents that reflect their purpose.

3. **Verify your datasource**: Use `kb list-databases` to confirm your HackerNews datasource exists before ingesting.

4. **Check your JSON syntax**: Use online JSON validators to verify complex JSON parameters before using them in commands.

5. **Environment setup**: Ensure all required environment variables (API keys, MindsDB connection details) are properly configured.

6. **Column mapping strategy**: For custom use cases, understand your source data structure and plan your content/metadata column mapping accordingly.

## Troubleshooting

### Common Issues

1. **JSON parsing errors**: Usually caused by incorrect quoting/escaping. Check the platform-specific examples above.
   - **PowerShell**: Use `'{\"key\":\"value\"}'` or `"{`"key`":`"value`"}"`
   - **Command Prompt**: Use `"{\"key\":\"value\"}"`
   - **Bash/Zsh**: Use `'{"key":"value"}'`
   - **Error "Expecting value: line 1 column 1"**: Your JSON string is empty or malformed due to shell parsing issues

2. **Table not found**: Ensure the HackerNews datasource is set up and the table name is correct (usually 'stories' or 'comments').

3. **Column not found**: Verify that the columns you're referencing actually exist in the source table.

4. **Agent creation failures**: Check that the model name is correct and any required API keys are configured.

5. **Connection errors**: Verify MindsDB is running and accessible at the configured host/port.

### Getting Help

- Use `--help` with any command to see available options
- Check the main README.md for setup and configuration details
- Verify your environment configuration matches the examples in the documentation

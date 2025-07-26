# Kleos CLI Command Reference

This document provides detailed information on all available Kleos CLI commands, their options, arguments, and platform-specific usage examples. Kleos enhances your MindsDB workflow with an improved user experience, featuring rich text formatting and clear tabular data displays.

---

# Utility Commands

General utility commands for the Kleos CLI.

## `cls`

Clears the terminal screen.
This command is os-dependent and uses 'cls' on Windows and 'clear' on Unix-like systems.

**Usage:**
```bash
kleos cls
```

**Options:**

| Option       | Description                 |
|--------------|-----------------------------|
| `-h, --help` | Show help message and exit. |

*(This command takes no other options or arguments besides help.)*

---

## `info`

Displays version, description, and project information for Kleos CLI.

Provides details about the current version of the Kleos tool, its main purpose and description (including the '`telos`' quote), and a link to the project's GitHub repository.

**Usage:**
```bash
kleos info
```

**Options:**

| Option       | Description                 |
|--------------|-----------------------------|
| `-h, --help` | Show help message and exit. |

*(This command takes no other options or arguments besides help.)*

**Example Output (structure and style, content may vary slightly):**
![](./public/Kleos%20Info%20Banner.jpeg)
---

## `about`

Displays information about the author of the Kleos CLI.

Provides details about the author, including their name, a short bio, and links to their GitHub profile and sponsorship page.

**Usage:**
```bash
kleos about
```

**Options:**

| Option       | Description                 |
|--------------|-----------------------------|
| `-h, --help` | Show help message and exit. |

*(This command takes no other options or arguments besides help.)*

**Example Output (structure and style, content may vary slightly):**
![](./public/Kleos%20About%20Banner.jpeg)

---

## JSON Parameter Handling

When passing complex parameters as JSON strings via options like `--metadata-map` (in `kb ingest`), `--metadata-filter` (in `kb query`), or `--other-params` (in `kb create-agent`), ensure they are correctly quoted and escaped for your specific command-line shell. Incorrect quoting is a common source of errors.

*   **For Windows Command Prompt (`cmd.exe`):**
    Enclose the entire JSON string in double quotes (`"`) and escape all inner double quotes with a backslash (`\"`).
    Example: `kleos kb query mykb "test" --metadata-filter "{\"author\":\"John Doe\"}"`

*   **For Linux/macOS (bash, zsh) or PowerShell:**
    Often, enclosing the JSON string in single quotes (`'`) is sufficient.
    Example: `kleos kb query mykb "test" --metadata-filter '{"author":"John Doe"}'`

    If your JSON itself contains single quotes, you might need to use double quotes for the outer layer and escape inner double quotes, or use more advanced shell quoting techniques.

Refer to your shell's documentation for robust quoting mechanisms if you encounter issues.

---

# Setup Commands (`setup`)

Commands for initial setup and project configuration.
This includes setting up necessary datasources or other initial configurations required for Kleos to interact effectively with MindsDB.

## `setup hackernews`

Creates or verifies the HackerNews datasource in MindsDB.

The HackerNews datasource provides access to stories, comments, and other data from Hacker News (news.ycombinator.com). This is often used as a sample dataset for examples and testing Knowledge Bases or AI Models.

If a datasource with the specified name already exists, its presence will be confirmed. Otherwise, a new datasource connection will be created.

**Usage:**
```bash
kleos setup hackernews [OPTIONS]
```

**Options:**

| Option             | Description                                                                          | Default      |
|--------------------|--------------------------------------------------------------------------------------|--------------|
| `--name TEXT`      | Specify the name for the HackerNews datasource in MindsDB.                             | `hackernews` |
| `-h, --help`       | Show help message and exit.                                                          |              |

**Example:**
```bash
kleos setup hackernews --name my_hackernews_source
```

![](./public/Kleos%20setup.jpeg)


---

# Knowledge Base Commands (`kb`)

Commands for managing Knowledge Bases (KBs) and associated AI Agents.

Knowledge Bases in MindsDB enable semantic search over large text datasets.
They typically use an embedding model to convert text into vectors and may
optionally use a reranking model to refine search relevance. AI Agents can
leverage these KBs to answer questions based on the stored knowledge.

---

## `kb create <kb_name>`

Creates a new Knowledge Base (KB) in MindsDB.

KBs are designed for storing and querying textual data using semantic search. You must specify an EMBEDDING_MODEL to convert text into vector embeddings. A RERANKING_MODEL is optional but can be used to improve the relevance of search results by re-processing the initial set of documents found by the embedding model.

The `--content-columns` option specifies which columns from your source data will be combined and embedded. `--metadata-columns` are stored alongside the embeddings and can be used for filtering queries. `--id-column` sets a unique key for each record.

**Usage:**
```bash
kleos kb create <kb_name> [OPTIONS]
```

**Arguments:**

| Argument    | Description                     |
|-------------|---------------------------------|
| `KB_NAME`   | Name for the new Knowledge Base. |

**Options:**

| Option                       | Description                                                                                                | Default            |
|------------------------------|------------------------------------------------------------------------------------------------------------|--------------------|
| `--embedding-provider TEXT`  | Provider for the embedding model (e.g., 'ollama', 'openai', 'google').                                     | `ollama`           |
| `--embedding-model TEXT`     | Name of the embedding model (e.g., 'nomic-embed-text', 'text-embedding-ada-002').                          | `nomic-embed-text` |
| `--embedding-base-url TEXT`  | Base URL for embedding provider if self-hosted (e.g., Ollama URL 'http://localhost:11434').                 |                    |
| `--embedding-api-key TEXT`   | API key if required by the embedding provider (e.g., Google, OpenAI).                                      |                    |
| `--reranking-provider TEXT`  | Provider for the reranking model (optional; e.g., 'ollama', 'google', 'cohere').                             |                    |
| `--reranking-model TEXT`     | Name of the reranking model (optional; e.g., 'llama3', 'gemini-1.5-flash').                                  |                    |
| `--reranking-base-url TEXT`  | Base URL for reranking provider if self-hosted (optional).                                                 |                    |
| `--reranking-api-key TEXT`   | API key if required by the reranking provider (optional).                                                    |                    |
| `--content-columns TEXT`     | Comma-separated list of source column names to embed as content. E.g., 'title,text'.                         |                    |
| `--metadata-columns TEXT`    | Comma-separated list of source column names to store as filterable metadata. E.g., 'id,author,timestamp'.   |                    |
| `--id-column TEXT`           | Name of the source column to use as a unique identifier for records within the KB.                             |                    |
| `-h, --help`                 | Show help message and exit.                                                                                |                    |

**Examples:**

Create a KB using default Ollama embedder (nomic-embed-text):
```bash
kb create hn_stories_kb --embedding-model nomic-embed-text --reranking-provider ollama --reranking-model gemma3 --content-columns 'title,text' --metadata-columns 'id,by,score,time' --id-column id
```

Create a KB with Google's gemini and an Ollama Llama3 embedding:
```bash
kleos kb create gemini_ollama_kb --embedding-provider ollama --embedding-model nomic-embed-text --reranking-provider Google --reranking-model gemini-2.0-flash --gemini-api-key YOUR_GEMINI_KEY --content-columns "question,answer"
```

![](./public/Kleos%20KB%20create%20Execute.jpeg)

---

## `kb index <kb_name>`

Creates or refreshes the vector index for a specified Knowledge Base.

After ingesting data into a KB, an index must be built (or updated) to enable efficient semantic search. This command triggers that process. MindsDB typically uses a vector database (like ChromaDB by default) under the hood, and this command ensures its index is up-to-date with the KB's content.

**Usage:**
```bash
kleos kb index <kb_name> [OPTIONS]
```

**Arguments:**

| Argument    | Description                          |
|-------------|--------------------------------------|
| `KB_NAME`   | The name of the Knowledge Base to index. |

**Options:**

| Option       | Description                 |
|--------------|-----------------------------|
| `-h, --help` | Show help message and exit. |

**Example:**
```bash
kleos kb index my_docs_kb
```

>[!NOTE]
> If the KB is large, indexing may take some time. You can check the status of the index creation in MindsDB's UI or logs.
> KB indexing does not support default chromadb vector stores as these are managed internally and created by MindsDB.
---

## `kb ingest <kb_name>`

Ingests data into an existing Knowledge Base from a HackerNews table.

This command uses MindsDB's `INSERT INTO ... SELECT ...` syntax for efficient ingestion. It includes smart defaults for HackerNews tables ('stories', 'comments') regarding which columns are used for content embedding and which for metadata. The HackerNews datasource will be automatically created if it doesn't exist using the name provided by `--hn-datasource`.

**Usage:**
```bash
kleos kb ingest <kb_name> --from-hackernews <from_hackernews_table> [OPTIONS]
```

**Arguments:**

| Argument    | Description                                  |
|-------------|----------------------------------------------|
| `KB_NAME`   | Name of the existing Knowledge Base to ingest into. |

**Options:**

| Option                          | Description                                                                                                                               | Default      |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|--------------|
| `--from-hackernews TEXT`        | (Required) Name of the HackerNews table to ingest from (e.g., 'stories', 'comments').                                                      |              |
| `--hn-datasource TEXT`          | Name of the HackerNews datasource in MindsDB.                                                                                             | `hackernews` |
| `--limit INTEGER`               | Maximum number of records to ingest from the HackerNews table.                                                                              | `100`        |
| `--content-column TEXT`         | Source column(s) for KB content, comma-separated. Auto-detects for HN tables (e.g., 'title,text' for stories, 'text' for comments).         |              |
| `--metadata-map TEXT`           | JSON string mapping your desired KB metadata column names to source table column names. E.g., `'{\"doc_id\":\"id\", \"author\":\"by\"}'`. Auto-detects for HN. |              |
| `-h, --help`                    | Show help message and exit.                                                                                                               |              |

**Examples:**

Ingest 500 stories into `my_hn_kb` using default mappings:
```bash
kleos kb ingest my_hn_kb --from-hackernews stories --limit 500
```

Custom mapping for 'stories' table:
```bash
kleos kb ingest my_hn_kb --from-hackernews stories --content-column "title" \
  --metadata-map '{"id_in_kb":"id", "user":"by", "points":"score"}' --limit 100
```
*(Note on JSON parameters: Ensure correct quoting for your shell as described in the main README)*

![](./public/Kleos%20KB%20ingest%20Execute.jpeg)
---

## `kb query <kb_name> <query_text>`

Queries a Knowledge Base using semantic search and optional metadata filters.

The command searches for content similar to the `<query_text>`. You can further refine results using `--metadata-filter` with a JSON string. The filter supports simple key-value equality and comparison operators like `$gt` (greater than), `$gte` (greater than or equal), `$lt` (less than), `$lte` (less than or equal) nested within the JSON.

**Usage:**
```bash
kleos kb query <kb_name> <query_text> [OPTIONS]
```

**Arguments:**

| Argument       | Description                                                              |
|----------------|--------------------------------------------------------------------------|
| `KB_NAME`      | Name of the Knowledge Base to query.                                     |
| `QUERY_TEXT`   | The natural language text to search for within the Knowledge Base.       |

**Options:**

| Option                  | Description                                                                                                                               | Default     |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|-------------|
| `--metadata-filter TEXT`| JSON string for filtering results based on metadata. Supports operators like `$gt`, `$gte`, `$lt`, `$lte`. Example: `'{\"year\":{\"$gt\":2022}}'` |             |
| `--limit INTEGER`       | Maximum number of search results to return.                                                                                               | `5`         |
| `-h, --help`            | Show help message and exit.                                                                                                               |             |

**Examples:**

Basic query:
```bash
kleos kb query my_docs_kb "latest advancements in AI"
```

Query with a limit:
```bash
kleos kb query my_hn_kb "python programming tips" --limit 10
```

Query with metadata filter (ensure proper JSON escaping for your shell):
```bash
# Bash/Zsh/PowerShell
kleos kb query product_faq "warranty information" --metadata-filter '{"product_line":"X Series", "year":{"$gte": 2023}}'

# Windows CMD
kleos kb query product_faq "warranty information" --metadata-filter "{\"product_line\":\"X Series\", \"year\":{\"$gte\": 2023}}"
```
*(Note on JSON parameters: Ensure correct quoting for your shell as described in the main README)*

---

## `kb list-databases`

Lists all available databases and datasources connected to your MindsDB instance.

This can be useful to verify datasource creation (like HackerNews) or to see all available data sources you can potentially ingest from or use with models.

**Usage:**
```bash
kleos kb list-databases [OPTIONS]
```

**Options:**

| Option       | Description                 |
|--------------|-----------------------------|
| `-h, --help` | Show help message and exit. |

**Example Output (example, actual output may vary):**
![](./public/Kleos%20List%20Databases%20Execute.jpeg)


---

## `kb create-agent <agent_name>`

Creates an AI Agent in MindsDB, linking it to Knowledge Bases and/or tables.

Agents use an LLM (specified by `--model-name`) to answer questions or perform tasks based on the data provided from the included KBs and tables. The `model` parameter in the `USING` clause of `CREATE AGENT` refers to the LLM itself.

**Usage:**
```bash
kleos kb create-agent <agent_name> --model-name <model_name> --include-knowledge-bases <kb_names_list> [OPTIONS]
```

**Arguments:**

| Argument       | Description              |
|----------------|--------------------------|
| `AGENT_NAME`   | Name for the new AI Agent. |

**Options:**

| Option                             | Description                                                                                                                               |
|------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `--model-name TEXT`                | (Required) LLM model to power the agent (e.g., 'gemini-1.5-flash', 'llama3', 'openai/gpt-4'). This is the `model` parameter in `CREATE AGENT`. |
| `--include-knowledge-bases TEXT` | (Required) Comma-separated list of Knowledge Base names for the agent to use as its knowledge source.                                       |
| `--google-api-key TEXT`            | Your Google API key. Required if using a Google LLM (e.g., Gemini) and not globally configured in MindsDB.                                |
| `--include-tables TEXT`            | Comma-separated list of additional table names (format: 'datasource.tablename') to provide context to the agent.                          |
| `--prompt-template TEXT`           | A custom prompt template guiding the agent's behavior and response format. Use `{{question}}` and `{{context}}` placeholders.             |
| `--other-params TEXT`              | JSON string for other parameters to pass to the agent's `USING` clause (e.g., `'{\"temperature\": 0.7}'`). Refer to MindsDB docs for model-specific params. |
| `-h, --help`                       | Show help message and exit.                                                                                                               |

**Examples:**

Create an agent using Google Gemini and linked to KBs:
```bash
# Ensure GOOGLE_GEMINI_API_KEY is in your .env or provide --google-api-key
kleos kb create-agent my_kb_assistant --model-name gemini-2.0-flash \
  --include-knowledge-bases "product_docs_kb,faq_kb" \
  --include-tables "product_db.products,faq_db.faq_entries" \
  --prompt-template "Answer based on provided documents: {{question}}"
```

Create an agent using Google Gemini model (ensure MindsDB integration is set up, cause this command works asynchronously so no callback check):
```bash
# PowerShell/Bash/Zsh
kleos kb create-agent --model-name gemini-2.0-flash --include-knowledge-bases ["hn_kb_test"] --google-api-key "YOUR_GEMINI_API_KEY" --include-tables ["hackernews.hnstories"] --prompt-template "You are a wise scholar who knows everything about the current YC hackernews"

kleos kb create-agent --model-name gemini-2.0-flash --include-knowledge-bases ["gemini_kb_5"] --google-api-key "AIzaSyCiYSVMSw3ZF2ijcRloS2Y36X_m9qLof9k" --include-tables ["hackernews.stories"] --prompt-template "You are a wise scholar who knows everything about the current YC hackernews"
```

---

## `kb query-agent <agent_name> <question>`

Queries an existing AI Agent with a natural language question.

The agent will use its configured LLM and linked Knowledge Bases/tables to generate an answer.

**Usage:**
```bash
kleos kb query-agent <agent_name> <question> [OPTIONS]
```

**Arguments:**

| Argument     | Description                                             |
|--------------|---------------------------------------------------------|
| `AGENT_NAME` | Name of the AI Agent to query.                          |
| `QUESTION`   | The natural language question to ask the AI Agent.      |

**Options:**

| Option       | Description                 |
|--------------|-----------------------------|
| `-h, --help` | Show help message and exit. |

**Example:**
```bash
kleos kb query-agent my_kb_assistant "How do I reset my password?"
```

---

## `kb evaluate <kb_name>`

Evaluates a Knowledge Base's retrieval accuracy and relevance using a test dataset.

This command can operate in two main modes specified by `--version`:
1.  `doc_id`: Checks if the KB returns the expected document ID for given questions. The `--test-table` should contain at least `question` and `expected_doc_id` columns.
2.  `llm_relevancy`: Uses a specified LLM to evaluate the relevance of the content returned by the KB for given questions. The `--test-table` should contain at least a `question` column, and optionally `expected_content` or `expected_answer` columns for more detailed evaluation.

Test data can be automatically generated from the KB itself (using `--generate-data`) or from a custom SQL query (using `--generate-data-from-sql`). If generating data, the specified `--test-table` will be created and populated. Results can be printed to the console or saved to a MindsDB table using `--save-to-table`.

**Usage:**
```bash
kleos kb evaluate <kb_name> --test-table <datasource.table_name> [OPTIONS]
```

**Arguments:**

| Argument    | Description                                |
|-------------|--------------------------------------------|
| `KB_NAME`   | Name of the Knowledge Base to evaluate.    |

**Options:**

| Option                             | Description                                                                                                                              | Default    |
|------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|------------|
| `--test-table TEXT`                | (Required) Test table for evaluation in 'datasource.table_name' format. Structure depends on `--version`.                                |            |
| `--version TEXT`                   | Evaluation version: 'doc_id' or 'llm_relevancy'.                                                                                         | `doc_id`   |
| `--generate-data`                  | Flag to enable automatic test data generation (fetches from the KB being evaluated).                                                       |            |
| `--generate-data-from-sql TEXT`  | SQL query to fetch data for test data generation. E.g., `"SELECT q, id FROM src.tests"`.                                               |            |
| `--generate-data-count INTEGER`    | Number of test data items to generate if data generation is active.                                                                        | `20`       |
| `--no-evaluate`                    | If set, only generates test data (if generation options active) and saves to `--test-table` without running the evaluation.              |            |
| `--llm-provider TEXT`              | LLM provider for evaluation (e.g., 'google', 'openai', 'ollama'), required if `version='llm_relevancy'`.                                  |            |
| `--llm-api-key TEXT`               | API key for the LLM provider, if required.                                                                                               |            |
| `--llm-model-name TEXT`            | Name of the LLM model for evaluation (e.g., 'gemini-1.5-flash'), required if `version='llm_relevancy'`.                                    |            |
| `--llm-base-url TEXT`              | Base URL for the LLM provider (e.g., for local Ollama).                                                                                  |            |
| `--llm-other-params TEXT`          | JSON string for other LLM parameters (e.g., `'{\"method\":\"multi-class\"}'`). Example: `'{\"key\":\"value\"}'`.                            |            |
| `--save-to-table TEXT`             | Table to save evaluation results, in 'datasource.table_name' format. If not provided, results are printed to console.                   |            |
| `-h, --help`                       | Show help message and exit.                                                                                                              |            |

**Examples:**

Evaluate using `doc_id` version with an existing test table:
```bash
kleos kb evaluate my_docs_kb --test-table my_project.eval_questions --version doc_id
```

Generate test data and evaluate using LLM relevancy with Google Gemini, saving results:
```bash
# Ensure GOOGLE_GEMINI_API_KEY is in .env or provide --llm-api-key
kleos kb evaluate sales_kb --test-table my_project.generated_sales_eval \\
  --generate-data --generate-data-count 30 --version llm_relevancy \\
  --llm-provider google --llm-model-name gemini-pro
  --save-to-table my_project.sales_eval_results
```

Only generate test data from a custom SQL query and save it (no evaluation run):
```bash
kleos kb evaluate main_kb --test-table tests.custom_data \\
  --generate-data-from-sql "SELECT query as question, answer as expected_answer FROM source_db.qa_pairs" \\
  --generate-data-count 50 --no-evaluate
```
*(Note on JSON parameters: Ensure correct quoting for your shell as described in the main README)*

---

# AI Model Commands (`ai`)

Commands for managing and querying AI Models, often called 'Generative AI Tables' in MindsDB.

These models are created from your data using a `CREATE MODEL ... FROM (SELECT ...)` SQL statement. They can be used for various tasks such as text classification, summarization, translation, or other generative AI tasks, depending on the chosen engine and prompt template.

---

## `ai create-model <model_name>`

Creates an AI Model (Generative AI Table) by training it on data from a SELECT query.

This command constructs a `CREATE MODEL ... FROM (SELECT ...) PREDICT ... USING ...` SQL statement. The `MODEL_NAME` will be created in the specified `--project-name` or the default connected project.

`--select-data-query` provides the training data. Ensure columns referenced in the prompt template are selected in this query. `--predict-column` is the target variable the AI Model will learn to generate. `--engine` specifies the underlying LLM or ML engine. `--prompt-template` guides the model's generation process. Use `{{column_name}}` for features. `--param` allows passing engine-specific parameters like API keys, model variants (e.g., 'gpt-4'), temperature, etc.

**Usage:**
```bash
kleos ai create-model <model_name> --select-data-query <query> --predict-column <column> [OPTIONS]
```

**Arguments:**

| Argument      | Description                     |
|---------------|---------------------------------|
| `MODEL_NAME`  | Name for the new AI Model.      |

**Options:**

| Option                     | Description                                                                                                                               | Default    |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|------------|
| `--project-name TEXT`      | MindsDB project where the model will be created. Defaults to the currently connected project.                                               |            |
| `--select-data-query TEXT` | (Required) SQL SELECT query to fetch training data. E.g., `'SELECT text, cat FROM ds.train_data'`.                                        |            |
| `--predict-column TEXT`    | (Required) Name of the column the AI Model should learn to predict or generate.                                                             |            |
| `--engine TEXT`            | AI engine to use (e.g., 'openai', 'google_gemini', 'anthropic', 'ollama'). Check MindsDB docs.                                            | `openai`   |
| `--prompt-template TEXT`   | Prompt template for the AI Model. Use `{{column_name}}` for placeholders. E.g., `'Summarize: {{text_column}}'`.                               |            |
| `--param TEXT TEXT`        | Additional `USING` parameters as key-value pairs. Specify multiple times for multiple params. E.g., `--param model_name gpt-4 --param temp 0.7`. |            |
| `-h, --help`               | Show help message and exit.                                                                                                               |            |

**Examples:**

Create a text summarizer using OpenAI:
```bash
kleos ai create-model story_summarizer
  --select-data-query "SELECT title, text, score FROM hackernews.hnstories" 
  --predict-column summary --engine google_gemini
  --prompt-template "Summarize the {{text}} of the hackernews stories, with {{title}}, {{score}} and explain in short passage." 
  --param api_key YOUR_GEMINI_KEY --param model_name "gemini-2.0-flash"
```

Create a sentiment classifier using Google Gemini:
```bash
# Ensure GOOGLE_GEMINI_API_KEY is in .env or provide --param api_key YOUR_GOOGLE_KEY
kleos ai create-model review_sentiment \\
  --select-data-query "SELECT review, sentiment FROM my_reviews.data" \\
  --predict-column sentiment --engine google_gemini \\
  --prompt-template "Classify sentiment: {{review}}"
```

---

## `ai list-models`

Lists all AI Models within a specified MindsDB project.

If `--project-name` is not provided, it lists models from the default connected project. Output includes model name, status, engine, version, and other relevant details, presented in a table.

**Usage:**
```bash
kleos ai list-models [OPTIONS]
```

**Options:**

| Option                | Description                                                                                      |
|-----------------------|--------------------------------------------------------------------------------------------------|
| `--project-name TEXT` | MindsDB project from which to list models. Defaults to the currently connected project.        |
| `-h, --help`          | Show help message and exit.                                                                      |

**Example:**
```bash
kleos ai list-models --project-name my_nlp_project
```
List models in the current project:
```bash
kleos ai list-models
```

![](./public/Kleos%20AI%20list-model%20Exeucte.jpeg)
---

## `ai describe-model <model_name>`

Shows detailed information about a specific AI Model.

This includes the model's schema (input and output columns), current status (e.g., training, complete, error), version, the original training query, and any error messages if the model failed. The output is presented as a key-value table.

**Usage:**
```bash
kleos ai describe-model <model_name> [OPTIONS]
```

**Arguments:**

| Argument     | Description                         |
|--------------|-------------------------------------|
| `MODEL_NAME` | Name of the AI Model to describe.   |

**Options:**

| Option                | Description                                                                                |
|-----------------------|--------------------------------------------------------------------------------------------|
| `--project-name TEXT` | MindsDB project where the model resides. Defaults to the currently connected project.    |
| `-h, --help`          | Show help message and exit.                                                                |

**Example:**
```bash
kleos ai describe-model news_summarizer --project-name my_nlp_project
```

![](./public/Kleos%20AI%20describe-model%20Exeucte.jpeg)
---

## `ai drop-model <model_name>`

Drops (deletes) a specified AI Model from a MindsDB project.

This action is irreversible and will remove the model and its associated training artifacts. You will be prompted for confirmation before deletion.

**Usage:**
```bash
kleos ai drop-model <model_name> [OPTIONS]
```

**Arguments:**

| Argument     | Description                       |
|--------------|-----------------------------------|
| `MODEL_NAME` | Name of the AI Model to drop.     |

**Options:**

| Option                | Description                                                                                |
|-----------------------|--------------------------------------------------------------------------------------------|
| `--project-name TEXT` | MindsDB project where the model resides. Defaults to the currently connected project.    |
| `-h, --help`          | Show help message and exit.                                                                |

**Example:**
```bash
kleos ai drop-model old_text_classifier --project-name my_nlp_project
```
*(You will be prompted: "Are you sure you want to drop this AI Model? This action is irreversible.")*

![](./public/Kleos%20AI%20drop-model%20Exeucte.jpeg)

---

## `ai refresh-model <model_name>`

Refreshes an existing AI Model.

This typically involves retraining the model with the latest data from its original data source, using its original training parameters (effectively running `RETRAIN model_name;` in SQL). The model status will change to 'training' or 'generating' during this process.

**Usage:**
```bash
kleos ai refresh-model <model_name> [OPTIONS]
```

**Arguments:**

| Argument     | Description                           |
|--------------|---------------------------------------|
| `MODEL_NAME` | Name of the AI Model to refresh.      |

**Options:**

| Option                | Description                                                                                |
|-----------------------|--------------------------------------------------------------------------------------------|
| `--project-name TEXT` | MindsDB project where the model resides. Defaults to the currently connected project.    |
| `-h, --help`          | Show help message and exit.                                                                |

**Example:**
```bash
kleos ai refresh-model news_summarizer
```

---

## `ai query <query_string>`

Executes an arbitrary SQL query against the MindsDB project.

This is commonly used to query AI Models by joining them with data tables or selecting from them with a `WHERE` clause that provides input to the model. Ensure your query string correctly references table and model names, including project and datasource prefixes if necessary (e.g., `mindsdb.my_model`, `my_datasource.input_data`).

**Usage:**
```bash
kleos ai query <query_string> [OPTIONS]
```

**Arguments:**

| Argument        | Description                                                                                      |
|-----------------|--------------------------------------------------------------------------------------------------|
| `QUERY_STRING`  | The SQL query to execute. Enclose in quotes if it contains spaces or special characters.        |

**Options:**

| Option                | Description                                                                                           |
|-----------------------|-------------------------------------------------------------------------------------------------------|
| `--project-name TEXT` | MindsDB project context for the query. Defaults to the currently connected project.                 |
| `-h, --help`          | Show help message and exit.                                                                           |

**Examples:**

Query an AI Model 'my_summarizer_model' by joining with HackerNews data:
```bash
kleos ai query "SELECT t.title, t.text, m.summary FROM hackernews.hnstories AS t JOIN mindsdb.test_model_4 AS m WHERE t.score > 100 LIMIT 2"
```

Directly query a model 'my_translator_model' that takes input via a WHERE clause:
```bash
kleos ai query "SELECT * FROM mindsdb.my_translator_model WHERE text_to_translate = 'Hello world' AND target_language = 'Spanish'"
```

---

# Job Commands (`job`)

Commands for managing and monitoring MindsDB Jobs.

MindsDB Jobs are used to automate SQL-based tasks, such as periodic data
ingestion, model retraining, or any sequence of SQL commands that need to
be executed on a schedule or triggered by certain conditions.

---

## `job update-hn-refresh <job_name>`

Creates a specific MindsDB Job to periodically refresh the HackerNews database.

This job automates the process of dropping the existing HackerNews datasource (specified by `--hn-datasource`) and recreating it, ensuring the data is kept up-to-date according to the defined `--schedule`.

**Usage:**
```bash
kleos job update-hn-refresh <job_name> [OPTIONS]
```

**Arguments:**

| Argument    | Description                     |
|-------------|---------------------------------|
| `JOB_NAME`  | A unique name for the new job.  |

**Options:**

| Option                | Description                                                                                                                    | Default         |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------|-----------------|
| `--hn-datasource TEXT`| The name of the HackerNews datasource in MindsDB that this job will refresh.                                                     | `hackernews`    |
| `--schedule TEXT`     | Schedule interval for the job, using MindsDB's `SCHEDULE` syntax (e.g., 'EVERY 1 hour', 'EVERY 1 day at 03:00').                | `EVERY 1 day`   |
| `--project TEXT`      | MindsDB project where the job should be created. Defaults to the currently connected project.                                    |                 |
| `-h, --help`          | Show help message and exit.                                                                                                    |                 |

**Example:**
```bash
kleos job update-hn-refresh hn_update_job --hn-datasource my_hndb --schedule "EVERY 1 day"
```

---

## `job list`

Lists all MindsDB jobs in a specified project or the current project.

Displays information such as job name, creation date, schedule, status, and the next run time in a table format.

**Usage:**
```bash
kleos job list [OPTIONS]
```

**Options:**

| Option           | Description                                                                                               |
|------------------|-----------------------------------------------------------------------------------------------------------|
| `--project TEXT` | Filter jobs by a specific MindsDB project name. If omitted, lists jobs from the currently connected project. |
| `-h, --help`     | Show help message and exit.                                                                               |

**Example:**
```bash
kleos job list --project my_automations
```
List jobs in the current project:
```bash
kleos job list
```

![](./public/Kleos%20Jobs.jpeg)
---

## `job status <job_name>`

Get the current status and details of a specific MindsDB job.

This includes information like the last execution time, next run time, and current status (e.g., active, inactive, error), displayed in a table.

**Usage:**
```bash
kleos job status <job_name> [OPTIONS]
```

**Arguments:**

| Argument    | Description                               |
|-------------|-------------------------------------------|
| `JOB_NAME`  | The name of the job to get status for.    |

**Options:**

| Option           | Description                                                                                          |
|------------------|------------------------------------------------------------------------------------------------------|
| `--project TEXT` | MindsDB project where the job is located. Defaults to the currently connected project.               |
| `-h, --help`     | Show help message and exit.                                                                          |

**Example:**
```bash
kleos job status daily_hackernews_refresh --project my_automations
```

![](./public/Kleos%20Jobs%20status%20Execute.jpeg)

---

## `job history <job_name>`

Get the execution history of a specific MindsDB job.

Shows records of past job runs, including start time, end time, status, and any error messages, displayed in a table.
*Note: Job history is often stored in a `log.jobs_history` table which might require specific permissions or configuration in MindsDB to access.*

**Usage:**
```bash
kleos job history <job_name> [OPTIONS]
```

![](./public/Kleos%20Jobs%20History%20Execute.jpeg)

**Arguments:**

| Argument    | Description                                                  |
|-------------|--------------------------------------------------------------|
| `JOB_NAME`  | The name of the job to retrieve execution history for.       |

**Options:**

| Option           | Description                                                                                                                  |
|------------------|------------------------------------------------------------------------------------------------------------------------------|
| `--project TEXT` | MindsDB project where the job is located. Defaults to the currently connected project. History is typically in the 'log' database. |
| `-h, --help`     | Show help message and exit.                                                                                                  |

**Example:**
```bash
kleos job history daily_hackernews_refresh
```

---

## `job create <job_name> <sql_statements>`

Create a generic MindsDB job with one or more custom SQL statements.

Allows for flexible automation of tasks using SQL. `SQL_STATEMENTS` should be a single string containing one or more SQL commands, separated by semicolons. If your SQL statements contain quotes, ensure they are properly escaped or that the entire `SQL_STATEMENTS` string is quoted in a way that your shell understands.

**Usage:**
```bash
kleos job create <job_name> <sql_statements> [OPTIONS]
```

**Arguments:**

| Argument         | Description                                                                                                                                   |
|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `JOB_NAME`       | A unique name for the new job.                                                                                                                |
| `SQL_STATEMENTS` | The SQL statements the job will execute. Multiple statements should be separated by semicolons. Enclose in quotes if containing spaces/special chars. |

**Options:**

| Option              | Description                                                                                                                              |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| `--project TEXT`    | MindsDB project where the job should be created. Defaults to the currently connected project.                                            |
| `--schedule TEXT`   | Schedule interval for the job, using MindsDB's `SCHEDULE` syntax (e.g., 'EVERY 1 hour', 'EVERY MONDAY AT 09:00').                         |
| `--start-date TEXT` | Job start date/time. Format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.                                                                      |
| `--end-date TEXT`   | Job end date/time. Format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.                                                                        |
| `--if-condition TEXT`| A SQL query (as a string) that must return rows for the job to execute. E.g., `"SELECT 1 FROM my_table WHERE new_data_flag = TRUE"`.      |
| `-h, --help`        | Show help message and exit.                                                                                                              |

**Example:**
```bash
kleos job create my_nightly_ingest
  "INSERT INTO main_table SELECT * FROM staging_table WHERE date = CURRENT_DATE; DELETE FROM staging_table;" 
  --schedule "EVERY 1 day"
```

---

## `job logs <job_name>`

Get the logs or details of a specific MindsDB job.

*Note: Currently, this command primarily shows the job's status information (similar to `job status`) as detailed execution logs might reside in specific system tables (e.g., `log.jobs_history` or `information_schema.jobs_history`) which can vary by MindsDB setup and version. For in-depth execution logs, direct SQL queries using `kleos ai query` might be necessary.*

**Usage:**
```bash
kleos job logs <job_name> [OPTIONS]
```

**Arguments:**

| Argument    | Description                                        |
|-------------|----------------------------------------------------|
| `JOB_NAME`  | The name of the job to get logs/details for.       |

**Options:**

| Option           | Description                                                                                          |
|------------------|------------------------------------------------------------------------------------------------------|
| `--project TEXT` | MindsDB project where the job is located. Defaults to the currently connected project.               |
| `-h, --help`     | Show help message and exit.                                                                          |

**Example:**
```bash
kleos job logs daily_hackernews_refresh
```

![](./public/Kleos%20Jobs%20Logs%20Execute.jpeg)

---

## `job drop <job_name>`

Drops (deletes) a specified MindsDB job.

This action is irreversible. You will be prompted for confirmation.

**Usage:**
```bash
kleos job drop <job_name> [OPTIONS]
```

**Arguments:**

| Argument    | Description                             |
|-------------|-----------------------------------------|
| `JOB_NAME`  | The name of the job to drop/delete.     |

**Options:**

| Option           | Description                                                                                                |
|------------------|------------------------------------------------------------------------------------------------------------|
| `--project TEXT` | MindsDB project where the job is located. Defaults to the currently connected project if not specified.    |
| `-h, --help`     | Show help message and exit.                                                                                |

**Example:**
```bash
kleos job drop my_nightly_ingest
```
*(You will be prompted: "Are you sure you want to drop this job? This action is irreversible.")*

![](./public/Kleos%20Jobs%20Drop%20Execute.jpeg)


---

# Best Practices & Troubleshooting

(This section can be expanded or refined based on common user feedback)

## Best Practices
1.  **Use Virtual Environments**: Always use a Python virtual environment (`venv`, `conda`, `uv venv`) when working with Kleos and its dependencies.
2.  **Start Small**: When ingesting data or training models, start with small limits or datasets (`--limit 10`) to verify configurations before running large jobs.
3.  **Descriptive Naming**: Use clear, descriptive names for Knowledge Bases, AI Models, and Jobs.
4.  **Check Datasources**: Use `kleos kb list-databases` to confirm datasource existence and names before referencing them.
5.  **Validate JSON**: For complex JSON parameters, use an online validator or linter to check syntax before passing them to Kleos commands.
6.  **Environment Configuration**: Ensure `.env` (or `config/config.py`) is correctly set up with API keys and connection details for MindsDB, Ollama, and any other services.
7.  **Review Logs**: If commands fail or behave unexpectedly, check the MindsDB server logs and the Kleos console output for error messages.

## Troubleshooting Common Issues
1.  **JSON Parsing Errors**:
    *   Usually due to incorrect quoting/escaping for your shell. See the "JSON Parameter Handling" section above.
    *   Error messages like "Expecting value: line 1 column 1" often indicate a malformed or empty JSON string due to shell interpretation.
2.  **Connection Errors**:
    *   Verify MindsDB (and Ollama, if used) is running and accessible at the host/port specified in your Kleos configuration.
    *   Check network connectivity, firewalls, and Docker container port mappings.
    *   Ensure `MINDSDB_HOST`, `MINDSDB_PORT`, `OLLAMA_BASE_URL` in your `.env` file are correct.
3.  **"Table not found" / "Datasource not found"**:
    *   Ensure the datasource (e.g., `hackernews`) has been created in MindsDB (e.g., via `kleos setup hackernews`).
    *   Verify the table name is correct (e.g., 'stories', 'comments' for HackerNews).
    *   Check for typos in datasource or table names.
4.  **"Column not found"**:
    *   Verify that the columns you are referencing (e.g., in `--content-columns`, `--metadata-map`, or SQL queries) actually exist in the source table with the exact spelling.
5.  **Model/Agent Creation Failures**:
    *   Check that the specified model name for an engine (e.g., `gemini-1.5-flash` for Google, `nomic-embed-text` for Ollama) is correct and available to your MindsDB instance.
    *   Ensure any required API keys (e.g., `GOOGLE_GEMINI_API_KEY`) are correctly configured in `.env` or passed as parameters.
    *   For Ollama models, ensure they have been pulled into your Ollama instance (e.g., `ollama pull nomic-embed-text`).
    *   Consult MindsDB server logs for more detailed error messages from the ML engines.

## Getting Help
*   Use the `--help` option with any command or subcommand (e.g., `kleos --help`, `kleos kb --help`, `kleos kb create --help`) to see available options and descriptions.
*   Refer to this `Command-references.md` document.
*   Check the main `README.md` for setup, installation, and configuration details.
*   For MindsDB-specific issues or features, consult the official [MindsDB Documentation](https://docs.mindsdb.com/).
```

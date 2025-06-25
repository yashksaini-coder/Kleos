# Kleos-Quira CLI Commands Reference

This document provides detailed information on all available CLI commands, their options, and platform-specific usage examples.

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
        --embedding-provider ollama \
        --embedding-model nomic-embed-text \
        --embedding-base-url "http://host.docker.internal:11434" \
        --reranking-provider google \
        --reranking-model gemini-1.5-flash \
        --reranking-api-key "YOUR_GOOGLE_API_KEY" \
        --content-columns "text" \  
        --metadata-columns "title,score,descendants" \
        --id-column "id"
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
        --content-columns "text" \
        --metadata-columns "title,score,descendants" \
        --id-column "id"
    ```
    ```cmd
    REM Windows Command Prompt (ensure correct JSON escaping if any complex params were JSON)
    python main.py kb create my_mixed_provider_kb 
        --embedding-provider ollama 
        --embedding-model nomic-embed-text 
        --embedding-base-url "http://host.docker.internal:11434"
        --reranking-provider google 
        --reranking-model gemini-1.5-flash 
        --reranking-api-key "YOUR_GOOGLE_API_KEY" \
        --content-columns "text" \
        --metadata-columns "title,score,descendants" \
        --id-column "id"
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

### `kb create-agent` - Create an AI Agent for a Knowledge Base

Creates an AI agent that can answer questions using a specific Knowledge Base as its knowledge source.

**Usage:**
```bash
python main.py kb create-agent <agent_name> <kb_name> --model-name <model> [options]
```

**Arguments:**
- `<agent_name>`: Name for the new agent
- `<kb_name>`: Name of the Knowledge Base to use as knowledge source
- `--model-name`: AI model to use (e.g., gemini-pro, gpt-4, etc.)
- `--agent-params`: JSON parameters for the agent configuration (optional)

**Common Agent Parameters:**
- `temperature`: Controls randomness (0.0-1.0)
- `prompt_template`: Custom prompt template for the agent
- `max_tokens`: Maximum response length
- `api_key`: Model-specific API key (if not in environment)

**Examples:**

**PowerShell/Bash/Zsh:**
```bash
# Basic agent creation
python main.py kb create-agent my_kb_agent my_documents_kb --model-name gemini-pro

# Agent with custom temperature and prompt
python main.py kb create-agent hn_expert hn_stories_kb --model-name gemini-pro --agent-params '{"temperature":0.2, "prompt_template":"You are an expert analyst of HackerNews content. Answer questions based on the provided articles."}'

# Agent with specific API configuration
python main.py kb create-agent research_assistant research_kb --model-name gpt-4 --agent-params '{"temperature":0.1, "max_tokens":500, "api_key":"your-openai-key"}'
```

**Windows Command Prompt:**
```cmd
RUN Basic agent creation
python main.py kb create-agent my_kb_agent my_documents_kb --model-name gemini-pro
```

```cmd
RUN Agent with custom temperature and prompt
python main.py kb create-agent hn_expert hn_stories_kb --model-name gemini-pro --agent-params "{\"temperature\":0.2, \"prompt_template\":\"You are an expert analyst of HackerNews content. Answer questions based on the provided articles.\"}"
```

```cmd
RUN Agent with specific API configuration
python main.py kb create-agent research_assistant research_kb --model-name gpt-4 --agent-params "{\"temperature\":0.1, \"max_tokens\":500, \"api_key\":\"your-openai-key\"}"
```

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

---

## AI Commands

### `ai chat` - Interactive chat with AI models

Start an interactive chat session with various AI models.

**Usage:**
```bash
python main.py ai chat --model <model_name> [options]
```

**Arguments:**
- `--model`: AI model to use
- `--temperature`: Sampling temperature (optional)
- `--max-tokens`: Maximum tokens in response (optional)

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

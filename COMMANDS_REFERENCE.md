# Kleos-Quira CLI Commands Reference

This document provides detailed information on all available CLI commands, their options, and platform-specific usage examples.

## JSON Parameter Handling

When passing complex parameters as JSON strings via options like `--metadata-map`, `--metadata-filter`, or `--agent-params`, ensure they are correctly quoted and escaped for your specific command-line shell.

### Windows Command Prompt (`cmd.exe`)
- Enclose the entire JSON string in double quotes (`"`)
- Escape all inner double quotes with a backslash (`\"`)
- Example: `--metadata-map "{\"key\":\"value\"}"`

### PowerShell, Bash, Zsh
- Enclose the JSON string in single quotes (`'`)
- Example: `--metadata-map '{"key":"value"}'`

---

## Setup Commands

### `setup hackernews` - Setup HackerNews Datasource

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

## Knowledge Base Commands

### `kb create` - Create a new Knowledge Base

Creates a new Knowledge Base with specified embedding and reranking models.

**Usage:**
```bash
python main.py kb create <kb_name> --embedding-model <model> --reranking-model <model> [options]
```

**Required Arguments:**
- `<kb_name>`: Name of the Knowledge Base to create
- `--embedding-model`: Embedding model to use (e.g., nomic-embed-text)  
- `--reranking-model`: Reranking model to use (e.g., llama3)

**Optional Arguments:**
- `--content-columns`: Comma-separated list of columns to use as content (default: auto-detect based on table)
- `--metadata-columns`: Comma-separated list of columns to store as metadata (default: auto-detect based on table)
- `--id-column`: Column to use as unique identifier (default: id)

**Examples:**
```bash
# Basic KB creation
python main.py kb create my_documents_kb --embedding-model nomic-embed-text --reranking-model llama3

# KB with custom content and metadata columns for HackerNews stories
python main.py kb create hn_stories_kb --embedding-model nomic-embed-text --reranking-model llama3 --content-columns "title,text" --metadata-columns "id,by,score,time" --id-column id

# KB optimized for comments
python main.py kb create hn_comments_kb --embedding-model nomic-embed-text --reranking-model llama3 --content-columns "text" --metadata-columns "id,by,parent,time" --id-column id
```

### `kb ingest` - Ingest data into a Knowledge Base

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
REM Simple ingestion with auto-detected columns
python main.py kb ingest my_documents_kb --from-hackernews stories --limit 50

REM Custom content columns only
python main.py kb ingest my_documents_kb --from-hackernews stories --content-columns title --limit 100

REM Custom content and metadata mapping
python main.py kb ingest my_documents_kb --from-hackernews stories --content-columns title --metadata-map "{\"story_id\":\"id\", \"author\":\"by\", \"score\":\"score\"}" --limit 100

REM Ingest comments with custom mapping
python main.py kb ingest comment_kb --from-hackernews comments --metadata-map "{\"comment_id\":\"id\", \"author\":\"by\", \"parent_story\":\"parent\"}" --limit 200
```

### `kb query` - Query a Knowledge Base

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
REM Basic query
python main.py kb query my_documents_kb "latest trends in AI"

REM Query with result limit
python main.py kb query my_documents_kb "Python programming tips" --limit 5

REM Query with metadata filter
python main.py kb query my_documents_kb "machine learning" --metadata-filter "{\"author\":\"tech_expert\", \"score\":{\"$gt\":50}}"

REM Search specific topics in HackerNews stories
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
REM Basic agent creation
python main.py kb create-agent my_kb_agent my_documents_kb --model-name gemini-pro

REM Agent with custom temperature and prompt
python main.py kb create-agent hn_expert hn_stories_kb --model-name gemini-pro --agent-params "{\"temperature\":0.2, \"prompt_template\":\"You are an expert analyst of HackerNews content. Answer questions based on the provided articles.\"}"

REM Agent with specific API configuration
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
python main.py kb query-agent my_kb_agent "What are the main topics discussed in the articles?"

# Query HackerNews expert agent
python main.py kb query-agent hn_expert "What are the most popular programming languages mentioned in recent stories?"

# Complex analytical query
python main.py kb query-agent research_assistant "Summarize the key trends in AI research from the past year and identify emerging themes."
```

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

2. **Table not found**: Ensure the HackerNews datasource is set up and the table name is correct (usually 'stories' or 'comments').

3. **Column not found**: Verify that the columns you're referencing actually exist in the source table.

4. **Agent creation failures**: Check that the model name is correct and any required API keys are configured.

5. **Connection errors**: Verify MindsDB is running and accessible at the configured host/port.

### Getting Help

- Use `--help` with any command to see available options
- Check the main README.md for setup and configuration details
- Verify your environment configuration matches the examples in the documentation

# MindsDB CLI & Knowledge Base Toolkit

[![MindsDB](https://img.shields.io/badge/Powered%20by-MindsDB-blue)](https://mindsdb.com)

This project provides a powerful Command Line Interface (CLI) for interacting with MindsDB, with a special focus on its Knowledge Base features and AI Agent integration. It also includes a suite of scripts for performance benchmarking, stress testing, and evaluating MindsDB's reranking capabilities.

**Detailed Documentation:**
*   For a comprehensive guide to all CLI commands, options, and examples, please see [**COMMANDS_REFERENCE.md**](./COMMANDS_REFERENCE.md).
*   For an in-depth article covering project architecture, workflow, and code explanations, refer to [**ARTICLE.md**](./ARTICLE.md).

## Features

*   **CLI (`main.py`)**:
    *   Manage MindsDB datasources (e.g., setup HackerNews).
    *   Create, index, and query Knowledge Bases.
    *   Ingest data into Knowledge Bases from sources like HackerNews.
    *   Create and query AI Agents linked to Knowledge Bases (e.g., using Google Gemini).
    *   Automate ingestion using MindsDB Jobs.
    *   Create and query general AI models/tables (e.g., using Google Gemini for classification).
*   **Reporting Scripts (`src/report_scripts/`)**:
    *   **Performance Benchmarking**: Measure ingestion times and query latencies.
    *   **Stress Testing**: Test system stability under heavy load.
    *   **Reranking Evaluation**: Compare search results with and without reranking.
*   **Docker Support**: Includes a `Dockerfile` to build and run the CLI tool in a containerized environment.

## 1. Setup and Installation

### 1.1. Prerequisites

*   Python 3.8+
*   Access to a running MindsDB instance (local or cloud).
    *   Ensure Ollama is running and accessible if you plan to use default Ollama models for embeddings/reranking (e.g., `ollama pull nomic-embed-text`, `ollama pull llama3`).
*   Google Gemini API Key if using Google Gemini models for AI Agents or general AI tables.
*   (Optional) Docker for containerized execution.

### 1.2. Installation Steps

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 1.3. Configuration

The application requires configuration for connecting to MindsDB and for API keys.

1.  **Copy the example configuration file:**
    ```bash
    cp config/config.py.example config/config.py
    ```
    Alternatively, set environment variables directly. The application prioritizes environment variables.

2.  **Edit `config/config.py` or set environment variables:**
    *   **MindsDB Connection:** `MINDSDB_HOST`, `MINDSDB_PORT`, `MINDSDB_USER` (optional), `MINDSDB_PASSWORD` (optional).
    *   **Google Gemini API Key (required for Google AI features):** `GOOGLE_GEMINI_API_KEY`.
    *   **Ollama Settings (if using default models):** `OLLAMA_BASE_URL`, `OLLAMA_EMBEDDING_MODEL`, `OLLAMA_RERANKING_MODEL`.

    **Using a `.env` file (recommended for local development):**
    Create a `.env` file in the project root (add this file to `.gitignore`):
    ```env
    MINDSDB_HOST="http://127.0.0.1"
    MINDSDB_PORT=47334
    GOOGLE_GEMINI_API_KEY="your_gemini_key"
    OLLAMA_BASE_URL="http://127.0.0.1:11434"
    # Add other variables as needed
    ```
    `python-dotenv` (in `requirements.txt`) will load these variables.

## 2. Usage

### 2.1. CLI (`main.py`)

The main CLI application is run using `python main.py`.

**General Help:**
```bash
python main.py --help
```
This lists available command groups: `ai`, `job`, `kb`, `setup`.

**Important Note on JSON Parameters:**

When passing complex parameters as JSON strings via options like `--metadata-map`, `--metadata-filter`, or `--agent-params`, ensure they are correctly quoted and escaped for your specific command-line shell. Incorrect quoting is a common source of errors.

*   **For Windows Command Prompt (`cmd.exe`):** Typically, you'll need to enclose the entire JSON string in double quotes (`"`) and escape all inner double quotes with a backslash (`\"`).
    Example: `--metadata-map "{\"key\":\"value\"}"`
*   **For Linux/macOS (bash, zsh) or PowerShell:** Often, enclosing the JSON string in single quotes (`'`) is sufficient:
    Example: `--metadata-map '{"key":"value"}'`

For more detailed examples and explanations for different shells, please consult the [**COMMANDS_REFERENCE.md**](./COMMANDS_REFERENCE.md) file.

**Detailed Command Reference:**
For detailed information on all commands, options, and examples, please consult the [**COMMANDS_REFERENCE.md**](./COMMANDS_REFERENCE.md) file.

**Quick Examples:**

*   **Setup HackerNews Datasource:**
    ```bash
    python main.py setup hackernews --name my_hackernews_db
    ```
*   **Create a Knowledge Base:**
    ```bash
    python main.py kb create my_documents_kb --embedding-model nomic-embed-text
    ```
*   **Ingest Data into a Knowledge Base (Windows CMD/PowerShell example):**
    ```bash
    python main.py kb ingest my_documents_kb --from-hackernews stories --content-column title --metadata-map "{\"doc_id\":\"id\"}" --limit 50
    ```
*   **Query a Knowledge Base (Windows CMD/PowerShell example with filter):**
    ```bash
    python main.py kb query my_documents_kb "latest trends in AI"
    python main.py kb query my_documents_kb "search specific topic" --metadata-filter "{\"author\":\"some_user\"}"
    ```
*   **Create an AI Agent for a Knowledge Base (Windows CMD/PowerShell example with params):**
    ```bash
    python main.py kb create-agent my_kb_agent my_documents_kb --model-name gemini-pro --agent-params "{\"temperature\":0.2, \"prompt_template\":\"Answer questions based on the KB.\"}"
    # (Ensure GOOGLE_GEMINI_API_KEY is configured if using Google provider and api_key isn't in --agent-params)
    ```
*   **Query the AI Agent:**
    ```bash
    python main.py kb query-agent my_kb_agent "Summarize articles about Python."
    ```

### 2.2. Reporting Scripts (`src/report_scripts/`)

These standalone scripts perform specific evaluations and generate JSON reports.

1.  **Run from the project root directory.**
    Use the `--help` flag on any script to see its specific options.
    ```bash
    python src/report_scripts/benchmark_report.py --help
    ```

2.  **Performance Benchmark Report:**
    ```bash
    python src/report_scripts/benchmark_report.py --kb-name benchmark_test --ingestion-sizes 100 500
    ```

3.  **Stress Test Report:**
    ```bash
    python src/report_scripts/stress_test_report.py --kb-name stress_test_run --initial-load 1000
    ```

4.  **Reranking Evaluation Report:**
    ```bash
    python src/report_scripts/reranking_eval_report.py --kb-no-reranker kb_baseline --kb-with-reranker kb_reranked
    ```
    *Remember to manually fill in the `"qualitative_analysis_notes"` in the generated JSON report for this script.*

## 3. Docker Usage

A `Dockerfile` is provided to build and run the CLI application.

1.  **Build the Docker image:**
    ```bash
    docker build -t mindsdb-cli-app .
    ```

2.  **Run the CLI tool using Docker:**
    Use `--env-file` to pass your `.env` file for configuration.
    ```bash
    docker run -it --rm --env-file .env mindsdb-cli-app kb query my_docker_kb "search via docker"
    ```
    Or pass environment variables individually:
    ```bash
    docker run -it --rm -e MINDSDB_HOST="http://host.docker.internal:47334" mindsdb-cli-app --help
    ```
    *(Note: `host.docker.internal` can be used to access services running on your host machine from Docker Desktop).*

## 4. Project Internals & Development

For a detailed understanding of the project's architecture, code structure, and workflows, please see [**ARTICLE.md**](./ARTICLE.md).

The core logic for MindsDB interactions is encapsulated in `src/core/mindsdb_handler.py`.
CLI commands are defined in modules within `src/commands/`.

## 5. Contributing

Contributions are welcome! Please follow standard fork-and-pull-request workflows. Ensure documentation is updated for any new features or changes.

---

<a href="https://github.com/yashksaini-coder">
    <table>
        <tbody>
            <tr>
                <td align="left" valign="top" width="14.28%">
                    <img src="https://github.com/yashksaini-coder.png?s=60" width="130px;"/>
                    <br/>
                    <h4 align="center">
                        <b>Yash K. Saini</b>
                    </h4>
                    <div align="center">
                        <p>(Author)</p>
                    </div>
                </td>
                <td align="left" valign="top" width="85%">
                    <p>
                        👋 Hi there! I'm <u><em><strong>Yash K. Saini</strong></em></u>, a self-taught software developer and a computer science student from India.
                    </p>
                    <ul>
                     <li>
                        Building products & systems that can benefit & solve problems for many other DEVs.
                    </li>
                </td>
            </tr>
        </tbody>
    </table>
</a>
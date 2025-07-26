# Quick Examples

## Setup
```bash
setup hackernews --name test_Hn
```

## Knowledge Base Operations

### Create Knowledge Base
```bash
kb create hn_stories_kb --embedding-model nomic-embed-text --reranking-provider ollama --reranking-model gemma3 --content-columns 'title,text' --metadata-columns 'id,by,score,time' --id-column id

kb create gemini_kb --embedding-provider ollama --embedding-model nomic-embed-text --reranking-provider ollama --reranking-provider google --reranking-model gemini-2.0-flash --reranking-api-key AIzaSyCiYSVMSw3ZF2ijcRloS2Y36X_m9qLof9k --content-columns text --metadata-columns 'score,title' --id-column id
```

### Ingest Data
```bash
kleos kb ingest my_hn_kb --from-hackernews stories --limit 500
```

### List Databases
```bash
kleos kb list-databases
```

### Create Agent
```bash
kb create-agent --model-name gemini-2.0-flash --include-knowledge-bases ["hn_kb_test"] --google-api-key "YOUR_GEMINI_API_KEY" --include-tables ["hackernews.hnstories"] --prompt-template "You are a wise scholar who knows everything about the current YC hackernews"
```

### Query Agent
```bash
kb query-agent hn_agent5 "total number of stories ?"
```

## AI Model Operations

### List Models
```bash
ai list-models
```

### Create Model
```bash
ai create-model story_summarizer --select-data-query "SELECT title, text, score FROM hackernews.hnstories" --predict-column summary --engine google_gemini --prompt-template "Summarize the {{text}} of the hackernews stories, with {{title}}, {{score}} and explain in short passage." --param api_key YOUR_GEMINI_KEY --param model_name "gemini-2.0-flash"
```

### Describe Model
```bash
ai describe-model story_summarizer
```

### Query with Model
```bash
ai query "SELECT t.title, t.text, m.summary FROM hackernews.hnstories AS t JOIN mindsdb.test_model_4 AS m WHERE t.score > 100 LIMIT 2"
```

### Refresh Model
```bash
ai refresh-model test_model_4
```

### Drop Model
```bash
ai drop-model test_model_4
```

## Job Management

### Update Job
```bash
job update-hn-refresh hn_update_job --hn-datasource my_hndb --schedule "EVERY 1 day"
```

### List Jobs
```bash
job list
```

### Job Status
```bash
job status hn_update_job
```

### Job History
```bash
job history hn_update_job
```

### Create Job
```bash
job create my_nightly_ingest "INSERT INTO main_table SELECT * FROM staging_table WHERE date = CURRENT_DATE; DELETE FROM staging_table;" --schedule "EVERY 1 day"

job create refresh_hn "DROP DATABASE IF EXISTS hackernews; CREATE DATABASE hackernews WITH ENGINE = 'hackernews';" --schedule "EVERY 1 day"

```

### Job Logs
```bash
job logs
```

### Drop Job
```bash
job drop my_nightly_ingest
```
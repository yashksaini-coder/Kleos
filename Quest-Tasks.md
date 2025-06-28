# 🌡️ 019: Help MindsDB stress-test KBs!

[MindsDB](https://mindsdb.com/) is an AI data solution that enables humans, agents, and applications to query data in natural language and SQL across disparate data sources and types.

Recently, MindsDB released [🔗 Knowledge Bases (KBs)](https://docs.mindsdb.com/mindsdb_sql/knowledge-bases#how-knowledge-bases-work) which allow you to store and retrieve information using semantic search capabilities. The goal of this quest is to help MindsDB stress-test this release by creating a functional application (CLI, Web App, API, Bot Interface etc.) where the primary interaction or feature relies on the semantic query results from the KB.

This quest has two stages with two different prize pools.

> [!NOTE]
> _Submissions collecting 85 points or more will be considered valid submissions and receive a badge for this quest._

---

### **🛠️ [40 pts] Build an app with KBs**  

Build a functional application (CLI, Web App, API, Bot Interface etc.) where the primary interaction or feature relies on the semantic query results from the KB. To claim these points make sure:

- [X] Your app executes [🔗 `CREATE KNOWLEDGE_BASE`](https://docs.mindsdb.com/mindsdb_sql/knowledge-bases#create-knowledge-base-syntax)
- [X] Your app ingests data using [🔗 `INSERT INTO knowledge_base`](https://docs.mindsdb.com/mindsdb_sql/knowledge-bases#insert-into-syntax)
- [X] Your app retrieves relevant data based on on semantic queries [🔗 `SELECT ... FROM ... WHERE content LIKE '<query>'`](https://docs.mindsdb.com/mindsdb_sql/knowledge-bases#select-from-kb-syntax)
- [X] Your app uses [🔗 `CREATE INDEX ON KNOWLEDGE_BASE`](https://docs.mindsdb.com/mindsdb_sql/knowledge-bases#create-index-on-knowledge-base-syntax)

> [!IMPORTANT]  
> MindsDB KBs by default use ChromaDB and it provides the index features by default. [Docs](https://docs.mindsdb.com/mindsdb_sql/knowledge-bases#create-index-on-knowledge-base-syntax)

---

### - [X] **🛠️ [10 pts]  Use metadata columns**  

Define [🔗 `metadata_columns`](https://docs.mindsdb.com/mindsdb_sql/knowledge-bases#metadata-columns) during ingestion and use `WHERE` clauses that combine semantic search with SQL attribute filtering on `metadata_columns`.

---

### - [X] **🛠️ [10 pts] Integrate JOBS**

Set up a [🔗 `MindsDB JOB`](https://docs.mindsdb.com/rest/jobs/create#create-a-job) that periodically checks a data source and inserts *new* data into the KB (using LAST or similar logic).

---

### - [X] **🛠️ [10 pts] Integrate with AI Tables or Agents**

Build a multi-step workflow within MindsDB by taking the results from a KB semantic query and feeding them as input into another [🔗 `MindsDB AI Table`](https://docs.mindsdb.com/generative-ai-tables#what-are-generative-ai-tables) (e.g., for summarisation, classification, generation).

---

### - [X] **✍️ [30 pts] Upload a video and write a nice README**  

You can claim this if:

- [x] You upload a short video demo explaining the app & showcasing the KB interaction.
- [x] Your project has a `README.md` with clear setup instructions.

---

### - [X] **✍️ [5 pts] Document the process and showcase your app** 

Write an article on DevTo, HashNode, Medium, or any blogging platform of your choice to document how you built this app and to showcase the practical product use cases for these features.

---

### - [X] **✍️ [5 pts] Give feedback and suggest features**

You submit the [🔗 Product Feedback Form](https://quira-org.typeform.com/to/magewvh9). Extra points might be given here if you suggest really good features 😉

---

### - [X] **🎁 [10 pts] Secret Challenge #1 --> Integreate `CREATE Agent`**

Projects that integrate [`CREATE Agent`](https://docs.mindsdb.com/mindsdb_sql/agents/agent) will be rewarded with an additional 10 points.

---

### - [X] **🎁  [10 pts] Secret Challenge #2 --> Integrate `EVALUATE KNOWLEDGE_BASE`**

_To be announced on June 24th, 2025_


## 2️⃣ Bug-hunt & stress-testing [$1,000 prize pool]

If you made it here, you can use your app to catch bugs and test the performance of the system. To claim these rewards you must have created an app in the previous section.


| Points | Rewarded if |
| --- | --- |
| 💵 **$100** | You find an unknown critical bug. |
| 💵 **$20-$100** | You create a Performance Benchmarking report. |
| 💵 **$20-$100** | You create a Stress Testing report. |
| 💵 **$20-$100** | You create a Reranking Evaluation report. |

> [!NOTE]
> You can submit as many reports as you want, but we care more about quality than quantity. Ech report must be a shareable URL. For example, a Google Doc, a PDF on Dropbox, etcetera. Make sure the link is set to “_anyone with the link can view_.” To submit, paste the link into the “_Additional Link_” fields in the submission panel.
> Also note that rewards will be issued until the prize pool is depleted. We will be reviewing submissions regularly and informing participants on the state of the prize pool.

---

### - [X] 🏷️ **Bug Hunting** [**$100 per unknown critical bug**]

Rigorously test the functionality of your KB across all steps: creation, ingestion, querying, different data types, edge cases. If you find a bug, submit a GitHub issue in https://github.com/mindsdb/mindsdb/issues and provide clear steps to reproduce it.

*You can see all submitted bugs by filtering issues by the `bug` label.*

---

### - [ ] 🏷️ **Performance Benchmarking** [**$20-$100 per report**]

Create a reproducible benchmark report to provide concrete performance numbers for specific scenarios. For example, select a reasonably sized dataset (e.g., 10k, 100k, 1M+ rows, specify size), document their test environment (hardware/cloud specs, MindsDB version/config), methodology (e.g., script used), and report clear metrics (e.g., total ingestion time, time per 1k records, average/p95/p99 query latency over N queries of varying complexity).

*Rewards will be allocated based on how much insight the report provides critical optimisation areas.*

---

### - [ ] 🏷️ **Stress Testing** [**$20-$100 per report**]

Stress-test the system by systematically increasing load. For example, by using very large datasets, a high number of concurrent queries, or deeply nested/complex semantic queries, until KB operations either fail or exhibit unacceptable latency. Create a report to document the configuration used, load parameters, sequence of steps executed, and the observed failure mode or point of performance degradation.

*Rewards will be allocated based on how much insight the report provide about scalability boundaries.*

---

### - [ ] 🏷️ **Reranking Effectiveness Evaluation** [**$20-$100 per report**]

Demonstrating the impact (positive or negative) of the reranking feature on search relevance for specific types of queries: set up two KBs (or query one KB with/without the reranker enabled via session settings) using the same data and define a set of nuanced/ambiguous queries where simple vector similarity might be insufficient. Execute these queries on both setups and produce a qualitative comparative analysis report with concrete examples (e.g., showing side-by-side results, explaining *why* the reranked results are better/worse/different, assessing overall relevance improvement). 
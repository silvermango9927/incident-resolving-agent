Agents Overview

Folders/files of interest:

- analyzer-helpers/
  - build_vector_db.py: Convert consolidated CSV into Chroma collections (incidents_cache, problems_cache)
  - cache_requests.py: Duplicate detection via Chroma with CSV spaCy fallback
  - remediation_cache.py: Duplicate detection for remediation problems
  - vector_db_utils.py: Chroma helpers and embedder
- knowledge_base_ingest.py: Index PDFs from knowledge_base/ into kb_docs collection
- cause_analysis_agent.py: Cache check + KB search + (stub) GCRNN + ranking
- remediation_agent.py: Supervised baseline + RL-ready harness
- execution_agent.py: Contact selection, email drafting/sending, summary rendering
- orchestrator.py: Wires agents together and emits JSON/Markdown/HTML summary

How to prepare data (manual run, do not execute automatically):

1. Build vector DB from CSV

   - Ensure processed CSV exists at agents/analyzer-helpers/data/processed-data/consolidated_incidents.csv
   - Run:
     python -m agents.analyzer-helpers.build_vector_db --csv agents/analyzer-helpers/data/processed-data/consolidated_incidents.csv

2. Index knowledge base PDFs

   - Place PDFs under knowledge_base/
   - In Python or CLI, call:
     from agents.knowledge_base_ingest import index_kb_pdfs
     index_kb_pdfs(Path('knowledge_base'))

3. Orchestrate an incident
   - Example:
     python -m agents.orchestrator --summary "Database connection failures after deploy" --time "2025-10-20 10:30" --sender "oncall@example.com" --component "database"

SMTP and dry run

- Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS to send email. Without them, the system returns dry-run.

Optional local LLM

- You can integrate an ollama/llama.cpp step to polish email or summary text. The current build uses Jinja templates and works fully without an LLM.

# Orchestration Agent

This directory contains the MCP (Model Context Protocol) orchestration agent for incident resolution.

## Requirements

- Python 3.10 or higher
- fastmcp library (already installed for Python 3.10)

## Running the Orchestration Agent

The orchestration agent must be run with Python 3.10+ due to fastmcp requirements:

```bash
python3.10 orchestration_agent.py
```

## Architecture

### Tools (Functions)

The orchestration agent provides three callable tools:

1. **FunctionA** - General data processing

   - Input: `input_data` (string)
   - Output: Processed result dictionary

2. **FunctionB** - Parameter-based operations

   - Input: `parameters` (dictionary)
   - Output: Result dictionary with processed parameters

3. **FunctionC** - Task and action execution
   - Input: `task_id` (string), `action` (string)
   - Output: Task execution result dictionary

### Resources (Data Sources)

The agent provides access to multiple data sources:

1. **knowledge-base://pdfs** - PDF documents in the knowledge_base folder
2. **knowledge-base://documents** - All documents in the knowledge_base folder
3. **resources://available** - Additional resources
4. **ui://connection-status** - UI connection status (to be implemented)

### Prompts

Pre-defined interaction patterns:

1. **incident_analysis_prompt** - Structured incident analysis
2. **orchestration_prompt** - Task orchestration guidance

## Directory Structure

```
incident-resolving-agent/
├── agents/
│   ├── orchestration_agent.py    # Main MCP server
│   └── README.md                 # This file
├── knowledge_base/               # PDF and document storage
├── resources/                    # Additional resources
└── requirements.txt
```

## Adding Knowledge Base Documents

Place your PDF documents and other reference materials in the `knowledge_base/` directory. The orchestration agent will automatically detect and provide access to them through the MCP resources.

## Future Development

- Implement concrete logic for FunctionA, FunctionB, and FunctionC
- Add UI connection handler
- Integrate with other agents in the `agents/` directory
- Add document parsing capabilities for PDF knowledge base

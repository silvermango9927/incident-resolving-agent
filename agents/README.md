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

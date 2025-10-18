# Orchestration Agent Setup Guide

## Overview

The orchestration agent is an MCP (Model Context Protocol) server that coordinates incident resolution by providing callable tools and access to knowledge base resources.

## Prerequisites

- **Python 3.10 or higher** (fastmcp requirement)
- fastmcp library

## Installation

1. Ensure Python 3.10+ is installed:

```bash
python3.10 --version
```

2. Install dependencies (already installed):

```bash
python3.10 -m pip install fastmcp
```

## Quick Start

### Running the Orchestration Agent

```bash
cd agents
python3.10 orchestration_agent.py
```

### Testing the Agent

Run the test client to verify all functionality:

```bash
cd agents
python3.10 test_client.py
```

## Architecture

### MCP Server Components

#### 1. Tools (Callable Functions)

- **function_a** - General data processing
- **function_b** - Parameter-based operations
- **function_c** - Task and action execution

#### 2. Resources (Data Sources)

- **knowledge-base://pdfs** - PDF documents
- **knowledge-base://documents** - All document types
- **resources://available** - Additional resources
- **ui://connection-status** - UI connection (planned)

#### 3. Prompts

- **incident_analysis_prompt** - Structured incident analysis
- **orchestration_prompt** - Task orchestration guidance

## Project Structure

```
incident-resolving-agent/
├── agents/
│   ├── orchestration_agent.py    # Main MCP server
│   ├── test_client.py            # Test client
│   └── README.md                 # Agent documentation
├── knowledge_base/               # PDF and document storage
│   └── README.md
├── resources/                    # Additional resources
│   └── README.md
├── incident-analyzer-hackathon/  # Web UI (separate component)
├── requirements.txt
└── PROJECT_SETUP.md             # This file
```

## Usage Examples

### Connecting to the Agent

```python
from fastmcp import Client
from orchestration_agent import mcp as server

async def example():
    client = Client(server)
    async with client:
        # Call a tool
        result = await client.call_tool("function_a",
            {"input_data": "example"})

        # Access a resource
        docs = await client.read_resource("knowledge-base://pdfs")

        # Get a prompt
        prompt = await client.get_prompt("incident_analysis_prompt",
            {"incident_description": "Server issue"})
```

### Adding Knowledge Base Documents

1. Place PDF files in `knowledge_base/` directory
2. Agent automatically detects them
3. Access via `knowledge-base://pdfs` resource

## Python Version Note

⚠️ **Important**: The orchestration agent MUST be run with Python 3.10 or higher because:

- fastmcp requires Python 3.10+
- Modern async features are used
- Type hints require Python 3.10+ syntax

If you see import errors for fastmcp in VS Code, this is because the default Python environment is 3.8. The code will run correctly when executed with Python 3.10.

## Next Steps

1. **Implement Function Logic**: Update FunctionA, FunctionB, and FunctionC with actual orchestration logic
2. **Add PDF Parsing**: Integrate PDF parsing libraries to extract content from knowledge base
3. **Connect UI**: Implement the UI connection handler
4. **Add More Agents**: Create additional agents in the `agents/` directory
5. **Enhance Resources**: Add more sophisticated resource access patterns

## Integration with Other Components

### Web UI (incident-analyzer-hackathon)

The Flask web application can connect to the orchestration agent to:

- Submit incidents for analysis
- Retrieve resolution recommendations
- Access knowledge base content

### Future Agents

Other agents can be created in the `agents/` directory and can:

- Communicate with the orchestration agent
- Share the knowledge base
- Coordinate on complex incident resolution tasks

## Troubleshooting

### Import Error for fastmcp

- **Symptom**: VS Code shows "Import 'fastmcp' could not be resolved"
- **Cause**: Workspace using Python 3.8, fastmcp installed for Python 3.10
- **Solution**: Run with `python3.10` command - the code will work correctly

### Server Not Starting

- Verify Python 3.10+ is being used
- Check fastmcp is installed: `python3.10 -m pip list | grep fastmcp`
- Ensure no port conflicts if running as HTTP server

## Contributing

When adding new functionality:

1. Update tool/resource/prompt decorators as needed
2. Add corresponding tests in test_client.py
3. Update documentation in READMEs
4. Ensure Python 3.10+ compatibility

## License

[Add license information here]

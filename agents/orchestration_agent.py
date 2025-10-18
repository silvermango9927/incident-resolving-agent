import asyncio
from pathlib import Path
from typing import Any, Dict, List
from fastmcp import FastMCP

mcp = FastMCP("Orchestration Agent")

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
RESOURCES_DIR = BASE_DIR / "resources"

KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)
RESOURCES_DIR.mkdir(exist_ok=True)

# TOOLS

@mcp.tool()
async def function_a(input_data: str) -> Dict[str, Any]:
    """
    FunctionA: Placeholder for future implementation.
    This function will be implemented to handle specific orchestration tasks.
    
    Args:
        input_data: Input data for processing
    
    Returns:
        Dictionary containing the result of the operation
    """
    return {
        "status": "success",
        "function": "FunctionA",
        "message": "FunctionA executed successfully",
        "input": input_data,
        "result": f"Processed: {input_data}"
    }


@mcp.tool()
async def function_b(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    FunctionB: Placeholder for future implementation.
    This function will be implemented to handle specific orchestration tasks.
    
    Args:
        parameters: Dictionary of parameters for processing
    
    Returns:
        Dictionary containing the result of the operation
    """
    return {
        "status": "success",
        "function": "FunctionB",
        "message": "FunctionB executed successfully",
        "parameters": parameters,
        "result": f"Processed parameters: {list(parameters.keys())}"
    }


@mcp.tool()
async def function_c(task_id: str, action: str) -> Dict[str, Any]:
    """
    FunctionC: Placeholder for future implementation.
    This function will be implemented to handle specific orchestration tasks.
    
    Args:
        task_id: Unique identifier for the task
        action: Action to be performed
    
    Returns:
        Dictionary containing the result of the operation
    """
    return {
        "status": "success",
        "function": "FunctionC",
        "message": "FunctionC executed successfully",
        "task_id": task_id,
        "action": action,
        "result": f"Task {task_id} - Action {action} completed"
    }


# RESOURCES (Data sources)

@mcp.resource("knowledge-base://pdfs")
async def get_pdf_knowledge_base() -> str:
    """
    Provides access to the PDF knowledge base.
    This resource will contain incident resolution documentation and guidelines.
    
    Returns:
        Information about available PDF documents in the knowledge base
    """
    pdf_files = list(KNOWLEDGE_BASE_DIR.glob("*.pdf"))
    
    if not pdf_files:
        return "No PDF files found in knowledge base. Please add PDF documents to the knowledge_base folder."
    
    file_list = "\n".join([f"- {pdf.name}" for pdf in pdf_files])
    return f"Available PDF documents in knowledge base:\n{file_list}"


@mcp.resource("knowledge-base://documents")
async def get_all_documents() -> str:
    """
    Provides access to all documents in the knowledge base.
    
    Returns:
        Information about all available documents
    """
    all_files = list(KNOWLEDGE_BASE_DIR.glob("*"))
    files = [f for f in all_files if f.is_file()]
    
    if not files:
        return "No documents found in knowledge base. Please add documents to the knowledge_base folder."
    
    file_list = "\n".join([f"- {file.name} ({file.suffix})" for file in files])
    return f"Available documents in knowledge base ({len(files)} total):\n{file_list}"


@mcp.resource("ui://connection-status")
async def get_ui_connection_status() -> str:
    """
    Provides information about the UI connection status.
    This will be used when the user interface is connected.
    
    Returns:
        Current UI connection status
    """
    # This will be implemented when UI is connected
    return "UI connection: Not yet implemented. This resource will provide real-time UI connection status."


@mcp.resource("resources://available")
async def get_available_resources() -> str:
    """
    Lists all available resources in the resources directory.
    
    Returns:
        Information about available resources
    """
    resource_files = list(RESOURCES_DIR.glob("*"))
    files = [f for f in resource_files if f.is_file()]
    
    if not files:
        return "No additional resources found. Resources directory is empty."
    
    file_list = "\n".join([f"- {file.name}" for file in files])
    return f"Available resources ({len(files)} total):\n{file_list}"


# PROMPTS (Pre-defined interaction patterns)

@mcp.prompt()
def incident_analysis_prompt(incident_description: str) -> str:
    """
    Generates a prompt for incident analysis.
    
    Args:
        incident_description: Description of the incident
    
    Returns:
        Formatted prompt for incident analysis
    """
    return f"""Analyze the following incident and provide a structured response:

Incident Description:
{incident_description}

Please provide:
1. Initial assessment of the incident
2. Potential root causes
3. Recommended actions
4. Priority level
5. Required resources from knowledge base
"""


@mcp.prompt()
def orchestration_prompt(task: str, context: str = "") -> str:
    """
    Generates a prompt for orchestration tasks.
    
    Args:
        task: The task to be orchestrated
        context: Additional context for the task
    
    Returns:
        Formatted prompt for orchestration
    """
    prompt = f"""Orchestration Task: {task}"""
    if context:
        prompt += f"\n\nContext:\n{context}"
    
    prompt += """

Available Functions:
- FunctionA: General data processing
- FunctionB: Parameter-based operations
- FunctionC: Task and action execution

Available Resources:
- knowledge-base://pdfs - PDF documents
- knowledge-base://documents - All documents
- resources://available - Additional resources
- ui://connection-status - UI connection info

Please determine the appropriate sequence of function calls and resources to use.
"""
    return prompt

# Server Management

async def main():
    """
    Main function to run the orchestration agent server.
    """
    # Run the FastMCP server
    await mcp.run()


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())
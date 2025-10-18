from flask import Flask, render_template, request, jsonify, send_file
import time
import csv
import io
import json
import re
import asyncio
from datetime import datetime
from openai import OpenAI
from fastmcp import Client

app = Flask(__name__)

# Initialize OpenAI client
client_openai = OpenAI()

# Initialize MCP client (assuming orchestration agent is running)
mcp_client = Client("http://127.0.0.1:8000") # Default FastMCP server address

# Store the last analysis result for CSV download
last_analysis_result = None

async def get_incident_analysis_prompt_from_mcp(incident_description: str) -> str:
    """
    Retrieves the incident analysis prompt from the MCP orchestration agent.
    """
    try:
        async with mcp_client:
            prompt = await mcp_client.get_prompt("incident_analysis_prompt", {"incident_description": incident_description})
            return prompt
    except Exception as e:
        print(f"Error getting prompt from MCP: {e}")
        # Fallback to a default prompt if MCP is unavailable or errors
        return f"""You are an expert incident response analyst. Analyze the following incident log or report and provide a structured response in JSON format.

Incident Content:
{incident_description}

Provide your analysis in the following JSON format (return ONLY valid JSON, no other text):
{{
    "root_cause": "A detailed explanation of the root cause based on the incident data",
    "remediation_steps": [
        "Step 1: First action to take",
        "Step 2: Second action to take",
        "Step 3: Third action to take",
        "Step 4: Fourth action to take",
        "Step 5: Fifth action to take"
    ],
    "escalation_summary": "A multi-line summary for escalation purposes with key details about the incident, severity, duration, impact, and resolution",
    "ticket_status": "PROJ-XXXX"
}}

Ensure the response is valid JSON that can be parsed. Make the analysis specific to the incident content provided."""

async def analyze_incident_with_ai(content: str) -> dict:
    """
    Analyze incident content using OpenAI API, with the prompt retrieved from the MCP agent.
    """
    try:
        # Get the analysis prompt from the MCP orchestration agent
        analysis_prompt_template = await get_incident_analysis_prompt_from_mcp(content)
        
        # Call OpenAI API
        response = client_openai.chat.completions.create(
            model="gpt-4.1-mini", # Using gpt-4.1-mini as specified in environment
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert incident response analyst. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": analysis_prompt_template
                }
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        # Extract the response text
        response_text = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        analysis_result = json.loads(response_text)
        
        # Ensure all required fields are present
        if "root_cause" not in analysis_result:
            analysis_result["root_cause"] = "Unable to determine root cause from the provided incident data."
        if "remediation_steps" not in analysis_result:
            analysis_result["remediation_steps"] = [
                "Review the incident logs in detail",
                "Identify affected systems and services",
                "Implement temporary mitigation measures",
                "Deploy permanent fix or patch",
                "Monitor system for recurrence"
            ]
        if "escalation_summary" not in analysis_result:
            analysis_result["escalation_summary"] = "Incident analysis completed. See root cause and remediation steps above."
        if "ticket_status" not in analysis_result:
            analysis_result["ticket_status"] = "PROJ-AUTO"
        
        return analysis_result
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return {
            "root_cause": "The incident analysis could not be completed due to a processing error. Please review the incident logs manually.",
            "remediation_steps": [
                "Review incident logs for error patterns",
                "Check system health and resource availability",
                "Verify database and service connectivity",
                "Implement monitoring and alerting",
                "Schedule post-incident review"
            ],
            "escalation_summary": "Incident analysis encountered an error. Manual review recommended.",
            "ticket_status": "PROJ-ERROR"
        }
    except Exception as e:
        print(f"Error during analysis: {e}")
        return {
            "root_cause": f"An error occurred during analysis: {str(e)}",
            "remediation_steps": [
                "Check the incident data format",
                "Verify system connectivity",
                "Retry the analysis",
                "Contact support if issues persist",
                "Document the incident for review"
            ],
            "escalation_summary": f"Analysis failed with error: {str(e)}",
            "ticket_status": "PROJ-FAILED"
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze endpoint that accepts either file upload or text input.
    Now integrated with OpenAI for real, dynamic incident analysis, using prompt from MCP agent.
    """
    global last_analysis_result
    
    content = None
    source_name = None
    
    if "file" in request.files and request.files["file"].filename != "":
        file = request.files["file"]
        source_name = file.filename
        try:
            content = file.read().decode("utf-8")
        except UnicodeDecodeError:
            return jsonify({"error": "File must be a valid text file (UTF-8 encoded)"}), 400
    elif "text" in request.form and request.form["text"].strip():
        content = request.form["text"]
        source_name = "Text Input"
    else:
        return jsonify({"error": "No file or text provided"}), 400
    
    if len(content.strip()) < 10:
        return jsonify({"error": "Incident content must be at least 10 characters long"}), 400
    
    try:
        # Run the async analysis function
        analysis_results = asyncio.run(analyze_incident_with_ai(content))
        
        analysis_results["filename"] = source_name
        analysis_results["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        last_analysis_result = analysis_results
        
        return jsonify(analysis_results)
        
    except Exception as e:
        print(f"Error in analyze endpoint: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route("/download-csv", methods=["GET"])
def download_csv():
    """
    Generate and download a CSV file with the analysis results.
    """
    global last_analysis_result
    
    if not last_analysis_result:
        return jsonify({"error": "No analysis results available"}), 400
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["Incident Analysis Report"])
    writer.writerow(["Generated:", last_analysis_result.get("timestamp", "N/A")])
    writer.writerow(["Source:", last_analysis_result.get("filename", "N/A")])
    writer.writerow([])
    
    writer.writerow(["Root Cause Analysis"])
    writer.writerow([last_analysis_result.get("root_cause", "")])
    writer.writerow([])
    
    writer.writerow(["Remediation Steps"])
    for i, step in enumerate(last_analysis_result.get("remediation_steps", []), 1):
        writer.writerow([f"{i}. {step}"])
    writer.writerow([])
    
    writer.writerow(["Escalation Summary"])
    for line in last_analysis_result.get("escalation_summary", "").split("\n"):
        writer.writerow([line])
    writer.writerow([])
    
    writer.writerow(["Ticket Status"])
    writer.writerow([f'Ticket {last_analysis_result.get("ticket_status", "N/A")} created successfully.'])
    
    output.seek(0)
    bytes_output = io.BytesIO()
    bytes_output.write(output.getvalue().encode("utf-8"))
    bytes_output.seek(0)
    
    filename = f'incident_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return send_file(
        bytes_output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Incident Analyzer",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


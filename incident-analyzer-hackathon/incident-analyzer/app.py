from flask import Flask, render_template, request, jsonify, send_file
import time
import csv
import io
import json
import re
import asyncio
import urllib.request
import os
import sys
from datetime import datetime
from pathlib import Path
import sys

# Add the agents directory to the path to import orchestration_agent
# sys.path.append(str(Path(__file__).parent.parent.parent / "agents"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "agents"))

app = Flask(__name__)

# Store the last analysis result for CSV download
last_analysis_result = None


def get_mcp_client():
    """
    Get an MCP client connected to the orchestration agent.
    Uses in-memory connection for reliability.
    """
    try:
        from fastmcp import Client
        from orchestration_agent import mcp as orchestration_server

        return Client(orchestration_server)
    except Exception as e:
        print(f"Warning: Could not initialize MCP client: {e}")
        return None


async def get_incident_analysis_prompt_from_mcp(incident_description: str) -> str:
    """
    Retrieves the incident analysis prompt from the MCP orchestration agent.
    """
    try:
        client = get_mcp_client()
        if client is None:
            raise Exception("MCP client not available")

        async with client:
            prompt_result = await client.get_prompt(
                "incident_analysis_prompt",
                {"incident_description": incident_description},
            )
            # Extract the text content from the prompt result
            if hasattr(prompt_result, "messages") and len(prompt_result.messages) > 0:
                prompt_text = str(prompt_result.messages[0].content)
                # Clean up the prompt text if it has extra formatting
                if prompt_text.startswith(
                    "type='text' text='"
                ) or prompt_text.startswith('type="text" text="'):
                    # Extract the actual text content
                    import re

                    match = re.search(
                        r"text=['\"](.+?)['\"](?:\s|$)", prompt_text, re.DOTALL
                    )
                    if match:
                        prompt_text = match.group(1)
                return prompt_text
            else:
                raise Exception("Invalid prompt structure")
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
        "Step 3: Third action to take"
    ],
    "escalation_summary": "A multi-line summary for escalation purposes with key details about the incident, severity, duration, impact, and resolution",
    "systems_thinking": "A causal-loop/systems-thinking analysis describing key variables, feedback loops, delays, and leverage points",
    "ticket_status": "PROJ-XXXX"
}}

IMPORTANT: At the end of your response, include an 'escalation_summary' block in this exact format (use the labels exactly as shown, and fill in values):

Details about the Incident Report
Time sent: <ISO-8601 or human-readable timestamp>
Sender: <name or system that sent the report>
Summary: <one-paragraph, concise summary suitable for escalation>

Also include a top-level 'systems_thinking' field that contains a causal-loop style analysis:
- List key variables (2-5)
- Describe at least one reinforcing loop (R) and one balancing loop (B)
- Note any key delays
- Propose 2-3 leverage points
- Optionally include a tiny ASCII causal-loop diagram

Ensure the response is valid JSON only. The 'escalation_summary' field must contain the multi-line block shown above as a single string value, and 'systems_thinking' must be a string with the causal-loop analysis.
"""


async def analyze_incident_with_ai(content: str) -> dict:
    """
    Analyze incident content using OpenAI API, with the prompt retrieved from the MCP agent.
    """
    try:
        # Get the analysis prompt from the MCP orchestration agent
        analysis_prompt_template = await get_incident_analysis_prompt_from_mcp(content)

        # Make sure we append an explicit instruction that enforces the escalation summary and systems-thinking format
        # This ensures enforcement even if the MCP prompt doesn't contain the instruction.
        enforcement_block = """

ADDITIONAL REQUIREMENT: At the end of your JSON response include both:
1) an 'escalation_summary' block in this exact format:

Details about the Incident Report
Time sent: <ISO-8601 or human-readable timestamp>
Sender: <name or system that sent the report>
Summary: <one-paragraph, concise summary suitable for escalation>

2) a 'systems_thinking' field containing a causal-loop / systems-thinking analysis. The 'systems_thinking' string must include:
- Key variables (2-5)
- At least one reinforcing loop and one balancing loop (label R1/B1)
- Noted delays affecting behavior
- 2-3 concrete leverage points
- Optionally a tiny ASCII causal-loop diagram

The entire output must be valid JSON only. 'escalation_summary' must be the multi-line block above as a single string value. 'systems_thinking' must be a string value with the causal-loop analysis.
"""
        full_user_prompt = analysis_prompt_template + enforcement_block

        url = "https://psacodesprint2025.azure-api.net/openai/deployments/gpt-4.1-nano/chat/completions?api-version=2025-01-01-preview"

        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if not api_key:
            return {
                "root_cause": "Azure OpenAI API key not configured. Please set the AZURE_OPENAI_API_KEY environment variable.",
                "remediation_steps": [],
                "escalation_summary": "Configuration error: Missing API key.",
                "systems_thinking": "Configuration error: Missing API key.",
                "ticket_status": "PROJ-CONFIG-ERROR",
            }

        hdr = {
            "Content-Type": "application/json",
            "api-key": api_key,
            "Cache-Control": "no-cache",
        }

        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert incident response analyst. Always respond with valid JSON only.",
                },
                {"role": "user", "content": full_user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1500,
        }

        data_json = json.dumps(data)
        req = urllib.request.Request(url, headers=hdr, data=data_json.encode("utf-8"))
        req.get_method = lambda: "POST"

        try:
            response = urllib.request.urlopen(req)
            response_data = json.loads(response.read().decode("utf-8"))
            response_text = response_data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as http_err:
            error_body = (
                http_err.read().decode("utf-8") if http_err.fp else str(http_err)
            )
            print(f"HTTP Error from API: {http_err.code} - {error_body}")
            return {
                "root_cause": f"API request failed with HTTP error {http_err.code}. Please check your API key and endpoint configuration.",
                "remediation_steps": [
                    "Verify the Azure OpenAI API key is correct",
                    "Check the API endpoint URL",
                    "Ensure your subscription has access to the deployment",
                    "Review API quota and rate limits",
                    "Contact API administrator if issues persist",
                ],
                "escalation_summary": f"API call failed with HTTP {http_err.code}: {error_body[:200]}",
                "ticket_status": "PROJ-API-ERROR",
            }
        except urllib.error.URLError as url_err:
            print(f"URL Error from API: {url_err}")
            return {
                "root_cause": f"Network error when connecting to API: {str(url_err.reason)}",
                "remediation_steps": [
                    "Check network connectivity",
                    "Verify firewall settings",
                    "Ensure DNS resolution is working",
                    "Check if API endpoint is reachable",
                    "Review proxy settings if applicable",
                ],
                "escalation_summary": f"Network connectivity issue: {str(url_err)}",
                "ticket_status": "PROJ-NETWORK-ERROR",
            }

        # Parse the JSON response
        if not response_text:
            return {
                "root_cause": "API returned empty response. Please check the API configuration.",
                "remediation_steps": [
                    "Verify API endpoint is correct",
                    "Check API deployment status",
                    "Review API request parameters",
                    "Check API logs for errors",
                    "Contact API administrator",
                ],
                "escalation_summary": "Empty response received from API.",
                "ticket_status": "PROJ-EMPTY-RESPONSE",
            }

        # Try to extract JSON from response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)

        try:
            analysis_result = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            print(f"JSON parsing error: {json_err}")
            print(f"Response text was: {response_text[:500]}")
            return {
                "root_cause": f"API returned invalid JSON. Response: {response_text[:200]}",
                "remediation_steps": [
                    "Check if the API model is responding correctly",
                    "Verify the prompt format is correct",
                    "Review API response format expectations",
                    "Try reducing the incident content size",
                    "Contact API support",
                ],
                "escalation_summary": f"Invalid JSON in API response: {str(json_err)}",
                "ticket_status": "PROJ-JSON-ERROR",
            }

        # Ensure all required fields are present
        if "root_cause" not in analysis_result:
            analysis_result["root_cause"] = (
                "Unable to determine root cause from the provided incident data."
            )
        if "remediation_steps" not in analysis_result:
            analysis_result["remediation_steps"] = [
                "Review the incident logs in detail",
                "Identify affected systems and services",
                "Implement temporary mitigation measures",
                "Deploy permanent fix or patch",
                "Monitor system for recurrence",
            ]
        if "escalation_summary" not in analysis_result:
            analysis_result["escalation_summary"] = (
                "Incident analysis completed. See root cause and remediation steps above."
            )
        if "ticket_status" not in analysis_result:
            analysis_result["ticket_status"] = "PROJ-AUTO"

        return analysis_result

    except KeyError as key_err:
        print(f"KeyError in API response: {key_err}")
        return {
            "root_cause": f"API response missing expected field: {str(key_err)}",
            "remediation_steps": [
                "Verify API response format",
                "Check API deployment configuration",
                "Review API documentation",
                "Ensure correct API version is being used",
                "Contact API administrator",
            ],
            "escalation_summary": f"API response format error: missing {str(key_err)}",
            "ticket_status": "PROJ-FORMAT-ERROR",
        }
    except Exception as e:
        print(f"Unexpected error during analysis: {e}")
        import traceback

        traceback.print_exc()
        return {
            "root_cause": f"An unexpected error occurred during analysis: {str(e)}",
            "remediation_steps": [
                "Check the incident data format",
                "Verify system connectivity",
                "Review application logs for details",
                "Retry the analysis",
                "Contact support if issues persist",
            ],
            "escalation_summary": f"Analysis failed with unexpected error: {str(e)}",
            "ticket_status": "PROJ-FAILED",
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
            return jsonify(
                {"error": "File must be a valid text file (UTF-8 encoded)"}
            ), 400
    elif "text" in request.form and request.form["text"].strip():
        content = request.form["text"]
        source_name = "Text Input"
    else:
        return jsonify({"error": "No file or text provided"}), 400

    if len(content.strip()) < 10:
        return jsonify(
            {"error": "Incident content must be at least 10 characters long"}
        ), 400

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
    writer.writerow(
        [
            f"Ticket {last_analysis_result.get('ticket_status', 'N/A')} created successfully."
        ]
    )

    output.seek(0)
    bytes_output = io.BytesIO()
    bytes_output.write(output.getvalue().encode("utf-8"))
    bytes_output.seek(0)

    filename = f"incident_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return send_file(
        bytes_output, mimetype="text/csv", as_attachment=True, download_name=filename
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "service": "Incident Analyzer",
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

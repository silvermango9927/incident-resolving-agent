from flask import Flask, render_template, request, jsonify, send_file
import time
import csv
import io
import json
import re
import asyncio
import urllib.request
import os
from datetime import datetime
from fastmcp import Client

app = Flask(__name__)

# Initialize MCP client (assuming orchestration agent is running)
mcp_client = Client("http://127.0.0.1:8000")  # Default FastMCP server address

# Store the last analysis result for CSV download
last_analysis_result = None


async def get_incident_analysis_prompt_from_mcp(incident_description: str) -> str:
    """
    Retrieves the incident analysis prompt from the MCP orchestration agent.
    """
    try:
        async with mcp_client:
            prompt = await mcp_client.get_prompt(
                "incident_analysis_prompt",
                {"incident_description": incident_description},
            )
            # prompt is an MCP prompt object; extract the generated text content
            return str(prompt.messages[0].content)
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

        data = json.dumps(data)
        req = urllib.request.Request(url, headers=hdr, data=bytes(data.encode("utf-8")))
        req.get_method = lambda: "POST"

        response = urllib.request.urlopen(req)

        response_text = ""
        # read response
        resp_body = response.read().decode("utf-8")
        # The exact parsing will depend on API response shape; attempt to parse for content
        try:
            resp_json = json.loads(resp_body)
            # If Azure OpenAI style: choices[0].message.content
            if "choices" in resp_json and len(resp_json["choices"]) > 0:
                response_text = resp_json["choices"][0]["message"]["content"]
            else:
                # fallback: raw text
                response_text = resp_body
        except Exception:
            response_text = resp_body

        # The model is instructed to return valid JSON only, so parse it
        try:
            parsed = json.loads(response_text)
            return parsed
        except Exception as e:
            # If parsing fails, return a helpful error structure
            return {
                "root_cause": "",
                "remediation_steps": [],
                "escalation_summary": f"ERROR: Failed to parse model response as JSON. Raw response: {response_text}",
                "systems_thinking": f"ERROR: Failed to parse model response as JSON. Raw response: {response_text}",
                "ticket_status": "PARSE-ERROR",
            }
    except Exception as e:
        return {
            "root_cause": f"Error calling AI: {e}",
            "remediation_steps": [],
            "escalation_summary": "Error during AI call",
            "systems_thinking": "Error during AI call",
            "ticket_status": "AI-CALL-ERROR",
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

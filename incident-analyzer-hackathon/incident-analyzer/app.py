from flask import Flask, render_template, request, jsonify, send_file
import time
import csv
import io
from datetime import datetime

app = Flask(__name__)

# Store the last analysis result for CSV download
last_analysis_result = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Simulated analysis endpoint.
    In production, this would call your Python backend for actual incident analysis.
    """
    global last_analysis_result
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Simulate processing time
    time.sleep(2)
    
    # Simulated analysis results
    results = {
        'root_cause': 'Database connection pool exhaustion caused by a memory leak in the connection handler. The pool reached maximum capacity (100 connections) at 14:23 UTC, preventing new database queries from executing.',
        'remediation_steps': [
            'Restart the database connection pool service to immediately restore functionality',
            'Deploy the hotfix patch (v2.3.1) that addresses the memory leak in the connection handler',
            'Increase the connection pool size from 100 to 200 as a temporary mitigation',
            'Implement connection timeout monitoring with alerts at 80% capacity threshold',
            'Schedule a full audit of database connection patterns across all services'
        ],
        'escalation_summary': '''Incident: Database Connection Pool Exhaustion
Severity: P1 - Critical
Duration: 23 minutes (14:23 - 14:46 UTC)
Impact: 100% of API requests failed during the incident window
Root Cause: Memory leak in connection handler
Resolution: Service restart + hotfix deployment
Follow-up: Connection pool monitoring enhancement required''',
        'ticket_status': 'PROJ-1234',
        'filename': file.filename,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Store for CSV download
    last_analysis_result = results
    
    return jsonify(results)

@app.route('/download-csv', methods=['GET'])
def download_csv():
    """
    Generate and download a CSV file with the analysis results.
    """
    global last_analysis_result
    
    if not last_analysis_result:
        return jsonify({'error': 'No analysis results available'}), 400
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Incident Analysis Report'])
    writer.writerow(['Generated:', last_analysis_result.get('timestamp', 'N/A')])
    writer.writerow(['Source File:', last_analysis_result.get('filename', 'N/A')])
    writer.writerow([])
    
    # Root Cause
    writer.writerow(['Root Cause Analysis'])
    writer.writerow([last_analysis_result.get('root_cause', '')])
    writer.writerow([])
    
    # Remediation Steps
    writer.writerow(['Remediation Steps'])
    for i, step in enumerate(last_analysis_result.get('remediation_steps', []), 1):
        writer.writerow([f'{i}. {step}'])
    writer.writerow([])
    
    # Escalation Summary
    writer.writerow(['Escalation Summary'])
    for line in last_analysis_result.get('escalation_summary', '').split('\n'):
        writer.writerow([line])
    writer.writerow([])
    
    # Ticket Status
    writer.writerow(['Ticket Status'])
    writer.writerow([f'Ticket {last_analysis_result.get("ticket_status", "N/A")} created successfully.'])
    
    # Prepare file for download
    output.seek(0)
    bytes_output = io.BytesIO()
    bytes_output.write(output.getvalue().encode('utf-8'))
    bytes_output.seek(0)
    
    filename = f'incident_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


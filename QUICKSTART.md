# Quick Start Guide

## Running the Incident Analyzer

To get started with the Incident Analyzer Flask application:

### Step 1: Navigate to the Application Directory

```bash
cd incident-analyzer-hackathon/incident-analyzer
```

### Step 2: Run the Flask Application

**Option A: Direct Python Command**

```bash
python3.10 app.py
```

**Option B: With Azure OpenAI API Key**

```bash
export AZURE_OPENAI_API_KEY='your-api-key-here'
python3.10 app.py
```

### Step 3: Access the Application

Once the server is running, open your web browser and navigate to:

```
http://localhost:5000
```

## Requirements

- **Python 3.10 or higher** (required for fastmcp compatibility)
- **Flask** (will be imported from requirements if installed)

## Testing

To verify the application is working correctly:

```bash
cd incident-analyzer-hackathon/incident-analyzer
python3.10 test_app.py
```

## Note About API Key

⚠️ The application will start without an Azure OpenAI API key, but incident analysis features will not work until you set the `AZURE_OPENAI_API_KEY` environment variable.

To set the API key:

```bash
export AZURE_OPENAI_API_KEY='your-actual-api-key'
```

Then start the application.

## Troubleshooting

- **Python version error**: Ensure you're using Python 3.10+

  ```bash
  python3.10 --version
  ```

- **Import errors**: The orchestration agent integration may show warnings if dependencies are missing, but the app will still work using fallback prompts.

- **Port already in use**: If port 5000 is already in use, modify the port in `app.py`:
  ```python
  app.run(debug=True, host="0.0.0.0", port=5001)  # Change to different port
  ```

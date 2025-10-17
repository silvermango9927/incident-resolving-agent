# Incident Analyzer - Hackathon Edition

A modern, visually stunning AI-powered incident analysis tool built with Flask, featuring a professional UI/UX design with rich animations, gradients, and full accessibility support.

## Features

### Design & Visual Appeal

The application features a **professional, modern interface** that goes far beyond basic design:

- **Vibrant Gradient Background**: Beautiful purple-to-pink gradient (light mode) and deep indigo gradient (dark mode)
- **Smooth Animations**: Fade-in effects, transitions, hover states, and micro-interactions
- **Rich Color System**: Comprehensive color palette with CSS custom properties
- **Professional Typography**: Inter font family with carefully crafted hierarchy
- **Advanced Shadows**: Multi-level shadow system for depth and elevation
- **Gradient Elements**: Buttons, badges, and cards with gradient backgrounds
- **Terminal-Style Code Blocks**: Dark theme with green monospace text for technical content

### User Experience

- **Intuitive File Upload**: Drag-and-drop with visual feedback and hover effects
- **Direct Text Entry**: Paste incident logs directly into a dedicated text area
- **Clear State Management**: Distinct visual states for upload, loading, and results
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Keyboard Navigation**: Full keyboard accessibility with visible focus states
- **Loading Indicators**: Animated spinner with dual-color gradient
- **Success Feedback**: Green gradient card for ticket creation confirmation

### Accessibility

- **ARIA Labels**: Comprehensive screen reader support
- **Semantic HTML**: Proper use of section, article, and header tags
- **Focus Management**: Clear focus indicators for keyboard navigation
- **Live Regions**: Dynamic content updates announced to screen readers
- **Color Contrast**: WCAG-compliant text and background combinations

### Structured Results Display

Analysis results are presented in beautifully designed cards:

1. **Root Cause Analysis**: Clean card with info icon and detailed explanation
2. **Remediation Steps**: Numbered list with gradient circular badges
3. **Escalation Summary**: Terminal-style code block with syntax highlighting
4. **Ticket Status**: Success card with checkmark and confirmation message

## Project Structure

```
incident-analyzer/
├── app.py                    # Flask application with /analyze endpoint
├── templates/
│   └── index.html           # Enhanced HTML with accessibility features, tabs, and text input
├── static/
│   ├── style.css            # Modern CSS with animations, gradients, and dark theme support
│   └── main.js              # Vanilla JavaScript with smooth transitions, theme, tabs, and CSV download
├── sample-incident.log      # Example log file for testing
└── README.md                # This file
```

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. Install Flask:
   ```bash
   pip install flask
   ```

2. Navigate to the project directory:
   ```bash
   cd incident-analyzer
   ```

## Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open your web browser and visit:
   ```
   http://localhost:5000
   ```

3. The application will be running with hot reload enabled (debug mode)

## Usage Guide

### Step 1: Provide Incident Data

You have two options to provide incident data:

- **Upload File**: Drag a `.txt`, `.log`, or `.json` file onto the highlighted upload area, or click "Select a file".
- **Paste Text**: Switch to the "Paste Text" tab and paste your incident logs or report directly into the text area.

The interface provides visual feedback:
- Hover effects and animations on the drop zone.
- Selected file name appears in a styled badge.
- Character count updates dynamically for text input.

### Step 2: Analyze

Once a file is selected or text is entered:
- The "Analyze Incident" button becomes active (gradient blue background).
- Click the button to start analysis.
- The interface transitions to a loading state with an animated spinner.

### Step 3: Review Results

After analysis completes (approximately 2 seconds):
- Results appear in structured, color-coded cards.
- Root cause is displayed with detailed explanation.
- Remediation steps are numbered with gradient badges.
- Escalation summary appears in a terminal-style code block.
- Ticket creation status is shown in a success card.

### Step 4: Download CSV (Optional)

- Click the "Download CSV" button in the results header to export the analysis report.

### Step 5: New Analysis

Click the "New Analysis" button to:
- Reset the interface to the input state.
- Clear all previous results.
- Start a new analysis with a different file or text.

## Backend Integration

The current implementation includes a **simulated analysis endpoint** for demonstration purposes. To integrate with your actual Python backend:

### 1. Modify the `/analyze` Route

Replace the simulated logic in `app.py` with your actual incident analysis code:

```python
@app.route("/analyze", methods=["POST"])
def analyze():
    # ... (content extraction logic remains the same)
    
    # YOUR ANALYSIS LOGIC HERE
    # Replace this with your actual AI-powered analysis
    results = your_analysis_function(content)
    
    return jsonify(results)
```

### 2. Expected Response Format

Your backend should return JSON in this structure:

```json
{
  "root_cause": "Detailed description of the root cause...",
  "remediation_steps": [
    "Step 1: Action to take...",
    "Step 2: Another action...",
    "Step 3: Follow-up action..."
  ],
  "escalation_summary": "Multi-line summary text\nwith preserved formatting\nfor escalation purposes",
  "ticket_status": "PROJ-1234"
}
```

### 3. Error Handling

The frontend handles errors gracefully with toast messages. Ensure your backend returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid input)
- `500`: Server error (analysis failure)

## Design System

### Color Palette

- **Primary**: Indigo (`#4f46e5`) - Main actions and accents
- **Secondary**: Cyan (`#06b6d4`) - Secondary elements
- **Success**: Green (`#10b981`) - Success states
- **Warning**: Orange (`#f59e0b`) - Warning states
- **Danger**: Red (`#ef4444`) - Error states
- **Grayscale**: 10 shades for backgrounds and text

### Typography

- **Font Family**: Inter (loaded from Google Fonts) for UI, Fira Code for code/logs
- **Weights**: 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 800 (extrabold)
- **Sizes**: Responsive scale from 14px to 48px

### Spacing

- **Card Padding**: 56px (desktop), 40px (tablet), 32px (mobile)
- **Element Gaps**: 16px, 24px, 32px, 48px
- **Border Radius**: 8px (small), 12px (medium), 16px (large), 24px (extra-large)

### Shadows

Five levels of shadows for different elevation needs:
- `shadow-sm`: Subtle elements
- `shadow`: Default cards
- `shadow-md`: Elevated cards
- `shadow-lg`: Hover states
- `shadow-xl`: Main container

## Browser Compatibility

The application works on all modern browsers:

- **Chrome/Edge**: Latest (recommended)
- **Firefox**: Latest
- **Safari**: Latest
- **Mobile Browsers**: iOS Safari, Chrome Mobile

Note: Internet Explorer is not supported due to modern CSS features.

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Fonts**: Google Fonts (Inter, Fira Code)
- **No Dependencies**: No Bootstrap, React, Vue, or other heavy frameworks

## Performance

The application is highly optimized:

- **Lightweight**: No heavy framework overhead
- **Fast Loading**: Minimal external resources (only Google Fonts)
- **Smooth Animations**: CSS transforms and opacity for GPU acceleration
- **Efficient DOM**: Minimal manipulation and reflows

## Accessibility Compliance

The application follows WCAG 2.1 Level AA guidelines:

- Keyboard navigation support
- Screen reader compatibility
- Sufficient color contrast
- Focus indicators
- Semantic HTML structure
- ARIA labels and roles

## Sample File

A `sample-incident.log` file is included for testing. It contains:

```
[2025-10-17 14:23:15] ERROR: Database connection failed - Connection pool exhausted
[2025-10-17 14:23:16] ERROR: API request timeout - Unable to establish database connection
[2025-10-17 14:23:17] CRITICAL: Service degradation detected - 100% error rate
...
```

Use this file to test the upload and analysis functionality.

## Customization

### Changing Colors

Edit the CSS custom properties in `static/style.css`:

```css
:root {
    --primary: #4f46e5;  /* Change to your brand color */
    --secondary: #06b6d4;
    --success: #10b981;
    /* ... */
}
```

### Modifying Animations

Adjust animation timing in `static/style.css`:

```css
.section {
    animation: fadeInUp 0.6s ease-out 0.2s both;
}
```

### Updating Typography

Change the font family in `templates/index.html`:

```html
<link href="https://fonts.googleapis.com/css2?family=YourFont:wght@400;700&display=swap" rel="stylesheet">
```

Then update the CSS:

```css
body {
    font-family: 'YourFont', sans-serif;
}
```

## License

This project is provided as-is for your use and customization.

## Support

For questions or issues, please refer to the code comments or the `ENHANCED_DESIGN_SHOWCASE.md` and `HACKATHON_FEATURES.md` files for detailed design and feature documentation.


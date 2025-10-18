// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const textInput = document.getElementById('text-input');
const charCount = document.getElementById('char-count');
const clearTextBtn = document.getElementById('clear-text-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const uploadSection = document.getElementById('upload-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const newAnalysisBtn = document.getElementById('new-analysis-btn');
const downloadCsvBtn = document.getElementById('download-csv-btn');
const themeToggle = document.getElementById('theme-toggle');
const sunIcon = document.getElementById('sun-icon');
const moonIcon = document.getElementById('moon-icon');

// Voice-to-text and autocomplete variables
let isListening = false;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;
const autocompleteList = [
    'Database connection failed',
    'API request timeout',
    'Service degradation detected',
    'Memory leak detected',
    'CPU usage spike',
    'Disk space critical',
    'Network latency increased',
    'Authentication failed',
    'Permission denied',
    'Resource exhaustion',
    'Connection refused',
    'Timeout error',
    'Invalid configuration',
    'Deployment failed',
    'Service unavailable'
];

// Tab elements
const fileTab = document.getElementById('file-tab');
const textTab = document.getElementById('text-tab');
const filePanel = document.getElementById('file-panel');
const textPanel = document.getElementById('text-panel');

// State
let selectedFile = null;
let currentInputMode = 'file'; // 'file' or 'text'

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'block';
    }
}

themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    
    // Toggle icons
    sunIcon.style.display = isDark ? 'none' : 'block';
    moonIcon.style.display = isDark ? 'block' : 'none';
    
    // Save preference
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    
    // Show toast notification
    showToast(isDark ? '🌙 Dark mode enabled' : '☀️ Light mode enabled');
});

// Tab Management
fileTab.addEventListener('click', () => switchTab('file'));
textTab.addEventListener('click', () => switchTab('text'));

function switchTab(mode) {
    currentInputMode = mode;
    
    if (mode === 'file') {
        // Activate file tab
        fileTab.classList.add('active');
        textTab.classList.remove('active');
        filePanel.classList.add('active');
        textPanel.classList.remove('active');
        fileTab.setAttribute('aria-selected', 'true');
        textTab.setAttribute('aria-selected', 'false');
        
        // Enable button if file is selected
        analyzeBtn.disabled = !selectedFile;
    } else {
        // Activate text tab
        textTab.classList.add('active');
        fileTab.classList.remove('active');
        textPanel.classList.add('active');
        filePanel.classList.remove('active');
        textTab.setAttribute('aria-selected', 'true');
        fileTab.setAttribute('aria-selected', 'false');
        
        // Enable button if text is entered
        analyzeBtn.disabled = textInput.value.trim() === '';
        
        // Focus on textarea
        setTimeout(() => textInput.focus(), 100);
    }
}

// Text Input Handlers
textInput.addEventListener('input', () => {
    const length = textInput.value.length;
    charCount.textContent = `${length.toLocaleString()} character${length !== 1 ? 's' : ''}`;
    
    // Enable/disable analyze button based on text content
    if (currentInputMode === 'text') {
        analyzeBtn.disabled = textInput.value.trim() === '';
    }
});

clearTextBtn.addEventListener('click', () => {
    textInput.value = '';
    charCount.textContent = '0 characters';
    analyzeBtn.disabled = true;
    textInput.focus();
    showToast('🗑️ Text cleared');
});

// Toast Notification
function showToast(message) {
    // Remove existing toast if any
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// Voice-to-text functionality
function initVoiceRecognition() {
    if (!recognition) {
        console.warn('Speech Recognition not supported in this browser');
        return;
    }
    
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
        isListening = true;
        showToast('🎤 Listening...');
    };
    
    recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                textInput.value += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }
        
        const length = textInput.value.length;
        charCount.textContent = `${length.toLocaleString()} character${length !== 1 ? 's' : ''}`;
        
        if (currentInputMode === 'text') {
            analyzeBtn.disabled = textInput.value.trim() === '';
        }
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        showToast('❌ Voice input error: ' + event.error);
    };
    
    recognition.onend = () => {
        isListening = false;
        const voiceBtn = document.getElementById('voice-btn');
        if (voiceBtn) {
            voiceBtn.classList.remove('listening');
        }
        showToast('🎤 Voice input ended');
    };
}

// Autocomplete functionality
function initAutocomplete() {
    const autocompleteContainer = document.createElement('div');
    autocompleteContainer.id = 'autocomplete-list';
    autocompleteContainer.className = 'autocomplete-list';
    const textInputContainer = document.querySelector('.text-input-container');
    if (textInputContainer) {
        textInputContainer.style.position = 'relative'; // Ensure parent is relatively positioned
        textInputContainer.appendChild(autocompleteContainer);
    } else {
        console.error('text-input-container not found');
    }
    
    textInput.addEventListener('input', () => {
        const value = textInput.value.trim();
        const lastLine = value.split('\n').pop();
        
        if (lastLine.length < 2) {
            autocompleteContainer.innerHTML = '';
            return;
        }
        
        const matches = autocompleteList.filter(item => 
            item.toLowerCase().includes(lastLine.toLowerCase())
        );
        
        if (matches.length === 0) {
            autocompleteContainer.innerHTML = '';
            return;
        }
        
        autocompleteContainer.innerHTML = matches.map((match, index) => 
            `<div class="autocomplete-item" data-index="${index}">${match}</div>`
        ).join('');
        
        // Add click handlers to autocomplete items
        document.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                const lines = textInput.value.split('\n');
                lines[lines.length - 1] = item.textContent;
                textInput.value = lines.join('\n');
                autocompleteContainer.innerHTML = '';
                
                const length = textInput.value.length;
                charCount.textContent = `${length.toLocaleString()} character${length !== 1 ? 's' : ''}`;
                
                if (currentInputMode === 'text') {
                    analyzeBtn.disabled = textInput.value.trim() === '';
                }
                
                textInput.focus();
            });
        });
    });
    
    // Close autocomplete on blur
    textInput.addEventListener('blur', () => {
        setTimeout(() => {
            autocompleteContainer.innerHTML = '';
        }, 200);
    });
}

// Drag and Drop Handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

// Click to select file
dropZone.addEventListener('click', (e) => {
    if (e.target !== fileInput && !e.target.closest('.file-label')) {
        fileInput.click();
    }
});

// Keyboard accessibility for drop zone
dropZone.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
    }
});

// File input change handler
fileInput.addEventListener('change', (e) => {
    const files = e.target.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

// Handle file selection
function handleFileSelect(file) {
    selectedFile = file;
    fileName.textContent = `Selected: ${file.name}`;
    fileName.style.display = 'inline-block';
    
    if (currentInputMode === 'file') {
        analyzeBtn.disabled = false;
    }
    
    // Add animation to file name
    fileName.style.animation = 'none';
    setTimeout(() => {
        fileName.style.animation = 'fadeInUp 0.3s ease-out';
    }, 10);
    
    showToast('📄 File selected successfully');
}

// Analyze button click handler
analyzeBtn.addEventListener('click', async () => {
    // Show loading state with animation
    uploadSection.style.animation = 'fadeOut 0.3s ease-out';
    setTimeout(() => {
        uploadSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');
        loadingSection.style.animation = 'fadeInUp 0.4s ease-out';
    }, 300);
    
    // Create FormData and send to backend
    const formData = new FormData();
    
    if (currentInputMode === 'file' && selectedFile) {
        formData.append('file', selectedFile);
    } else if (currentInputMode === 'text') {
        formData.append('text', textInput.value);
    } else {
        showToast('❌ No input provided');
        resetToUpload();
        return;
    }
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Analysis failed');
        }
        
        const results = await response.json();
        
        // Display results with delay for smooth transition
        setTimeout(() => {
            displayResults(results);
        }, 500);
        
    } catch (error) {
        console.error('Error:', error);
        showToast('❌ Analysis failed. Please try again.');
        resetToUpload();
    }
});

// Display results
function displayResults(data) {
    // Hide loading, show results with animation
    loadingSection.style.animation = 'fadeOut 0.3s ease-out';
    setTimeout(() => {
        loadingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        resultsSection.style.animation = 'fadeInUp 0.4s ease-out';
    }, 300);
    
    // Populate root cause
    document.getElementById('root-cause-text').textContent = data.root_cause;
    
    // Populate remediation steps with staggered animation
    const remediationList = document.getElementById('remediation-list');
    remediationList.innerHTML = '';
    data.remediation_steps.forEach((step, index) => {
        const li = document.createElement('li');
        li.textContent = step;
        li.style.opacity = '0';
        li.style.animation = `fadeInUp 0.4s ease-out ${0.1 * index}s forwards`;
        remediationList.appendChild(li);
    });
    
    // Populate escalation summary
    document.getElementById('escalation-text').textContent = data.escalation_summary;
    
    // Populate ticket status
    document.getElementById('ticket-text').textContent = 
        `Ticket ${data.ticket_status} created successfully.`;
    
    showToast('✅ Analysis complete!');
}

// Download CSV button handler
downloadCsvBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/download-csv');
        
        if (!response.ok) {
            throw new Error('Download failed');
        }
        
        // Get the blob from response
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `incident_analysis_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('📥 CSV downloaded successfully');
        
    } catch (error) {
        console.error('Download error:', error);
        showToast('❌ Download failed. Please try again.');
    }
});

// Reset to upload state
function resetToUpload() {
    selectedFile = null;
    fileName.textContent = '';
    fileName.style.display = 'none';
    fileInput.value = '';
    textInput.value = '';
    charCount.textContent = '0 characters';
    analyzeBtn.disabled = true;
    
    // Reset to file tab
    switchTab('file');
    
    resultsSection.style.animation = 'fadeOut 0.3s ease-out';
    setTimeout(() => {
        resultsSection.classList.add('hidden');
        loadingSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        uploadSection.style.animation = 'fadeInUp 0.4s ease-out';
    }, 300);
}

// New analysis button handler
newAnalysisBtn.addEventListener('click', resetToUpload);

// Prevent default drag behavior on the whole document
document.addEventListener('dragover', (e) => {
    e.preventDefault();
});

document.addEventListener('drop', (e) => {
    e.preventDefault();
});

// Add CSS animations dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }
    
    /* Autocomplete styles */
    .autocomplete-list {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-top: none;
        border-radius: 0 0 12px 12px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 100;
        box-shadow: var(--shadow-md);
    }
    
    .autocomplete-item {
        padding: 12px 16px;
        cursor: pointer;
        color: var(--text-primary);
        transition: background-color 0.2s ease;
        border-bottom: 1px solid var(--border-color);
    }
    
    .autocomplete-item:last-child {
        border-bottom: none;
    }
    
    .autocomplete-item:hover {
        background-color: var(--card-bg-secondary);
    }
    
    /* Voice button styles */
    .voice-btn {
        padding: 10px 16px;
        background: var(--secondary);
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 6px;
        box-shadow: var(--shadow-sm);
    }
    
    .voice-btn:hover {
        background: var(--secondary);
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    .voice-btn:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    .voice-btn.listening {
        background: var(--danger);
        animation: pulse 1s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }
    
    .voice-btn svg {
        width: 18px;
        height: 18px;
    }
`;
document.head.appendChild(style);

// Initialize theme on page load
initTheme();

// Initialize voice recognition
initVoiceRecognition();

// Initialize autocomplete
initAutocomplete();

// Add voice input button to text panel
const voiceBtn = document.createElement('button');
voiceBtn.id = 'voice-btn';
voiceBtn.className = 'voice-btn';
voiceBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v12a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg> Voice Input';
voiceBtn.setAttribute('aria-label', 'Voice input button');
voiceBtn.addEventListener('click', () => {
    if (!recognition) {
        showToast('❌ Voice input not supported in this browser');
        return;
    }
    
    if (isListening) {
        recognition.stop();
        voiceBtn.classList.remove('listening');
    } else {
        recognition.start();
        voiceBtn.classList.add('listening');
    }
});

// Insert voice button after clear button in text panel
const textInputFooter = document.querySelector('.text-input-footer');
if (textInputFooter) {
    textInputFooter.appendChild(voiceBtn);
}

// Add keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + D)
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        themeToggle.click();
    }
});



// Initialize functionality
initTheme();
initVoiceRecognition();
initAutocomplete();
switchTab(currentInputMode); // Set initial tab state


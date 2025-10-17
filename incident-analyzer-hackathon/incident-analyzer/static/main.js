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
`;
document.head.appendChild(style);

// Initialize theme on page load
initTheme();

// Add keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + D)
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        themeToggle.click();
    }
});


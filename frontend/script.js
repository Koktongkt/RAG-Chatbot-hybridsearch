const API_BASE_URL = 'http://localhost:5000';

const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const ingestBtn = document.getElementById('ingestBtn');
const uploadBtn = document.getElementById('uploadBtn');
const pdfUpload = document.getElementById('pdfUpload');
const clearBtn = document.getElementById('clearBtn');
const statusMessage = document.getElementById('status');
const themeToggle = document.getElementById('themeToggle');

// Theme toggle functionality
themeToggle.addEventListener('change', toggleTheme);

function toggleTheme() {
    const isDark = themeToggle.checked;
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

// Load saved theme preference
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeToggle.checked = savedTheme === 'dark';
}

// Initialize theme on page load
loadTheme();

// Event listeners
sendBtn.addEventListener('click', sendMessage);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

ingestBtn.addEventListener('click', ingestDocuments);
uploadBtn.addEventListener('click', () => pdfUpload.click());
pdfUpload.addEventListener('change', uploadPDFs);
clearBtn.addEventListener('click', clearDatabase);

async function sendMessage() {
    const question = questionInput.value.trim();
    
    if (!question) {
        showStatus('Please enter a question', 'error');
        return;
    }

    // Add user message to chat
    addMessage(question, 'user');
    questionInput.value = '';

    try {
        showStatus('Thinking...', 'loading');
        
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        addMessage(data.answer, 'assistant');
        
        if (data.sources && data.sources.length > 0) {
            addMessage(`📎 Sources:\n${data.sources.slice(0, 1).join('\n')}`, 'system');
        }
        
        showStatus('');
    } catch (error) {
        console.error('Error:', error);
        addMessage(`Sorry, I encountered an error: ${error.message}`, 'assistant');
        showStatus('Error sending message', 'error');
    }
}

async function ingestDocuments() {
    try {
        ingestBtn.disabled = true;
        showStatus('Ingesting documents...', 'loading');

        const response = await fetch(`${API_BASE_URL}/ingest`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        
        // Build detailed message
        let message = `✅ Successfully ingested ${data.documents_count} documents with ${data.chunks_count} chunks!`;
        const details = [];
        
        if (data.new_count > 0) {
            details.push(`${data.new_count} new documents added`);
        }
        if (data.replaced_count > 0) {
            details.push(`${data.replaced_count} existing documents replaced`);
        }
        
        if (details.length > 0) {
            message += `\n📋 Details: ${details.join(', ')}`;
        }
        
        addMessage(message, 'system');
        showStatus(`${data.documents_count} documents loaded`, 'success');
    } catch (error) {
        console.error('Error:', error);
        addMessage(`❌ Error ingesting documents: ${error.message}`, 'system');
        showStatus('Failed to ingest documents', 'error');
    } finally {
        ingestBtn.disabled = false;
    }
}

async function uploadPDFs(event) {
    const files = event.target.files;
    
    if (!files || files.length === 0) {
        return;
    }

    try {
        uploadBtn.disabled = true;
        showStatus('Uploading and processing PDFs...', 'loading');

        const formData = new FormData();
        for (let file of files) {
            if (!file.name.toLowerCase().endsWith('.pdf')) {
                throw new Error(`Invalid file: ${file.name}. Only PDF files are allowed.`);
            }
            formData.append('files', file);
        }

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        
        // Build detailed message
        let message = `✅ Successfully uploaded and embedded ${data.documents_count} documents with ${data.chunks_count} chunks!`;
        const details = [];
        
        if (data.new_count > 0) {
            details.push(`${data.new_count} new documents added`);
        }
        if (data.replaced_count > 0) {
            details.push(`${data.replaced_count} existing documents replaced`);
        }
        
        if (details.length > 0) {
            message += `\n📋 Details: ${details.join(', ')}`;
        }
        
        addMessage(message, 'system');
        showStatus(`${data.documents_count} PDFs processed`, 'success');
        
        // Reset file input
        pdfUpload.value = '';
    } catch (error) {
        console.error('Error:', error);
        addMessage(`❌ Error uploading PDFs: ${error.message}`, 'system');
        showStatus('Failed to upload PDFs', 'error');
        pdfUpload.value = '';
    } finally {
        uploadBtn.disabled = false;
    }
}

async function clearDatabase() {
    if (!confirm('Are you sure you want to clear the database? This cannot be undone.')) {
        return;
    }

    try {
        clearBtn.disabled = true;
        showStatus('Clearing database...', 'loading');

        const response = await fetch(`${API_BASE_URL}/clear`, {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        addMessage('🗑️ Database cleared successfully!', 'system');
        showStatus('Database cleared', 'success');
    } catch (error) {
        console.error('Error:', error);
        addMessage(`❌ Error clearing database: ${error.message}`, 'system');
        showStatus('Failed to clear database', 'error');
    } finally {
        clearBtn.disabled = false;
    }
}

function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const p = document.createElement('p');
    p.textContent = content;
    
    messageDiv.appendChild(p);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showStatus(message, type = 'info') {
    statusMessage.textContent = message;
    statusMessage.className = `status-message status-${type}`;
}

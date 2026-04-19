const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const clearBtn = document.getElementById('clearBtn');
const quickReplies = document.getElementById('quickReplies');
const loginContainer = document.getElementById('loginContainer');
const appContainer = document.getElementById('appContainer');
const loginForm = document.getElementById('loginForm');

// State management
let isWaitingForOrderId = false;
let isEscalated = false;
let conversationHistory = [];
const sessionId = 'session_' + Date.now();

// Login Handling
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Check if input is empty (HTML5 required attribute handles basic checks)
    const loginInput = document.getElementById('loginInput').value.trim();
    if (!loginInput) return;

    // Fade out login container
    loginContainer.style.opacity = '0';
    
    // Wait for fade out, then hide it and show app
    setTimeout(() => {
        loginContainer.style.display = 'none';
        appContainer.style.display = 'flex';
        appContainer.style.opacity = '0';
        
        // Trigger reflow
        void appContainer.offsetWidth;
        
        // Fade in app container
        appContainer.style.transition = 'opacity 0.6s ease';
        appContainer.style.opacity = '1';
        
        // Start greeting after a small delay
        setTimeout(() => {
            addMessage("Hello! I'm Nexus, your Smart Support Assistant. How can I assist you today? You can ask me about order tracking, refunds, or our FAQs.", 'ai');
        }, 800);
    }, 500);
});

// Event Listeners
sendBtn.addEventListener('click', handleSend);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});
clearBtn.addEventListener('click', clearChat);

// Voice Mock
let isRecording = false;
voiceBtn.addEventListener('click', () => {
    if (!isRecording) {
        isRecording = true;
        voiceBtn.classList.add('recording');
        userInput.placeholder = "Listening...";
        
        // Mock voice recognition after 2 seconds
        setTimeout(() => {
            isRecording = false;
            voiceBtn.classList.remove('recording');
            userInput.value = "Where is my order?";
            userInput.placeholder = "Type your message here...";
            handleSend();
        }, 2000);
    } else {
        isRecording = false;
        voiceBtn.classList.remove('recording');
        userInput.placeholder = "Type your message here...";
    }
});

function handleQuickReply(text) {
    userInput.value = text;
    handleSend();
}

function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    // Add user message to UI
    addMessage(text, 'user');
    userInput.value = '';
    
    // Hide quick replies after interaction to clean up UI
    quickReplies.style.opacity = '0.5';

    // Show typing indicator
    const typingId = showTypingIndicator();

    // Process thinking time before response
    setTimeout(() => {
        removeTypingIndicator(typingId);
        processIntent(text.toLowerCase());
    }, 150 + Math.random() * 100); // Super fast 150-250ms delay
}

async function processIntent(input) {
    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: input,
                history: conversationHistory
            })
        });

        const data = await response.json();
        
        if (data.action === 'escalate') {
            escalateToHuman(data.reply);
            return;
        }

        if (data.reply) {
            addMessage(data.reply, 'ai', data.buttons || null);
        } else {
            addMessage("I am having trouble connecting to my central systems.", 'ai');
        }
    } catch (error) {
        console.error("Backend error:", error);
        addMessage("I'm sorry, my systems are currently offline. Please ensure the backend server is running.", 'ai');
    }
}

function escalateToHuman(message) {
    isEscalated = true;
    addMessage(message || "I'm escalating your chat to a human agent now to assist you better.", 'ai');
    
    setTimeout(() => {
        addMessage("<b>[System Update]</b> You have been connected to Agent Sarah. She will be with you shortly.", 'ai');
    }, 200);
}

// UI Helpers
function addMessage(text, sender, buttons = null) {
    // Record into history
    conversationHistory.push({ role: sender === 'ai' ? 'assistant' : 'user', content: text });

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let html = `
        <div class="msg-bubble">${text}</div>
        <div class="msg-time">${time}</div>
    `;
    
    msgDiv.innerHTML = html;
    
    // Add action buttons if provided
    if (buttons && buttons.length > 0) {
        const btnContainer = document.createElement('div');
        btnContainer.className = 'action-buttons';
        
        buttons.forEach(btn => {
            const buttonEl = document.createElement('button');
            buttonEl.className = 'action-btn';
            buttonEl.innerText = btn.text;
            buttonEl.onclick = () => handleAction(btn.action, btn.text);
            btnContainer.appendChild(buttonEl);
        });
        
        // Append inside the div holding the bubble so it flexes properly
        msgDiv.insertBefore(btnContainer, msgDiv.querySelector('.msg-time'));
    }

    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai typing';
    msgDiv.id = id;
    
    msgDiv.innerHTML = `
        <div class="msg-bubble typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearChat() {
    chatMessages.innerHTML = '';
    isWaitingForOrderId = false;
    isEscalated = false;
    quickReplies.style.opacity = '1';
    addMessage("Chat history cleared. How can I help you today?", 'ai');
}

// Handle predefined button actions
window.handleAction = (action, text) => {
    // Add user message for the button click
    addMessage(text, 'user');
    
    // Instead of a hardcoded switch, directly route the action text to our backend!
    const typingId = showTypingIndicator();
    setTimeout(() => {
        removeTypingIndicator(typingId);
        processIntent(text);
    }, 500);
}

// ===== AccelerateAI - Chatbot Logic =====

document.addEventListener('DOMContentLoaded', () => {
    const chatToggle = document.getElementById('chat-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const chatSend = document.getElementById('chat-send');
    const chatInput = document.getElementById('chat-input');
    const chatBody = document.getElementById('chat-body');

    if (!chatToggle || !chatWindow) return;

    // Toggle Window
    chatToggle.addEventListener('click', () => {
        const isOpen = chatWindow.style.display === 'flex';
        chatWindow.style.display = isOpen ? 'none' : 'flex';
        if (!isOpen) chatInput.focus();
    });

    chatClose.addEventListener('click', () => {
        chatWindow.style.display = 'none';
    });

    // History for context (stored in session)
    let chatHistory = [];

    // Send Message
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // User Message UI
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-message user';
        userMsg.textContent = text;
        chatBody.appendChild(userMsg);

        chatHistory.push({ role: 'user', text: text });
        chatInput.value = '';
        chatBody.scrollTop = chatBody.scrollHeight;

        // Bot Loading State
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'chat-message bot';
        loadingMsg.innerHTML = '<i>Thinking...</i>';
        chatBody.appendChild(loadingMsg);
        chatBody.scrollTop = chatBody.scrollHeight;

        try {
            const apiBase = (typeof API_BASE !== 'undefined') ? API_BASE : 'http://localhost:8000/api';
            const res = await fetch(`${apiBase}/chat/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, history: chatHistory })
            });
            const data = await res.json();

            // Remove loading and show reply
            loadingMsg.textContent = data.reply || "I'm sorry, I couldn't process that.";
            chatHistory.push({ role: 'bot', text: loadingMsg.textContent });
            chatBody.scrollTop = chatBody.scrollHeight;
        } catch (err) {
            loadingMsg.textContent = "Offline. Please try again later.";
            console.error('Chat Error:', err);
        }
    }

    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

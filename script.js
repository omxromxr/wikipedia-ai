document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Get all the HTML elements we need ---
    const chatWindow = document.getElementById('chat-window');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const modeSwitch = document.getElementById('mode-switch');
    const modeLabelFast = document.getElementById('mode-label-fast');
    const modeLabelThinking = document.getElementById('mode-label-thinking');
    const darkModeToggle = document.getElementById('darkModeToggle');

    let currentMode = 'fast'; // Default mode

    // --- 2. Define Helper Functions ---

    /**
     * Adds a message to the chat window
     * @param {string} message - The text content of the message
     * @param {string} sender - 'user', 'ai', or 'loading'
     * @returns {HTMLElement} - The message element just created
     */
    function addMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender);
        
        // Simple text for now. In a real app, you'd parse markdown.
        messageElement.innerHTML = `<p>${message}</p>`; 
        
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to bottom
        return messageElement;
    }

    /**
     * The main function to send a message to the backend
     */
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return; // Don't send empty messages

        // 1. Display the user's message immediately
        addMessage(message, 'user');
        chatInput.value = ''; // Clear the input

        // 2. Show a "thinking..." bubble
        const loadingMessage = addMessage('Thinking...', 'ai');
        loadingMessage.classList.add('loading');
        
        try {
            // 3. Send the message and mode to the Flask backend
            const response = await fetch('http://127.0.0.1:5000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    mode: currentMode 
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // 4. Remove the "thinking..." bubble
            loadingMessage.remove();

            // 5. Display the AI's final answer
            addMessage(data.answer, 'ai');

        } catch (error) {
            // 6. Handle errors
            loadingMessage.remove();
            addMessage(`Sorry, something went wrong: ${error.message}`, 'ai');
            console.error('Error sending message:', error);
        }
    }

    // --- 3. Set up Event Listeners ---

    // Send on button click
    sendBtn.addEventListener('click', sendMessage);

    // Send on "Enter" key press (but not "Shift + Enter" for new line)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent new line
            sendMessage();
        }
    });

    // Handle the "Fast" vs "Thinking" mode toggle
    modeSwitch.addEventListener('change', () => {
        if (modeSwitch.checked) {
            currentMode = 'thinking';
            modeLabelThinking.classList.add('active');
            modeLabelFast.classList.remove('active');
        } else {
            currentMode = 'fast';
            modeLabelFast.classList.add('active');
            modeLabelThinking.classList.remove('active');
        }
        console.log("Mode changed to:", currentMode);
    });

    // Handle Dark Mode toggle
    darkModeToggle.addEventListener('change', () => {
        document.body.classList.toggle('dark-mode');
    });

});

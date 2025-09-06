var nav = document.querySelector('nav');

window.addEventListener('scroll', function () {
    if (this.window.pageYOffset > 200) {
        nav.classList.add('bg-dark', 'shadow');
    }else {
        nav.classList.remove('bg-dark', 'shadow');
    }
});

// Initialize WebSocket connection for chat
function initializeChat(roomName, senderId, receiverId, senderType) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/chat/${roomName}/`;
    
    const chatSocket = new WebSocket(url);

    chatSocket.onopen = function(e) {
        console.log('WebSocket connection established');
    };

    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        console.log('Received data:', data);

        if (data.type === 'chat_message') {
            displayMessage(data.message, data.sender_type, data.sender_id);
        } else if (data.type === 'connection_established') {
            console.log('Connected to chat room');
        }
    };

    chatSocket.onclose = function(e) {
        console.log('WebSocket connection closed');
    };

    chatSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
    };

    // Function to send message
    window.sendMessage = function(messageBody) {
        if (chatSocket.readyState === WebSocket.OPEN && messageBody.trim()) {
            chatSocket.send(JSON.stringify({
                'type': 'chat_message',
                'message': messageBody,
                'sender_id': senderId,
                'receiver_id': receiverId,
                'sender_type': senderType
            }));
            return true;
        }
        return false;
    };

    return chatSocket;
}

// Function to display messages in the chat
function displayMessage(message, senderType, senderId) {
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;

    const isCurrentUser = (senderType === 'buyer' && senderId == window.currentBuyerId) || 
                         (senderType === 'seller' && senderId == window.currentSellerId);
    
    // Create message container
    const messageContainer = document.createElement('div');
    
    if (isCurrentUser) {
        // Current user's message (right aligned)
        messageContainer.innerHTML = `
            <div class="d-flex justify-content-between mb-2">
                <p class="small mb-1">You</p>
                <p class="small mb-1 text-muted">Just now</p>
            </div>
            <div class="d-flex flex-row justify-content-end mb-3">
                <div>
                    <p class="small p-2 me-3 mb-0 rounded-3" style="background-color: #007bff; color: white; max-width: 250px; word-wrap: break-word;">${message}</p>
                </div>
                <img src="https://mdbcdn.b-cdn.net/img/Photos/new-templates/bootstrap-chat/ava6-bg.webp"
                    alt="avatar" style="width: 35px; height: 35px; border-radius: 50%;">
            </div>
        `;
    } else {
        // Other user's message (left aligned)
        messageContainer.innerHTML = `
            <div class="d-flex justify-content-between mb-2">
                <p class="small mb-1">${senderType === 'buyer' ? 'Buyer' : 'Seller'}</p>
                <p class="small mb-1 text-muted">Just now</p>
            </div>
            <div class="d-flex flex-row justify-content-start mb-3">
                <img src="https://mdbcdn.b-cdn.net/img/Photos/new-templates/bootstrap-chat/ava5-bg.webp"
                    alt="avatar" style="width: 35px; height: 35px; border-radius: 50%;">
                <div>
                    <p class="small p-2 ms-3 mb-0 rounded-3" style="background-color: #f5f6f7; max-width: 250px; word-wrap: break-word;">${message}</p>
                </div>
            </div>
        `;
    }
    
    messagesContainer.appendChild(messageContainer);
    
    // Auto-scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Auto-scroll to bottom of messages
function scrollToBottom() {
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        // Use setTimeout to ensure DOM is updated
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
}
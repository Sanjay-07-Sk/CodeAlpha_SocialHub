document.addEventListener('DOMContentLoaded', function() {
    // Escape HTML to prevent XSS
    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag] || tag)
        );
    }

    const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
    
    // --- Global Notifications Socket ---
    let notificationSocket = null;
    
    function connectNotificationSocket() {
        if (document.body.dataset.authenticated !== 'true') return;
        
        const notificationUrl = `${wsScheme}://${window.location.host}/ws/notifications/`;
        notificationSocket = new WebSocket(notificationUrl);
        
        notificationSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            
            if (data.type === 'message_notification') {
                // 1. Update Global Navbar Badge
                const navbarBadge = document.getElementById('navbar-unread-badge');
                if (navbarBadge) {
                    if (data.total_unread_count > 0) {
                        navbarBadge.textContent = data.total_unread_count;
                        navbarBadge.style.display = 'block';
                    } else {
                        navbarBadge.textContent = '';
                        navbarBadge.style.display = 'none';
                    }
                }
                
                // 2. Update Inbox/Conversation list item
                const convId = data.conversation_id;
                
                // Update specific conversation badge
                const convBadge = document.querySelector(`.conv-unread-badge[data-conversation-id="${convId}"]`);
                if (convBadge) {
                    if (data.unread_count > 0) {
                        convBadge.textContent = data.unread_count;
                        convBadge.style.display = 'inline-block';
                    } else {
                        convBadge.textContent = '';
                        convBadge.style.display = 'none';
                    }
                }
                
                // Update last message text preview
                const lastMsgText = document.querySelector(`.conv-last-msg-text[data-conversation-id="${convId}"]`);
                if (lastMsgText) {
                    const isMe = data.sender_id === parseInt(document.body.dataset.userId);
                    lastMsgText.textContent = (isMe ? 'You: ' : '') + data.content;
                    
                    if (!isMe && data.unread_count > 0) {
                        lastMsgText.classList.add('fw-bold', 'text-dark');
                        lastMsgText.classList.remove('text-muted');
                    } else {
                        lastMsgText.classList.remove('fw-bold', 'text-dark');
                        lastMsgText.classList.add('text-muted');
                    }
                }
                
                // Update last message time preview
                const lastMsgTime = document.querySelector(`.conv-last-msg-time[data-conversation-id="${convId}"]`);
                if (lastMsgTime) {
                    lastMsgTime.textContent = data.timestamp;
                }
                
                // Sort conversation list by moving this conversation to the top
                const listItem = document.getElementById(`conv-list-item-${convId}`);
                if (listItem) {
                    const listContainer = listItem.parentElement;
                    listContainer.insertBefore(listItem, listContainer.firstChild);
                }
            }
            
            else if (data.type === 'status_notification') {
                const userId = data.user_id;
                const status = data.status;
                
                // Update online status dots
                const dots = document.querySelectorAll(`.user-online-dot[data-user-id="${userId}"]`);
                dots.forEach(dot => {
                    if (status === 'online') {
                        dot.style.display = 'block';
                    } else {
                        dot.style.display = 'none';
                    }
                });
                
                // Update active chat header online dot & status text if matches
                const activeText = document.getElementById('active-user-status-text');
                if (activeText && activeText.dataset.userId === userId.toString()) {
                    if (status === 'online') {
                        activeText.textContent = 'Active now';
                    } else {
                        activeText.textContent = data.last_seen ? `Active ${data.last_seen}` : 'Offline';
                    }
                }
            }
        };
        
        notificationSocket.onclose = function(e) {
            console.log('Notification socket closed. Reconnecting in 5s...', e.reason);
            setTimeout(connectNotificationSocket, 5000);
        };
        
        notificationSocket.onerror = function(err) {
            console.error('Notification socket error, closing.', err);
            notificationSocket.close();
        };
    }
    
    // --- Active Chat Conversation Socket ---
    const chatMessages = document.getElementById('chat-messages');
    let chatSocket = null;
    let typingTimeout = null;
    let isTyping = false;
    
    function connectChatSocket() {
        if (!chatMessages) return; // Not on conversation page
        
        const conversationId = chatMessages.dataset.conversationId;
        const chatUrl = `${wsScheme}://${window.location.host}/ws/chat/${conversationId}/`;
        
        chatSocket = new WebSocket(chatUrl);
        
        chatSocket.onopen = function() {
            console.log('Chat socket connected.');
            showConnectionStatus(true);
            
            // Mark as read upon open
            chatSocket.send(JSON.stringify({
                'action': 'read_receipt'
            }));
        };
        
        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            
            if (data.type === 'message') {
                const message = data.message;
                const senderId = message.sender_id;
                const currentUserId = parseInt(document.body.dataset.userId);
                
                // Remove empty state if it exists
                const emptyState = document.getElementById('chat-empty-state');
                if (emptyState) {
                    emptyState.remove();
                }
                
                // Hide typing indicator for sender
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator && senderId !== currentUserId) {
                    typingIndicator.classList.add('d-none');
                }
                
                let messageHtml = '';
                if (senderId === currentUserId) {
                    messageHtml = `
                        <div class="d-flex justify-content-end mb-3 align-items-end">
                            <div class="message-bubble sent bg-gradient-primary text-white rounded-4 rounded-bottom-end-0 py-2 px-3 shadow-sm" style="max-width: 75%; white-space: pre-line;">${escapeHTML(message.content)}</div>
                        </div>
                    `;
                } else {
                    let avatarHtml = '';
                    if (message.sender_avatar) {
                        avatarHtml = `<img src="${message.sender_avatar}" class="rounded-circle" style="width: 28px; height: 28px; object-fit: cover;">`;
                    } else {
                        const initial = message.sender_username.charAt(0).toUpperCase();
                        avatarHtml = `<div class="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center" style="width: 28px; height: 28px; font-size: 0.7rem;">${initial}</div>`;
                    }
                    messageHtml = `
                        <div class="d-flex justify-content-start mb-3 align-items-end">
                            <a href="/profile/${message.sender_username}/" class="me-2 text-decoration-none">
                                ${avatarHtml}
                            </a>
                            <div class="message-bubble received bg-light text-dark rounded-4 rounded-bottom-start-0 py-2 px-3 shadow-sm border" style="max-width: 75%; white-space: pre-line;">${escapeHTML(message.content)}</div>
                        </div>
                    `;
                }
                
                // Append message before typing indicator
                if (typingIndicator) {
                    typingIndicator.insertAdjacentHTML('beforebegin', messageHtml);
                } else {
                    chatMessages.insertAdjacentHTML('beforeend', messageHtml);
                }
                
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                // Send read receipt if we are not the sender
                if (senderId !== currentUserId) {
                    chatSocket.send(JSON.stringify({
                        'action': 'read_receipt'
                    }));
                }
            }
            
            else if (data.type === 'typing') {
                const senderId = data.sender_id;
                const currentUserId = parseInt(document.body.dataset.userId);
                
                if (senderId !== currentUserId) {
                    const typingIndicator = document.getElementById('typing-indicator');
                    const typingUsername = document.getElementById('typing-username');
                    
                    if (typingIndicator && typingUsername) {
                        if (data.typing) {
                            typingUsername.textContent = data.sender_username;
                            typingIndicator.classList.remove('d-none');
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                        } else {
                            typingIndicator.classList.add('d-none');
                        }
                    }
                }
            }
        };
        
        chatSocket.onclose = function(e) {
            console.log('Chat socket closed. Reconnecting in 3s...', e.reason);
            showConnectionStatus(false);
            setTimeout(connectChatSocket, 3000);
        };
        
        chatSocket.onerror = function(err) {
            console.error('Chat socket encountered error, closing.', err);
            chatSocket.close();
        };
    }
    
    function showConnectionStatus(connected) {
        const input = document.getElementById('chat-message-input');
        const form = document.getElementById('chat-form');
        if (input) {
            if (connected) {
                input.removeAttribute('disabled');
                input.placeholder = "Message...";
                if (form) form.classList.remove('opacity-75');
            } else {
                input.setAttribute('disabled', 'true');
                input.placeholder = "Connection lost. Reconnecting...";
                if (form) form.classList.add('opacity-75');
            }
        }
    }
    
    // --- Chat Form & Typing Event Handlers ---
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-message-input');
    
    if (chatForm && chatInput) {
        // Prevent default submit and send message over WebSocket
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (message && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify({
                    'action': 'message',
                    'message': message
                }));
                chatInput.value = '';
                
                // Clear typing indicator state
                clearTimeout(typingTimeout);
                isTyping = false;
                chatSocket.send(JSON.stringify({
                    'action': 'typing',
                    'typing': false
                }));
            }
        });
        
        // Typing Event detection
        chatInput.addEventListener('input', function() {
            if (!isTyping && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                isTyping = true;
                chatSocket.send(JSON.stringify({
                    'action': 'typing',
                    'typing': true
                }));
            }
            
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(function() {
                if (isTyping && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
                    isTyping = false;
                    chatSocket.send(JSON.stringify({
                        'action': 'typing',
                        'typing': false
                    }));
                }
            }, 3000); // 3 seconds of inactivity to auto-hide
        });
    }
    
    // Initialize WebSockets
    connectNotificationSocket();
    connectChatSocket();
});

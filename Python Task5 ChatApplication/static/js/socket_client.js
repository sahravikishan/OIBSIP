/**
 * Sanwad Real-Time Socket.IO Client
 * Manages WebSocket connection, events, room subscriptions, and messaging
 */

class ChatSocketClient {
    constructor() {
        this.socket = null;
        this.currentRoomId = null;
        this.currentRoomName = "General";
        this.typingTimeout = null;
        this.currentUserId = null;
        this.currentUsername = null;
        
        this.init();
    }

    init() {
        const usernameEl = document.getElementById("current-username");
        if (usernameEl) {
            this.currentUsername = usernameEl.textContent.trim();
            this.currentUserId = parseInt(usernameEl.dataset.userId, 10);
        }

        // Connect via Socket.IO
        this.socket = io({
            reconnectionAttempts: 10,
            reconnectionDelay: 1000
        });

        this.bindEvents();
    }

    bindEvents() {
        const statusIndicator = document.getElementById("connection-status");
        const statusDot = statusIndicator?.querySelector(".status-indicator");
        const statusLabel = document.getElementById("status-label");

        this.socket.on("connect", () => {
            if (statusDot) {
                statusDot.className = "status-indicator status-online";
                if (statusLabel) statusLabel.textContent = "Online";
            }
            // Auto-join active room if set
            if (this.currentRoomId) {
                this.joinRoom(this.currentRoomId);
            }
        });

        this.socket.on("disconnect", (reason) => {
            if (statusDot) {
                statusDot.className = "status-indicator status-offline";
                if (statusLabel) statusLabel.textContent = "Disconnected";
            }
        });

        this.socket.on("connect_error", () => {
            if (statusDot) {
                statusDot.className = "status-indicator status-connecting";
                if (statusLabel) statusLabel.textContent = "Reconnecting...";
            }
        });

        this.socket.on("room_history", (data) => {
            this.currentRoomId = data.room_id;
            this.currentRoomName = data.room_name;
            window.chatUI.renderRoomHistory(data);
        });

        this.socket.on("new_message", (msg) => {
            const isCurrentRoom = !this.currentRoomId || parseInt(msg.room_id, 10) === parseInt(this.currentRoomId, 10);
            const isOwn = (msg.username === this.currentUsername);

            if (isCurrentRoom) {
                // Append message bubble to current active viewport
                window.chatUI.appendMessage(msg, isOwn);
            } else {
                // If message is for another room, increment badge
                if (window.chatUI && window.chatUI.incrementRoomBadge) {
                    window.chatUI.incrementRoomBadge(msg.room_id);
                }
            }

            // Trigger notification if message is from another user
            if (!isOwn && window.notificationManager) {
                window.notificationManager.notifyMessage(msg.username, msg.content, this.currentRoomName);
            }
        });

        this.socket.on("system_message", (data) => {
            window.chatUI.appendSystemEvent(data);
        });

        this.socket.on("room_users_update", (data) => {
            if (data.room_id === this.currentRoomId) {
                window.chatUI.updateOnlineParticipants(data.users);
            }
        });

        this.socket.on("user_typing", (data) => {
            if (data.room_id === this.currentRoomId) {
                window.chatUI.displayTypingIndicator(data.username, data.is_typing);
            }
        });

        this.socket.on("global_presence_update", (data) => {
            if (window.chatUI && window.chatUI.updateGlobalPresence) {
                window.chatUI.updateGlobalPresence(data.online_users || []);
            }
        });

        this.socket.on("direct_message_alert", (data) => {
            // Only trigger alert if user is not actively viewing this room
            if (this.currentRoomId !== data.room_id) {
                if (window.chatUI && window.chatUI.incrementDmBadge) {
                    window.chatUI.incrementDmBadge(data.room_id);
                }
                if (window.showToast) {
                    window.showToast(`@${data.sender_username} sent you a message: "${data.preview}"`, "info");
                }
                if (window.notificationManager) {
                    window.notificationManager.notifyMessage(data.sender_username, data.preview, `@${data.sender_username}`);
                }
            }
        });

        this.socket.on("error", (err) => {
            if (err.locked && window.openUnlockModal) {
                window.openUnlockModal(err.room_id);
                return;
            }
            const errMsg = "Chat Error: " + (err.message || "An unexpected error occurred.");
            if (window.showToast) {
                window.showToast(errMsg, "error");
            } else {
                console.error(errMsg);
            }
        });
    }

    joinRoom(roomId) {
        this.currentRoomId = roomId;
        this.socket.emit("join_chat_room", { room_id: roomId });
    }

    sendMessage(roomId, content) {
        if (!content || !content.trim()) return;
        if (!this.socket || !this.socket.connected) {
            if (window.showToast) {
                window.showToast("Cannot send: Reconnecting to chat server...", "error");
            }
            return;
        }
        this.socket.emit("send_message", {
            room_id: roomId,
            content: content.trim()
        });
    }

    sendTyping(isTyping) {
        if (!this.currentRoomId) return;
        this.socket.emit("typing", {
            room_id: this.currentRoomId,
            is_typing: isTyping
        });
    }
}

// Global instance
window.chatSocket = new ChatSocketClient();

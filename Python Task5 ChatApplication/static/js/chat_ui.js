/**
 * Sanwad UI Controller
 * Manages DOM manipulation, message rendering, room switching, and modals
 */

class ChatUI {
    constructor() {
        this.messagesViewport = document.getElementById("messages-viewport");
        this.messagesStream = document.getElementById("messages-stream");
        this.messageInput = document.getElementById("message-input");
        this.typingTimer = null;
        this.isCurrentlyTyping = false;

        this.init();
    }

    init() {
        // Restore last active room or default to the first room in the sidebar
        const savedRoomId = localStorage.getItem("sanwad_active_room_id");
        let initialBtn = null;
        if (savedRoomId) {
            initialBtn = document.querySelector(`.room-item[data-room-id="${savedRoomId}"]`);
        }
        if (!initialBtn) {
            initialBtn = document.querySelector(".room-item");
        }
        if (initialBtn) {
            const roomId = parseInt(initialBtn.dataset.roomId, 10);
            this.selectRoom(roomId);
        }

        // Typing input listener
        if (this.messageInput) {
            this.messageInput.addEventListener("input", () => this.handleInputChange());
            this.messageInput.focus();
        }

        // Modal triggers
        const btnCreateRoom = document.getElementById("btn-open-create-room");
        if (btnCreateRoom) {
            btnCreateRoom.addEventListener("click", () => openCreateRoomModal());
        }

        const btnDirectModal = document.getElementById("btn-open-direct-modal");
        if (btnDirectModal) {
            btnDirectModal.addEventListener("click", () => openDirectChatModal());
        }

        const btnTransparency = document.getElementById("btn-open-transparency");
        if (btnTransparency) {
            btnTransparency.addEventListener("click", () => openTransparencyModal());
        }

        // Theme Toggle
        const btnThemeToggle = document.getElementById("btn-theme-toggle");
        if (btnThemeToggle) {
            btnThemeToggle.addEventListener("click", () => this.toggleTheme());
        }
        this.updateThemeIcon();

        // Mobile drawer toggle
        const btnMobileMenu = document.getElementById("btn-mobile-menu");
        if (btnMobileMenu) {
            btnMobileMenu.addEventListener("click", () => {
                const sidebar = document.getElementById("chat-sidebar");
                if (sidebar) sidebar.classList.toggle("open");
            });
        }
    }

    toggleTheme() {
        const current = document.documentElement.getAttribute("data-theme") || "dark";
        const nextTheme = (current === "dark") ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", nextTheme);
        localStorage.setItem("sanwad_theme", nextTheme);
        localStorage.setItem("novachat_theme", nextTheme);
        this.updateThemeIcon();
    }

    updateThemeIcon() {
        const current = document.documentElement.getAttribute("data-theme") || "dark";
        const icon = document.getElementById("theme-toggle-icon");
        const toggleBtn = document.getElementById("btn-theme-toggle");
        if (toggleBtn) {
            toggleBtn.setAttribute("title", current === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode");
            toggleBtn.setAttribute("aria-label", current === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode");
        }
        if (icon) {
            icon.innerHTML = (current === "dark")
                ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`
                : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
        }
    }

    selectRoom(roomId) {
        const targetId = parseInt(roomId, 10);
        if (isNaN(targetId)) return;

        try {
            localStorage.setItem("sanwad_active_room_id", String(targetId));
        } catch (e) {}

        // Highlight active room in sidebar (handles both group rooms and dm items)
        const roomButtons = document.querySelectorAll(".room-item");
        let selectedBtn = null;
        roomButtons.forEach(btn => {
            if (parseInt(btn.dataset.roomId, 10) === targetId) {
                btn.classList.add("active");
                selectedBtn = btn;
            } else {
                btn.classList.remove("active");
            }
        });

        if (selectedBtn) {
            const isDm = selectedBtn.classList.contains("dm-item");
            const roomName = selectedBtn.dataset.roomName;
            const partnerName = selectedBtn.dataset.partnerUsername || (roomName ? roomName.replace("@", "") : "");
            const roomDesc = selectedBtn.dataset.roomDesc;

            // Clear unread badge on active room selection
            const badge = document.getElementById(`badge-room-${roomId}`);
            if (badge) {
                badge.textContent = "0";
                badge.style.display = "none";
            }
            this.refreshTotalDmBadge();

            // Update Header Elements
            const hashEl = document.getElementById("active-room-hash");
            const avatarEl = document.getElementById("dm-header-avatar");
            const titleEl = document.getElementById("active-room-title");
            const typeBadgeEl = document.getElementById("chat-type-badge");
            const descEl = document.getElementById("active-room-description");

            // Update Welcome Banner Elements
            const welcomeTitleEl = document.getElementById("welcome-room-title");
            const welcomeDescEl = document.getElementById("welcome-room-desc");
            const welcomePrivacyNotice = document.getElementById("welcome-privacy-notice");

            if (isDm) {
                if (hashEl) hashEl.style.display = "none";
                if (avatarEl) {
                    avatarEl.style.display = "inline-flex";
                    avatarEl.textContent = (partnerName || "U").charAt(0).toUpperCase();
                }
                if (titleEl) titleEl.textContent = `@${partnerName}`;
                if (typeBadgeEl) {
                    typeBadgeEl.textContent = "Personal Chat";
                    typeBadgeEl.className = "chat-type-badge personal";
                }
                if (descEl) descEl.textContent = `Direct private conversation with @${partnerName}`;
                if (welcomeTitleEl) welcomeTitleEl.textContent = `Private Chat with @${partnerName}`;
                if (welcomeDescEl) welcomeDescEl.textContent = "This conversation is strictly private between you two.";
                if (welcomePrivacyNotice) welcomePrivacyNotice.style.display = "inline-flex";
            } else {
                if (hashEl) {
                    hashEl.style.display = "inline-block";
                    hashEl.textContent = "#";
                }
                if (avatarEl) avatarEl.style.display = "none";
                if (titleEl) titleEl.textContent = roomName;
                if (typeBadgeEl) {
                    typeBadgeEl.textContent = "Chat Room";
                    typeBadgeEl.className = "chat-type-badge";
                }
                if (descEl) descEl.textContent = roomDesc || `Group discussion in #${roomName}`;
                if (welcomeTitleEl) welcomeTitleEl.textContent = `Welcome to #${roomName}`;
                if (welcomeDescEl) welcomeDescEl.textContent = roomDesc || "This is the start of this channel. Messages are stored persistently.";
                if (welcomePrivacyNotice) welcomePrivacyNotice.style.display = "none";
            }

            // Synchronize active mode tab
            switchChatMode(isDm ? 'direct' : 'rooms');

            if (this.messageInput) {
                this.messageInput.placeholder = isDm ? `Message @${partnerName}...` : `Message #${roomName}...`;
            }

            // Close mobile sidebar if open
            const sidebar = document.getElementById("chat-sidebar");
            if (sidebar) sidebar.classList.remove("open");
        }

        // Emit room join to server
        if (window.chatSocket) {
            window.chatSocket.joinRoom(roomId);
        }
    }

    updateGlobalPresence(onlineUsernames) {
        // Update green dots on all direct message contacts
        const dmDots = document.querySelectorAll(".dm-status-dot");
        dmDots.forEach(dot => {
            const user = dot.dataset.user;
            if (onlineUsernames.includes(user)) {
                dot.classList.add("online");
                dot.title = `${user} is Online`;
            } else {
                dot.classList.remove("online");
                dot.title = `${user} is Offline`;
            }
        });
    }

    incrementDmBadge(roomId) {
        const badge = document.getElementById(`badge-room-${roomId}`);
        if (badge) {
            const current = parseInt(badge.textContent, 10) || 0;
            badge.textContent = current + 1;
            badge.style.display = "inline-flex";
        }
        this.refreshTotalDmBadge();
    }

    refreshTotalDmBadge() {
        const badges = document.querySelectorAll(".dm-badge");
        let total = 0;
        badges.forEach(b => {
            const val = parseInt(b.textContent, 10) || 0;
            total += val;
        });
        const totalBadge = document.getElementById("total-dm-badge");
        if (totalBadge) {
            if (total > 0) {
                totalBadge.textContent = total > 99 ? "99+" : total;
                totalBadge.style.display = "inline-flex";
            } else {
                totalBadge.style.display = "none";
            }
        }
    }


    renderRoomHistory(data) {
        if (!this.messagesStream) return;
        this.messagesStream.innerHTML = "";

        const messages = data.messages || [];
        const currentUsername = window.chatSocket?.currentUsername;

        messages.forEach(msg => {
            const isOwn = (msg.username === currentUsername);
            this.appendMessage(msg, isOwn, false);
        });

        this.scrollToBottom();
    }

    formatTimestamp(dateStr) {
        if (!dateStr) return "";
        try {
            const str = String(dateStr).trim();
            if (str.includes("AM") || str.includes("PM")) {
                return str.startsWith("[") ? str : `[${str}]`;
            }
            // Parse SQLite YYYY-MM-DD HH:MM:SS or ISO 8601
            const iso = str.replace(" ", "T") + (str.includes("Z") ? "" : "Z");
            const date = new Date(iso);
            if (!isNaN(date.getTime())) {
                let hours = date.getHours();
                const minutes = String(date.getMinutes()).padStart(2, "0");
                const ampm = hours >= 12 ? "PM" : "AM";
                hours = hours % 12 || 12;
                const hoursStr = String(hours).padStart(2, "0");
                return `[${hoursStr}:${minutes} ${ampm}]`;
            }
            // Fallback for time-only strings "HH:MM" or "HH:MM:SS"
            const match = str.match(/(\d{1,2}):(\d{2})/);
            if (match) {
                let h = parseInt(match[1], 10);
                const m = match[2];
                const ampm = h >= 12 ? "PM" : "AM";
                h = h % 12 || 12;
                const hStr = String(h).padStart(2, "0");
                return `[${hStr}:${m} ${ampm}]`;
            }
            return `[${str}]`;
        } catch (e) {
            return String(dateStr);
        }
    }

    appendMessage(msg, isOwn = false, shouldScroll = true) {
        if (!this.messagesStream) return;

        const entry = document.createElement("div");
        entry.className = `message-entry ${isOwn ? 'own-message' : ''}`;

        // Avatar
        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = (msg.username || "?").charAt(0).toUpperCase();

        // Bubble Wrapper
        const bubbleWrapper = document.createElement("div");
        bubbleWrapper.className = "message-bubble-wrapper";

        // Meta (Username and Timestamp)
        const meta = document.createElement("div");
        meta.className = "message-meta";

        const usernameSpan = document.createElement("span");
        usernameSpan.className = "msg-username";
        usernameSpan.textContent = isOwn ? "You" : msg.username;

        const timeSpan = document.createElement("span");
        timeSpan.className = "msg-timestamp";
        timeSpan.textContent = this.formatTimestamp(msg.created_at);

        if (isOwn) {
            meta.appendChild(timeSpan);
            meta.appendChild(usernameSpan);
        } else {
            meta.appendChild(usernameSpan);
            meta.appendChild(timeSpan);
        }

        // Bubble (Content text node to completely prevent XSS)
        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.textContent = msg.content; // textContent escapes all HTML tags safely

        bubbleWrapper.appendChild(meta);
        bubbleWrapper.appendChild(bubble);

        entry.appendChild(avatar);
        entry.appendChild(bubbleWrapper);

        this.messagesStream.appendChild(entry);

        if (shouldScroll) {
            this.scrollToBottom();
        }
    }

    appendSystemEvent(data) {
        if (!this.messagesStream) return;

        const container = document.createElement("div");
        container.className = "system-event-entry";

        const pill = document.createElement("div");
        pill.className = `system-pill ${data.type || 'info'}`;

        const textSpan = document.createElement("span");
        textSpan.textContent = data.content;

        const timeSpan = document.createElement("span");
        timeSpan.className = "system-time";

        let timeText = data.timestamp || "";
        if (timeText && !timeText.includes("AM") && !timeText.includes("PM")) {
            // Convert 24hr HH:MM to 12hr AM/PM
            const match = timeText.match(/(\d{1,2}):(\d{2})/);
            if (match) {
                let h = parseInt(match[1], 10);
                const m = match[2];
                const ampm = h >= 12 ? "PM" : "AM";
                h = h % 12 || 12;
                const hStr = String(h).padStart(2, "0");
                timeText = `${hStr}:${m} ${ampm}`;
            }
        }
        timeSpan.textContent = timeText ? `[${timeText}]` : "";

        pill.appendChild(textSpan);
        if (timeText) pill.appendChild(timeSpan);

        container.appendChild(pill);
        this.messagesStream.appendChild(container);
        this.scrollToBottom();
    }

    updateOnlineParticipants(usersList) {
        const badge = document.getElementById("participants-count");
        if (!badge) return;
        const count = usersList.length;
        badge.textContent = `${count} online`;
        badge.parentElement.title = `Users in room: ${usersList.join(", ")}`;
    }

    displayTypingIndicator(username, isTyping) {
        const indicator = document.getElementById("typing-indicator");
        const typingText = document.getElementById("typing-text");
        if (!indicator || !typingText) return;

        if (isTyping) {
            typingText.textContent = `${username} is typing...`;
            indicator.style.display = "flex";
            this.scrollToBottom();
        } else {
            indicator.style.display = "none";
        }
    }

    handleInputChange() {
        if (!this.isCurrentlyTyping) {
            this.isCurrentlyTyping = true;
            window.chatSocket?.sendTyping(true);
        }

        clearTimeout(this.typingTimer);
        this.typingTimer = setTimeout(() => {
            this.isCurrentlyTyping = false;
            window.chatSocket?.sendTyping(false);
        }, 1200);
    }

    scrollToBottom() {
        if (this.messagesViewport) {
            this.messagesViewport.scrollTop = this.messagesViewport.scrollHeight;
        }
    }

    incrementRoomBadge(roomId) {
        const badge = document.getElementById(`badge-room-${roomId}`);
        if (badge) {
            const current = parseInt(badge.textContent, 10) || 0;
            badge.textContent = current + 1;
        }
    }
}

// Global functions for inline HTML event handlers

function selectRoom(roomId) {
    if (window.chatUI) {
        window.chatUI.selectRoom(roomId);
    }
}

function handleSendMessage(event) {
    event.preventDefault();
    const input = document.getElementById("message-input");
    if (!input) return;

    const content = input.value.trim();
    if (!content) return;

    const currentRoomId = window.chatSocket?.currentRoomId;
    if (!currentRoomId) {
        showToast("Please select a chat room first.", "info");
        return;
    }

    window.chatSocket.sendMessage(currentRoomId, content);
    input.value = "";
    input.focus();
}

function openCreateRoomModal() {
    const modal = document.getElementById("modal-create-room");
    const err = document.getElementById("create-room-error");
    if (err) {
        err.style.display = "none";
        err.textContent = "";
    }
    if (modal) modal.style.display = "flex";
    const nameInput = document.getElementById("new-room-name");
    if (nameInput) {
        nameInput.value = "";
        nameInput.focus();
    }
}

function closeCreateRoomModal() {
    const modal = document.getElementById("modal-create-room");
    if (modal) modal.style.display = "none";
}

function handleCreateRoom(event) {
    event.preventDefault();
    const nameInput = document.getElementById("new-room-name");
    const descInput = document.getElementById("new-room-desc");
    const passcodeInput = document.getElementById("new-room-passcode");
    const errBox = document.getElementById("create-room-error");

    const name = (nameInput?.value || "").trim();
    const description = (descInput?.value || "").trim();
    const passcode = (passcodeInput?.value || "").trim();

    if (!name) return;

    fetch("/api/rooms", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description, passcode })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            if (errBox) {
                errBox.textContent = data.error || "Failed to create room.";
                errBox.style.display = "block";
            }
            return;
        }

        // Successfully created: add to rooms list
        const room = data.room;
        const roomsNav = document.getElementById("rooms-list");
        if (roomsNav) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "room-item";
            btn.dataset.roomId = room.id;
            btn.dataset.roomName = room.name;
            btn.dataset.roomDesc = room.description || "";
            btn.dataset.isLocked = room.is_locked ? "1" : "0";
            btn.onclick = () => selectRoom(room.id);

            const iconHtml = room.is_locked
                ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>`
                : `#`;

            btn.innerHTML = `
                <span class="room-hash">${iconHtml}</span>
                <span class="room-name-label">${escapeHtml(room.name)}</span>
                <span class="room-msg-count" id="badge-room-${room.id}">0</span>
            `;
            roomsNav.appendChild(btn);
        }

        closeCreateRoomModal();
        // Switch to the newly created room
        selectRoom(room.id);
    })
    .catch(err => {
        if (errBox) {
            errBox.textContent = "Network error creating room. Please try again.";
            errBox.style.display = "block";
        }
    });
}

// --- Direct Chat (Personal 1-on-1) Directory Modal ---
let allDirectoryUsers = [];

function openDirectChatModal() {
    const modal = document.getElementById("modal-direct-chat");
    const container = document.getElementById("users-directory-list");
    const searchInput = document.getElementById("user-search-input");
    if (searchInput) searchInput.value = "";
    if (modal) modal.style.display = "flex";

    if (container) {
        container.innerHTML = `<div class="loading-spinner-small">Loading users...</div>`;
    }

    fetch("/api/users/directory")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                allDirectoryUsers = data.users || [];
                renderUsersDirectory(allDirectoryUsers);
            } else {
                if (container) container.innerHTML = `<div class="directory-empty">Could not load users.</div>`;
            }
        })
        .catch(() => {
            if (container) container.innerHTML = `<div class="directory-empty">Network error loading users.</div>`;
        });
}

function closeDirectChatModal() {
    const modal = document.getElementById("modal-direct-chat");
    if (modal) modal.style.display = "none";
}

function renderUsersDirectory(users) {
    const container = document.getElementById("users-directory-list");
    if (!container) return;

    if (users.length === 0) {
        container.innerHTML = `<div class="directory-empty">No other registered users found. Invite a friend to register!</div>`;
        return;
    }

    container.innerHTML = "";
    users.forEach(user => {
        const item = document.createElement("div");
        item.className = "directory-user-row";
        const initial = (user.username || "U").charAt(0).toUpperCase();

        item.innerHTML = `
            <div class="user-row-avatar">${initial}</div>
            <div class="user-row-info">
                <span class="user-row-name">@${escapeHtml(user.username)}</span>
                <span class="user-row-sub">Click to start private chat</span>
            </div>
            <button type="button" class="btn btn-sm btn-primary">Chat</button>
        `;

        item.addEventListener("click", () => startDirectConversation(user.id, user.username));
        container.appendChild(item);
    });
}

function filterUsersDirectory(query) {
    const q = (query || "").toLowerCase().trim();
    if (!q) {
        renderUsersDirectory(allDirectoryUsers);
        return;
    }
    const filtered = allDirectoryUsers.filter(u => u.username.toLowerCase().includes(q));
    renderUsersDirectory(filtered);
}

function startDirectConversation(userId, username) {
    fetch("/api/direct/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            showToast(data.error || "Could not start personal chat.", "error");
            return;
        }

        closeDirectChatModal();

        // Check if DM is already in the sidebar list
        const dmNav = document.getElementById("dm-list");
        const existingBtn = dmNav ? dmNav.querySelector(`[data-room-id="${data.room_id}"]`) : null;

        if (!existingBtn && dmNav) {
            // Remove empty hint if present
            const hint = document.getElementById("empty-dm-hint");
            if (hint) hint.remove();

            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "room-item dm-item";
            btn.dataset.roomId = data.room_id;
            btn.dataset.roomName = `@${username}`;
            btn.dataset.partnerUsername = username;
            btn.dataset.roomDesc = `Private personal chat with ${username}`;
            btn.onclick = () => selectRoom(data.room_id);

            btn.innerHTML = `
                <span class="dm-status-dot" data-user="${escapeHtml(username)}"></span>
                <span class="room-name-label">@${escapeHtml(username)}</span>
                <span class="room-msg-count dm-badge" id="badge-room-${data.room_id}" style="display: none;">0</span>
            `;
            dmNav.appendChild(btn);
        }

        // Switch view to Personal Chat tab and select room
        switchChatMode('direct');
        selectRoom(data.room_id);
    })
    .catch(() => {
        showToast("Network error starting personal chat.", "error");
    });
}

function switchChatMode(mode, userInitiated = false) {
    const tabRooms = document.getElementById("tab-btn-rooms");
    const tabDirect = document.getElementById("tab-btn-direct");
    const panelRooms = document.getElementById("view-panel-rooms");
    const panelDirect = document.getElementById("view-panel-direct");

    if (mode === "rooms") {
        if (tabRooms) {
            tabRooms.classList.add("active");
            tabRooms.setAttribute("aria-selected", "true");
        }
        if (tabDirect) {
            tabDirect.classList.remove("active");
            tabDirect.setAttribute("aria-selected", "false");
        }
        if (panelRooms) panelRooms.style.display = "flex";
        if (panelDirect) panelDirect.style.display = "none";

        if (userInitiated) {
            const activeItem = document.querySelector(".room-item.active");
            if (!activeItem || activeItem.classList.contains("dm-item")) {
                const firstRoom = document.querySelector("#rooms-list .room-item");
                if (firstRoom) {
                    selectRoom(parseInt(firstRoom.dataset.roomId, 10));
                }
            }
        }
    } else if (mode === "direct") {
        if (tabDirect) {
            tabDirect.classList.add("active");
            tabDirect.setAttribute("aria-selected", "true");
        }
        if (tabRooms) {
            tabRooms.classList.remove("active");
            tabRooms.setAttribute("aria-selected", "false");
        }
        if (panelRooms) panelRooms.style.display = "none";
        if (panelDirect) panelDirect.style.display = "flex";

        if (userInitiated) {
            const activeItem = document.querySelector(".room-item.active");
            if (!activeItem || !activeItem.classList.contains("dm-item")) {
                const firstDm = document.querySelector("#dm-list .dm-item");
                if (firstDm) {
                    selectRoom(parseInt(firstDm.dataset.roomId, 10));
                }
            }
        }
    }
}

// --- Protected Passcode Room Unlock Modal ---
function openUnlockModal(roomId) {
    const modal = document.getElementById("modal-unlock-room");
    const idInput = document.getElementById("unlock-room-id");
    const passInput = document.getElementById("unlock-passcode");
    const err = document.getElementById("unlock-room-error");

    if (idInput) idInput.value = roomId;
    if (passInput) {
        passInput.value = "";
        passInput.focus();
    }
    if (err) {
        err.style.display = "none";
        err.textContent = "";
    }
    if (modal) modal.style.display = "flex";
}

function closeUnlockModal() {
    const modal = document.getElementById("modal-unlock-room");
    if (modal) modal.style.display = "none";
}

function handleUnlockRoom(event) {
    event.preventDefault();
    const idInput = document.getElementById("unlock-room-id");
    const passInput = document.getElementById("unlock-passcode");
    const err = document.getElementById("unlock-room-error");

    const roomId = idInput ? parseInt(idInput.value, 10) : null;
    const passcode = (passInput ? passInput.value : "").trim();

    if (!roomId) return;

    fetch("/api/rooms/unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ room_id: roomId, passcode })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            if (err) {
                err.textContent = data.error || "Incorrect passcode.";
                err.style.display = "block";
            }
            return;
        }

        closeUnlockModal();
        showToast("Room unlocked successfully!", "success");
        // Re-join room with authorized membership
        selectRoom(roomId);
    })
    .catch(() => {
        if (err) {
            err.textContent = "Network error verifying passcode.";
            err.style.display = "block";
        }
    });
}

window.switchChatMode = switchChatMode;
window.openUnlockModal = openUnlockModal;
window.closeUnlockModal = closeUnlockModal;
window.handleUnlockRoom = handleUnlockRoom;
window.openDirectChatModal = openDirectChatModal;
window.closeDirectChatModal = closeDirectChatModal;



function openTransparencyModal() {
    const modal = document.getElementById("modal-transparency");
    if (modal) modal.style.display = "flex";
}

function closeTransparencyModal() {
    const modal = document.getElementById("modal-transparency");
    if (modal) modal.style.display = "none";
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Shows an auto-dismissing toast notification popup.
 * Stays visible for exactly duration ms (default 5000ms / 5s) before fading out.
 */
function showToast(message, type = "info", duration = 5000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-message toast-${type}`;

    let iconSvg = "";
    if (type === "error") {
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
    } else if (type === "success") {
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
    } else {
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
    }

    toast.innerHTML = `
        <span class="toast-icon">${iconSvg}</span>
        <span class="toast-body">${escapeHtml(message)}</span>
        <button type="button" class="toast-close" aria-label="Close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;

    const closeBtn = toast.querySelector(".toast-close");
    let dismissTimeout;

    const dismissToast = () => {
        clearTimeout(dismissTimeout);
        toast.classList.add("fade-out");
        setTimeout(() => {
            if (toast.parentElement) toast.remove();
        }, 400);
    };

    if (closeBtn) {
        closeBtn.addEventListener("click", dismissToast);
    }

    container.appendChild(toast);

    // Auto dismiss after exactly duration ms (default 5000ms = 5 seconds)
    dismissTimeout = setTimeout(dismissToast, duration);
}

// Make showToast accessible globally
window.showToast = showToast;

// Instantiate UI controller on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    window.chatUI = new ChatUI();
});


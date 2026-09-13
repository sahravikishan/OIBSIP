/**
 * Sanwad Emoji Engine & Picker
 * Handles shortcode translation and interactive emoji selector
 */

let emojiCatalog = [];

function initEmojiEngine() {
    const dataEl = document.getElementById("emoji-catalog-data");
    if (dataEl) {
        try {
            emojiCatalog = JSON.parse(dataEl.textContent);
        } catch (e) {
            console.error("Failed to parse emoji catalog:", e);
        }
    }

    renderEmojiGrid();
}

function renderEmojiGrid() {
    const grid = document.getElementById("emoji-grid");
    if (!grid || !emojiCatalog.length) return;

    grid.innerHTML = "";
    emojiCatalog.forEach(item => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "emoji-btn";
        btn.textContent = item.char;
        btn.title = item.code;
        btn.onclick = () => insertEmoji(item.char);
        grid.appendChild(btn);
    });
}

function insertEmoji(emojiChar) {
    const input = document.getElementById("message-input");
    if (!input) return;

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const text = input.value;

    input.value = text.substring(0, start) + emojiChar + text.substring(end);
    input.focus();
    input.selectionStart = input.selectionEnd = start + emojiChar.length;

    // Close picker after inserting
    const picker = document.getElementById("emoji-picker-dropdown") || document.getElementById("emoji-picker");
    if (picker) picker.style.display = "none";
}

function toggleEmojiPicker() {
    const picker = document.getElementById("emoji-picker-dropdown") || document.getElementById("emoji-picker");
    if (!picker) return;
    picker.style.display = (picker.style.display === "none" || !picker.style.display) ? "block" : "none";
}

// Close picker on outside click
document.addEventListener("click", (e) => {
    const picker = document.getElementById("emoji-picker-dropdown") || document.getElementById("emoji-picker");
    const toggleBtn = document.getElementById("btn-emoji-picker") || document.getElementById("btn-toggle-emoji");
    if (!picker || !toggleBtn) return;

    if (picker.style.display === "block" && !picker.contains(e.target) && !toggleBtn.contains(e.target)) {
        picker.style.display = "none";
    }
});

document.addEventListener("DOMContentLoaded", () => {
    initEmojiEngine();

    const toggleBtn = document.getElementById("btn-emoji-picker") || document.getElementById("btn-toggle-emoji");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            toggleEmojiPicker();
        });
    }

    const closeBtn = document.getElementById("btn-close-emoji");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            const picker = document.getElementById("emoji-picker-dropdown") || document.getElementById("emoji-picker");
            if (picker) picker.style.display = "none";
        });
    }
});

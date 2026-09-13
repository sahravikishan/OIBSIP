/**
 * Sanwad Authentication Controller
 * Handles tab switching and client-side form validation
 */

function switchTab(mode) {
    const tabLogin = document.getElementById("tab-login");
    const tabRegister = document.getElementById("tab-register");
    const formLogin = document.getElementById("form-login");
    const formRegister = document.getElementById("form-register");

    if (mode === "login") {
        if (tabLogin) tabLogin.classList.add("active");
        if (tabRegister) tabRegister.classList.remove("active");
        if (formLogin) formLogin.classList.remove("hidden");
        if (formRegister) formRegister.classList.add("hidden");
        history.replaceState(null, "", "/login");
    } else {
        if (tabRegister) tabRegister.classList.add("active");
        if (tabLogin) tabLogin.classList.remove("active");
        if (formRegister) formRegister.classList.remove("hidden");
        if (formLogin) formLogin.classList.add("hidden");
        history.replaceState(null, "", "/register");
    }
}

function dismissToastElement(el) {
    if (!el) return;
    el.classList.add("fade-out");
    setTimeout(() => {
        if (el.parentElement) el.remove();
    }, 400);
}

function showToast(message, type = "error", duration = 5000) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-message toast-${type}`;

    let iconSvg = "";
    if (type === "danger" || type === "error") {
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
    } else if (type === "success") {
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`;
    } else {
        iconSvg = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>`;
    }

    const textSpan = document.createElement("span");
    textSpan.className = "toast-body";
    textSpan.textContent = message;

    toast.innerHTML = `
        <span class="toast-icon">${iconSvg}</span>
    `;
    toast.appendChild(textSpan);

    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "toast-close";
    closeBtn.setAttribute("aria-label", "Close");
    closeBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
    closeBtn.addEventListener("click", () => dismissToastElement(toast));
    toast.appendChild(closeBtn);

    container.appendChild(toast);

    setTimeout(() => {
        dismissToastElement(toast);
    }, duration);
}

document.addEventListener("DOMContentLoaded", () => {
    const formRegister = document.getElementById("form-register");

    if (formRegister) {
        formRegister.addEventListener("submit", (e) => {
            const usernameInput = document.getElementById("reg-username");
            const passwordInput = document.getElementById("reg-password");
            const confirmInput = document.getElementById("reg-confirm");

            const username = (usernameInput.value || "").trim();
            const password = passwordInput.value || "";
            const confirm = confirmInput.value || "";

            // Client-side validation displayed as separate toasts outside the card
            if (username.length < 3 || username.length > 25) {
                e.preventDefault();
                showToast("Username must be between 3 and 25 characters.", "danger");
                usernameInput.focus();
                return;
            }

            const validPattern = /^[a-zA-Z0-9_-]+$/;
            if (!validPattern.test(username)) {
                e.preventDefault();
                showToast("Username can only contain letters, numbers, hyphens, and underscores.", "danger");
                usernameInput.focus();
                return;
            }

            if (password.length < 6) {
                e.preventDefault();
                showToast("Password must be at least 6 characters long.", "danger");
                passwordInput.focus();
                return;
            }

            if (password !== confirm) {
                e.preventDefault();
                showToast("Passwords do not match. Please verify.", "danger");
                confirmInput.focus();
                return;
            }
        });
    }

    // Auto-dismiss any pre-rendered server flash toasts after 5 seconds
    const existingToasts = document.querySelectorAll(".toast-message[data-auto-dismiss]");
    existingToasts.forEach(toastEl => {
        const ms = parseInt(toastEl.dataset.autoDismiss, 10) || 5000;
        setTimeout(() => {
            dismissToastElement(toastEl);
        }, ms);
    });

    // Sync theme toggle icon
    updateThemeIcon();
});

function toggleGlobalTheme() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const nextTheme = (current === "dark") ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", nextTheme);
    localStorage.setItem("sanwad_theme", nextTheme);
    localStorage.setItem("novachat_theme", nextTheme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const icon = document.getElementById("theme-toggle-icon");
    const toggleBtn = document.querySelector(".btn-theme-pill, .btn-theme-toggle-auth");
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

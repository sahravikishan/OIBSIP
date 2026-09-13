/**
 * Sanwad Notification Manager
 * Handles desktop notifications, window focus detection, and audio cues
 */

class NotificationManager {
    constructor() {
        this.isWindowFocused = !document.hidden;
        this.hasNotificationPermission = ("Notification" in window) && Notification.permission === "granted";
        this.audioCtx = null;
        this.initFocusListeners();
        this.initUI();
    }

    initFocusListeners() {
        window.addEventListener("focus", () => {
            this.isWindowFocused = true;
        });

        window.addEventListener("blur", () => {
            this.isWindowFocused = false;
        });

        document.addEventListener("visibilitychange", () => {
            this.isWindowFocused = !document.hidden;
        });
    }

    initUI() {
        const promptBanner = document.getElementById("notification-prompt");
        const enableBtn = document.getElementById("btn-enable-notifications");

        if ("Notification" in window) {
            if (Notification.permission === "default" && promptBanner) {
                promptBanner.style.display = "flex";
            }
        }

        if (enableBtn) {
            enableBtn.addEventListener("click", () => {
                this.requestPermission();
            });
        }
    }

    requestPermission() {
        if (!("Notification" in window)) {
            if (window.showToast) {
                window.showToast("Desktop notifications are not supported in this browser.", "info");
            } else {
                console.warn("Desktop notifications are not supported in this browser.");
            }
            return;
        }

        Notification.requestPermission().then((permission) => {
            this.hasNotificationPermission = (permission === "granted");
            const promptBanner = document.getElementById("notification-prompt");
            if (promptBanner) {
                promptBanner.style.display = "none";
            }
        });
    }

    playNotificationSound() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            if (!this.audioCtx) {
                this.audioCtx = new AudioContext();
            }
            if (this.audioCtx.state === "suspended") {
                this.audioCtx.resume();
            }

            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();

            osc.type = "sine";
            osc.frequency.setValueAtTime(587.33, this.audioCtx.currentTime); // D5
            osc.frequency.exponentialRampToValueAtTime(880, this.audioCtx.currentTime + 0.12); // A5

            gain.gain.setValueAtTime(0.08, this.audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + 0.25);

            osc.connect(gain);
            gain.connect(this.audioCtx.destination);

            osc.start();
            osc.stop(this.audioCtx.currentTime + 0.25);
        } catch (e) {
            // Audio context not allowed or failed; ignore
        }
    }

    notifyMessage(sender, content, roomName) {
        // Do not notify if window is currently focused and active
        if (this.isWindowFocused && document.hasFocus()) {
            return;
        }

        // Play gentle chime
        this.playNotificationSound();

        // Browser desktop notification
        if ("Notification" in window && Notification.permission === "granted") {
            try {
                const title = `#${roomName} - ${sender}`;
                const options = {
                    body: content.length > 80 ? content.substring(0, 77) + "..." : content,
                    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><text y='20' font-size='20'>💬</text></svg>",
                    tag: `room_${roomName}`,
                    renotify: true
                };

                const notif = new Notification(title, options);
                notif.onclick = () => {
                    window.focus();
                    notif.close();
                };
            } catch (err) {
                console.warn("Could not dispatch desktop notification:", err);
            }
        }
    }
}

window.notificationManager = new NotificationManager();

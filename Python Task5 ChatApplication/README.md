# Sanwad - Advanced Real-Time Python Chat Application
**Oasis Infobyte Internship (OIBSIP) – Python Programming Task 5**

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1.1-green.svg)
![Flask-SocketIO](https://img.shields.io/badge/Flask--SocketIO-5.6.1-red.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)
![Status](https://img.shields.io/badge/Status-Fully%20Functional-brightgreen.svg)

---

## 1. Project Title
**Sanwad: Advanced Multi-Room & Personal Real-Time Chat Workspace**  
*(OIBSIP Python Programming Internship – Task 5: Chat Application)*

---

## 2. Project Overview
Sanwad is an independently architected, production-structured real-time web chat application engineered in Python. It replaces outdated terminal chat scripts with a modern web-based graphical user interface (GUI), bidirectional WebSocket communication powered by Flask-SocketIO, and persistent relational data storage backed by SQLite3. Sanwad enables multiple users to register securely, authenticate via salted password hashes, join or create distinct topical chat rooms, connect in 1-on-1 personal private chats, exchange instant messages with emoji shortcodes, toggle dynamically between Nordic Pine (Dark) and Fresh Mint (Light) themes, view persistent message histories across server restarts, and receive desktop notifications when the chat tab is unfocused.

---

## 3. UI Previews & Screenshots (Light & Dark Mode)

### 📸 Application Interface Previews

#### 1. Group Room Chat
| Dark Mode (Nordic Pine) | Light Mode (Fresh Mint) |
| :---: | :---: |
| ![Group Room Chat Dark](screenshots/Room_chat_dark_mode.png) | ![Group Room Chat Light](screenshots/Room_chat_light_mode.png) |

#### 2. 1-on-1 Personal Private Chat
| Dark Mode (Nordic Pine) | Light Mode (Fresh Mint) |
| :---: | :---: |
| ![Personal Chat Dark](screenshots/Personal_chat_dark_mode.png) | ![Personal Chat Light](screenshots/Personal_chat_light_mode.png) |

#### 3. User Authentication: Sign In
| Dark Mode (Nordic Pine) | Light Mode (Fresh Mint) |
| :---: | :---: |
| ![Sign In Dark](screenshots/Singup_page_dark_mode.png) | ![Sign In Light](screenshots/Singup_page_light_mode.png) |

#### 4. User Authentication: Registration
| Dark Mode (Nordic Pine) | Light Mode (Fresh Mint) |
| :---: | :---: |
| ![Registration Dark](screenshots/Register_page_dark_mode.png) | ![Registration Light](screenshots/Register_page_light_mode.png) |

---

### 📝 Screenshot Capture Prompts

Use the following exact prompts to reproduce or capture UI screenshots for both Light and Dark modes:

#### 🌙 Prompt 1: Dark Mode Chat Screenshot Capture
```text
Navigate to http://127.0.0.1:5000 in your web browser.
1. Sign in or register with username 'Alice' and password 'password123'.
2. Select any room (e.g., '#Projects') or switch to 'Personal Chat' mode to select a direct contact.
3. Ensure Dark Mode is active (default Nordic Pine theme with dark slate background #0b141a / #111b21 and emerald green accents #00a884; toggle via the circular Sun/Moon icon in the top header if currently in light mode).
4. Verify the active participant counter, 12-hour AM/PM timestamps, and floating composer.
5. Capture a high-resolution, full-window screenshot of the active interface and save it in screenshots/.
```

#### ☀️ Prompt 2: Light Mode Chat Screenshot Capture
```text
Navigate to http://127.0.0.1:5000 in your web browser.
1. Sign in or register with username 'Alice' and password 'password123'.
2. Select any room (e.g., '#Projects') or switch to 'Personal Chat' mode to select a direct contact.
3. Switch to Light Mode by clicking the circular Sun/Moon theme toggle button in the top navigation header (verify clean light background #f0f2f5 / #ffffff and fresh mint accents).
4. Confirm that the message composer, chat bubbles, sidebar, and 12-hour AM/PM timestamps display with high contrast and sharp typography.
5. Capture a high-resolution, full-window screenshot of the active interface and save it in screenshots/.
```

---

## 4. Objective
The objective of this project is to satisfy 100% of both **Beginner** and **Advanced** requirements specified for the OIBSIP Chat Application task, demonstrating sound software engineering, robust database design, WebSocket protocol handling, input validation, and security/privacy transparency without relying on boilerplate templates or copied repositories.

---

## 5. Features Summary

| Requirement Tier | Capability | Implementation Status |
| :--- | :--- | :--- |
| **Beginner** | Server script accepting incoming connections | **Implemented** (`Flask-SocketIO` on localhost) |
| **Beginner** | Real client connecting to server | **Implemented** (Browser WebSocket/HTTP long-polling client) |
| **Beginner** | Real-time bidirectional messaging | **Implemented** (Instant two-way event emission without page refresh) |
| **Beginner** | Timestamped messages with usernames | **Implemented** (`[hh:mm AM/PM]` 12-hour timestamps + author attribution) |
| **Beginner** | Graceful disconnection handling | **Implemented** (System notices on close/leave without server crash) |
| **Beginner** | Localhost execution | **Implemented** (`http://127.0.0.1:5000`) |
| **Advanced** | GUI Chat Application | **Implemented** (Responsive HTML5/CSS3/JavaScript interface) |
| **Advanced** | User Registration & Login | **Implemented** (PBKDF2-HMAC-SHA256 password hashing + session management) |
| **Advanced** | SQLite Authentication & Data Storage | **Implemented** (Users, Rooms, and Messages relational schema) |
| **Advanced** | Multiple Chat Rooms & 1-on-1 Personal Chat | **Implemented** (Dedicated channels & isolated 1-on-1 direct messaging) |
| **Advanced** | Light / Dark Theme Switching | **Implemented** (Nordic Pine Dark & Fresh Mint Light with persistent preference) |
| **Advanced** | Room Creation & Joining | **Implemented** (Dynamic room creation modal and live room switching) |
| **Advanced** | Persistent Message History | **Implemented** (History survives server restarts, queries via SQLite) |
| **Advanced** | Desktop / In-App Notifications | **Implemented** (HTML5 Web Notifications API + Page Visibility API) |
| **Advanced** | Emoji Shortcode Support | **Implemented** (50+ shortcodes like `:smile:`, `:heart:`, `:rocket:` + visual picker) |
| **Advanced** | Security & Privacy Transparency | **Implemented** (Full disclosure of SQLite storage and lack of E2EE) |

---

## 6. Beginner Features
1. **Dedicated Server Script (`app.py`)**: Launches a multi-threaded Flask-SocketIO server that listens on `127.0.0.1:5000` to manage incoming WebSocket connections.
2. **Standard Client Architecture**: Standard web clients connect directly via `socket.io-client` over standard WebSockets (falling back to HTTP long-polling if necessary).
3. **True Bidirectional Messaging**: Connected peers exchange messages instantly without manual page refreshes or short-polling timers.
4. **Timestamped Records**: Every message records author identity and server timestamp, formatted cleanly in 12-hour format as `[hh:mm AM/PM]`.
5. **Graceful Disconnection**: The server listens for socket disconnect events, cleans up memory, and alerts remaining room occupants with `"{Username} has left the room."` without crashing.
6. **Localhost Execution**: Simple, single-command startup locally on `http://127.0.0.1:5000`.

---

## 7. Advanced Features
1. **Bespoke Graphical User Interface**: A responsive interface featuring dual Group Rooms and Personal Chat modes, active participant counter, collapsible sidebar, avatar badges, and interactive modals.
2. **Dual Theme Engine (Dark & Light)**: Dynamic toggle between Nordic Pine (Dark) and Fresh Mint (Light) themes with instant transitions, smooth contrast, and `localStorage` persistence.
3. **1-on-1 Personal Chat**: Private direct messaging between individual users isolated from group rooms.
4. **Cryptographic Authentication**: PBKDF2-HMAC-SHA256 password hashing with 16-byte random salts via Werkzeug; rejects plain-text passwords, prevents duplicate usernames, and manages session cookies.
5. **Multi-Room Channel Isolation**: Socket.IO rooms segregate traffic so messages sent to `#General` never leak into `#Python Lounge` or private DM channels.
6. **Persistent SQLite Store**: Database schema records all messages, rooms, and users. Messages survive complete application and server restarts.
7. **Smart Tab-Focus Notifications**: Detects when the user has minimized or switched tabs using the HTML5 Page Visibility API and fires browser desktop notifications with audio chimes.
8. **Emoji Shortcode Engine**: Automatic regex translation of shortcodes (`:smile:` -> 😄, `:heart:` -> ❤️, `:fire:` -> 🔥) with an intuitive popover picker and safe fallback for unrecognized shortcodes.
9. **Security Transparency Dashboard**: In-app modal and documentation explicitly explaining data storage mechanisms and encryption boundaries.

---

## 8. Technology Stack
- **Backend**: Python 3.13
- **Web Framework**: Flask 3.1.1
- **Real-Time Engine**: Flask-SocketIO 5.6.1 (with `simple-websocket` & `threading` mode)
- **Database**: SQLite3 (relational, WAL mode, foreign keys enabled)
- **Password Security**: Werkzeug Security (`pbkdf2:sha256`)
- **Frontend Core**: Semantic HTML5, Vanilla JavaScript (ES6+), CSS3 (Flexbox & CSS Grid)
- **Fonts & Typography**: Google Fonts (*Plus Jakarta Sans*, *JetBrains Mono*)
- **Testing**: `pytest 9.1.1` automated test suite (19 test cases)

---

## 9. Project Structure

```
Python Task5 ChatApplication/
│
├── app.py                      # Application bootstrap & entry point
├── config.py                   # Configuration parameters (session secret, database URI)
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive project documentation
├── .gitignore                  # Git ignore rules
├── generate_screenshots.py     # Script to render visual UI documentation assets
│
├── database/
│   ├── __init__.py
│   ├── schema.sql              # DDL schema for SQLite (tables, indices)
│   ├── db.py                   # Parameterized SQLite query helpers & connection manager
│   └── chat.db                 # SQLite database file (created on initialization)
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py          # Blueprints for user register, login, logout, and session API
│   └── chat_routes.py          # Blueprints for chat views, room listings, and message history
│
├── sockets/
│   ├── __init__.py
│   └── events.py               # Real-time WebSocket event dispatchers & room roster
│
├── utils/
│   ├── __init__.py
│   ├── emoji.py                # Emoji shortcode dictionary and parsing regex
│   └── security.py             # Password hashing and input validation routines
│
├── static/
│   ├── css/
│   │   ├── style.css           # Custom dark-slate theme and responsive chat layout
│   │   └── auth.css            # Clean authentication card and form styling
│   └── js/
│       ├── auth.js             # Authentication form validation and tab switching
│       ├── chat_ui.js          # DOM manipulation, history rendering, and room switcher
│       ├── emoji.js            # Emoji palette and caret insertion
│       ├── notifications.js    # Focus tracking and desktop notification dispatcher
│       └── socket_client.js    # Client-side WebSocket connection and event handlers
│
├── templates/
│   ├── base.html               # Base HTML layout
│   ├── auth.html               # Combined login and registration page
│   └── chat.html               # Main real-time chat application interface
│
├── screenshots/
│   ├── Room_chat_dark_mode.png       # Group chat interface in Dark Mode
│   ├── Room_chat_light_mode.png      # Group chat interface in Light Mode
│   ├── Personal_chat_dark_mode.png   # 1-on-1 personal private chat in Dark Mode
│   ├── Personal_chat_light_mode.png  # 1-on-1 personal private chat in Light Mode
│   ├── Singup_page_dark_mode.png     # Sign In authentication in Dark Mode
│   ├── Singup_page_light_mode.png    # Sign In authentication in Light Mode
│   ├── Register_page_dark_mode.png   # User registration in Dark Mode
│   └── Register_page_light_mode.png  # User registration in Light Mode
│
└── tests/
    ├── __init__.py
    ├── test_auth.py            # Automated tests for hashing, registration, duplicate prevention
    ├── test_db.py              # Automated tests for schema and message persistence
    ├── test_sockets.py         # Automated tests for two-way messaging, room isolation, disconnect
    └── test_validation_and_security.py # Tests for XSS safety, length bounds, empty input
```

---

## 10. Database Design

The relational SQLite database schema contains three core tables with foreign key enforcement:

```sql
-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Rooms Table
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
    description TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fast lookup indices
CREATE INDEX IF NOT EXISTS idx_messages_room_created ON messages(room_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_rooms_name ON rooms(name);
```

### Relational Schema Diagram
```
users (1) ───< creates >─── (0..N) rooms
  │                                   │
 (1)                                 (1)
  │                                   │
  └───< posts >── (0..N) messages >───┘
```

---

## 11. Installation Guide

### Prerequisites
- Python 3.10 or higher (Tested on Python 3.13)
- Git (optional, for cloning)

### Clone / Navigate to Directory
```powershell
cd "c:\Users\Hp\OneDrive\Documents\OIBSIP\Python Task5 ChatApplication"
```

---

## 12. Virtual Environment Setup (Recommended)
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1
```

---

## 13. Dependency Installation
Install required packages using `requirements.txt`:
```powershell
pip install -r requirements.txt
```

Packages installed:
- `Flask==3.1.1`
- `Flask-SocketIO==5.6.1`
- `simple-websocket==1.1.0`
- `Werkzeug==3.1.3`
- `pytest==9.1.1`

---

## 14. Database Initialization
Database initialization occurs automatically upon first startup. The database schema is applied and default rooms (`General`, `Python Lounge`, `Projects`, `Random`) are seeded.

---

## 15. How to Start the Server
Run `app.py` directly:
```powershell
python app.py
```

Console output upon successful startup:
```text
============================================================
   OIBSIP TASK 5: ADVANCED REAL-TIME CHAT APPLICATION
============================================================
 [+] Server starting on: http://127.0.0.1:5000
 [+] Real-time engine:   Flask-SocketIO (threading)
 [+] Database:           SQLite (database/chat.db)
 [+] Password Security:  Werkzeug PBKDF2-HMAC-SHA256
 [!] Notice:             Messages stored in SQLite (not E2E encrypted)
============================================================
 * Running on http://127.0.0.1:5000
```

---

## 16. How to Access the Application
Open any modern web browser (Chrome, Edge, Firefox, Safari) and navigate to:
```
http://127.0.0.1:5000
```
or
```
http://localhost:5000
```

---

## 17. How to Register
1. On the authentication screen, click the **Register** tab.
2. Enter a username (3 to 25 characters, alphanumeric, underscores, or hyphens).
3. Enter a password (minimum 6 characters) and confirm it.
4. Click **Create Account**.
5. Your password is automatically salted and hashed via PBKDF2-SHA256 and stored in SQLite. You are immediately logged in and redirected to the chat room.

---

## 18. How to Login
1. Click the **Sign In** tab.
2. Enter your registered username and password.
3. Click **Sign In to Sanwad**.
4. The server verifies your password hash. Upon success, an encrypted session cookie is issued and you are redirected to `/chat`.

---

## 19. How to Use Group Chat & Personal/Private Chat
- **Switching Between Modes**: Click the **Chat Rooms** or **Personal Chat** toggle buttons at the top of the sidebar.
- **Joining an Existing Room**: In Chat Rooms mode, click any room in the sidebar (e.g. `# General`, `# Python Lounge`). The client signals the server to leave the previous channel and subscribe to the new one, loading that room's message history.
- **Creating a New Room**:
  1. Click the **`+`** button next to *CHAT ROOMS* in the sidebar.
  2. Enter a room name (e.g. `Algorithms`) and an optional description.
  3. Click **Create Room**. The room is written to SQLite and immediately becomes available to all connected participants.
- **Personal 1-on-1 Chat**: In Personal Chat mode, click on any registered user from the contact list to open an isolated private conversation.

---

## 20. How Real-Time Messaging Works
1. When a user enters text and presses **Enter** (or clicks **Send**), the client emits a `send_message` event over WebSocket.
2. The server verifies the user's session and membership in the target room.
3. Content is validated against length and blank-message rules.
4. Emoji shortcodes (e.g., `:smile:`) are converted to Unicode characters.
5. The message is inserted into the `messages` table in SQLite with an authoritative server timestamp.
6. The server broadcasts a `new_message` payload to all clients subscribed to that room's channel.
7. Clients receive the event and render the message bubble immediately without reloading the page.

---

## 21. Message History Explanation
Unlike ephemeral in-memory chat systems, Sanwad persists all messages to SQLite. When a user joins a room, the server executes:
```sql
SELECT m.id, m.content, m.created_at, u.username
FROM messages m
JOIN users u ON m.user_id = u.id
WHERE m.room_id = ?
ORDER BY m.created_at ASC, m.id ASC
LIMIT 100;
```
This guarantees:
- Messages are displayed in strictly chronological order.
- Previous messages reload when switching rooms.
- Conversation history survives server restarts.

---

## 22. Notification Behavior
- **Tab-Focus Detection**: Uses the HTML5 Page Visibility API (`document.hidden`) and window focus listeners.
- **Active Window**: When the chat tab is actively focused, incoming messages appear in the message stream with no annoying popups.
- **Background / Minimized Window**: When the tab is inactive or minimized, a native desktop notification (`#Room - Sender: Message`) appears, accompanied by a subtle audio chime.
- **Own Messages**: Desktop notifications are never triggered for the sender's own messages.
- **Permission Handling**: Handled gracefully; if permission is denied, desktop notifications are skipped while in-app badges continue to function.

---

## 23. Emoji Support
Sanwad natively supports emoji shortcodes. Users can type shortcodes directly or use the visual picker.

### Supported Common Shortcodes
- Emotions: `:smile:` (😄), `:laughing:` (😆), `:joy:` (😂), `:rofl:` (🤣), `:sunglasses:` (😎), `:thinking:` (🤔), `:cry:` (😢)
- Gestures: `:thumbsup:` (👍), `:thumbsdown:` (👎), `:clap:` (👏), `:wave:` (👋), `:pray:` (🙏), `:eyes:` (👀)
- Symbols: `:heart:` (❤️), `:fire:` (🔥), `:rocket:` (🚀), `:100:` (💯), `:check:` (✅), `:star:` (⭐), `:sparkles:` (✨)
- Unknown shortcodes (e.g., `:unknown:`) are preserved as text without crashing.

---

## 24. Security Considerations
- **SQL Injection Prevention**: 100% of database interactions utilize parameterized queries (`?`). String interpolation/concatenation is strictly forbidden.
- **Cross-Site Scripting (XSS) Prevention**: All message contents are rendered using DOM `textContent` (text nodes) rather than raw `innerHTML`. Malicious tags like `<script>` or `<img onerror=...>` are rendered as harmless text.
- **Session Identity Enforcement**: The server determines message authorship strictly from the server-side signed session cookie. Clients cannot forge the sender username in the socket payload.
- **Security Headers**: Automatic response headers including `X-Content-Type-Options: nosniff` and `X-Frame-Options: SAMEORIGIN`.

---

## 25. Password Storage Explanation
- Passwords are **never stored in plain text**.
- Passwords are encrypted using **PBKDF2-HMAC-SHA256** with a unique 16-byte random salt per user (via `werkzeug.security`).
- Even with direct access to the SQLite database file, stored password hashes cannot be reversed back to plain text.

---

## 26. Message Storage Explanation
- Chat messages are stored in plain text inside the server's local SQLite database (`database/chat.db`).
- Each record retains `room_id`, `user_id`, `content`, and `created_at`.
- System administrators or anyone with read access to the host server can inspect message contents in `chat.db`.

---

## 27. End-to-End Encryption Limitation Notice

> [!WARNING]
> ### IMPORTANT SECURITY STATEMENT
> **Sanwad is NOT end-to-end encrypted (E2EE).**
> - Messages are transmitted between the browser client and the Flask server via WebSockets.
> - The server terminates the connection, processes the content, and stores messages in plaintext within the SQLite database.
> - Transport security depends entirely on whether the application is served over HTTP or HTTPS/WSS (TLS/SSL).
> - On local development (`localhost`), traffic runs in cleartext.

---

## 28. Privacy Considerations
- User registration requires only a username and password; no email or Personally Identifiable Information (PII) is gathered.
- Disconnecting or logging out removes the active session from server memory.
- Messages posted in public rooms are visible to any authenticated user who joins that room.

---

## 29. Testing & Verification

### Automated Test Suite
Sanwad includes an automated test suite implemented with `pytest` covering all beginner and advanced requirements:

```powershell
python -m pytest -v
```

### Test Suite Results:
```text
============================= test session starts =============================
collected 19 items

tests/test_auth.py::test_password_hashing PASSED                         [  5%]
tests/test_auth.py::test_username_validation PASSED                      [ 10%]
tests/test_auth.py::test_registration_and_duplicate_rejection PASSED     [ 15%]
tests/test_auth.py::test_login_flow PASSED                               [ 21%]
tests/test_auth.py::test_unauthenticated_chat_redirect PASSED            [ 26%]
tests/test_db.py::test_default_rooms_seeded PASSED                       [ 31%]
tests/test_db.py::test_create_custom_room_and_duplicates PASSED          [ 36%]
tests/test_db.py::test_message_persistence_across_connections PASSED     [ 42%]
tests/test_db.py::test_direct_messaging_and_isolation PASSED             [ 47%]
tests/test_db.py::test_passcode_protected_rooms PASSED                   [ 52%]
tests/test_sockets.py::test_unauthenticated_socket_connection_rejected PASSED [ 57%]
tests/test_sockets.py::test_authenticated_socket_flow_and_two_way_messaging PASSED [ 63%]
tests/test_sockets.py::test_room_message_isolation PASSED                [ 68%]
tests/test_sockets.py::test_emoji_shortcodes_and_unknown_handling PASSED [ 73%]
tests/test_validation_and_security.py::test_empty_and_whitespace_message_validation PASSED [ 78%]
tests/test_validation_and_security.py::test_excessively_long_message_validation PASSED [ 84%]
tests/test_validation_and_security.py::test_room_name_validation PASSED  [ 89%]
tests/test_validation_and_security.py::test_xss_content_safety PASSED    [ 94%]
tests/test_validation_and_security.py::test_socket_send_empty_message_rejected PASSED [100%]

============================= 19 passed in 55.12s =============================
```

### Manual Verification Checklist:
- [x] **Two-Browser Multi-User Test**: Open two different browser tabs (e.g. Regular Chrome and Incognito/Edge), register Alice and Bob, join `#General`, and verify instant real-time message exchange.
- [x] **Group Rooms vs. Personal Chat**: Toggle between Chat Rooms and Personal Chat; verify 1-on-1 private messaging works exclusively between selected users.
- [x] **Dark & Light Theme Switching**: Toggle between Nordic Pine (Dark) and Fresh Mint (Light) themes; verify instant palette transitions, clean contrast, and preference persistence.
- [x] **12-Hour AM/PM Timestamps**: Verify all message bubbles and system notices format time cleanly as `[hh:mm AM/PM]`.
- [x] **Room Channel Isolation**: Switch Bob to `#Python Lounge` and verify Alice's messages in `#General` do not appear in Bob's view.
- [x] **Server Restart History Test**: Stop `app.py`, restart it, and refresh the browser; all previous messages reappear.
- [x] **Desktop Notification Test**: Switch tabs while connected as Bob; send a message from Alice; verify desktop notification pops up.
- [x] **Emoji Shortcode Test**: Send `"Hello :smile: :rocket:"` and verify it renders as `"Hello 😄 🚀"`.
- [x] **Graceful Disconnect**: Close Bob's tab; Alice receives `"[14:35] Bob has left the room."`.

---

## 30. Known Limitations
- **SQLite Concurrency**: SQLite in WAL mode performs well for hundreds of concurrent local users, but a distributed production deployment would benefit from PostgreSQL and Redis message queuing.
- **Attachment Uploads**: Currently limited to text and emojis; media file uploads (images/videos) are not implemented.
- **End-to-End Encryption**: As transparently documented, messages are stored plaintext in SQLite on the server.

---

## 31. Future Improvements
1. **File & Image Attachments** with thumbnail generation and virus scanning.
2. **Signal Protocol End-to-End Encryption (E2EE)** for client-to-client cryptographic confidentiality.
3. **Message Reactions**: Adding interactive emoji reactions to specific message IDs.
4. **Read Receipts**: Double checkmarks indicating message delivery and read status.
5. **Voice / Video Calling**: WebRTC peer-to-peer audio and video communication.

---

## License & Originality Notice
This project was independently developed for the **Oasis Infobyte (OIBSIP) Python Programming Internship Task 5**. It does not copy existing repository code or tutorials. All architecture, database schemas, styling, and event dispatchers are independently authored and tested.

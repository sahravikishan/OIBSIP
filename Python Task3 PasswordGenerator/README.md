# Advanced Random Password Generator (OIBSIP - Task 3)

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Security: Secrets Standard](https://img.shields.io/badge/Security-CSPRNG%20(secrets)-brightgreen.svg)]()
[![Internship: Oasis Infobyte](https://img.shields.io/badge/OIBSIP-Task%203-orange.svg)]()

An independently designed, cryptographically secure Desktop Password Generator built with Python and Tkinter for the **Oasis Infobyte Internship Program (OIBSIP) — Python Programming Task 3 (Advanced Version)**.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Objective](#2-objective)
3. [Beginner Features](#3-beginner-features)
4. [Advanced Features](#4-advanced-features)
5. [Technology Stack](#5-technology-stack)
6. [Why `secrets` is Used Instead of `random`](#6-why-secrets-is-used-instead-of-random)
7. [Password Generation Approach](#7-password-generation-approach)
8. [Character Type Guarantee](#8-character-type-guarantee)
9. [Password Strength Logic](#9-password-strength-logic)
10. [Ambiguous Character Exclusion](#10-ambiguous-character-exclusion)
11. [Clipboard Functionality & Fallback](#11-clipboard-functionality--fallback)
12. [Generation History Behavior & Privacy Decisions](#12-generation-history-behavior--privacy-decisions)
13. [Security Considerations](#13-security-considerations)
14. [Privacy Considerations](#14-privacy-considerations)
15. [Project Structure](#15-project-structure)
16. [Installation](#16-installation)
17. [System Requirements](#17-system-requirements)
18. [How to Run](#18-how-to-run)
19. [How to Use](#19-how-to-use)
20. [Validation Rules](#20-validation-rules)
21. [Automated and Manual Testing](#21-automated-and-manual-testing)
22. [GUI Design & Visual Layout](#22-gui-design--visual-layout)
23. [Known Limitations](#23-known-limitations)
24. [Future Improvements](#24-future-improvements)
25. [OIBSIP Evaluation Verification Matrix](#25-oibsip-evaluation-verification-matrix)

---

## 1. Project Overview

The **Advanced Random Password Generator** is a graphical desktop application engineered to generate cryptographically resilient passwords configured to user specifications. It is designed from first principles with zero external code imitation, strictly conforming to modern cryptographic standards and safe software engineering practices.

## 2. Objective

The primary objective of this project is to deliver a password generation tool that:
- Allows fine-grained user control over length, diversity, and character exclusion.
- Eliminates predictable patterns using hardware-backed cryptographic randomness.
- Guarantees complete representation of all user-selected character categories.
- Evaluates and displays visual password strength metrics based on information entropy and character variety.
- Automatically and safely handles clipboard transfers.
- Preserves session generation history exclusively in volatile RAM.

---

## 3. Beginner Features

All fundamental internship specifications are implemented:
- **Length Specification**: Configurable password length with strict validation (minimum length of 8).
- **Character Diversity Selection**: Checkboxes for Uppercase, Lowercase, Digits, and Symbols.
- **Strict Diversity Enforcement**: Enforces selection of at least 2 character types; rejects invalid requests.
- **Criterion Adherence**: Generated passwords match selected criteria without unrequested character types.
- **Input Validation**: Gracefully handles non-numeric or invalid inputs with clear UI dialogs.
- **Continuous Generation**: Users can repeatedly generate passwords without application restarts.

---

## 4. Advanced Features

Every advanced internship specification is implemented:
- **Tkinter GUI**: Modern slate-themed user interface with clean component grouping.
- **Dual Length Control**: Synchronized Tkinter Slider and Spinbox with live value indicator.
- **CSPRNG Generation**: 100% powered by Python's `secrets` module.
- **Guaranteed Character Types**: At least one character from every active set is guaranteed before pool sampling.
- **Cryptographic Fisher-Yates Shuffle**: Positions are shuffled with `secrets.randbelow` to eliminate positional predictability.
- **Ambiguous Character Filtering**: Optional exclusion of visually confusing glyphs (`0`, `O`, `o`, `1`, `l`, `I`, `|`).
- **Dynamic Strength Indicator**: Live multi-color progress bar with level classification (Weak, Medium, Strong) and Shannon entropy bit calculations.
- **Clipboard Integration**: Instant automatic clipboard copy upon generation, plus manual copy buttons.
- **In-Memory Session History**: FIFO sliding window of the last 5 generated passwords during the session.
- **Anti-Shoulder Surfing Masking**: Mask/Unmask toggle for historical passwords.
- **One-Click History Copy & Clear**: Easily copy individual past passwords or purge history on demand.

---

## 5. Technology Stack

- **Python 3.8+**: Core programming language.
- **`secrets` (Standard Library)**: Cryptographically secure pseudo-random number generator (CSPRNG) utilizing OS entropy sources (`CryptGenRandom` on Windows, `/dev/urandom` / `getrandom()` on Linux/macOS).
- **`string` (Standard Library)**: Standardized ASCII character set definitions.
- **`tkinter` & `ttk` (Standard Library)**: Cross-platform GUI framework.
- **`collections.deque` (Standard Library)**: Fixed-size bounded queue (`maxlen=5`) for session-only history.
- **`pyperclip` (External)**: Cross-platform clipboard read/write library with automatic fallback to native Tkinter clipboard routines.
- **`unittest` (Standard Library)**: Comprehensive automated test suite.

---

## 6. Why `secrets` is Used Instead of `random`

Python's built-in `random` module uses the **Mersenne Twister (MT19937)** algorithm.
- **The Problem with `random`**: The Mersenne Twister is a deterministic PRNG designed for modeling, scientific simulations, and games. It is **not** cryptographically secure. By observing just 624 consecutive 32-bit outputs of `random`, an adversary can reconstruct the internal state matrix and accurately predict every past and future generated password.
- **The Solution with `secrets`**: The `secrets` module (introduced in Python 3.6, [PEP 506](https://peps.python.org/pep-0506/)) accesses the operating system's kernel-level entropy pools. It is safe against state reconstruction and cryptanalysis attacks, making it the required standard for passwords, encryption keys, and security tokens.

> [!IMPORTANT]
> The `random` module (`random.choice`, `random.randint`, `random.shuffle`) is **strictly forbidden and not used anywhere** in this application.

---

## 7. Password Generation Approach

1. **Parameter Validation**: Validate length ($8 \le L \le 128$) and ensure $\ge 2$ character categories are selected.
2. **Pool Construction & Ambiguous Filtering**: Assemble active pools (Uppercase, Lowercase, Digits, Symbols). If ambiguous character filtering is enabled, visually confusing characters are stripped from active pools while verifying that no pool is left empty.
3. **Guaranteed Type Seeding**: Exactly one character is selected from each active pool using `secrets.choice(pool)`.
4. **Remaining Position Sampling**: The remaining $L - K$ slots (where $K$ is the number of active pools) are filled by selecting characters from the combined union of all active pools using `secrets.choice(combined_pool)`.
5. **Cryptographic Fisher-Yates Permutation**: The assembled list of characters is shuffled using a secure Fisher-Yates shuffle driven by `secrets.randbelow(i + 1)`.

```
Selected Pools: [Uppercase, Lowercase, Digits, Symbols]
Step 1 (Guaranteed Seed): ['K', 'm', '7', '$']
Step 2 (Fill to Length 16): ['K', 'm', '7', '$', 'p', '9', 'X', '!', 'a', '2', 'R', '#', 'q', '8', 'L', '^']
Step 3 (CSPRNG Fisher-Yates): ['9', 'X', 'm', '$', '2', 'K', '!', 'p', '8', 'R', '#', '7', 'a', 'q', 'L', '^']
```

---

## 8. Character Type Guarantee

Standard naive generators select all characters randomly from a single combined pool. While the probability of missing an entire category decreases as length increases, short passwords generated this way frequently fail to contain all selected types.

This application **explicitly guarantees** representation:
- If 4 types are selected, the initial 4 slots are reserved and filled with one character from each selected category.
- The remaining slots are sampled from the composite pool.
- The entire array is then uniformly shuffled with the CSPRNG Fisher-Yates algorithm, ensuring that guaranteed characters are distributed randomly across the password rather than appearing in predictable positions.

---

## 9. Password Strength Logic

Password strength is calculated using a multi-factor scoring model that balances **length**, **character diversity**, and **Shannon pool entropy**:

### Scoring Breakdown (0 to 100 Points):
1. **Length Factor (Up to 50 pts)**:
   - $L < 8$: $L \times 3.5$ (heavily penalized)
   - $8 \le L \le 12$: $28 + (L - 8) \times 4$
   - $13 \le L \le 16$: $44 + (L - 12) \times 1.25$
   - $L > 16$: 50 points
2. **Character Diversity (Up to 40 pts)**:
   - Lowercase present: +8 pts
   - Uppercase present: +10 pts
   - Digits present: +10 pts
   - Symbols present: +12 pts
3. **Diversity Bonus / Single-Type Penalties (Up to 10 pts)**:
   - 4 types present: +10 pts bonus
   - 3 types present: +5 pts bonus
   - Only 1 type present: -20 pts penalty
4. **Estimated Information Entropy**:
   $$\text{Entropy (bits)} = L \times \log_2(N)$$
   Where $N$ is the effective character pool size.

### Classification Thresholds:
| Score Range | Level | UI Color | Approximate Entropy |
| :--- | :--- | :--- | :--- |
| **0 – 49** | **Weak** | Red (`#ef4444`) | $< 45\text{ bits}$ |
| **50 – 74** | **Medium** | Amber (`#f59e0b`) | $45 - 65\text{ bits}$ |
| **75 – 100** | **Strong** | Emerald Green (`#10b981`) | $> 65\text{ bits}$ |

---

## 10. Ambiguous Character Exclusion

When the user checks **"Exclude ambiguous characters"**, the following glyphs are filtered out from all pools:
- `0` (Digit zero), `O` (Uppercase O), `o` (Lowercase o)
- `1` (Digit one), `l` (Lowercase L), `I` (Uppercase i), `|` (Pipe)
- `` ` `` (Backtick), `'` (Single quote), `"` (Double quote)

This prevents transcription errors when passwords must be entered manually on mobile devices or displayed in fonts where glyphs look identical.

---

## 11. Clipboard Functionality & Fallback

- **Automatic Copy**: Upon clicking **Generate Password**, the newly created password is automatically copied to the system clipboard.
- **Manual Copy**: A dedicated **"Copy"** button allows re-copying at any time.
- **Two-Tier Architecture**:
  1. Primary: Uses `pyperclip.copy(password)` for cross-platform integration.
  2. Fallback: If `pyperclip` is missing or encounters an OS clipboard access lock, the application falls back seamlessly to Tkinter's native `clipboard_clear()` and `clipboard_append()`.
- **User Feedback**: The application displays instant visual feedback ("✓ Generated and copied to clipboard!").

---

## 12. Generation History Behavior & Privacy Decisions

### In-Memory Storage Only (RAM)
- Recent passwords are held in an in-memory `collections.deque(maxlen=5)` object.
- **Never written to disk**: No SQLite database, JSON, CSV, text log, or cache file is ever created.
- **Session Lifespan**: Once the window or process terminates, the memory is completely deallocated by the Python garbage collector and operating system.

### Shoulder-Surfing Protection
- By default, recent passwords in the history pane are displayed masked with bullets (`••••••••••••`).
- An **"👁 Unmask" / "🔒 Mask"** toggle lets the user inspect the passwords if needed.
- Each historical entry includes an individual **"Copy"** button to copy that specific past password.
- A **"Clear History"** button allows immediate in-memory purging.

---

## 13. Security Considerations

- **No Passwords Written to Logs or Terminal**: The application avoids printing generated passwords to stdout or stderr.
- **No Hardcoded Credentials or Seeds**: Randomness originates strictly from OS entropy.
- **Zero Use of `random`**: Verified through automated inspection tests.
- **Bounds Checking**: Prevents denial-of-service via huge length requests (max 128).

---

## 14. Privacy Considerations

- **Clipboard Persistence Notice**: Clipboard contents are managed by the host operating system. Depending on your OS and third-party clipboard managers (e.g., Windows Clipboard History `Win + V`), copied passwords may remain stored in clipboard memory until cleared.
- **No Telemetry**: The application makes zero network requests.

---

## 15. Project Structure

```
Python Task3 PasswordGenerator/
│
├── src/
│   ├── __init__.py               # Package marker
│   ├── main.py                   # Application launch script
│   ├── gui.py                    # Tkinter GUI, styles, clipboard, history
│   ├── password_generator.py     # Secure generation, CSPRNG shuffle, guarantees
│   └── strength.py               # Scoring logic, entropy, levels, feedback
│
├── tests/
│   ├── __init__.py               # Test suite marker
│   ├── test_generator.py         # 100-sample guarantee tests, validation, security
│   ├── test_strength.py          # Weak/Med/Strong checks, entropy calculation
│   └── test_gui.py               # Headless GUI interaction & history limit tests
│
├── requirements.txt              # Project dependencies (pyperclip)
└── README.md                     # Complete project documentation
```

---

## 16. Installation

1. **Clone or Download the Repository**:
   ```bash
   cd "Python Task3 PasswordGenerator"
   ```

2. **(Optional) Create a Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 17. System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Version 3.8 or higher.
- **Tkinter**: Included with standard Python Windows/macOS installers. On Debian/Ubuntu Linux: `sudo apt-get install python3-tk`.

---

## 18. How to Run

Launch the application directly:

```bash
python src/main.py
```

---

## 19. How to Use

1. **Adjust Length**: Drag the slider or use the spinbox to choose a password length ($8 - 64$ via slider, up to $128$ via spinbox).
2. **Select Character Types**: Check the desired boxes (minimum 2).
3. **Exclude Ambiguous (Optional)**: Check to remove look-alike characters like `0` and `O`.
4. **Generate**: Click **"⚡ GENERATE PASSWORD"**.
   - The password is displayed in the monospace box.
   - It is automatically copied to your clipboard.
   - The strength bar and entropy meter update immediately.
5. **View History**: Look at the "Session History" card. Click **"Copy"** next to any previous password to retrieve it, or click **"👁 Unmask"** to reveal them.
6. **Reset / Clear**:
   - Click **"↺ Reset Defaults"** to restore standard options.
   - Click **"Clear History"** to wipe session memory.
   - Click **"Exit"** to close the application.

---

## 20. Validation Rules

| Rule | Requirement | Error Feedback |
| :--- | :--- | :--- |
| **Minimum Length** | Must be $\ge 8$ | Warning dialog: *"Password length must be at least 8 characters."* |
| **Maximum Length** | Must be $\le 128$ | Warning dialog: *"Password length cannot exceed 128 characters."* |
| **Numeric Length** | Integer only | Error dialog: *"Password length must be a valid integer."* |
| **Character Types** | At least 2 active categories | Warning dialog: *"Please select at least 2 character types."* |
| **Ambiguous Filtering**| Active pool must retain characters | Warning dialog: *"Character set became empty after ambiguous exclusion."* |

---

## 21. Automated and Manual Testing

### Automated Test Suite
Run the full automated test suite containing 23 test cases:

```bash
python -m unittest discover tests
```

#### Test Coverage:
- `test_generator.py`:
  - Enforces minimum length of 8 and maximum of 128.
  - Rejects non-integer lengths.
  - Rejects 0 or 1 character types.
  - Generates 100 consecutive passwords to verify 100% guaranteed inclusion of all selected types.
  - Verifies zero occurrence of ambiguous characters when enabled.
  - Audits module source code to ensure `random` is never imported.
- `test_strength.py`:
  - Validates Weak, Medium, and Strong classifications.
  - Validates monotonicity of entropy calculations.
- `test_gui.py`:
  - Verifies default UI state.
  - Validates password generation updates current password and session history.
  - Verifies sliding window FIFO keeps strictly the last 5 items.
  - Tests history mask toggling and reset defaults.

### Manual Test Checklist
- [x] Application launches without command-line flags.
- [x] Length slider dynamically updates the number display.
- [x] Typing into the spinbox updates the slider position.
- [x] Unchecking 3 checkboxes and clicking Generate shows clear validation warning.
- [x] Generated password pastes into other applications automatically.
- [x] Generating 6 passwords pushes the first password out of the history panel.
- [x] Closing the app and inspecting the directory shows 0 password log files.

---

## 22. GUI Design & Visual Layout

The graphical interface is built with a clean, responsive two-column layout supporting both **Golden Light Theme** (default) and **Obsidian Gold Dark Theme** with an instant 1-click theme switcher:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   Random Password Generator        [ 🌙 Dark Theme ] / [☀️ Light] │
│                  Cryptographically secure via Python secrets                     │
├────────────────────────────────────────┬─────────────────────────────────────────┤
│ PASSWORD CONFIGURATION                 │ GENERATED PASSWORD                      │
│                                        │                                         │
│ Password Length:                [ 16 ] │ ┌─────────────────────────────┐ ┌─────┐ │
│ ────●─────────────────────────── [ 16 ] │ │ K9#mQ2!vL7$zW1*x            │ │Copy │ │
│                                        │ └─────────────────────────────┘ └─────┘ │
│ Character Types                        │                                         │
│ (minimum 2 required)                   │ Strength: Strong     ~95.2 bits entropy │
│ ☑ Uppercase (A-Z)   ☑ Lowercase (a-z)  │ [█████████████████████████████████████] │
│ ☑ Numbers (0-9)     ☑ Symbols (!@#$%)  │ ✓ Generated and copied to clipboard!    │
│                                        │                                         │
│ ☑ Exclude ambiguous characters         │ Session History (Last 5 - RAM) [👁Unmask]│
│                                        │ 1. ••••••••••••••••              [Copy] │
│                                        │ 2. ••••••••••••••••              [Copy] │
│      [ ⚡ GENERATE PASSWORD ]          │ 3. ••••••••••••••••              [Copy] │
├────────────────────────────────────────┴─────────────────────────────────────────┤
│ [↺ Reset Defaults]    [Clear History]                                   [Exit]   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

- **Golden Light Theme (Default)**: Soft warm ivory background (`#f8f6f0`), crisp white cards (`#ffffff`), warm champagne inputs (`#fdf8ee`), deep golden-amber buttons (`#d97706`), and dark stone-charcoal typography (`#1c1917`) with rich amber monospace text (`#92400e`).
- **Obsidian Gold Dark Theme**: Deep obsidian background (`#12100b`), dark bronze cards (`#1c1810`), radiant pure gold accents (`#f59e0b`), and warm golden-cream text (`#fef9c3`).
- **1-Click Switcher**: Located in the upper right corner of the header, allowing instantaneous live repainting without restarting the application.

---

## 23. Known Limitations

1. **OS Clipboard History**: On Windows 10/11 with Clipboard History enabled (`Win + V`), copied passwords are saved in the operating system's clipboard stack until cleared by the user.
2. **Headless Execution**: Requires an active desktop graphical environment or virtual framebuffer (`Xvfb`) to launch the GUI.

---

## 24. Future Improvements

- Option to configure custom symbol sets.
- Built-in automatic clipboard clearing timer (e.g., auto-purge clipboard after 30 seconds).
- Optional Diceware / passphrase generator mode using secure wordlists.
- Export encrypted password backup file using user-provided master password.

---

## 25. OIBSIP Evaluation Verification Matrix

| Requirement | Implementation Status | Evidence / Location |
| :--- | :---: | :--- |
| **Password Length Control** | Completed | `src/gui.py` (Slider & Spinbox), `src/password_generator.py` |
| **Minimum 8 Characters** | Completed | `MIN_PASSWORD_LENGTH = 8` in `src/password_generator.py` |
| **Character Type Selection** | Completed | 4 Checkbuttons in `src/gui.py`, `PasswordCriteria` |
| **At Least 2 Types Required** | Completed | `validate_criteria()` in `src/password_generator.py` |
| **Guaranteed Inclusion** | Completed | Seed loop in `src/password_generator.py` (tested in 100 iterations) |
| **Cryptographic Randomness** | Completed | `secrets.choice` & `secrets.randbelow` |
| **No `random` Module Used** | Completed | Verified in `tests/test_generator.py` (`test_no_random_module_used`) |
| **Ambiguous Character Filter** | Completed | `AMBIGUOUS_CHARS` set exclusion in `src/password_generator.py` |
| **Password Strength Indicator** | Completed | `src/strength.py` (Weak, Medium, Strong + Entropy bits) |
| **Copy to Clipboard** | Completed | `pyperclip` + Tkinter fallback in `src/gui.py` |
| **Automatic Clipboard Copy** | Completed | Triggered on generate in `generate_password_action()` |
| **Session-Only History** | Completed | `collections.deque(maxlen=5)` in RAM only |
| **No File Persistence** | Completed | Zero files created, no disk writes for passwords |
| **Input Validation & Error Dialogs** | Completed | Handled cleanly via Tkinter `messagebox` |
| **Continuous Generation** | Completed | Re-usable Generate button without restart |
| **Clean Architecture** | Completed | Modularized into `main.py`, `gui.py`, `password_generator.py`, `strength.py` |

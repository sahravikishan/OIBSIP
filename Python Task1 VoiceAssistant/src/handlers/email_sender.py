"""
Email sender handler — interactive voice-driven email sending via SMTP.

Credentials are loaded from environment variables (never hard-coded).
"""

import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.utils.config import validate_email_config


def _is_valid_email(address: str) -> bool:
    """Basic email format validation using regex."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, address))


def handle_email(
    recipient: str,
    subject: str,
    body: str,
) -> str:
    """
    Send an email using SMTP with TLS.

    All credentials come from environment variables via config module.

    Args:
        recipient: The email address to send to.
        subject: Email subject line.
        body: Email body text.

    Returns:
        A spoken response confirming success or describing the error.
    """
    # Validate email configuration
    email_cfg = validate_email_config()

    if not email_cfg["configured"]:
        return (
            "Email is not configured. Please set EMAIL_ADDRESS and "
            "EMAIL_PASSWORD in your environment variables. "
            "See the .env.example file for details."
        )

    # Validate recipient
    if not recipient or not _is_valid_email(recipient):
        return (
            f"The recipient address '{recipient}' does not look valid. "
            "Please provide a proper email address."
        )

    # Build the email message
    message = MIMEMultipart()
    message["From"] = email_cfg["address"]
    message["To"] = recipient
    message["Subject"] = subject or "(No Subject)"
    message.attach(MIMEText(body or "(Empty message)", "plain"))

    # Attempt to send
    try:
        with smtplib.SMTP(email_cfg["server"], email_cfg["port"], timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_cfg["address"], email_cfg["password"])
            server.send_message(message)
        return f"Email sent successfully to {recipient}."

    except smtplib.SMTPAuthenticationError:
        return (
            "Email authentication failed. Please check your EMAIL_ADDRESS "
            "and EMAIL_PASSWORD. If using Gmail, you may need an App Password."
        )
    except smtplib.SMTPRecipientsRefused:
        return f"The recipient address {recipient} was rejected by the mail server."
    except smtplib.SMTPException as exc:
        return f"An email error occurred: {exc}"
    except ConnectionError:
        return "Could not connect to the email server. Please check your internet connection."
    except TimeoutError:
        return "Connection to the email server timed out. Please try again later."


def collect_email_details_flow(listen_fn, speak_fn) -> str:
    """
    Interactive voice-driven flow to collect email details and send.

    This function guides the user through providing:
    1. Recipient address
    2. Subject line
    3. Message body

    Args:
        listen_fn: A callable that captures voice input and returns text (or None).
        speak_fn: A callable that speaks text aloud.

    Returns:
        Final result message (already spoken inside this function).
    """
    # Step 1: Get recipient
    speak_fn("Who would you like to send the email to? Please say the email address.")
    recipient_raw = listen_fn(timeout=8, phrase_time_limit=15)
    if not recipient_raw:
        speak_fn("I didn't catch the email address. Cancelling email.")
        return "Email cancelled — no recipient provided."

    # Normalise spoken email (e.g., "john at gmail dot com" → "john@gmail.com")
    recipient = _normalise_spoken_email(recipient_raw)
    speak_fn(f"Got it. Sending to {recipient}.")

    # Step 2: Get subject
    speak_fn("What should the subject be?")
    subject = listen_fn(timeout=8, phrase_time_limit=15)
    if not subject:
        subject = "(No Subject)"
        speak_fn("No subject heard. I'll leave it blank.")
    else:
        speak_fn(f"Subject: {subject}.")

    # Step 3: Get body
    speak_fn("What is the message?")
    body = listen_fn(timeout=8, phrase_time_limit=20)
    if not body:
        body = "(Empty message)"
        speak_fn("No message heard. Sending with an empty body.")
    else:
        speak_fn(f"Message: {body}.")

    # Confirm and send
    speak_fn("Sending your email now.")
    result = handle_email(recipient, subject, body)
    speak_fn(result)
    return result


def _normalise_spoken_email(spoken: str) -> str:
    """
    Convert a spoken email address into a proper format.
    E.g., "john at gmail dot com" → "john@gmail.com"
    """
    normalised = spoken.lower().strip()
    normalised = normalised.replace(" at ", "@")
    normalised = normalised.replace(" dot ", ".")
    # Remove remaining spaces (people sometimes spell parts)
    normalised = normalised.replace(" ", "")
    return normalised

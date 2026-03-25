"""
One-time script: generates a Telethon StringSession string.

Run this ONCE on your local machine:
    cd telegram_trading
    python generate_session_string.py

It will prompt for your phone number + the Telegram OTP code,
then print a long session string.

Copy that string and set it as TELEGRAM_SESSION_STRING in Render's
Environment Variables. You never need to run this again unless you
revoke the session or change accounts.
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# ── Edit these if you are not using the .env values ──────────────────────────
API_ID   = 31821869
API_HASH = "fc4068a4dced2951486b9ecc9d4fc6b7"
# ─────────────────────────────────────────────────────────────────────────────


async def main():
    print("\nGenerating Telegram StringSession...\n")
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session_string = client.session.save()

    print("\n" + "=" * 70)
    print("YOUR SESSION STRING (copy everything between the lines):\n")
    print(session_string)
    print("\n" + "=" * 70)
    print("\nPaste this into Render -> Environment Variables as:")
    print("    TELEGRAM_SESSION_STRING = <the string above>\n")


if __name__ == "__main__":
    asyncio.run(main())

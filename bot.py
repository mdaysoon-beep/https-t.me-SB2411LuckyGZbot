"""
SB2411LuckyGZbot — Telegram Bot
Sends daily productivity and focus tips on request or subscription.

Run locally:
    export BOT_TOKEN="your-token-from-botfather"
    python bot.py

Deployed on Railway, BOT_TOKEN is read from an environment variable you set
in the Railway dashboard (Variables tab) — never hard-code it in this file.
"""

import json
import logging
import os
import random
from datetime import time as dtime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SUBSCRIBERS_FILE = "subscribers.json"

# ---------------------------------------------------------------------------
# CONTENT LIBRARY — add new entries any time, no other code needs to change
# ---------------------------------------------------------------------------

TIPS = [
    {
        "title": "🧱 Start With the Smallest Version",
        "body": (
            "When a task feels overwhelming, shrink it until it feels almost too easy "
            "to skip.\n\n"
            "'Write one sentence' is easier to start than 'write the report' — and "
            "starting is usually the hardest part."
        ),
    },
    {
        "title": "🚪 Design Your Environment, Not Just Your Willpower",
        "body": (
            "Willpower runs out. Environment doesn't.\n\n"
            "Put the things you want to do more of within easy reach, and the things "
            "you want to do less of a few steps further away."
        ),
    },
    {
        "title": "⏳ Time-Block Instead of List-Make",
        "body": (
            "A to-do list tells you what to do. A calendar tells you when.\n\n"
            "Assigning a specific time slot to a task makes it far more likely to "
            "actually happen than just writing it down."
        ),
    },
    {
        "title": "🔕 Protect Deep Work With Real Boundaries",
        "body": (
            "Notifications don't just interrupt — they take minutes to recover from "
            "afterward.\n\n"
            "Turning off notifications during focus blocks protects more time than "
            "the interruption itself takes."
        ),
    },
    {
        "title": "🎯 One Priority, Not Five",
        "body": (
            "A day with five 'top priorities' has no real priority at all.\n\n"
            "Pick the single task that would make the day a win if nothing else got "
            "done, and do that one first."
        ),
    },
    {
        "title": "🧠 Close Open Loops Before They Cost You Focus",
        "body": (
            "An unfinished task sitting in the back of your mind quietly drains "
            "attention, even when you're not actively thinking about it.\n\n"
            "Writing it down — even just the next physical step — frees up that "
            "mental space."
        ),
    },
    {
        "title": "🪫 Rest Is Part of the System, Not a Break From It",
        "body": (
            "Pushing through fatigue usually produces lower-quality work slower, not "
            "faster.\n\n"
            "Built-in recovery time isn't lost productivity — it's what makes the "
            "next focused block possible."
        ),
    },
    {
        "title": "📏 Measure Progress, Not Just Activity",
        "body": (
            "Being busy and being productive aren't the same thing.\n\n"
            "At the end of the day, ask what actually moved forward — not just what "
            "filled the hours."
        ),
    },
]

WELCOME_MESSAGE = (
    "👋 Welcome!\n\n"
    "This bot sends you short, practical tips on focus, productivity, and "
    "getting things done.\n\n"
    "Commands:\n"
    "/tip — get a random tip\n"
    "/subscribe — get a daily tip automatically\n"
    "/unsubscribe — stop daily tips\n"
    "/help — show this message again"
)

# ---------------------------------------------------------------------------
# SUBSCRIBER STORAGE
# ---------------------------------------------------------------------------


def load_subscribers() -> set:
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_subscribers(subscribers: set) -> None:
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(list(subscribers), f)


subscribers = load_subscribers()

# ---------------------------------------------------------------------------
# COMMAND HANDLERS
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME_MESSAGE)


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pick = random.choice(TIPS)
    text = f"{pick['title']}\n\n{pick['body']}"
    await update.message.reply_text(text)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in subscribers:
        await update.message.reply_text("You're already subscribed to daily tips.")
        return
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text(
        "✅ Subscribed! You'll get one tip a day. Use /unsubscribe to stop anytime."
    )


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in subscribers:
        await update.message.reply_text("You're not currently subscribed.")
        return
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text("You've been unsubscribed from daily tips.")


async def send_daily_tip(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs once a day, sends one random tip to every subscriber."""
    if not subscribers:
        return
    pick = random.choice(TIPS)
    text = f"{pick['title']}\n\n{pick['body']}"
    for chat_id in list(subscribers):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as exc:
            logger.warning("Failed to send to %s: %s", chat_id, exc)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------


def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. "
            "Set it locally with `export BOT_TOKEN=...` or in Railway's Variables tab."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tip", tip))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Daily tip at 09:00 UTC — adjust the hour to suit your audience's timezone.
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_tip, time=dtime(hour=9, minute=0))

    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

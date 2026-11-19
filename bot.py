import json
import logging
import os
import random
import subprocess
import sys
import time
from pathlib import Path

# Ensure python-telegram-bot is installed at runtime
try:
    import telegram  # noqa: F401
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot==20.7"])

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")

# Follow-up timing configuration (in seconds)
# 1800 seconds = 30 minutes (you can change to 600 for 10 mins or 3600 for 1 hour)
FOLLOWUP_DELAY_SECONDS = 1800
CHECK_INTERVAL_SECONDS = 60
MAX_FOLLOWUPS_PER_ISSUE = 2

DATA_FILE = Path("followups.json")


def load_followups() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Failed to load followups.json: {e}")
        return {}


def save_followups(data: dict) -> None:
    try:
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Failed to save followups.json: {e}")


def _pick(options: list[str]) -> str:
    return random.choice(options)


def is_resolved_reply(lower: str) -> bool:
    resolved_words = [
        "সমাধান হয়েছে", "ঠিক হয়ে গেছে", "কাজ করছে", "হয়ে গেছে",
        "solved", "fixed", "done", "thik hoye geche", "kaj korche", "solve hoye geche"
    ]
    return any(w in lower for w in resolved_words)


def is_still_problem_reply(lower: str) -> bool:
    unresolved_words = [
        "হয়নি", "হচ্ছে না", "আটকে আছে", "একই সমস্যা", "কাজ করছে না",
        "not solved", "still", "hoyni", "hocche na", "kaj korche na", "problem"
    ]
    return any(w in lower for w in unresolved_words)


def build_daily_help_reply(raw_text: str, active_issue: dict | None) -> tuple[str, bool]:
    """
    Returns (reply_text, should_track_as_new_issue).
    should_track_as_new_issue=True means bot should follow up later on this issue.
    """
    text = raw_text.strip()
    lower = text.lower()

    # If user is replying to an active follow-up
    if active_issue and active_issue.get("awaiting_status"):
        issue_summary = active_issue.get("summary", "ওই বিষয়টা")

        if is_resolved_reply(lower):
            return (
                f"দারুণ! শুনে ভালো লাগলো যে '{issue_summary}' নিয়ে তোমার কাজটা মিটে গেছে। "
                "দৈনন্দিন জীবনে আর কোনো সাহায্য লাগলে নির্দ্বিধায় বলো।",
                False,
            )

        if is_still_problem_reply(lower):
            return (
                f"বুঝলাম, '{issue_summary}' নিয়ে এখনো ঝামেলা হচ্ছে। "
                "একটু ভেঙে বলো তো ঠিক কোন জায়গায় আটকাচ্ছো—তাহলে আরেকটু সহজ উপায় দেখছি।",
                True,
            )

    # 1. Greetings / casual opening
    greetings = [
        "হ্যালো", "হাই", "hello", "hi", "hey", "সালাম",
        "আসসালামু", "assalamu", "কেমন আছো", "কেমন আছেন",
        "kemon acho", "kemon achen", "ki khobor", "কি খবর"
    ]
    if any(w in lower for w in greetings) and len(lower) <= 35:
        return (
            _pick([
                "জি বলছি আমি! ভালো আছি, তুমি কেমন আছো? আজকের দিনে কোনো কাজ বা সমস্যা নিয়ে হেল্প লাগলে বলো।",
                "হ্যাঁ ভাই, বলো! কী নিয়ে সাহায্য লাগবে বা কোন বিষয়টা নিয়ে কথা বলতে চাচ্ছো?",
                "আরে বলো! আমি আছি তো—দৈনন্দিন কোনো সমস্যা বা প্রশ্ন থাকলে খুলে বলো।"
            ]),
            False,
        )

    # 2. Identity / creator logic (only when asked directly)
    identity_triggers = [
        "ovi", "অভি", "কে বানিয়েছে", "কে তৈরি", "তোর মালিক", "তোমার মালিক",
        "কার বট", "কে তুই", "তুমি কে", "tumi ke", "tui ke", "পরিচয়", "admin", "অ্যাডমিন"
    ]
    if any(w in lower for w in identity_triggers):
        return (
            _pick([
                "আমি অভির বানানো হেল্পিং বট—মানুষের দৈনন্দিন ছোটখাটো সমস্যা ও প্রশ্নে সহজ বাংলায় পাশে থাকার জন্য বানানো হয়েছে। বলো, তোমার কী হেল্প লাগবে?",
                "এটা অভির বট। মূলত সবার যেন সাধারণ সমস্যায় একটা সহজ সমাধান বা দিকনির্দেশনা পাওয়া যায়, সেভাবেই সাজানো। তুমি কী জানতে চাচ্ছো?"
            ]),
            False,
        )

    # 3. Capabilities / help overview
    capability_triggers = [
        "কি কি করতে পারো", "কী কী করতে পারো", "ki ki korte paro",
        "কি পারো", "ki paro", "কাজ কি", "কিভাবে সাহায্য", "হেল্প", "help"
    ]
    if any(w in lower for w in capability_triggers):
        return (
            "আমি দৈনন্দিন জীবনের নানা সাধারণ বিষয়ে তোমাকে হেল্প করতে পারি:\n"
            "• নেটওয়ার্ক, ইন্টারনেট বা ফোন স্লো/গরম হওয়ার প্রাথমিক সমাধান\n"
            "• অ্যাকাউন্ট লগইন, সেফটি বা অনলাইন সতর্কতার সহজ টিপস\n"
            "• কাজের রুটিন বা কোনো কাজ গুছিয়ে শুরু করার পরামর্শ\n"
            "• যেকোনো সমস্যা বললে কিছুক্ষণ পর নিজে থেকেই খোঁজ নেওয়া যে ঠিক হয়েছে কি না\n\n"
            "এখন তোমার কোন বিষয়টা নিয়ে হেল্প লাগবে?"
        ), False

    # 4. Network / internet / device lag
    net_device_triggers = [
        "নেট", "net", "ইন্টারনেট", "internet", "ওয়াইফাই", "wifi", "wi-fi",
        "স্লো", "slow", "ল্যাগ", "lag", "পিং", "ping", "ফোন", "phone", "গরম", "hang", "হ্যাং"
    ]
    if any(w in lower for w in net_device_triggers):
        reply = _pick([
            (
                "নেট বা ডিভাইস নিয়ে ঝামেলা হলে শুরুতে এই সহজ ধাপগুলো দেখে নাও:\n"
                "• ব্যাকগ্রাউন্ডে ভারী অ্যাপ বা ডাউনলোড চলছে কি না চেক করো।\n"
                "• নেটওয়ার্ক স্লো হলে একবার এয়ারপ্লেন মোড অন-অফ বা রাউটার/ডেটা রিসেট করে দেখো।\n"
                "• ফোন স্লো বা গরম হলে অপ্রয়োজনীয় ট্যাব/অ্যাপ বন্ধ করে একটু রেস্ট দাও।"
            ),
            (
                "মাঝেমধ্যে নেট বা ফোন হঠাৎ স্লো হয়ে গেলে বিরক্তি লাগে। আগে এগুলো ট্রাই করে দেখো:\n"
                "• কানেকশন দুর্বল মনে হলে কিছুক্ষণ পর আবার চেষ্টা করো।\n"
                "• স্টোরেজ একদম ভরে গেলে বা অনেক অ্যাপ একসাথে চললে ফোন ল্যাগ করে—একটু জায়গা খালি রাখো।"
            )
        ])
        return reply, True

    # 5. Account / login / online safety
    account_triggers = [
        "লগইন", "login", "অ্যাকাউন্ট", "account", "আইডি", "id",
        "পাসওয়ার্ড", "password", "ওটিপি", "otp", "স্ক্যাম", "scam", "সেফ", "safe"
    ]
    if any(w in lower for w in account_triggers):
        reply = _pick([
            (
                "অ্যাকাউন্ট বা অনলাইন সেফটি নিয়ে কয়েকটা জরুরি কথা:\n"
                "• আগে দেখো যে অ্যাকাউন্টে ঢুকতে চাচ্ছো, সেটার মূল তথ্য বা লগইন ঠিক আছে কি না।\n"
                "• পাসওয়ার্ড, OTP বা কোনো গোপন তথ্য কখনো কারও সাথে শেয়ার করবে না।\n"
                "• অপরিচিত লিংক বা সন্দেহজনক অফার এড়িয়ে চললেই বড় ঝুঁকি থেকে বাঁচা যায়।"
            ),
            (
                "লগইন বা অ্যাকাউন্টের বিষয়ে ধাপে ধাপে এগোলে ভুল কম হয়:\n"
                "• সঠিক ইমেইল/নম্বর ও মাধ্যম ব্যবহার করছো কি না যাচাই করো।\n"
                "• বারবার চেষ্টা করলে সাময়িক ব্লক বা লিমিট পড়তে পারে, তাই একটু সময় নিয়ে ট্রাই করো।"
            )
        ])
        return reply, True

    # 6. Routine / productivity / planning
    routine_triggers = [
        "রুটিন", "routine", "সময়", "time", "কাজ", "work", "পড়াশোনা", "study", "পরিকল্পনা", "plan"
    ]
    if any(w in lower for w in routine_triggers) and len(lower) <= 80:
        reply = _pick([
            "কাজ বা রুটিন গুছিয়ে নিতে চাইলে একসাথে সব না ধরে সবচেয়ে জরুরি ১–২টা কাজ আগে শেষ করার টার্গেট নাও। ছোট ছোট ধাপে এগোলে চাপ কম লাগে।",
            "দিনটা সুন্দরভাবে গুছিয়ে নিতে চাইলে জরুরি কাজগুলো আগে লিখে নাও এবং কাজের মাঝে অল্প একটু ব্রেক রাখো—তাহলে মনোযোগ ধরে রাখা সহজ হয়।"
        ])
        return reply, True

    # 7. Thanks / acknowledgment
    thanks_triggers = ["ধন্যবাদ", "thanks", "thank you", "ঠিক আছে", "ok", "okay", "ওকে", "বুঝলাম"]
    if any(w in lower for w in thanks_triggers) and len(lower) <= 25:
        return (
            _pick([
                "একদম ঠিক আছে! আর কোনো হেল্প লাগলে বলো।",
                "কোনো ব্যাপার না ভাই, দরকার হলে আবার মেসেজ দিও।"
            ]),
            False,
        )

    # 8. General problem / any other issue user shares -> track for follow-up!
    short_preview = text if len(text) <= 60 else text[:57] + "..."
    reply = _pick([
        (
            f"বুঝলাম, তুমি '{short_preview}' নিয়ে কথা বলছো। "
            "এই বিষয়ে আগে শান্ত মাথায় মূল কারণটা কী তা দেখে নাও, আর প্রয়োজন হলে ধাপে ধাপে সমাধান করার চেষ্টা করো।\n"
            "আমি বিষয়টা নোট করে রাখলাম—একটু পর আবার খোঁজ নেবো যে এটার কী অবস্থা।"
        ),
        (
            f"তোমার কথাটা পেলাম—'{short_preview}'। "
            "একটু সময় নিয়ে সহজ উপায়টা ট্রাই করে দেখো। আমি পরে আবার জিজ্ঞেস করবো তোমার এটা ঠিক হয়েছে কি না।"
        )
    ])
    return reply, True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "জি বলছি আমি! দৈনন্দিন জীবনের যেকোনো সমস্যা বা কাজে হেল্প লাগলে বলো—সহজ বাংলায় কথা বলি, "
        "আর দরকার হলে পরে নিজে থেকেই খোঁজ নেবো যে তোমার কাজটা ঠিক হয়েছে কি না।"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "যে কোনো সমস্যা বা বিষয় বাংলায় বা ইংরেজিতে লিখে পাঠাও। সমাধানের আইডিয়া দেওয়ার পর "
        "আমি কিছুক্ষণ পর নিজে থেকেই জিজ্ঞেস করবো বিষয়টার কী অবস্থা।"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or not update.effective_chat:
        return

    chat_id = str(update.effective_chat.id)
    user_text = update.message.text.strip()

    data = load_followups()
    current_issue = data.get(chat_id)

    reply_text, should_track = build_daily_help_reply(user_text, current_issue)
    await update.message.reply_text(reply_text)

    if should_track:
        summary = user_text if len(user_text) <= 60 else user_text[:57] + "..."
        now = time.time()
        data[chat_id] = {
            "summary": summary,
            "created_at": now,
            "next_check_at": now + FOLLOWUP_DELAY_SECONDS,
            "followup_count": 0,
            "awaiting_status": True,
        }
        save_followups(data)
    elif current_issue and is_resolved_reply(user_text.lower()):
        data.pop(chat_id, None)
        save_followups(data)


async def check_followups_job(context: ContextTypes.DEFAULT_TYPE):
    data = load_followups()
    if not data:
        return

    now = time.time()
    changed = False

    for chat_id, item in list(data.items()):
        if not item.get("awaiting_status"):
            continue

        if now >= item.get("next_check_at", 0):
            count = item.get("followup_count", 0)
            summary = item.get("summary", "ওই বিষয়টা")

            if count == 0:
                msg = (
                    f"আরে, একটু আগে যে '{summary}' নিয়ে কথা বলছিলাম—ওইটার কী অবস্থা? "
                    "সমাধান হয়েছে নাকি এখনো কোনো সমস্যা হচ্ছে?"
                )
            else:
                msg = (
                    f"আবার একটু খোঁজ নিলাম—'{summary}' নিয়ে কি কোনো অগ্রগতি হলো, "
                    "নাকি এখনো হেল্প লাগবে?"
                )

            try:
                await context.bot.send_message(chat_id=int(chat_id), text=msg)
                item["followup_count"] = count + 1
                changed = True

                if item["followup_count"] >= MAX_FOLLOWUPS_PER_ISSUE:
                    # Stop automatic pinging after max attempts so user isn't spammed
                    item["awaiting_status"] = False
                else:
                    item["next_check_at"] = now + FOLLOWUP_DELAY_SECONDS

            except Exception as e:
                logger.warning(f"Could not send follow-up to {chat_id}: {e}")
                item["awaiting_status"] = False
                changed = True

    if changed:
        save_followups(data)


def main():
    if not TOKEN:
        logger.error("CRITICAL: TOKEN environment variable is missing.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if app.job_queue:
        app.job_queue.run_repeating(
            check_followups_job,
            interval=CHECK_INTERVAL_SECONDS,
            first=15,
        )
    else:
        logger.warning("JobQueue is not available; automatic follow-ups require extras.")

    logger.info("Daily Life Helping Bot (No API Key, Auto Follow-up) started...")
    app.run_polling()


if __name__ == "__main__":
    main()

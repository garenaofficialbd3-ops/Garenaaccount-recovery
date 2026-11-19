import logging
import os
import subprocess
import sys

# Ensure python-telegram-bot is installed
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


def get_smart_ff_reply(text: str) -> str:
    msg = text.lower().strip()

    greetings = ["হ্যালো", "হাই", "hello", "hi", "সালাম", "assalamu", "আসসালামু", "কেমন আছো", "কেমন আছেন"]
    if any(word in msg for word in greetings) and len(msg) <= 30:
        return (
            "জি বলছি আমি! আমি অভির বট, বলো 🎮✨\n\n"
            "Free Fire নিয়ে কোনো সমস্যা বা সাজেশন লাগলে নির্দ্বিধায় বলো—আমি বাংলায় সাহায্য করার চেষ্টা করবো!"
        )

    if any(word in msg for word in ["পিং", "ping", "নেট", "net", "ল্যাগ", "lag", "হাই পিং", "high ping", "স্লো"]):
        return (
            "আমি অভির বট, বলো! হাই পিং বা ল্যাগের সমস্যার জন্য নিচের টিপসগুলো ফলো করো:\n"
            "• খেলার আগে ব্যাকগ্রাউন্ডের অপ্রয়োজনীয় অ্যাপ ও ডাউনলোড বন্ধ রাখো।\n"
            "• Wi-Fi বা মোবাইল ডেটায় একটানা পিং উঠানামা করলে কানেকশন রিসেট বা রিম্যাচ ট্রাই করো।\n"
            "• ফোনের গ্রাফিক্স সেটিংস Smooth বা Standard-এ রেখে FPS High/Normal সেট করে দেখো।\n"
            "• ফোন অতিরিক্ত গরম হলে কিছুক্ষণ বিরতি নিয়ে খেললে ল্যাগ কমবে।"
        )

    if any(word in msg for word in ["লগইন", "login", "বাইন্ড", "bind", "অ্যাকাউন্ট", "account", "আইডি", "id", "রিকভারি", "recovery", "ফেসবুক", "facebook", "গুগল", "google", "জিমেইল", "gmail"]):
        return (
            "জি বলছি আমি! অ্যাকাউন্ট লগইন বা বাইন্ডিং নিয়ে সাজেশন:\n"
            "• যে Facebook, Google বা বাইন্ড অ্যাকাউন্টের সাথে ID যুক্ত আছে, আগে সেই অ্যাকাউন্টে ঠিকঠাক লগইন আছে কি না নিশ্চিত করো।\n"
            "• ব্রাউজার বা গেম ক্যাশে সমস্যার কারণে অনেক সময় লগইন আটকায়—সঠিক লিংক/অফিসিয়াল মাধ্যমে পুনরায় চেষ্টা করো।\n"
            "• নিজের ID-র পাসওয়ার্ড, কোড বা গোপন তথ্য কখনো কারও সাথে শেয়ার করবে না।"
        )

    if any(word in msg for word in ["সেন্সিটিভিটি", "sensitivity", "হেডশট", "headshot", "aim", "এম", "সেটিংস", "setting", "settings", "hud"]):
        return (
            "আমি অভির বট, বলো! সেন্সিটিভিটি ও সেটিংস নিয়ে সাজেশন:\n"
            "• কারও কপি করা সেন্সিটিভিটি অন্ধভাবে না বসিয়ে নিজের ফোনের স্ক্রিন সাইজ ও টাচ রেসপন্স অনুযায়ী ধীরে ধীরে অ্যাডজাস্ট করো।\n"
            "• General ও Red Dot একসাথে অনেক বাড়িয়ে না দিয়ে Training Ground-এ ২–৩টা ম্যাচ প্র্যাকটিস করে ঠিক করো।\n"
            "• Custom HUD এমনভাবে রাখো যেন ফায়ার, মুভমেন্ট ও গ্লু-ওয়াল বাটনে আঙুল সহজে পৌঁছায়।"
        )

    if any(word in msg for word in ["ব্যান", "ban", "সাসপেন্ড", "suspend", "হ্যাক", "hack", "স্ক্রিপ্ট", "script"]):
        return (
            "জি বলছি আমি! অ্যাকাউন্ট সেফটি নিয়ে পরিষ্কার সাজেশন:\n"
            "• কোনো থার্ড-পার্টি অ্যাপ, আনঅফিশিয়াল ফাইল, মোড বা স্ক্রিপ্ট ব্যবহার করলে আইডি ব্যান বা সাসপেন্ড হওয়ার ঝুঁকি থাকে।\n"
            "• সবসময় অফিসিয়াল গেম ও নিরাপদ নিয়ম মেনে খেললে আইডি সুরক্ষিত থাকবে।"
        )

    return (
        "আমি অভির বট, বলো! 🎮\n\n"
        "তোমার মেসেজটা পেলাম। Free Fire-এর নির্দিষ্ট সমস্যাটা আরেকটু পরিষ্কার করে বলো—"
        "যেমন **হাই পিং/ল্যাগ**, **লগইন বা বাইন্ডিং**, **সেন্সিটিভিটি/সেটিংস** নাকি **অ্যাকাউন্ট সেফটি**? "
        "তাহলে আমি বাংলায় সহজ সাজেশন দিচ্ছি!"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "আমি অভির বট, বলো! 🎮✨\n\n"
        "আমি একজন Free Fire সাজেশন বট। কোনো API Key ছাড়াই বাংলায় লগইন/বাইন্ডিং, পিং/ল্যাগ, "
        "সেটিংস বা গেমের সমস্যার সাজেশন দিতে পারি। তোমার সমস্যাটা বলো!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "জি বলছি আমি! কীভাবে কথা বলবে দেখে নাও:\n"
        "• 'হ্যালো' লিখে শুরু করতে পারো।\n"
        "• পিং/ল্যাগ, লগইন/বাইন্ডিং, সেন্সিটিভিটি বা সেটিংস—যে বিষয়ে সাজেশন চাও, বাংলায় লিখে পাঠাও।"
    )


async def ff_suggestion_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    reply_text = get_smart_ff_reply(user_text)
    await update.message.reply_text(reply_text)


def main():
    if not TOKEN:
        logger.error("CRITICAL: TOKEN environment variable is missing.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ff_suggestion_reply))

    logger.info("Ovi's Bangla Free Fire Suggestion Bot (No API Key) started...")
    app.run_polling()


if __name__ == "__main__":
    main()

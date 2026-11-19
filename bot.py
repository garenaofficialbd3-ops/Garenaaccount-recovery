import logging
import os
import random
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


def _pick(options: list[str]) -> str:
    return random.choice(options)


def build_human_reply(raw_text: str) -> str:
    text = raw_text.strip()
    lower = text.lower()

    # 1. Greeting / casual opening
    greetings = [
        "হ্যালো", "হাই", "hello", "hi", "hey", "সালাম",
        "আসসালামু", "assalamu", "কেমন আছো", "কেমন আছেন",
        "kemon acho", "kemon achen", "ki khobor", "কি খবর"
    ]
    if any(word in lower for word in greetings) and len(lower) <= 35:
        return _pick([
            "জি বলছি আমি! ভালো আছি, তুমি কেমন আছো? Free Fire নিয়ে কোনো ঝামেলা বা সাজেশন লাগলে বলো।",
            "হ্যাঁ ভাই, বলো! কী নিয়ে কথা বলতে চাচ্ছো বা Free Fire-এর কোন বিষয়টা নিয়ে হেল্প লাগবে?",
            "আরে বলো! আমি আছি তো—গেম বা আইডি নিয়ে কোনো সমস্যা হলে খুলে বলো, সমাধানের চেষ্টা করি।"
        ])

    # 2. Identity / creator logic (only when asked about identity or Ovi)
    identity_triggers = [
        "ovi", "অভি", "কে বানিয়েছে", "কে তৈরি", "তোর মালিক", "তোমার মালিক",
        "কার বট", "কে তুই", "তুমি কে", "tumi ke", "tui ke", "পরিচয়", "admin", "অ্যাডমিন"
    ]
    if any(word in lower for word in identity_triggers):
        return _pick([
            "আমি অভির বানানো বট—Free Fire নিয়ে কারও কোনো সমস্যা বা পরামর্শ লাগলে সহজ বাংলায় হেল্প করার জন্য রাখা হয়েছে। বলো, তোমার কী লাগবে?",
            "এটা অভির বট। মূলত Free Fire-এর লগইন, পিং, সেটিংস বা সেফটি নিয়ে যাতে সহজে একটা আইডিয়া পাওয়া যায়, সেভাবেই বানানো। তুমি কী জানতে চাচ্ছো?"
        ])

    # 3. Capabilities / what it can do
    capability_triggers = [
        "কি কি করতে পারো", "কী কী করতে পারো", "ki ki korte paro",
        "কি পারো", "ki paro", "কাজ কি", "কিভাবে সাহায্য", "হেল্প", "help"
    ]
    if any(word in lower for word in capability_triggers):
        return (
            "আমি মূলত Free Fire নিয়ে যেকোনো সাধারণ সমস্যায় সহজ পরামর্শ দিতে পারি:\n"
            "• আইডি লগইন বা বাইন্ডিং আটকে গেলে কী চেক করবে\n"
            "• হাই পিং বা গেম ল্যাগ করলে কীভাবে কমানো যায়\n"
            "• সেন্সিটিভিটি, গ্রাফিক্স বা কাস্টম HUD কীভাবে গুছিয়ে নেবে\n"
            "• আইডি নিরাপদ রাখার সহজ নিয়ম\n\n"
            "তোমার এখন কোন বিষয়টা নিয়ে সমস্যা হচ্ছে?"
        )

    # 4. Ping / lag / network
    ping_triggers = [
        "পিং", "ping", "নেট", "net", "ল্যাগ", "lag",
        "হাই পিং", "high ping", "স্লো", "slow", "ডিসকানেক্ট", "disconnect"
    ]
    if any(word in lower for word in ping_triggers):
        return _pick([
            (
                "হাই পিং বা ল্যাগ করলে আগে এই কয়টা জিনিস দেখে নাও:\n"
                "• ব্যাকগ্রাউন্ডে কোনো অ্যাপ ডাউনলোড বা আপডেট হচ্ছে কি না চেক করো।\n"
                "• Wi-Fi বা মোবাইল ডেটায় একটানা পিং খারাপ থাকলে একবার এয়ারপ্লেন মোড অন-অফ করে দেখো।\n"
                "• গ্রাফিক্স Smooth বা Standard-এ রেখে FPS স্বাভাবিক রাখলে গেম অনেকটা হালকা লাগে।\n"
                "• ফোন গরম হয়ে গেলে কিছুক্ষণ রেস্ট দিয়ে খেললে ল্যাগ কমে যায়।"
            ),
            (
                "খেলার মাঝে পিং বা ল্যাগ ধরলে বিরক্তি লাগে খুব। কয়েকটা সহজ কাজ করে দেখতে পারো:\n"
                "• খেলার সময় ফোনের বাকি ভারী অ্যাপগুলো বন্ধ রাখো।\n"
                "• নেটওয়ার্ক দুর্বল মনে হলে কানেকশন সুইচ বা রিসেট করে নতুন ম্যাচে ঢোকো।\n"
                "• হাই গ্রাফিক্সে ফোন চাপ নিলে সেটিংস একটু কমিয়ে নিলেই স্মুথ হয়।"
            )
        ])

    # 5. Login / binding / account access
    login_triggers = [
        "লগইন", "login", "বাইন্ড", "bind", "অ্যাকাউন্ট", "account",
        "আইডি", "id", "রিকভারি", "recovery", "ফেসবুক", "facebook",
        "গুগল", "google", "জিমেইল", "gmail", "কোড", "code"
    ]
    if any(word in lower for word in login_triggers):
        return _pick([
            (
                "লগইন বা বাইন্ডিং নিয়ে আটকালে শুরুতে এই কয়েকটা বিষয় মিলিয়ে দেখো:\n"
                "• যে Facebook, Google বা অন্য বাইন্ডের সাথে আইডি যুক্ত, আগে ওটায় ঠিকঠাক লগইন আছে কি না দেখো।\n"
                "• অনেক সময় ব্রাউজার বা গেম ক্যাশের কারণে লগইন আটকায়—একটু পর আবার চেষ্টা করে দেখো।\n"
                "• নিজের আইডির পাসওয়ার্ড বা কোনো গোপন কোড কখনো কারও সাথে শেয়ার করবে না।"
            ),
            (
                "অ্যাকাউন্টে ঢুকতে বা বাইন্ড নিয়ে সমস্যা হলে শান্ত মাথায় ধাপে ধাপে চেক করো:\n"
                "• সঠিক জিমেইল বা সোশ্যাল অ্যাকাউন্টেই লগইন করছো কি না তা নিশ্চিত হও।\n"
                "• বারবার চেষ্টা করলে সাময়িক লিমিট বা কুলডাউন পড়তে পারে, তাই একটু সময় নিয়ে ট্রাই করো।\n"
                "• কখনো কোনো অপরিচিত লিংকে বা কারও হাতে আইডির তথ্য দিও না।"
            )
        ])

    # 6. Sensitivity / settings / HUD / gameplay
    settings_triggers = [
        "সেন্সিটিভিটি", "sensitivity", "হেডশট", "headshot", "aim",
        "এম", "সেটিংস", "setting", "settings", "hud", "গ্রাফিক্স", "graphics"
    ]
    if any(word in lower for word in settings_triggers):
        return _pick([
            (
                "সেন্সিটিভিটি বা সেটিংসের ক্ষেত্রে এক কথায় বললে—নিজের হাতের সাথে যেটা মানায় সেটাই সেরা:\n"
                "• অন্যের কপি করা সেন্সিটিভিটি হুট করে বসিয়ে না দিয়ে নিজের ফোনের টাচ অনুযায়ী একটু একটু করে বদলাও।\n"
                "• ট্রেনিং গ্রাউন্ডে কিছুক্ষণ ড্র্যাগ ও মুভমেন্ট প্র্যাকটিস করে দেখো কোথায় কমফোর্ট পাচ্ছো।\n"
                "• HUD এমনভাবে রাখো যেন আঙুল স্বাভাবিক অবস্থানেই সব বাটনে পৌঁছায়।"
            ),
            (
                "সেটিংস আর সেন্সিটিভিটি নিয়ে খুব বেশি তাড়াহুড়ো না করে নিজের মতো গুছিয়ে নাও:\n"
                "• General আর Red Dot একসাথে অনেক বাড়িয়ে দিলে কন্ট্রোল কঠিন হতে পারে।\n"
                "• আগে নিজের ফোনের পারফরম্যান্স অনুযায়ী গ্রাফিক্স ঠিক করো, তারপর সেন্সিটিভিটি মিলিয়ে নাও।"
            )
        ])

    # 7. Ban / safety / third-party risk
    safety_triggers = [
        "ব্যান", "ban", "সাসপেন্ড", "suspend", "হ্যাক", "hack",
        "স্ক্রিপ্ট", "script", "মোড", "mod", "সেফ", "safe"
    ]
    if any(word in lower for word in safety_triggers):
        return (
            "আইডি সেফ রাখতে হলে সরাসরি বলবো—কোনো থার্ড-পার্টি অ্যাপ, মোড, স্ক্রিপ্ট বা আনঅফিশিয়াল ফাইলের দিকে না যাওয়াই সবচেয়ে নিরাপদ। "
            "এসব জিনিসে আইডি ব্যান বা সাসপেন্ড হওয়ার বড় ঝুঁকি থাকে। অফিসিয়াল গেম ও স্বাভাবিক নিয়মে খেললেই আইডি সুরক্ষিত থাকে।"
        )

    # 8. Thanks / acknowledgment
    thanks_triggers = ["ধন্যবাদ", "thanks", "thank you", "ঠিক আছে", "ok", "okay", "ওকে", "বুঝলাম"]
    if any(word in lower for word in thanks_triggers) and len(lower) <= 25:
        return _pick([
            "একদম ঠিক আছে! আর কিছু জানার থাকলে বলো।",
            "কোনো ব্যাপার না ভাই, দরকার হলে আবার মেসেজ দিও।"
        ])

    # 9. Natural fallback
    return _pick([
        "বিষয়টা আরেকটু পরিষ্কার করে বলো তো—Free Fire-এর কোন অংশে সমস্যা হচ্ছে? যেমন পিং/ল্যাগ, লগইন বা বাইন্ডিং, সেটিংস নাকি সেফটি?",
        "তোমার কথাটা পুরোপুরি ক্লিয়ার হলো না। গেমের ঠিক কোন সমস্যাটার সমাধান খুঁজছো, একটু খুলে বললে সহজ আইডিয়া দিতে পারি।"
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "জি বলছি আমি! Free Fire নিয়ে কোনো সমস্যা বা সাজেশন লাগলে বলো—সহজ বাংলায় কথা বলি।"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "যে কোনো সমস্যা সহজভাবে বাংলায় লিখে পাঠাও—যেমন পিং/ল্যাগ, লগইন বা বাইন্ডিং, সেন্সিটিভিটি/সেটিংস অথবা আইডি সেফটি।"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    reply = build_human_reply(update.message.text)
    await update.message.reply_text(reply)


def main():
    if not TOKEN:
        logger.error("CRITICAL: TOKEN environment variable is missing.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Human-style Bangla Free Fire bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()

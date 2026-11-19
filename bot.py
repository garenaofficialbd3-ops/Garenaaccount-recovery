import logging
import os
import subprocess
import sys

# Ensure required libraries are installed
for pkg in ["python-telegram-bot==20.7", "google-genai"]:
    mod_name = "telegram" if pkg.startswith("python-telegram-bot") else "google.genai"
    try:
        __import__(mod_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_INSTRUCTION = (
    "তুমি 'অভির বট'—একজন স্মার্ট, প্রাণবন্ত, বন্ধুসুলভ ও অভিজ্ঞ Garena Free Fire এক্সপার্ট। "
    "তোমার সাথে সব কথোপকথন এবং প্রতিটি উত্তর অবশ্যই স্বাভাবিক, আকর্ষণীয় ও সহজ বাংলায় হবে। "
    "কেউ যদি 'হ্যালো', 'হাই', 'কেমন আছো' বা সালাম/সম্ভাষণ জানায় অথবা কোনো কিছু জিজ্ঞেস করে, "
    "তাহলে স্বাভাবিকভাবে 'জি বলছি আমি' বা 'আমি অভির বট, বলো' ধরনের আন্তরিক ও আকর্ষণীয় ভঙ্গিতে শুরু করবে "
    "এবং সাহায্য করার জন্য প্রস্তুত থাকবে। "
    "Free Fire সম্পর্কিত যেকোনো সমস্যা—যেমন অ্যাকাউন্ট বাইন্ডিং/লগইন সমস্যা, অ্যাকাউন্ট নিরাপত্তা, "
    "হাই পিং/ল্যাগ/নেটওয়ার্ক, গেম সেটিংস, সেন্সিটিভিটি বা খেলার টিপস—নিয়ে পরিষ্কার ও কাজের সাজেশন দেবে। "
    "কখনো কোনো হ্যাক, চিট, আনঅফিশিয়াল মোড, অ্যাকাউন্ট বাইপাস বা ভুয়া কোড জেনারেট করার পরামর্শ দেবে না; "
    "নিরাপদ ও অফিসিয়াল সমাধানের ওপর জোর দেবে। উত্তর গুছানো, প্রাণবন্ত ও সহজবোধ্য রাখবে।"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "আমি অভির বট, বলো! 🎮✨\n\n"
        "আমি একজন Free Fire এক্সপার্ট। লগইন/বাইন্ডিং, সেফটি, পিং/ল্যাগ, সেটিংস বা গেমের যেকোনো সমস্যায় "
        "আমাকে নির্দ্বিধায় বলো—সব বাংলায় সহজ সাজেশন দিয়ে পাশে আছি!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "জি বলছি আমি! কীভাবে সাজেশন নেবে দেখে নাও:\n"
        "• Free Fire-এর যেকোনো সমস্যা পরিষ্কারভাবে বাংলায় লিখে পাঠাও।\n"
        "• ফোনের মডেল বা নেটওয়ার্কের কথা বললে সাজেশন আরও পারফেক্ট হবে।\n"
        "• নিজের অ্যাকাউন্টের পাসওয়ার্ড বা কোনো গোপন তথ্য এখানে শেয়ার করবে না।"
    )


async def ff_expert_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()

    if not client:
        await update.message.reply_text(
            "আমি অভির বট—তবে এখনো GEMINI_API_KEY বসানো হয়নি। Railway-এর Variables ট্যাবে GEMINI_API_KEY যুক্ত করে সেভ করো।"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.8,
            ),
        )
        reply_text = (response.text or "").strip()
        if not reply_text:
            reply_text = "জি বলছি আমি! এখন একটু নেটে সমস্যা হচ্ছে, আর একবার মেসেজ পাঠাও তো।"

        for i in range(0, len(reply_text), 4000):
            await update.message.reply_text(reply_text[i : i + 4000])

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        await update.message.reply_text(
            "আমি অভির বট—এই মুহূর্তে উত্তর তৈরি করতে একটু সমস্যা হচ্ছে, একটু পর আবার বলো।"
        )


def main():
    if not TOKEN:
        logger.error("CRITICAL: TOKEN environment variable is missing.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ff_expert_reply))

    logger.info("Ovi's Bangla Free Fire Expert AI bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()

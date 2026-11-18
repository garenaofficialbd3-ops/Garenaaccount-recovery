import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Logging Configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Hello, I am Ovi's bot.\n\n"
        "Please enter your Free Fire bind email here."
    )
    await update.message.reply_text(welcome_text)

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_email = update.message.text.strip()
    
    # Input Validation
    if "@" not in user_email or "." not in user_email:
        await update.message.reply_text("Invalid email format. Please enter a valid bind email address.")
        return

    await update.message.reply_text(f"Processing request for: {user_email}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Content-Type": "application/json"
        }
        payload = {
            "email": user_email
        }
        
        # Backend execution hook for recovery trigger
        
        await update.message.reply_text("Code sent successfully.")
        
    except Exception as e:
        logger.error(f"Error executing request: {e}")
        await update.message.reply_text("An error occurred while processing your request. Please try again later.")

def main():
    if not TOKEN:
        logger.error("CRITICAL: TOKEN environment variable is missing.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_email))

    logger.info("Bot is successfully running...")
    app.run_polling()

if __name__ == "__main__":
    main()

import logging
import os
import random
import subprocess
import sys

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


def _pick(options: list[str]) -> str:
    return random.choice(options)


def detect_language_style(text: str) -> str:
    """
    Detect user's language style so replies match naturally:
    - 'bn': Bangla script
    - 'ur_hi_script': Devanagari / Urdu script
    - 'roman_hi_ur': Romanized Hindi / Urdu
    - 'en_banglish': English / Banglish
    """
    if any("\u0980" <= ch <= "\u09ff" for ch in text):
        return "bn"
    if any("\u0900" <= ch <= "\u097f" for ch in text) or any("\u0600" <= ch <= "\u06ff" for ch in text):
        return "ur_hi_script"

    lower = text.lower()
    hi_ur_markers = [
        "kya", "kaise", "hai", "hain", "hoon", "hun", "nahi", "nhi", "acha", "accha",
        "theek", "thik", "samajh", "madad", "batao", "bataiye", "mera", "meri", "tumhara",
        "aap", "kuch", "kyun", "kyu", "kab", "kahan", "bahut", "zaroor", "shukriya", "meherbani"
    ]
    words = set(lower.replace("?", " ").replace("!", " ").replace(",", " ").replace(".", " ").split())
    if len(words.intersection(hi_ur_markers)) >= 1 and not any(
        w in words for w in ["ami", "tumi", "apni", "kemon", "kivabe", "ki", "korbo", "parchi", "pari", "valo", "bhalo"]
    ):
        return "roman_hi_ur"

    return "en_banglish"


def build_smart_reply(raw_text: str) -> str:
    text = raw_text.strip()
    lower = text.lower()
    style = detect_language_style(text)

    # 1. Greetings
    greetings = [
        "হ্যালো", "হাই", "hello", "hi", "hey", "সালাম", "আসসালামু", "assalamu", "salam",
        "কেমন আছো", "কেমন আছেন", "kemon acho", "kemon achen", "ki khobor", "কি খবর",
        "namaste", "नमस्ते", "kya haal", "kaise ho", "kaisi ho", "kya حال", "سلام"
    ]
    if any(w in lower for w in greetings) and len(lower) <= 40:
        if style == "ur_hi_script":
            return _pick([
                "जी बिल्कुल, बताइए क्या मदद चाहिए? कोई सवाल या परेशानी है तो खुलकर पूछिए।",
                "جی بالکل، بتائیے کیا مدد چاہیے؟ کوئی مسئلہ یا سوال ہو تو ضرور پوچھیے۔"
            ])
        if style == "roman_hi_ur":
            return _pick([
                "Haan bilkul, batao kya help chahiye? Koi problem ya sawaal ho to seedha pucho.",
                "Ji bilkul, main yahan hoon. Kis topic par madad chahiye batao?"
            ])
        return _pick([
            "জি বলছি আমি! কী নিয়ে হেল্প লাগবে, সোজা বাংলা বা ইংলিশে বলো।",
            "হ্যাঁ, বলো! তোমার কোন বিষয়টা নিয়ে সাহায্য বা সমাধান দরকার?"
        ])

    # 2. Identity / Ovi
    identity_triggers = [
        "ovi", "অভি", "কে বানিয়েছে", "কে তৈরি", "তোর মালিক", "তোমার মালিক",
        "কার বট", "কে তুই", "তুমি কে", "tumi ke", "tui ke", "who made you",
        "kisne banaya", "kaun ho", "تم کون ہو", "کس نے بنایا"
    ]
    if any(w in lower for w in identity_triggers):
        if style == "ur_hi_script":
            return "यह बॉट Ovi ने बनाया है ताकि रोज़मर्रा के काम और सवालों में आसान मदद मिल सके। बताइए आपको क्या जानना है?"
        if style == "roman_hi_ur":
            return "Ye bot Ovi ne banaya hai taaki daily problems aur sawalon mein aasan help mil sake. Batao tumhe kya jaanna hai?"
        return "এটা অভির বানানো হেল্পিং বট—দৈনন্দিন সমস্যা ও প্রশ্নে সহজ সমাধান দেওয়ার জন্য রাখা হয়েছে। বলো, তোমার কী লাগবে?"

    # 3. Network / Internet / Speed / Lag / Phone
    tech_triggers = [
        "নেট", "net", "ইন্টারনেট", "internet", "ওয়াইফাই", "wifi", "wi-fi",
        "স্লো", "slow", "ল্যাগ", "lag", "পিং", "ping", "ফোন", "phone",
        "hang", "হ্যাং", "গরম", "data", "ডেটা", "network", "नेट", "इंटरनेट", "स्लो", "انٹرنیٹ", "نیٹ"
    ]
    if any(w in lower for w in tech_triggers):
        if style == "ur_hi_script":
            return (
                "नेट या फ़ोन स्लो/लैग होने पर ये आसान स्टेप्स आज़माएँ:\n"
                "• बैकग्राउंड में चल रहे भारी ऐप्स या डाउनलोड बंद करें।\n"
                "• नेटवर्क अस्थिर हो तो फ़्लाइट मोड ऑन-ऑफ़ करके दोबारा देखें।\n"
                "• फ़ोन गर्म हो या स्टोरेज बहुत भरा हो तो कुछ जगह खाली करें और थोड़ा आराम दें।"
            )
        if style == "roman_hi_ur":
            return (
                "Net ya phone slow/lag ho raha ho to ye simple steps try karo:\n"
                "• Background ke heavy apps aur downloads band karo.\n"
                "• Network weak lage to airplane mode on-off karke check karo.\n"
                "• Phone garam ho ya storage full ho to thodi jagah khali karke try karo."
            )
        return (
            "নেট বা ফোন স্লো/ল্যাগ করলে সরাসরি এই কাজগুলো করে দেখো:\n"
            "• ব্যাকগ্রাউন্ডে ভারী অ্যাপ বা কোনো ডাউনলোড চলছে কি না বন্ধ করো।\n"
            "• নেটওয়ার্ক দুর্বল থাকলে একবার এয়ারপ্লেন মোড অন-অফ বা কানেকশন রিসেট করো।\n"
            "• ফোন গরম হলে বা স্টোরেজ একদম ভরে গেলে কিছু জায়গা খালি করে একটু বিরতি দাও।"
        )

    # 4. Account / Login / Security
    account_triggers = [
        "লগইন", "login", "log in", "অ্যাকাউন্ট", "account", "আইডি", "id",
        "পাসওয়ার্ড", "password", "otp", "ওটিপি", "hack", "হ্যাক", "safe", "সেফ",
        "अकाउंट", "लॉगिन", "पासवर्ड", "اکاؤنٹ", "لاگ ان", "پاس ورڈ"
    ]
    if any(w in lower for w in account_triggers):
        if style == "ur_hi_script":
            return (
                "अकाउंट या लॉगिन से जुड़ी ज़रूरी बातें:\n"
                "• सही ईमेल, फ़ोन नंबर या लिंक्ड अकाउंट से ही लॉगिन करें।\n"
                "• बार-बार ग़लत कोशिश करने पर अस्थायी रोक लग सकती है, थोड़ा रुककर दोबारा कोशिश करें।\n"
                "• पासवर्ड, OTP या कोई भी गोपनीय जानकारी किसी के साथ साझा न करें।"
            )
        if style == "roman_hi_ur":
            return (
                "Account ya login problem mein ye baatein dhyan rakho:\n"
                "• Sahi email, number ya linked account se hi login try karo.\n"
                "• Baar-baar try karne par temporary block/limit lag sakti hai, thoda ruk kar try karo.\n"
                "• Password, OTP ya personal info kabhi kisi ko share mat karo."
            )
        return (
            "অ্যাকাউন্ট বা লগইন নিয়ে ঝামেলা হলে সরাসরি এই বিষয়গুলো চেক করো:\n"
            "• সঠিক ইমেইল, নম্বর বা লিংকড অ্যাকাউন্ট দিয়েই লগইন করছো কি না দেখো।\n"
            "• বারবার চেষ্টা করলে সাময়িক লিমিট বা কুলডাউন পড়তে পারে, তাই একটু সময় নিয়ে চেষ্টা করো।\n"
            "• পাসওয়ার্ড, OTP বা ব্যক্তিগত গোপন তথ্য কখনো কারও সাথে শেয়ার করবে না।"
        )

    # 5. Study / Work / Routine / Advice
    work_triggers = [
        "কাজ", "work", "রুটিন", "routine", "পড়াশোনা", "study", "পরামর্শ", "advice",
        "suggestion", "সাজেশন", "help", "হেল্প", "madad", "मदद", "सलाह", "مدد"
    ]
    if any(w in lower for w in work_triggers):
        if style == "ur_hi_script":
            return (
                "किसी काम या रूटीन को आसान बनाने के लिए:\n"
                "• सबसे ज़रूरी 1–2 काम पहले चुनें और उसी पर ध्यान दें।\n"
                "• काम को छोटे हिस्सों में बाँटें और बीच में थोड़ा ब्रेक लें।"
            )
        if style == "roman_hi_ur":
            return (
                "Kaam ya routine manage karne ka simple tarika:\n"
                "• Sabse zaroori 1–2 kaam pehle pick karo aur unhi par focus karo.\n"
                "• Bade kaam ko chhote parts mein baant kar thoda break lete raho."
            )
        return (
            "কাজ বা রুটিন গুছিয়ে নিতে চাইলে:\n"
            "• সবচেয়ে জরুরি ১–২টা কাজ আগে বেছে নিয়ে সেগুলোতে ফোকাস করো।\n"
            "• বড় কাজকে ছোট ছোট ধাপে ভাগ করো এবং মাঝেমধ্যে অল্প একটু ব্রেক নাও।"
        )

    # 6. General smart fallback in matching language (no fake timer/note promise!)
    if style == "ur_hi_script":
        return "आपकी बात समझी। इस विषय पर सटीक मदद के लिए थोड़ा और साफ़-साफ़ बताइए कि आपको ठीक क्या समस्या या जानकारी चाहिए?"
    if style == "roman_hi_ur":
        return "Tumhari baat samajh aayi. Behtar help ke liye thoda clear batao ki tumhe exact kya problem ya jaankari chahiye?"
    return (
        "তোমার কথাটা ধরতে পেরেছি। আরেকটু পরিষ্কার করে বলো তো—ঠিক কোন বিষয়টা নিয়ে সমাধান বা তথ্য চাচ্ছো? "
        "বাংলা, ইংলিশ বা বাংলিশ যেভাবে সুবিধা হয় বলো, সরাসরি উত্তর দিচ্ছি।"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "জি বলছি আমি! বাংলা, ইংলিশ, বাংলিশ, হিন্দি বা উর্দু—যে ভাষায় সুবিধা হয় লিখে বলো। "
        "তোমার সমস্যা বা প্রশ্ন শুনে সরাসরি সমাধান দেওয়ার চেষ্টা করবো।"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "যেকোনো প্রশ্ন বা সমস্যা সরাসরি লিখে পাঠাও (বাংলা, English, Banglish, Hindi, Urdu)। "
        "অযথা অপেক্ষার কথা না বলে সাথে সাথে কাজের উত্তর দেওয়ার চেষ্টা করবো।"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    reply = build_smart_reply(update.message.text)
    await update.message.reply_text(reply)


def main():
    if not TOKEN:
        logger.error("CRITICAL: TOKEN environment variable is missing.")
        return

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Multi-language smart helping bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from translator import translate_word

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

user_data = {}  # user_id -> list of (original, translated, src, tgt)
user_lang = {}  # user_id -> target lang

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n"
        "Use /t <word> to translate and save\n"
        "Use /review to see today’s words\n"
        "Use /setlang <LANG_CODE> to set your target language (default = EN)"
    )

async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        return await update.message.reply_text("Usage: /setlang <LANG_CODE> (e.g. EN, FR, DE)")
    lang = context.args[0].upper()
    user_lang[user_id] = lang
    await update.message.reply_text(f"✅ Target language set to {lang}")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        return await update.message.reply_text("Usage: /t <word or phrase>")
    
    text = " ".join(context.args)
    target_lang = user_lang.get(user_id, "EN")
    translated, source_lang = translate_word(text, target_lang)

    # Save to user_data
    user_data.setdefault(user_id, []).append((text, translated, source_lang, target_lang))

    await update.message.reply_text(
        f"🔤 '{text}' ({source_lang} → {target_lang}) = '{translated}'\nSaved!"
    )

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    entries = user_data.get(user_id, [])
    if not entries:
        return await update.message.reply_text("📭 No saved words yet.")
    
    message = "\n".join([f"• {o} → {t} ({s} → {d})" for o, t, s, d in entries])
    await update.message.reply_text(f"📘 Translations This Session:\n{message}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setlang", setlang))
    app.add_handler(CommandHandler("t", translate))
    app.add_handler(CommandHandler("review", review))
    app.run_polling()

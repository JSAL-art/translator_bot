import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from translator import translate_word
from telegram import BotCommand
from aiohttp import web
import os
import asyncio


async def healthcheck(request):
    return web.Response(text="✅ Bot is alive")

async def run_health_server():
    app = web.Application()
    app.add_routes([web.get("/", healthcheck)])

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))  # Render sets PORT automatically
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

user_data = {}  # user_id -> list of (original, translated, src, tgt)
user_lang = {}  # user_id -> target lang
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n"
        "Use /t <word> to translate and save\n"
        "Use /review to see today’s words\n"
        "Use /setlang <LANG_CODE> to set your target language (default = EN)"
    )
def get_user_id(update: Update):
    if update.message and update.message.from_user:
        return update.message.from_user.id
    elif update.callback_query and update.callback_query.from_user:
        return update.callback_query.from_user.id
    return None


async def setlang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_user_id(update)
    if user_id is None:
        return

    if not context.args:
        return await update.message.reply_text("Usage: /setlang <LANG_CODE> (e.g. EN, FR, DE)")
    lang = context.args[0].upper()
    user_lang[user_id] = lang
    await update.message.reply_text(f"✅ Target language set to {lang}")


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = get_user_id(update)
    if user_id is None:
        return

    if not context.args:
        return await update.message.reply_text("Usage: /t <word or phrase>")

    text = " ".join(context.args)
    target_lang = user_lang.get(user_id, "EN")
    translated, source_lang = translate_word(text, target_lang)

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

def add_handlers(app):
    app.add_handler(CommandHandler("start", start))
    # app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setlang", setlang))
    app.add_handler(CommandHandler("t", translate))
    app.add_handler(CommandHandler("review", review))
    # app.add_handler(CommandHandler("clear", clear))

async def set_bot_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        # BotCommand("help", "Show all commands"),
        BotCommand("setlang", "Set target language"),
        BotCommand("t", "Translate a word (e.g., /t hello)"),
        BotCommand("review", "Review saved words"),
        # BotCommand("clear", "Clear your saved words"),
    ])

if __name__ == "__main__":
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(set_bot_commands)  # ✅ FIXED HERE
        .build()
    )

    add_handlers(app)
    #app.run_polling()

    loop = asyncio.get_event_loop()
    loop.create_task(run_health_server())  # <-- Keeps Render port open
    app.run_polling()

# if __name__ == "__main__":
#     app = ApplicationBuilder().token(BOT_TOKEN).build()
#     app.add_handler(CommandHandler("start", start))
#     app.add_handler(CommandHandler("setlang", setlang))
#     app.add_handler(CommandHandler("t", translate))
#     app.add_handler(CommandHandler("review", review))
#     app.run_polling()

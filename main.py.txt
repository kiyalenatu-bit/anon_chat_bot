from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import db

TOKEN = "PASTE_NEW_TOKEN_HERE"

menu_idle = ReplyKeyboardMarkup([["🔍 Start Chat"]], resize_keyboard=True)
menu_chat = ReplyKeyboardMarkup([["⏭ Skip", "⛔ Stop"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.create_user(user_id)
    user = db.get_user(user_id)

    if user[1] is None:
        await update.message.reply_text("Choose an anonymous username:")
    else:
        await update.message.reply_text("Ready.", reply_markup=menu_idle)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    user = db.get_user(user_id)

    if user[1] is None:
        db.set_alias(user_id, text)
        await update.message.reply_text("Alias set. Tap Start Chat.", reply_markup=menu_idle)
        return

    if text == "🔍 Start Chat":
        db.set_state(user_id, "WAITING")
        partner = db.find_match(user_id)
        if partner:
            db.set_state(user_id, "CHATTING", partner)
            db.set_state(partner, "CHATTING", user_id)
            await update.message.reply_text("Connected.", reply_markup=menu_chat)
            await context.bot.send_message(partner, "Connected.", reply_markup=menu_chat)
        else:
            await update.message.reply_text("Searching…")
        return

    if user[2] == "CHATTING":
        partner_id = user[3]
        if text == "⏭ Skip":
            db.add_skip(user_id, partner_id)
            db.set_state(user_id, "WAITING")
            db.set_state(partner_id, "WAITING")
            await update.message.reply_text("Skipped. Searching…")
            await context.bot.send_message(partner_id, "Partner left.")
            return

        if text == "⛔ Stop":
            db.set_state(user_id, "IDLE")
            if partner_id:
                db.set_state(partner_id, "IDLE")
                await context.bot.send_message(partner_id, "Chat ended.")
            await update.message.reply_text("Stopped.", reply_markup=menu_idle)
            return

        await context.bot.send_message(partner_id, text)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.run_polling()

import threading
import random
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Replace this with your Telegram Bot Token
TOKEN = "Y8062030427:AAHM40ruZOHIXuztNqEkHMm8A9SYFk8RDa8"

# In-memory balance storage (use database for production)
user_balances = {}

# Flask app for Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "✅ Big-Small Bot is running on Render (Free Tier)"

# --- Telegram Bot Logic ---

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 100  # Give starting balance
    await update.message.reply_text(
        "🎲 Welcome to the Big-Small Betting Game!\nUse /bet <big/small> <amount>\nUse /balance to check balance."
    )

# /balance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = user_balances.get(user_id, 0)
    await update.message.reply_text(f"💰 Your balance: ₹{balance}")

# /bet big/small 50
async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if len(args) != 2:
        await update.message.reply_text("❌ Usage: /bet <big/small> <amount>")
        return

    choice = args[0].lower()
    amount = args[1]

    if choice not in ["big", "small"]:
        await update.message.reply_text("❌ Choose 'big' or 'small'")
        return

    try:
        amount = int(amount)
    except ValueError:
        await update.message.reply_text("❌ Amount must be a number")
        return

    balance = user_balances.get(user_id, 100)
    if amount > balance:
        await update.message.reply_text("❌ Insufficient balance")
        return

    roll = random.randint(1, 6)
    result = "big" if roll >= 4 else "small"
    win = choice == result

    if win:
        user_balances[user_id] = balance + amount
        msg = f"🎉 You WON! Dice rolled {roll} ({result.upper()})\n💰 New balance: ₹{user_balances[user_id]}"
    else:
        user_balances[user_id] = balance - amount
        msg = f"😢 You LOST! Dice rolled {roll} ({result.upper()})\n💰 New balance: ₹{user_balances[user_id]}"

    await update.message.reply_text(msg)

# Start the Telegram bot in a separate thread
def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("bet", bet))
    app.run_polling()

threading.Thread(target=run_bot).start()

# Run Flask app (Render requires binding to a port)
if __name__ == '__main__':
    web_app.run(host="0.0.0.0", port=10000)

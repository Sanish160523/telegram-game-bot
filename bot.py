# crash/bot.py

import logging
import random
import sqlite3
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace this with your bot token

# Setup logging
logging.basicConfig(level=logging.INFO)

# Database connection
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 1000
)''')
conn.commit()

# Helper functions
def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 1000

def update_balance(user_id, amount):
    current = get_balance(user_id)
    new = current + amount
    cursor.execute("INSERT OR REPLACE INTO users (user_id, balance) VALUES (?, ?)", (user_id, new))
    conn.commit()

# Bot commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_balance(user_id, 0)
    await update.message.reply_text("🎮 Welcome to Big Small Game!\n\nUse /big or /small to play.\nEach user starts with ₹1000.\nCheck your balance using /balance.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    await update.message.reply_text(f"💰 Your balance: ₹{bal}")

async def big(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_bet(update, context, "big")

async def small(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_bet(update, context, "small")

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE, guess: str):
    user_id = update.effective_user.id

    try:
        amount = int(context.args[0])
    except:
        await update.message.reply_text("❗ Usage: /big 100 or /small 100")
        return

    bal = get_balance(user_id)
    if amount > bal:
        await update.message.reply_text("😞 Insufficient balance.")
        return

    dice = random.randint(1, 6)
    result = "big" if dice >= 4 else "small"
    won = (guess == result)
    change = amount if won else -amount
    update_balance(user_id, change)

    await update.message.reply_text(
        f"🎲 Dice rolled: {dice} ({result})\n"
        + ("✅ You *won!*" if won else "❌ You *lost.*")
        + f"\n💰 New balance: ₹{get_balance(user_id)}",
        parse_mode="Markdown"
    )

# Start bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("big", big))
    app.add_handler(CommandHandler("small", small))
    app.run_polling()

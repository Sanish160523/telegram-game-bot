# telegram_botgame.py

import asyncio
import random
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = '8062030427:AAHM40ruZOHIXuztNqEkHMm8A9SYFk8RDa8'  # Replace with your actual bot token
ADMIN_USER_ID = 6269404426  # Replace with the correct admin Telegram ID
DB_FILE = 'crashbot.db'

crash_game_active = False
crash_players = {}
crash_cashouts = {}
crash_multiplier = 1.0
manual_crash_point = None

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 1000
    )''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return 1000
    return row[0]

def update_balance(user_id, amount):
    current = get_balance(user_id)
    new_balance = current + amount
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("REPLACE INTO users (user_id, balance) VALUES (?, ?)", (user_id, new_balance))
    conn.commit()
    conn.close()

# --- Command Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_balance(user_id, 0)
    await update.message.reply_text(f"🎮 Welcome to CrashBot! Your user ID is: `{user_id}`", parse_mode='Markdown')

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    await update.message.reply_text(f"💰 Your balance: ₹{bal}")

async def joincrash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global crash_game_active, crash_players

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /joincrash <amount>")
        return

    amount = int(context.args[0])
    user_id = update.effective_user.id

    if get_balance(user_id) < amount:
        await update.message.reply_text("❌ Not enough balance!")
        return

    if crash_game_active:
        if user_id in crash_players:
            await update.message.reply_text("❌ Already joined this round.")
            return
        crash_players[user_id] = amount
        update_balance(user_id, -amount)
        await update.message.reply_text(f"✅ Joined crash with ₹{amount}")
    else:
        crash_players = {user_id: amount}
        crash_cashouts.clear()
        update_balance(user_id, -amount)
        crash_game_active = True
        await update.message.reply_text("🚀 Crash round starting in 10s!")
        await asyncio.sleep(10)
        asyncio.create_task(run_crash_round(context, update.effective_chat.id))

async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in crash_players and user_id not in crash_cashouts:
        crash_cashouts[user_id] = crash_multiplier
        await update.message.reply_text(f"💸 Cashed out at {crash_multiplier:.2f}x!")
    else:
        await update.message.reply_text("❌ You're not in or already cashed out.")

async def setcrash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global manual_crash_point
    user_id = update.effective_user.id

    if user_id != ADMIN_USER_ID:
        await update.message.reply_text("❌ Only the admin can set the crash point.")
        return

    if not context.args or not context.args[0].replace(".", "", 1).isdigit():
        await update.message.reply_text("Usage: /setcrash <multiplier>")
        return

    manual_crash_point = float(context.args[0])
    await update.message.reply_text(f"✅ Crash point set to {manual_crash_point:.2f}x by admin.")

async def run_crash_round(context: ContextTypes.DEFAULT_TYPE, chat_id):
    global crash_multiplier, crash_game_active, crash_players, crash_cashouts, manual_crash_point

    crash_multiplier = 1.0
    crash_point = manual_crash_point if manual_crash_point else random.uniform(1.5, 5.0)
    manual_crash_point = None

    while crash_multiplier < crash_point:
        await context.bot.send_message(chat_id, f"📈 Multiplier: {crash_multiplier:.2f}x")
        crash_multiplier += round(random.uniform(0.1, 0.4), 2)
        await asyncio.sleep(1)

    await context.bot.send_message(chat_id, f"💥 CRASHED at {crash_multiplier:.2f}x!")

    for user_id, amount in crash_players.items():
        user = await context.bot.get_chat(user_id)
        if user_id in crash_cashouts:
            winnings = int(amount * crash_cashouts[user_id])
            update_balance(user_id, winnings)
            await context.bot.send_message(chat_id, f"✅ @{user.username or user.first_name} won ₹{winnings}")
        else:
            await context.bot.send_message(chat_id, f"❌ @{user.username or user.first_name} lost ₹{amount}")

    crash_game_active = False
    crash_players.clear()
    crash_cashouts.clear()

# --- Run Bot ---
def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("joincrash", joincrash))
    app.add_handler(CommandHandler("cashout", cashout))
    app.add_handler(CommandHandler("setcrash", setcrash))
    app.run_polling()

if __name__ == "__main__":
    main()

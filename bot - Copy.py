import json
import os
from datetime import date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ← Put your NEW bot token here
BOT_TOKEN = "8685345832:AAE4hJwpgc7wJiKUCuD6jXkokJzfD5aA9yM"

DATA_FILE = "streaks.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    today = date.today().isoformat()
    data = load_data()

    if user_id not in data:
        data[user_id] = {
            "name": user.full_name or user.username or "Unknown",
            "last_check": today,
            "streak": 1,
            "total_days": 1
        }
        save_data(data)
        await update.message.reply_text(
            f"✅ First day logged!\n Current streak: **1 day**"
        )
        return

    user_data = data[user_id]
    last = user_data["last_check"]
    current_streak = user_data["streak"]
    total = user_data.get("total_days", current_streak)

    last_date = date.fromisoformat(last)
    today_date = date.today()
    diff = (today_date - last_date).days

    if diff == 0:
        await update.message.reply_text(
            f"Already checked in today.\n"
            f" Current streak: **{current_streak} day{'s' if current_streak != 1 else ''}**\n"
            f"Total days: {total}"
        )
    elif diff == 1:
        current_streak += 1
        total += 1
        user_data["last_check"] = today
        user_data["streak"] = current_streak
        user_data["total_days"] = total
        save_data(data)
        await update.message.reply_text(
            f"✅ Day logged!\n"
            f" Current streak: **{current_streak} days**\n"
            f"Total days: {total}"
        )
    else:
        current_streak = 1
        total += 1
        user_data["last_check"] = today
        user_data["streak"] = current_streak
        user_data["total_days"] = total
        save_data(data)
        await update.message.reply_text(
            f"Streak reset (missed {diff-1} day{'s' if diff > 2 else ''}).\n"
            f"✅ New day logged.\n"
            f" Current streak: **1 day**\n"
            f"Total days: {total}"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("streak", streak))
    print("Bot is running... Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()
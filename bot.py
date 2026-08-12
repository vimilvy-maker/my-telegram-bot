import json
import os
from datetime import date, datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

BOT_TOKEN = os.getenv("BOT-TOKEN")  # Uses the variable from Railway
DATA_FILE = "streaks.json"

# Conversation state
WAITING_FOR_DATE = 1


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def streak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Must reply to someone's message
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Reply to someone's message and use /streak to give them a streak."
        )
        return

    target_user = update.message.reply_to_message.from_user
    caller = update.effective_user

    # Prevent giving streak to yourself
    if target_user.id == caller.id:
        await update.message.reply_text("You can't give a streak to yourself.")
        return

    user_id = str(target_user.id)
    today = date.today().isoformat()
    data = load_data()

    if user_id not in data:
        data[user_id] = {
            "name": target_user.full_name or target_user.username or "Unknown",
            "last_check": today,
            "streak": 1,
            "total_days": 1
        }
        save_data(data)
        await update.message.reply_text(
            f"✅ First day logged for {target_user.full_name}!\n"
            f"Current streak: **1 day**"
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
            f"{target_user.full_name} already has a check-in today.\n"
            f"Current streak: **{current_streak} day{'s' if current_streak != 1 else ''}**\n"
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
            f"✅ Day logged for {target_user.full_name}!\n"
            f"Current streak: **{current_streak} days**\n"
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
            f"Streak reset for {target_user.full_name} (missed {diff-1} day{'s' if diff > 2 else ''}).\n"
            f"✅ New day logged.\n"
            f"Current streak: **1 day**\n"
            f"Total days: {total}"
        )


async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me the deadline date in this format:\n\n"
        "<code>YYYY-MM-DD</code>\n\n"
        "Example: <code>2026-08-20</code>",
        parse_mode="HTML"
    )
    return WAITING_FOR_DATE


async def receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()

    try:
        deadline = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text(
            "❌ Wrong format.\nPlease send the date like this:\n<code>2026-08-20</code>",
            parse_mode="HTML"
        )
        return WAITING_FOR_DATE

    data = load_data()

    if user_id not in data:
        data[user_id] = {
            "name": update.effective_user.full_name or update.effective_user.username or "Unknown",
            "last_check": None,
            "streak": 0,
            "total_days": 0,
            "deadline": deadline.isoformat()
        }
    else:
        data[user_id]["deadline"] = deadline.isoformat()

    save_data(data)

    await update.message.reply_text(
        f"✅ Deadline set for <b>{deadline.strftime('%d %B %Y')}</b>",
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def deadline_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    user_data = data.get(user_id)
    if not user_data or "deadline" not in user_data or not user_data["deadline"]:
        await update.message.reply_text(
            "You don't have a deadline set yet.\nUse /set to create one."
        )
        return

    deadline = date.fromisoformat(user_data["deadline"])
    await update.message.reply_text(
        f"Your current deadline is: <b>{deadline.strftime('%d %B %Y')}</b>",
        parse_mode="HTML"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for /set
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set", set_command)],
        states={
            WAITING_FOR_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_date)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("streak", streak))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("deadline", deadline_command))

    print("Bot is running... Press Ctrl+C to stop")
    app.run_polling()


if __name__ == "__main__":
    main()

import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Директория для хранения файлов по штатам
DATA_DIR = "emails_by_state"
os.makedirs(DATA_DIR, exist_ok=True)

# Регулярное выражение для проверки email
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def is_valid_email(email: str) -> bool:
    return re.match(EMAIL_REGEX, email) is not None

def get_state_files() -> list:
    return [f.replace('.txt', '') for f in os.listdir(DATA_DIR) if f.endswith('.txt')]

def add_email_to_state(state: str, email: str):
    file_path = os.path.join(DATA_DIR, f"{state}.txt")
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"{email}\n")

def remove_email_from_state(state: str) -> str:
    file_path = os.path.join(DATA_DIR, f"{state}.txt")
    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return None

    email = lines[0].strip()  # берём первый email
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines[1:])  # записываем остаток

    return email

def count_emails_per_state() -> dict:
    counts = {}
    for state in get_state_files():
        file_path = os.path.join(DATA_DIR, f"{state}.txt")
        with open(file_path, 'r', encoding='utf-8') as f:
            counts[state] = len(f.readlines())
    return counts

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Взять email"), KeyboardButton("Добавить email")],
        [KeyboardButton("Количество email'ов")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать!", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Добавить email":
        await update.message.reply_text(
            "Отправьте email и штат в формате: email|штат\nПример: user@example.com|IL"
        )
        return

    elif text == "Взять email":
        states = get_state_files()
        if not states:
            await update.message.reply_text("Нет доступных email'ов.")
            return

        keyboard = [[KeyboardButton(state)] for state in states]
        keyboard.append([KeyboardButton("Назад")])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите штат:", reply_markup=reply_markup)
        return

    elif text == "Количество email'ов":
        counts = count_emails_per_state()
        if not counts:
            await update.message.reply_text("Нет email'ов в базе.")
        else:
            msg = "\n".join([f"{state} : {count} шт" for state, count in counts.items()])
            await update.message.reply_text(msg)
        return

    elif text == "Назад":
        await start(update, context)
        return

    # Обработка формата email|штат
    elif '|' in text:
        parts = text.split('|', 1)
        email, state = parts[0].strip(), parts[1].strip().upper()

        if not is_valid_email(email):
            await update.message.reply_text("Некорректный email. Попробуйте снова.")
            return

        if not state.isalpha() or len(state) != 2:
            await update.message.reply_text("Штат должен быть двухбуквенным кодом (например, IL).")
            return

        add_email_to_state(state, email)
        await update.message.reply_text(f"Email {email} добавлен в штат {state}.")
        return

    # Обработка выбора штата для взятия email
    elif len(text) == 2 and text.isalpha():
        state = text.upper()
        email = remove_email_from_state(state)
        if email:
            await update.message.reply_text(f"Взятый email из штата {state}: {email}")
        else:
            await update.message.reply_text(f"В штате {state} нет email'ов.")
        return

    else:
        await update.message.reply_text("Неизвестная команда. Используйте кнопки.")

def main():
    TOKEN = "8317792326:AAG9DCx6PEpWqNlILCnD8-55089_S7rqdco"  # Замените на токен вашего бота

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()
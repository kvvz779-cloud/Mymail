import os
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
        return  # ждём ввода без подсказки

    elif text == "Взять email":
        states = get_state_files()
        if not states:
            await update.message.reply_text("Нет доступных email'ов.")
            await start(update, context)
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

    # Обработка списка email (поддерживает & и |)
    elif any(sep in text for sep in ['&', '|']):
        lines = text.split('\n')
        added_count = 0

        for line in lines:
            line = line.strip()
            if not line:  # пропускаем пустые строки
                continue

            sep = '&' if '&' in line else '|'
            parts = line.split(sep, 1)
            if len(parts) != 2:
                continue  # пропускаем строки без разделителя

            email, state = parts[0].strip(), parts[1].strip().upper()

            if not is_valid_email(email):
                continue  # пропускаем некорректные email

            if not state.isalpha() or len(state) != 2:
                continue  # пропускаем некорректные штаты

            add_email_to_state(state, email)
            added_count += 1

        if added_count > 0:
            await update.message.reply_text(f"Добавлено {added_count} email(ов).")
        else:
            await update.message.reply_text("Не найдено корректных записей.")

        await start(update, context)
        return

    # Взятие email — отправляем только кликабельный email через HTML
    elif len(text) == 2 and text.isalpha():
        state = text.upper()
        email = remove_email_from_state(state)
        if email:
            # Используем HTML-режим для безопасной ссылки
            await update.message.reply_text(
                f'<a href="mailto:{email}">{email}</a>',
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text(f"В штате {state} нет email'ов.")

        await start(update, context)
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

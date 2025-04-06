import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import nest_asyncio
import db_manager
from fetch_data import fetch_earthquake_data
from db_manager import (save_earthquakes_to_db, get_all_users, get_new_earthquakes, mark_as_notified, db_connection)
import os
from dotenv import load_dotenv
load_dotenv()

nest_asyncio.apply()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"{user.first_name}, вы подписаны на уведомления о землетрясениях!\n"
        "/help - показать справку\n"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Бот уведомляет о землетрясениях.\n"
        "Команды:\n"
        "/help - показать справку\n"
        "/start - подписаться на уведомления\n"
        "/test - тестовое уведомление\n"
        "/stats - статистика землетрясений\n"
        "/stop - отписаться от уведомлений"
    )


async def fetch_and_save_earthquakes():
    while True:
        try:
            earthquakes = await asyncio.to_thread(fetch_earthquake_data)
            if earthquakes:
                await asyncio.to_thread(save_earthquakes_to_db, earthquakes)
                logger.info("Данные успешно сохранены")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Ошибка получения данных: {str(e)}")
            await asyncio.sleep(300)


async def check_for_new_earthquakes(app):
    while True:
        try:
            new_earthquakes = await asyncio.to_thread(get_new_earthquakes)
            if not new_earthquakes:
                await asyncio.sleep(60)
                continue

            users = await asyncio.to_thread(get_all_users)
            quake_ids = []

            for eq in new_earthquakes:
                eq_id, location, mag, time, url, radius = eq
                quake_ids.append(eq_id)

                message = (
                    f"🚨 Новое землетрясение!\n"
                    f"▫️ Магнитуда: {mag}\n"
                    f"▫️ Место: {location}\n"
                    f"▫️ Время: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"🔗 Подробнее: {url}"
                )

                for chat_id in users:
                    try:
                        await app.bot.send_message(
                            chat_id=chat_id,
                            text=message,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки: {str(e)}")

            if quake_ids:
                await asyncio.to_thread(mark_as_notified, quake_ids)

            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Ошибка проверки землетрясений: {str(e)}")
            await asyncio.sleep(300)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE chat_id = %s;", (chat_id,))
                conn.commit()
    await update.message.reply_text("Вы успешно отписались от уведомлений.")


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_msg = (
        "🚨 [ТЕСТ] Землетрясение!\n"
        "▫️ Магнитуда: 4.5\n"
        "▫️ Место: Test Location\n"
        "▫️ Время: 2024-01-01 12:00:00\n"
        "🔗 Подробнее: example.com"
    )
    await update.message.reply_text(test_msg)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total, max_mag, avg_mag = db_manager.get_stats()
    stats_text = (
        "📊 Статистика землетрясений:\n"
        f"▫️ Всего зарегистрировано: {total}\n"
        f"▫️ Максимальная магнитуда: {max_mag:.1f}\n"
        f"▫️ Средняя магнитуда: {avg_mag:.1f}"
    )
    await update.message.reply_text(stats_text)


async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(CommandHandler("stats", stats_command))

    asyncio.create_task(fetch_and_save_earthquakes())
    asyncio.create_task(check_for_new_earthquakes(application))

    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
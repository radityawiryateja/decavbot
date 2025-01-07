from telegram import Update, Bot
import logging
import re
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Token dan Channel
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = '@decavstore'  # Ganti dengan username channel kamu
ADMIN_GROUP_ID = -1001415535129  # Ganti dengan ID grup admin kamu

bot = Bot(token=BOT_TOKEN)

async def check_subscription(user_id):
    try:
        # Cek apakah user sudah bergabung dengan channel
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

async def start(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        # Abaikan perintah di grup
        return

    user_id = update.effective_user.id
    if await check_subscription(user_id):
        await update.message.reply_text("Halo! Kamu sudah subscribe channel kami. Silakan kirim feedback!")
    else:
        await update.message.reply_text(
            f"Halo! Kamu perlu subscribe channel kami terlebih dahulu untuk menggunakan bot ini.\n"
            f"Silakan subscribe di sini: {CHANNEL_ID}."
        )

async def handle_feedback(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        return

    user_id = update.effective_user.id
    message = update.message.text

    if await check_subscription(user_id):
        feedback_message = (
            f"📩 Feedback baru dari pengguna:\n"
            f"ID: `{user_id}`\n"
            f"Pesan: {message}"
        )
        logger.info(f"Mengirim pesan ke grup admin:\n{feedback_message}")
        await bot.send_message(chat_id=ADMIN_GROUP_ID, text=feedback_message, parse_mode="Markdown")
        await update.message.reply_text("Feedback kamu telah diterima! Terima kasih.")
    else:
        await update.message.reply_text(
            f"Kamu belum subscribe channel kami. Silakan subscribe di sini: {CHANNEL_ID}."
        )


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def handle_admin_reply(update: Update, context: CallbackContext):
    logger.info(f"Pesan diterima di grup admin: {update.message.text}")

    if update.effective_chat.id != ADMIN_GROUP_ID:
        logger.warning("Pesan ini bukan dari grup admin. Abaikan.")
        return

    if update.message.reply_to_message and update.message.reply_to_message.text:
        logger.info("Balasan terdeteksi.")
        original_message = update.message.reply_to_message.text

        # Debugging isi pesan asli
        logger.info(f"Pesan asli (reply_to_message): {original_message}")

        # Cari ID pengguna menggunakan regex
        match = re.search(r"ID:\s*(\d+)", original_message)
        if match:
            try:
                user_id = int(match.group(1))  # Ambil ID dari hasil regex
                admin_reply = update.message.text

                # Kirim balasan ke pengguna
                await bot.send_message(chat_id=user_id, text=f"📬 Balasan dari admin:\n\n{admin_reply}")
                await update.message.reply_text("Balasan telah dikirim ke pengguna.")
            except Exception as e:
                logger.error(f"Kesalahan saat mengirim balasan: {e}")
                await update.message.reply_text(f"Gagal mengirim balasan: {e}")
        else:
            logger.warning("ID pengguna tidak ditemukan dalam pesan asli.")
    else:
        logger.warning("Tidak ada balasan terdeteksi.")





def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Handler untuk perintah /start
    application.add_handler(CommandHandler('start', start))

    # Handler untuk pesan teks di chat pribadi (feedback)
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_feedback))

    # Handler untuk balasan admin di grup
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUP, handle_admin_reply))

    application.add_handler(MessageHandler(filters.TEXT & filters.Chat(ADMIN_GROUP_ID), handle_admin_reply))


    application.run_polling()

if __name__ == '__main__':
    main()

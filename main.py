import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import yt_dlp

# إعدادات التسجيل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# التوكين الخاص بك تم وضعه هنا
TOKEN = '7753317724:AAHUXeuoPc1dR6lQHanq7aWdvkfBk4Xk0Fg'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك! أرسل لي رابط فيديو وسأقوم بتحميله لك.")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data['url'] = url
    keyboard = [
        [InlineKeyboardButton("🎵 صوت (MP3)", callback_data='audio')],
        [InlineKeyboardButton("🎬 فيديو (MP4)", callback_data='video')]
    ]
    await update.message.reply_text("📥 كيف تريد تحميل الملف؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    url = context.user_data.get('url')
    choice = query.data

    await query.edit_message_text("⏳ جارٍ التحميل والمعالجة... يرجى الانتظار.")

    ydl_opts = {
        'outtmpl': 'downloaded_file.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    if choice == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })
    else:
        ydl_opts.update({'format': 'best'})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if choice == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        with open(filename, 'rb') as f:
            if choice == 'audio':
                await context.bot.send_audio(update.effective_chat.id, f, caption="تم التحميل بواسطة بوتك ✅")
            else:
                await context.bot.send_video(update.effective_chat.id, f, caption="تم التحميل بواسطة بوتك ✅")
        
        os.remove(filename) 

    except Exception as e:
        await context.bot.send_message(update.effective_chat.id, f"❌ عذراً، حدث خطأ: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("البوت يعمل الآن...")
    app.run_polling()

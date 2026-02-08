import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp

# ------------------- KEEP ALIVE -------------------
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot is alive"

def run():
    app_flask.run(host='0.0.0.0', port=10000)

threading.Thread(target=run).start()
# -------------------------------------------------

# توكن البوت الجديد
TOKEN = "7753317724:AAH7J21jgZKEln8uFrnwUAPOfEG2MMLIq-U"

user_links = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط الفيديو")

# استقبال الرابط
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    user_links[update.message.chat_id] = link

    keyboard = [
        [InlineKeyboardButton("240p", callback_data="240")],
        [InlineKeyboardButton("360p", callback_data="360")],
        [InlineKeyboardButton("720p", callback_data="720")],
        [InlineKeyboardButton("1080p", callback_data="1080")]
    ]

    await update.message.reply_text(
        "اختر الدقة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# تحميل الفيديو وإرساله كملف Document
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    resolution = query.data
    url = user_links.get(chat_id)

    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': 'video.%(ext)s'
    }

    await query.message.reply_text("جاري التحميل...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # إرسال كملف Document (لحل مشكلة الحجم)
    for file in os.listdir():
        if file.startswith("video."):
            await query.message.reply_document(document=open(file, 'rb'))
            os.remove(file)

# إنشاء التطبيق
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(download_video))

# تشغيل البوت
app.run_polling()

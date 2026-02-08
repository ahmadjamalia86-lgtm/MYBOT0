import os
import asyncio
import threading
import uuid
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- خادم صغير لمنع النوم (Flask) ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "البوت يعمل بنجاح!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

# --- إعدادات التحميل ---
def download_video(url, resolution, file_id):
    if resolution == 'audio':
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{file_id}.mp3',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
            'quiet': True
        }
    else:
        # محاولة جلب فيديو مدمج مسبقاً لتقليل الضغط على الرام
        opts = {
            'format': f'bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[height<={resolution}][ext=mp4]/best',
            'outtmpl': f'{file_id}.mp4',
            'quiet': True,
            'max_filesize': 48 * 1024 * 1024  # حد 48 ميجا ليقبله تلجرام
        }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            ext = 'mp3' if resolution == 'audio' else 'mp4'
            return f"{file_id}.{ext}"
    except Exception as e:
        print(f"Error: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" in url:
        context.user_data['url'] = url
        keyboard = [
            [InlineKeyboardButton("📺 1080p", callback_data='1080'), InlineKeyboardButton("📺 720p", callback_data='720')],
            [InlineKeyboardButton("📺 480p", callback_data='480'), InlineKeyboardButton("📺 360p", callback_data='360')],
            [InlineKeyboardButton("📺 240p", callback_data='240'), InlineKeyboardButton("🎵 MP3", callback_data='audio')]
        ]
        await update.message.reply_text("🎬 اختر الدقة المطلوبة:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = query.data
    url = context.user_data.get('url')
    
    status_msg = await query.edit_message_text(f"⏳ جاري التحميل بدقة {res}... يرجى الانتظار.")
    file_id = str(uuid.uuid4())
    
    file_path = await asyncio.to_thread(download_video, url, res, file_id)
    
    if file_path and os.path.exists(file_path):
        await query.message.reply_text("✅ تم التحميل، جاري الرفع إلى تلجرام...")
        with open(file_path, 'rb') as f:
            if res == 'audio': await query.message.reply_audio(audio=f)
            else: await query.message.reply_video(video=f)
        os.remove(file_path)
        await status_msg.delete()
    else:
        await query.edit_message_text("❌ فشل التحميل. الأسباب المحتملة:\n1. حجم الملف أكبر من 50MB.\n2. السيرفر المجاني استهلك الذاكرة.\n3. الدقة غير متوفرة.")

def main():
    token = os.getenv('BOT_TOKEN')
    if not token: return
    
    keep_alive() # تشغيل ميزة منع النوم
    
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == '__main__':
    main()

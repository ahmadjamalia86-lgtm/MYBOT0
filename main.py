import os
import asyncio
import threading
import uuid
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- 1. خادم Flask لإبقاء البوت مستيقظاً ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "I am alive!"

def run_flask():
    app_flask.run(host='0.0.0.0', port=10000)

# --- 2. دالة التحميل الذكية ---
def download_video(url, res_key, file_id):
    # إعدادات مرنة: إذا ما لقى الجودة المطلوبة بياخد اللي تحتها فوراً
    if res_key == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{file_id}.mp3',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        }
    else:
        ydl_opts = {
            'format': f'bestvideo[height<={res_key}][ext=mp4]+bestaudio[ext=m4a]/best[height<={res_key}]/best',
            'outtmpl': f'{file_id}.mp4',
            'max_filesize': 48 * 1024 * 1024, # حد 48 ميجا عشان تلجرام
            'merge_output_format': 'mp4',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            # البحث عن الملف الناتج (لأن اللاحقة قد تختلف)
            for f in os.listdir('.'):
                if f.startswith(file_id):
                    return f
        return None
    except Exception as e:
        print(f"Error logic: {e}")
        return None

# --- 3. معالجة الرسائل والأزرار ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" in url:
        context.user_data['url'] = url
        keyboard = [
            [InlineKeyboardButton("📺 1080p", callback_data='1080'), InlineKeyboardButton("📺 720p", callback_data='720')],
            [InlineKeyboardButton("📺 480p", callback_data='480'), InlineKeyboardButton("📺 360p", callback_data='360')],
            [InlineKeyboardButton("📺 240p", callback_data='240'), InlineKeyboardButton("🎵 MP3", callback_data='audio')]
        ]
        await update.message.reply_text("🎬 اختر الجودة المطلوبة للتحميل:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = query.data
    url = context.user_data.get('url')
    
    if not url:
        await query.edit_message_text("❌ حدث خطأ، أرسل الرابط مرة أخرى.")
        return

    msg = await query.edit_message_text(f"⏳ جاري تجهيز الطلب ({res})... انتظر قليلاً.")
    file_id = str(uuid.uuid4())
    
    # التحميل في خلفية منفصلة عشان البوت ما يعلق
    file_path = await asyncio.to_thread(download_video, url, res, file_id)
    
    if file_path and os.path.exists(file_path):
        try:
            await query.message.reply_text("✅ تم التحميل! جاري الرفع لتلجرام...")
            with open(file_path, 'rb') as f:
                if res == 'audio': await query.message.reply_audio(audio=f)
                else: await query.message.reply_video(video=f)
            os.remove(file_path) # حذف الملف بعد الرفع لتوفير المساحة
        except Exception as e:
            await query.message.reply_text("❌ فشل الرفع. قد يكون الملف كبيراً جداً.")
    else:
        await query.edit_message_text("❌ فشل التحميل. تأكد أن الفيديو ليس طويلاً جداً (أقل من 50MB) أو جرب جودة أقل.")

# --- 4. تشغيل البوت ---
def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("Error: BOT_TOKEN not found!")
        return

    # تشغيل Flask في Thread منفصل لمنع النوم
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    main()

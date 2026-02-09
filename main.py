import os
import asyncio
import threading
import uuid
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# --- 1. خادم Flask لمنع البوت من النوم ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    # تشغيل سيرفر وهمي لإبقاء البوت متصلاً
    app.run(host='0.0.0.0', port=10000)

# --- 2. دالة التحميل الاحترافية ---
def download_video(url, quality):
    # إنشاء اسم عشوائي للملف لتجنب التضارب
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.mp4"
    
    # إعدادات التحميل
    ydl_opts = {
        'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
        'outtmpl': filename,
        'geo_bypass': True,  # لتجاوز الحظر الجغرافي
        'noplaylist': True,  # تحميل فيديو واحد فقط وليس قائمة
        'quiet': True,
        'max_filesize': 49 * 1024 * 1024, # حد أقصى 49 ميجا (تلجرام لا يقبل أكثر من 50 للبوتات)
        'merge_output_format': 'mp4',
        # تحسينات لدعم انستغرام وفيسبوك
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    # إعدادات خاصة للصوت فقط
    if quality == 'audio':
        filename = f"{file_id}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{file_id}.%(ext)s",
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # التأكد من وجود الملف الناتج
        if os.path.exists(filename):
            return filename
        # محاولة البحث عن الملف إذا تغيرت الصيغة (مثلا mkv)
        for f in os.listdir('.'):
            if f.startswith(file_id):
                return f
        return None
    except Exception as e:
        print(f"Error downloading: {e}")
        return None

# --- 3. التعامل مع رسائل المستخدم ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # التحقق من أن النص هو رابط
    if "http" in url:
        context.user_data['url'] = url
        # لوحة الأزرار للجودات المختلفة
        keyboard = [
            [InlineKeyboardButton("💎 1080p", callback_data='1080'), InlineKeyboardButton("💿 720p", callback_data='720')],
            [InlineKeyboardButton("📺 480p", callback_data='480'), InlineKeyboardButton("📱 360p", callback_data='360')],
            [InlineKeyboardButton("📉 240p", callback_data='240'), InlineKeyboardButton("🎵 MP3 (صوت)", callback_data='audio')]
        ]
        await update.message.reply_text(
            "🎬 *تم استلام الرابط!*\nاختر الجودة المطلوبة للتحميل:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("مرحباً! أرسل لي رابط فيديو (يوتيوب، فيسبوك، انستغرام..) وسأقوم بتحميله لك.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    quality = query.data
    url = context.user_data.get('url')
    
    if not url:
        await query.edit_message_text("❌ انتهت صلاحية الجلسة، أرسل الرابط مرة أخرى.")
        return

    status_msg = await query.edit_message_text(f"⏳ *جاري التحميل بدقة {quality}...*\nقد يستغرق الأمر وقتاً حسب حجم الفيديو وسرعة السيرفر.", parse_mode='Markdown')

    # تشغيل التحميل في خيط منفصل (Thread) لعدم تجميد البوت
    file_path = await asyncio.to_thread(download_video, url, quality)

    if file_path and os.path.exists(file_path):
        try:
            await status_msg.edit_text("🚀 جاري الرفع إلى تلجرام...")
            
            with open(file_path, 'rb') as f:
                if quality == 'audio':
                    await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, title="Downloaded Audio", write_timeout=120)
                else:
                    await context.bot.send_video(chat_id=query.message.chat_id, video=f, caption="✅ تم التحميل بواسطة بوتك", write_timeout=120)
            
            # تنظيف الملف بعد الإرسال
            os.remove(file_path)
            await status_msg.delete()
            
        except Exception as e:
            error_text = str(e)
            if "Request Entity Too Large" in error_text:
                await status_msg.edit_text("❌ عذراً، حجم الفيديو أكبر من 50 ميجابايت (حدود تلجرام للبوتات). حاول اختيار جودة أقل.")
            else:
                await status_msg.edit_text(f"❌ حدث خطأ أثناء الرفع: {error_text}")
            # تنظيف الملف حتى لو فشل الرفع
            if os.path.exists(file_path): os.remove(file_path)
    else:
        await status_msg.edit_text("❌ فشل التحميل.\n\nالأسباب المحتملة:\n1. الفيديو خاص (Private).\n2. الفيديو طويل جداً أو حجمه ضخم.\n3. قيود من الموقع المصدر.")

# --- 4. التشغيل الرئيسي ---
def main():
    # الحصول على التوكن
    token = os.getenv('BOT_TOKEN')
    
    if not token:
        print("خطأ: لم يتم العثور على BOT_TOKEN في الإعدادات!")
        return

    # تشغيل سيرفر Flask في الخلفية
    threading.Thread(target=run_flask, daemon=True).start()

    # إعداد البوت
    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    application.add_handler(CallbackQueryHandler(button_click))

    print("Bot is starting...")
    # تشغيل البوت مع السماح بالتحديثات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

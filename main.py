import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp
import uuid

# قراءة التوكين من إعدادات Render
TOKEN = os.getenv('BOT_TOKEN')

# دالة التحميل (تعمل في الخلفية)
def run_yt_dlp(url, quality_setting):
    # تحديد خيارات الجودة
    if quality_setting == 'audio':
        # خيارات الصوت فقط (تحويل لـ MP3)
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{uuid.uuid4()}.%(ext)s',  # اسم عشوائي لمنع تداخل الملفات
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
    elif quality_setting == 'low':
        # خيارات جودة منخفضة (لتوفير الباقة)
        ydl_opts = {
            'format': 'worst[ext=mp4]/worst',
            'outtmpl': f'{uuid.uuid4()}.%(ext)s',
            'quiet': True,
        }
    else:
        # خيارات جودة عالية (الوضع الافتراضي)
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'{uuid.uuid4()}.%(ext)s',
            'quiet': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # إرجاع اسم الملف الذي تم تحميله
            if quality_setting == 'audio':
                return ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"Download Error: {e}")
        return None

# 1. استقبال الرابط وعرض الأزرار
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" in url:
        # حفظ الرابط مؤقتاً لنعرفه عند ضغط الزر
        context.user_data['current_url'] = url
        
        # تصميم الأزرار
        keyboard = [
            [InlineKeyboardButton("🎬 جودة عالية (HD)", callback_data='high')],
            [InlineKeyboardButton("📉 جودة متوسطة", callback_data='low')],
            [InlineKeyboardButton("🎵 صوت فقط (MP3)", callback_data='audio')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("🎥 اختر الجودة المطلوبة:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("أرسل رابط فيديو صالح من فضلك.")

# 2. تنفيذ الأمر عند ضغط الزر
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # تأكيد الضغط
    
    choice = query.data
    url = context.user_data.get('current_url')
    
    if not url:
        await query.edit_message_text("❌ انتهت صلاحية الجلسة، أرسل الرابط مجدداً.")
        return

    await query.edit_message_text(f"⏳ جاري التحميل... ({choice})")
    
    # تشغيل التحميل
    file_path = await asyncio.to_thread(run_yt_dlp, url, choice)
    
    if file_path and os.path.exists(file_path):
        await query.message.reply_text("🚀 جاري الرفع...")
        try:
            with open(file_path, 'rb') as f:
                if choice == 'audio':
                    await query.message.reply_audio(audio=f, title="Audio Clip")
                else:
                    await query.message.reply_video(video=f)
        except Exception as e:
            await query.message.reply_text("حدث خطأ أثناء الإرسال، حجم الملف قد يكون كبيراً جداً.")
        finally:
            # حذف الملف من السيرفر لتوفير المساحة
            os.remove(file_path)
    else:
        await query.message.reply_text("❌ فشل التحميل. تأكد أن الرابط عام وليس خاصاً.")

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN is missing!")
        return
        
    app = Application.builder().token(TOKEN).build()
    
    # ربط الوظائف
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

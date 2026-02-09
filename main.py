import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp
import asyncio
from pathlib import Path

# إعدادات البوت
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ لم يتم تعيين متغير البيئة BOT_TOKEN")

QUALITY_OPTIONS = {
    "360p": "worst",
    "480p": "18",
    "720p": "22",
    "1080p": "18+137"
}

# تفعيل السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء مجلد مؤقت
TEMP_DIR = Path("/tmp/bot_downloads")
TEMP_DIR.mkdir(exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر البداية"""
    welcome_message = '''
    👋 مرحباً بك في بوت تحميل الفيديوهات!
    
    📹 المميزات:
    ✅ تحميل من YouTube و Instagram و Facebook و TikTok
    ✅ خيارات جودة متعددة (360p, 480p, 720p, 1080p)
    ✅ تحميل سريع وآمن
    
    📌 الاستخدام:
    أرسل لي أي رابط فيديو وسأطلب منك اختيار الجودة المفضلة
    
    ⚠️ ملاحظة: قد يستغرق التحميل بعض الوقت حسب حجم الفيديو
    '''
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج أمر المساعدة"""
    help_text = '''
    🆘 تعليمات الاستخدام:
    
    1️⃣ أرسل رابط الفيديو من أي منصة:
       • YouTube
       • Instagram
       • Facebook
       • TikTok
    
    2️⃣ اختر جودة الفيديو المفضلة
    
    3️⃣ سيتم تحميل الفيديو وإرساله إليك
    
    💡 النصائح:
    • استخدم أقل جودة للملفات الكبيرة
    • قد يستغرق التحميل وقتاً - كن صبوراً
    • تأكد من أن الفيديو متاح للتحميل
    '''
    await update.message.reply_text(help_text)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الروابط المرسلة"""
    url = update.message.text.strip()
    
    # التحقق من صحة الرابط
    if not is_valid_url(url):
        await update.message.reply_text(
            "❌ الرابط غير صحيح.\n\n"
            "الرجاء إرسال رابط صحيح من:\n"
            "🔗 YouTube\n"
            "📷 Instagram\n"
            "👤 Facebook\n"
            "🎵 TikTok"
        )
        return
    
    # عرض خيارات الجودة
    keyboard = [
        [InlineKeyboardButton("360p 📱", callback_data=f"quality_360p_{url}"),
         InlineKeyboardButton("480p 📺", callback_data=f"quality_480p_{url}")],
        [InlineKeyboardButton("720p 🎬", callback_data=f"quality_720p_{url}"),
         InlineKeyboardButton("1080p 🎥", callback_data=f"quality_1080p_{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📊 اختر جودة الفيديو المفضلة:", reply_markup=reply_markup)

async def quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج اختيار الجودة"""
    query = update.callback_query
    await query.answer()
    
    # استخراج الجودة والرابط
    data_parts = query.data.split("_", 2)
    quality = data_parts[1]
    url = data_parts[2]
    
    # إرسال رسالة "جاري التحميل"
    status_message = await query.edit_message_text(
        text=f"⏳ جاري تحميل الفيديو بجودة {quality}...\n"
             "قد يستغرق بعض الوقت..."
    )
    
    try:
        # تحميل الفيديو
        video_path = await download_video(url, quality)
        
        if video_path and os.path.exists(video_path):
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # تحويل لـ MB
            
            # التحقق من حد الحجم (50 MB لـ Telegram)
            if file_size > 50:
                await status_message.edit_text(
                    f"❌ حجم الملف ({file_size:.2f} MB) أكبر من الحد المسموح به (50 MB)\n"
                    "جرب جودة أقل"
                )
                os.remove(video_path)
                return
            
            # إرسال الفيديو
            await status_message.edit_text("📤 جاري إرسال الفيديو...")
            
            with open(video_path, 'rb') as video:
                await query.message.reply_video(
                    video,
                    caption=f"✅ تم التحميل بنجاح!\n\n"
                            "الجودة: {quality}\n"
                            "الحجم: {file_size:.2f} MB"
                )
            
            # حذف الملف المؤقت
            os.remove(video_path)
            await status_message.delete()
            
        else:
            await status_message.edit_text(
                "❌ فشل تحميل الفيديو\n\n"
                "الأسباب المحتملة:\n"
                "• الرابط غير صحيح\n"
                "• الفيديو محذوف أو خاص\n"
                "• مشاكل في الاتصال\n\n"
                "جرب رابط آخر"
            )
        
    except Exception as e:
        logger.error(f"خطأ في التحميل: {str(e)}")
        error_msg = str(e)[:100]  # أول 100 حرف من الخطأ
        await status_message.edit_text(
            f"❌ حدث خطأ أثناء التحميل:\n\n"
            f"`{error_msg}`\n\n"
            f"جرب مع رابط آخر"
        )

async def download_video(url: str, quality: str) -> str:
    """تحميل الفيديو باستخدام yt-dlp"""
    import uuid
    
    # توليد اسم فريد للملف
    unique_id = str(uuid.uuid4())[:8]
    output_path = TEMP_DIR / f"video_{unique_id}.mp4"
    
    ydl_opts = {
        'format': QUALITY_OPTIONS.get(quality, "best"),
        'outtmpl': str(output_path),
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"جاري تحميل: {url} بجودة {quality}")
            ydl.download([url])
        
        return str(output_path)
    
    except Exception as e:
        logger.error(f"خطأ في yt-dlp: {str(e)}")
        # محاولة البحث عن ملف تم إنشاؤه حتى لو حدث خطأ
        for file in TEMP_DIR.glob(f"video_{unique_id}*"):
            return str(file)
        raise

def is_valid_url(url: str) -> bool:
    """التحقق من صحة الرابط"""
    valid_domains = [
        'youtube.com', 'youtu.be',
        'instagram.com', 'ig.com',
        'fb.watch', 'facebook.com', 'fb.com',
        'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in valid_domains)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logger.error(msg="خطأ في البوت:", exc_info=context.error)
    if update and update.message:
        await update.message.reply_text(
            "❌ حدث خطأ غير متوقع.\n\n"
            "الرجاء حاول مرة أخرى لاحقاً"
        )

def main():
    """تشغيل البوت"""
    application = Application.builder().token(TOKEN).build()
    
    # أضف المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(quality_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_error_handler(error_handler)
    
    # ابدأ البوت
    logger.info("🤖 البوت قيد التشغيل...")
    application.run_polling()

if __name__ == '__main__':
    main()
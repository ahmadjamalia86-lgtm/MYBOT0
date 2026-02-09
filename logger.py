"""
نظام السجلات للبوت
Logging system for the bot
"""

import logging
from pathlib import Path
from config import LOG_DIR

# إنشاء مجلد السجلات
LOG_DIR.mkdir(parents=True, exist_ok=True)

# إعداد صيغة السجل
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOG_DIR / 'bot.log'

# إنشاء logger
logger = logging.getLogger('MYBOT')
logger.setLevel(logging.INFO)

# معالج الملف
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# معالج الكونسول
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# إضافة المعالجات
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_logger(name):
    """الحصول على logger بتسمية محددة"""
    return logging.getLogger(f'MYBOT.{name}')
"""
دوال مساعدة للبوت
Utility functions for the bot
"""

import os
import uuid
from pathlib import Path
from config import SUPPORTED_PLATFORMS, TEMP_DIR
import yt_dlp
from logger import get_logger

logger = get_logger('utils')

def is_valid_url(url: str) -> bool:
    """
    التحقق من صحة الرابط
    Check if the URL is valid and from a supported platform
    """
    url_lower = url.lower()
    
    for platform, domains in SUPPORTED_PLATFORMS.items():
        for domain in domains:
            if domain in url_lower:
                logger.info(f"رابط صحيح من {platform}")
                return True
    
    return False

def get_platform_name(url: str) -> str:
    """
    الحصول على اسم المنصة من الرابط
    Get the platform name from the URL
    """
    url_lower = url.lower()
    
    for platform, domains in SUPPORTED_PLATFORMS.items():
        for domain in domains:
            if domain in url_lower:
                return platform
    
    return "unknown"

def format_file_size(size_bytes: int) -> str:
    """
    تنسيق حجم الملف لعرضه بشكل قراءة
    Format file size in human-readable format
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"

def cleanup_old_files(max_age_hours: int = 24):
    """
    حذف الملفات القديمة
    Clean up old temporary files
    """
    import time
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for file_path in TEMP_DIR.glob("video_*"):
        file_age = current_time - os.path.getmtime(file_path)
        if file_age > max_age_seconds:
            try:
                os.remove(file_path)
                logger.info(f"تم حذف الملف القديم: {file_path}")
            except Exception as e:
                logger.error(f"خطأ في حذف الملف: {e}")

def validate_bot_token(token: str) -> bool:
    """
    التحقق من صحة التوكن
    Validate bot token format
    """
    if not token:
        return False
    
    parts = token.split(':')
    return len(parts) == 2 and len(parts[0]) > 0 and len(parts[1]) > 0
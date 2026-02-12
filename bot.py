#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على التوكن من متغيرات البيئة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    logger.error("خطأ: TELEGRAM_BOT_TOKEN غير موجود!")
    exit(1)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    logger.info(f"تم استقبال /start من {update.effective_user.first_name}")
    await update.message.reply_text(
        f"مرحباً {update.effective_user.first_name}! 👋\n"
        "أنا بوت مساعد جامعة جلوفيوني الذكي.\n"
        "كيف يمكنني مساعدتك؟"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /help"""
    logger.info(f"تم استقبال /help من {update.effective_user.first_name}")
    help_text = """
الأوامر المتاحة:
/start - بدء المحادثة
/help - عرض هذه الرسالة
/about - معلومات عن البوت
"""
    await update.message.reply_text(help_text)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /about"""
    logger.info(f"تم استقبال /about من {update.effective_user.first_name}")
    await update.message.reply_text(
        "🤖 بوت مساعد جامعة جلوفيوني الذكي\n"
        "الإصدار: 1.0\n"
        "مطور بواسطة: فريق جلوفيوني"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الرسائل النصية"""
    logger.info(f"رسالة من {update.effective_user.first_name}: {update.message.text}")
    await update.message.reply_text(
        f"شكراً على رسالتك: {update.message.text}\n"
        "سيتم معالجتها قريباً!"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء"""
    logger.error(f"خطأ: {context.error}")

def main():
    """تشغيل البوت"""
    logger.info("🚀 بدء تشغيل البوت...")
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # إضافة معالجات الأوامر
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        
        # معالج الرسائل النصية
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # معالج الأخطاء
        application.add_error_handler(error_handler)
        
        logger.info("✅ البوت جاهز! بدء استقبال الرسائل...")
        
        # تشغيل البوت باستخدام Polling
        application.run_polling(
            allowed_updates=None,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ خطأ حرج: {e}")
        exit(1)

if __name__ == '__main__':
    main()

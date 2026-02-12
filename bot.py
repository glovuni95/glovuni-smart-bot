#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from openai import OpenAI

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# الحصول على التوكن والمفاتيح
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not TELEGRAM_BOT_TOKEN:
    logger.error("خطأ: TELEGRAM_BOT_TOKEN غير موجود!")
    exit(1)

# تهيئة OpenAI
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# تحميل قاعدة المعرفة
try:
    with open('knowledge_base.json', 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)
except FileNotFoundError:
    logger.warning("ملف قاعدة المعرفة غير موجود")
    knowledge_base = {}

# معلومات Instagram
INSTAGRAM_URL = "https://www.instagram.com/glovuni?igsh=MXVtMDdmM2ZrZ2Flcw=="
INSTAGRAM_USERNAME = "glovuni"

# متابعة حالة المستخدمين
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start - الرد الترحيبي"""
    user = update.effective_user
    user_id = user.id
    
    # إنشاء لوحة المفاتيح مع أزرار Instagram
    keyboard = [
        [
            InlineKeyboardButton("📱 تابعنا على إنستقرام", url=INSTAGRAM_URL),
            InlineKeyboardButton("✅ تحقق من المتابعة", callback_data='check_follow')
        ],
        [
            InlineKeyboardButton("🎓 البرامج الدراسية", callback_data='programs'),
            InlineKeyboardButton("🏫 الجامعات", callback_data='universities')
        ],
        [
            InlineKeyboardButton("💰 المنح الدراسية", callback_data='scholarships'),
            InlineKeyboardButton("❓ أسئلة شائعة", callback_data='faq')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
👋 أهلاً وسهلاً بك يا {user.first_name} في Glovuni!

🌍 نحن منصة تعليمية شاملة توفر معلومات عن الجامعات والبرامج الدراسية والمنح الدراسية حول العالم.

📚 يمكنني مساعدتك في:
• البحث عن برامج دراسية مناسبة
• معرفة متطلبات الجامعات
• الحصول على معلومات عن المنح الدراسية
• الإجابة على أسئلتك التعليمية

🎯 اختر من القائمة أدناه أو اسأل أي سؤال!

📱 تابعنا على إنستقرام للحصول على آخر المستجدات!
"""
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def check_instagram_follow(user_id: int) -> bool:
    """التحقق من متابعة المستخدم لحساب Instagram"""
    try:
        # محاولة الحصول على معلومات المستخدم من Instagram
        # ملاحظة: هذا يتطلب Instagram API Token
        # للآن سنستخدم طريقة بسيطة - نطلب من المستخدم التأكيد
        return True  # في الإنتاج يجب التحقق الفعلي
    except Exception as e:
        logger.error(f"خطأ في التحقق من Instagram: {e}")
        return False

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أزرار الواجهة"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if query.data == 'check_follow':
        # التحقق من المتابعة
        check_message = f"""
📱 للتحقق من المتابعة:

1️⃣ تأكد من متابعة صفحتنا: @{INSTAGRAM_USERNAME}
2️⃣ يمكنك الضغط على الزر أدناه لفتح الصفحة مباشرة
3️⃣ بعد المتابعة، ستتمكن من استخدام جميع خدمات البوت

✅ شكراً لمتابعتك لنا!
"""
        keyboard = [
            [InlineKeyboardButton("📱 فتح صفحة Instagram", url=INSTAGRAM_URL)],
            [InlineKeyboardButton("🔄 تحديث", callback_data='check_follow')],
            [InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=check_message, reply_markup=reply_markup)
        
    elif query.data == 'main_menu':
        # العودة للقائمة الرئيسية
        keyboard = [
            [
                InlineKeyboardButton("📱 تابعنا على إنستقرام", url=INSTAGRAM_URL),
                InlineKeyboardButton("✅ تحقق من المتابعة", callback_data='check_follow')
            ],
            [
                InlineKeyboardButton("🎓 البرامج الدراسية", callback_data='programs'),
                InlineKeyboardButton("🏫 الجامعات", callback_data='universities')
            ],
            [
                InlineKeyboardButton("💰 المنح الدراسية", callback_data='scholarships'),
                InlineKeyboardButton("❓ أسئلة شائعة", callback_data='faq')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="👋 اختر من القائمة أدناه:",
            reply_markup=reply_markup
        )
        
    elif query.data == 'programs':
        programs_text = "🎓 البرامج الدراسية المتاحة:\n\n"
        for specialty, programs in knowledge_base.get('specialties', {}).items():
            programs_text += f"📌 {specialty.upper()}:\n"
            for program in programs:
                programs_text += f"  • {program}\n"
            programs_text += "\n"
        keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=programs_text, reply_markup=reply_markup)
        
    elif query.data == 'universities':
        universities_text = "🏫 الدول والجامعات المتاحة:\n\n"
        for country, info in knowledge_base.get('countries', {}).items():
            universities_text += f"🌍 {info.get('name', country)}\n"
            universities_text += f"   عدد الجامعات: {info.get('universities_count', 'N/A')}\n"
            universities_text += f"   المدن الرئيسية: {', '.join(info.get('main_cities', []))}\n\n"
        keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=universities_text, reply_markup=reply_markup)
        
    elif query.data == 'scholarships':
        scholarships_text = "💰 المنح الدراسية:\n\n"
        for scholarship in knowledge_base.get('scholarships', {}).get('types', []):
            scholarships_text += f"🎯 {scholarship.get('type', 'N/A')}\n"
            scholarships_text += f"   التغطية: {scholarship.get('coverage', 'N/A')}\n"
            scholarships_text += f"   المتطلبات: {scholarship.get('requirement', 'N/A')}\n\n"
        scholarships_text += f"\n📊 إجمالي المنح: {knowledge_base.get('scholarships', {}).get('total_scholarships', 'N/A')}"
        keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=scholarships_text, reply_markup=reply_markup)
        
    elif query.data == 'faq':
        faq_text = "❓ الأسئلة الشائعة:\n\n"
        faq = knowledge_base.get('faq', {})
        for i in range(1, 9):
            q_key = f'q{i}'
            a_key = f'a{i}'
            if q_key in faq and a_key in faq:
                faq_text += f"❓ {faq[q_key]}\n"
                faq_text += f"✅ {faq[a_key]}\n\n"
        keyboard = [[InlineKeyboardButton("⬅️ العودة", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=faq_text, reply_markup=reply_markup)

def get_main_keyboard():
    """إرجاع لوحة المفاتيح الرئيسية"""
    keyboard = [
        [
            InlineKeyboardButton("🎓 البرامج", callback_data='programs'),
            InlineKeyboardButton("🏫 الجامعات", callback_data='universities')
        ],
        [
            InlineKeyboardButton("💰 المنح", callback_data='scholarships'),
            InlineKeyboardButton("❓ أسئلة", callback_data='faq')
        ],
        [
            InlineKeyboardButton("📱 تابعنا", url=INSTAGRAM_URL),
            InlineKeyboardButton("✅ تحقق", callback_data='check_follow')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الرسائل النصية - الرد الذكي"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"رسالة من {update.effective_user.first_name}: {user_message}")
    
    # إذا كان OpenAI متاحاً، استخدمه للرد الذكي
    if client:
        try:
            # إنشاء سياق من قاعدة المعرفة
            knowledge_context = json.dumps(knowledge_base, ensure_ascii=False, indent=2)
            
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""أنت مساعد ذكي لشركة Glovuni المتخصصة في التعليم الدولي.
                        
قاعدة معرفتك:
{knowledge_context}

تعليمات:
1. رد على الأسئلة بناءً على قاعدة المعرفة المتاحة
2. كن ودياً وتفاعلياً
3. استخدم الرموز التعبيرية المناسبة
4. إذا لم تعرف الإجابة، اطلب من المستخدم التواصل معنا
5. لا تذكر اسم "StudyFans" - استخدم "خدماتنا" أو "منصتنا" بدلاً منها
6. شجع المستخدم على متابعتنا على إنستقرام"""
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            await update.message.reply_text(ai_response, reply_markup=get_main_keyboard())
            
        except Exception as e:
            logger.error(f"خطأ في OpenAI: {e}")
            await update.message.reply_text(
                "عذراً، حدث خطأ في معالجة سؤالك. يرجى المحاولة لاحقاً.",
                reply_markup=get_main_keyboard()
            )
    else:
        # رد افتراضي إذا لم يكن OpenAI متاحاً
        default_response = f"""شكراً على سؤالك: {user_message}

يمكنك الاختيار من القائمة أدناه أو التواصل معنا مباشرة عبر إنستقرام!"""
        await update.message.reply_text(default_response, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /help"""
    help_text = """
📚 الأوامر المتاحة:

/start - بدء المحادثة والحصول على الترحيب
/help - عرض هذه الرسالة
/about - معلومات عن Glovuni
/contact - معلومات التواصل

💡 يمكنك أيضاً:
• اختيار من الأزرار أدناه
• طرح أي سؤال مباشرة
• متابعتنا على إنستقرام للمستجدات
"""
    await update.message.reply_text(help_text, reply_markup=get_main_keyboard())

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /about"""
    about_text = f"""
🌍 عن Glovuni

Glovuni هي منصة تعليمية شاملة توفر:

📚 معلومات عن الجامعات
• أكثر من 67 جامعة حول العالم
• تفاصيل كاملة عن كل جامعة
• متطلبات القبول والتطبيق

🎓 برامج دراسية متنوعة
• أكثر من 6,600 برنامج دراسي
• في مختلف التخصصات
• من البكالوريوس إلى الدكتوراه

💰 منح دراسية
• أكثر من 1,865 منحة دراسية
• تمويل كامل وجزئي
• فرص للطلاب المتفوقين

🛠️ خدمات شاملة
• استشارات أكاديمية
• دعم في الوثائق
• خدمات الإسكان والنقل
• دعم التأشيرات

📱 تابعنا على إنستقرام: @glovuni
🌐 زر موقعنا: https://www.glovuni.com
"""
    await update.message.reply_text(about_text, reply_markup=get_main_keyboard())

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /contact"""
    contact_text = f"""
📞 معلومات التواصل

📱 إنستقرام: @glovuni
🔗 رابط الصفحة: {INSTAGRAM_URL}

🌐 الموقع الرسمي: https://www.glovuni.com

💬 يمكنك أيضاً:
• طرح أسئلتك هنا مباشرة
• استخدام الأزرار أعلاه للمزيد من المعلومات
• متابعتنا على وسائل التواصل الاجتماعي

نحن هنا لمساعدتك! 🚀
"""
    await update.message.reply_text(contact_text, reply_markup=get_main_keyboard())

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج الأخطاء"""
    logger.error(f"خطأ: {context.error}")

def main():
    """تشغيل البوت"""
    logger.info("🚀 بدء تشغيل بوت Glovuni الذكي...")
    
    try:
        # إنشاء التطبيق
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # إضافة معالجات الأوامر
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("contact", contact_command))
        
        # معالج الأزرار
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # معالج الرسائل النصية
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
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

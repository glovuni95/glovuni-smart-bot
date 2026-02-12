#!/usr/bin/env python3
"""
Glovuni Smart Bot - نسخة محسّنة مع Google Sheets و WhatsApp و OpenAI
"""
import logging
import sys
import os
import json
import gspread
import requests
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from openai import OpenAI

# --- الإعدادات العامة ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- المتغيرات من متغيرات البيئة ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
WHATSAPP_PHONE_NUMBER = os.environ.get("WHATSAPP_PHONE_NUMBER", "+962781460847")
WHATSAPP_API_URL = os.environ.get("WHATSAPP_API_URL", "")  # سيتم تعيينه لاحقاً
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN", "")  # سيتم تعيينه لاحقاً

INSTAGRAM_URL = "https://www.instagram.com/glovuni/"
PORT = int(os.environ.get('PORT', 8000))
HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME", "glovuni-bot")
RAILWAY_URL = os.environ.get("RAILWAY_URL", "")  # URL من Railway

# --- حالات المحادثة ---
FOLLOW_CHECK, NAME, EMAIL, PHONE, MAJOR, COUNTRY, UPLOAD_DOCS = range(7)

# --- إعدادات Google Sheets ---
SCOPE = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
SHEET_NAME = 'Glovuni_Database'

# --- إعدادات OpenAI ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- قاعدة المعرفة الأساسية ---
KNOWLEDGE_BASE = {
    "الخدمات": {
        "type": "service",
        "content": "نحن في Glovuni نقدم حلولاً تعليمية متكاملة:\n\n🎓 **الخدمات المجانية:**\n• استشارة أولية مجانية\n• عرض تقديم واحد مجاني\n• معلومات عن الجامعات\n\n💼 **الخدمات المدفوعة:**\n• تقديم شامل على 5 جامعات\n• مراجعة السيرة الذاتية\n• كتابة رسالة الدافع\n• متابعة كاملة حتى القبول"
    },
    "المنح": {
        "type": "scholarship",
        "content": "Glovuni هي بوابتك لأقوى المنح العالمية. نقوم بـ:\n• دراسة ملفك الأكاديمي\n• اقتراح المنح المناسبة\n• مساعدتك في التقديم\n• متابعة طلبك"
    },
    "ألمانيا": {
        "type": "country",
        "content": "الدراسة في ألمانيا هي استثمار حقيقي:\n• جامعات عالمية المستوى\n• رسوم دراسية منخفضة أو مجانية\n• فرص عمل ممتازة\n• جودة حياة عالية\n\nنحن نوفر لك وصولاً مباشراً لأفضل الجامعات الألمانية."
    },
    "التواصل": {
        "type": "contact",
        "content": "يسعدنا دائماً تواصلك معنا:\n📱 واتساب: +962781460847\n📧 بريد: info@glovuni.com\n🌐 موقع: www.glovuni.com\n📸 إنستغرام: @glovuni"
    }
}

# --- دوال Google Sheets ---
def get_google_sheet():
    """الاتصال بـ Google Sheet"""
    try:
        creds_json = os.environ.get('GOOGLE_CREDS_JSON')
        if not creds_json:
            logger.warning("لم يتم تعيين GOOGLE_CREDS_JSON")
            return None
        
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
        client_gspread = gspread.authorize(creds)
        sheet = client_gspread.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        logger.error(f"خطأ في الاتصال بـ Google Sheets: {e}")
        return None

def save_student_data_to_sheet(sheet, data):
    """حفظ بيانات الطالب في Google Sheet"""
    if not sheet:
        logger.warning("لا يمكن حفظ البيانات - الاتصال بـ Google Sheets غير متاح")
        return False
    try:
        sheet.append_row([
            data.get('timestamp', datetime.now().isoformat()),
            data.get('user_id', ''),
            data.get('name', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('major', ''),
            data.get('country', ''),
            data.get('docs_uploaded', ''),
            data.get('service_type', 'free'),
            'pending'  # status
        ])
        logger.info(f"تم حفظ بيانات الطالب {data.get('user_id')}")
        return True
    except Exception as e:
        logger.error(f"خطأ في حفظ البيانات إلى Google Sheets: {e}")
        return False

def is_user_already_registered(sheet, user_id):
    """التحقق من تسجيل المستخدم مسبقاً"""
    if not sheet:
        return False
    try:
        cell = sheet.find(str(user_id))
        return cell is not None
    except gspread.exceptions.CellNotFound:
        return False
    except Exception as e:
        logger.error(f"خطأ في التحقق من تسجيل المستخدم: {e}")
        return False

# --- دوال WhatsApp ---
def send_whatsapp_message(phone_number, message):
    """إرسال رسالة WhatsApp"""
    if not WHATSAPP_API_URL or not WHATSAPP_API_TOKEN:
        logger.warning(f"WhatsApp API غير مُعد - لن يتم إرسال الرسالة إلى {phone_number}")
        return False
    
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"تم إرسال رسالة WhatsApp إلى {phone_number}")
            return True
        else:
            logger.error(f"خطأ في إرسال رسالة WhatsApp: {response.text}")
            return False
    except Exception as e:
        logger.error(f"خطأ في إرسال رسالة WhatsApp: {e}")
        return False

# --- دوال OpenAI ---
def get_smart_response(user_message, context_data=None):
    """الحصول على رد ذكي من OpenAI"""
    try:
        system_prompt = """أنت موظف استشاري متخصص في التقديم على الجامعات الألمانية لشركة Glovuni.
        
        مهامك:
        1. الرد على استفسارات الطلاب بشكل احترافي وودي
        2. تقديم معلومات دقيقة عن الجامعات والمنح
        3. توجيه الطلاب نحو الخدمات المناسبة
        4. جمع المعلومات بشكل ذكي دون أن تبدو مثل نموذج استمارة
        
        تذكر:
        - كن ودياً واحترافياً
        - استخدم اللغة العربية الفصحى
        - ركز على احتياجات الطالب
        - اقترح الخدمات المناسبة عند الحاجة"""
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"خطأ في الحصول على رد من OpenAI: {e}")
        return None

# --- معالجات الأوامر ---
async def start(update: Update, context) -> int:
    """معالج أمر /start"""
    try:
        user = update.effective_user
        keyboard = [
            [InlineKeyboardButton("تابعنا على إنستغرام", url=INSTAGRAM_URL)],
            [InlineKeyboardButton("تحقق من المتابعة", callback_data='check_follow')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_html(
            f"أهلاً بك يا {user.mention_html()} في <b>Glovuni</b>! 👋\n\n"
            "نحن هنا لمساعدتك في تحقيق حلمك بالدراسة في الجامعات العالمية.\n\n"
            "للاستفادة من خدماتنا، يرجى متابعة صفحتنا على إنستغرام أولاً.",
            reply_markup=reply_markup
        )
        logger.info(f"بدء محادثة جديدة مع المستخدم {user.id}")
        return FOLLOW_CHECK
    except Exception as e:
        logger.error(f"خطأ في معالج start: {e}")
        await update.message.reply_text("حدث خطأ. يرجى المحاولة لاحقاً.")
        return ConversationHandler.END

async def check_follow_callback(update: Update, context) -> int:
    """معالج التحقق من المتابعة"""
    try:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("شكراً لمتابعتك! 🎉\n\nالآن دعنا نبدأ. ما هو اسمك الكامل؟")
        logger.info(f"تم التحقق من المتابعة للمستخدم {query.from_user.id}")
        return NAME
    except Exception as e:
        logger.error(f"خطأ في check_follow_callback: {e}")
        return ConversationHandler.END

async def receive_name(update: Update, context) -> int:
    """استقبال الاسم"""
    try:
        context.user_data["name"] = update.message.text
        await update.message.reply_text("شكراً! ما هو بريدك الإلكتروني؟")
        return EMAIL
    except Exception as e:
        logger.error(f"خطأ في receive_name: {e}")
        return NAME

async def receive_email(update: Update, context) -> int:
    """استقبال البريد الإلكتروني"""
    try:
        context.user_data["email"] = update.message.text
        await update.message.reply_text("رائع! يرجى إرسال رقم هاتفك (مع رمز الدولة).")
        return PHONE
    except Exception as e:
        logger.error(f"خطأ في receive_email: {e}")
        return EMAIL

async def receive_phone(update: Update, context) -> int:
    """استقبال الهاتف"""
    try:
        context.user_data["phone"] = update.message.text
        await update.message.reply_text("ما هو التخصص الذي تهتم به؟")
        return MAJOR
    except Exception as e:
        logger.error(f"خطأ في receive_phone: {e}")
        return PHONE

async def receive_major(update: Update, context) -> int:
    """استقبال التخصص"""
    try:
        context.user_data["major"] = update.message.text
        await update.message.reply_text("ما هي الدولة التي ترغب بالدراسة فيها؟")
        return COUNTRY
    except Exception as e:
        logger.error(f"خطأ في receive_major: {e}")
        return MAJOR

async def receive_country(update: Update, context) -> int:
    """استقبال الدولة"""
    try:
        context.user_data["country"] = update.message.text
        user_id = update.effective_user.id
        sheet = get_google_sheet()
        
        if is_user_already_registered(sheet, user_id):
            await update.message.reply_text(
                "لقد قمت بالتسجيل معنا مسبقاً! 📝\n\n"
                "للحصول على خدمات إضافية، يرجى التواصل معنا عبر الواتساب: +962781460847"
            )
            return ConversationHandler.END
        
        await update.message.reply_text(
            "ممتاز! يرجى رفع ملفاتك (جواز السفر، الشهادات، رسالة الدافع).\n"
            "أرسل الملفات واحداً تلو الآخر.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إنهاء", callback_data='finish_upload')]])
        )
        context.user_data["docs_uploaded"] = []
        return UPLOAD_DOCS
    except Exception as e:
        logger.error(f"خطأ في receive_country: {e}")
        return COUNTRY

async def receive_document(update: Update, context) -> int:
    """استقبال الملفات"""
    try:
        doc = update.message.document
        if doc:
            context.user_data["docs_uploaded"].append(doc.file_name)
            await update.message.reply_text(
                f"✓ تم استلام: {doc.file_name}\n\n"
                "يمكنك رفع المزيد أو الضغط على 'إنهاء'.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("إنهاء", callback_data='finish_upload')]])
            )
            logger.info(f"تم استقبال ملف: {doc.file_name}")
        return UPLOAD_DOCS
    except Exception as e:
        logger.error(f"خطأ في receive_document: {e}")
        return UPLOAD_DOCS

async def finish_upload_callback(update: Update, context) -> int:
    """إنهاء رفع الملفات"""
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        phone = context.user_data.get("phone", "")
        
        # حفظ البيانات في Google Sheets
        sheet = get_google_sheet()
        data_to_save = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'name': context.user_data.get("name", ""),
            'email': context.user_data.get("email", ""),
            'phone': phone,
            'major': context.user_data.get("major", ""),
            'country': context.user_data.get("country", ""),
            'docs_uploaded': ", ".join(context.user_data.get("docs_uploaded", [])),
            'service_type': 'free'
        }
        save_student_data_to_sheet(sheet, data_to_save)
        
        # إرسال رسالة تأكيد على WhatsApp
        whatsapp_message = f"""✅ تم استلام طلبك بنجاح!

الاسم: {data_to_save['name']}
البريد: {data_to_save['email']}
التخصص: {data_to_save['major']}
الدولة: {data_to_save['country']}

سيقوم فريقنا بمراجعة ملفك وسنتواصل معك قريباً.

شكراً لاختيارك Glovuni! 🎓"""
        
        send_whatsapp_message(phone, whatsapp_message)
        
        await query.edit_message_text(
            "✓ تم استلام طلبك بنجاح! 🎉\n\n"
            "سيقوم فريقنا بمراجعة ملفك وسنتواصل معك قريباً عبر الواتساب.\n\n"
            "شكراً لاختيارك Glovuni!"
        )
        logger.info(f"تم إكمال تسجيل الطالب {user_id}")
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"خطأ في finish_upload_callback: {e}")
        return UPLOAD_DOCS

async def handle_text(update: Update, context) -> None:
    """معالج الرسائل النصية العامة"""
    try:
        text = update.message.text.lower()
        
        # البحث في قاعدة المعرفة
        for keyword, info in KNOWLEDGE_BASE.items():
            if keyword in text:
                await update.message.reply_text(info['content'])
                return
        
        # الحصول على رد ذكي من OpenAI
        smart_response = get_smart_response(update.message.text)
        if smart_response:
            await update.message.reply_text(smart_response)
        else:
            await update.message.reply_text(
                "أهلاً! يمكنك:\n"
                "• الضغط على /start للتقديم\n"
                "• السؤال عن (الخدمات، المنح، ألمانيا، التواصل)"
            )
    except Exception as e:
        logger.error(f"خطأ في handle_text: {e}")

async def cancel(update: Update, context) -> int:
    """إلغاء المحادثة"""
    try:
        await update.message.reply_text("تم إلغاء العملية. استخدم /start للبدء من جديد.")
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"خطأ في cancel: {e}")
        return ConversationHandler.END

async def error_handler(update: object, context) -> None:
    """معالج الأخطاء العامة"""
    logger.error(f"خطأ: {context.error}")

def main() -> None:
    """الدالة الرئيسية"""
    try:
        logger.info("بدء تشغيل البوت...")
        
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # معالج المحادثة
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                FOLLOW_CHECK: [CallbackQueryHandler(check_follow_callback, pattern='^check_follow$')],
                NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
                EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
                PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
                MAJOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_major)],
                COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_country)],
                UPLOAD_DOCS: [
                    MessageHandler(filters.Document.ALL, receive_document),
                    CallbackQueryHandler(finish_upload_callback, pattern='^finish_upload$')
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            allow_reentry=True
        )
        
        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        application.add_error_handler(error_handler)
        
        logger.info("بدء تشغيل البوت باستخدام Polling...")
        
        # استخدام Polling بدلاً من Webhook (أسهل وأكثر موثوقية)
        application.run_polling(
            allowed_updates=None,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"خطأ حرج: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

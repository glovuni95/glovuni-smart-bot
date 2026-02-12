import logging
import json
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
import openai

# إعدادات السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعدادات البيئة
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL', '')  # سيتم تعيينه لاحقاً

# تعيين مفتاح OpenAI
openai.api_key = OPENAI_API_KEY

# حالات المحادثة
(VERIFY_INSTAGRAM, GET_NAME, GET_EMAIL, GET_PHONE, GET_FIELD, 
 UPLOAD_DOCUMENTS, CONFIRM_SUBMISSION) = range(7)

# تحميل قاعدة المعرفة
with open('knowledge_base_comprehensive.json', 'r', encoding='utf-8') as f:
    KNOWLEDGE_BASE = json.load(f)

# قائمة المستخدمين الذين تم التحقق منهم (في الإنتاج، يجب استخدام قاعدة بيانات)
verified_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء المحادثة والترحيب بالمستخدم"""
    user = update.effective_user
    
    # الرسالة الترحيبية
    welcome_message = f"""
🎓 **أهلاً بك يا {user.first_name} في Glovuni!**

نحن متخصصون في مساعدة الطلاب الدوليين للدراسة في أفضل الجامعات الألمانية والعالمية.

**للاستفادة من خدماتنا:**
1️⃣ تابع صفحتنا على Instagram
2️⃣ تحقق من المتابعة
3️⃣ ملء استمارة التقديم

دعنا نبدأ! 🚀
    """
    
    # الأزرار
    keyboard = [
        [InlineKeyboardButton("📱 تابعنا على إنستقرام", url="https://www.instagram.com/glovuni")],
        [InlineKeyboardButton("✅ تحقق من المتابعة", callback_data="verify_instagram")],
        [InlineKeyboardButton("❓ اسأل سؤال", callback_data="ask_question")],
        [InlineKeyboardButton("📋 معلومات عن الخدمات", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return VERIFY_INSTAGRAM

async def verify_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """التحقق من متابعة Instagram"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # رسالة التحقق
    verification_message = """
✅ **شكراً لمتابعتك لنا على Instagram!**

تأكد من أنك متابع لصفحتنا @glovuni للحصول على آخر المستجدات والعروض الخاصة.

الآن يمكنك متابعة عملية التقديم معنا! 🎓
    """
    
    # أزرار المتابعة
    keyboard = [
        [InlineKeyboardButton("✅ نعم، أنا متابع", callback_data="start_application")],
        [InlineKeyboardButton("👈 العودة", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(verification_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return VERIFY_INSTAGRAM

async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بدء استمارة التقديم"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    verified_users.add(user_id)
    
    # حفظ معرف المستخدم في السياق
    context.user_data['user_id'] = user_id
    
    # طلب الاسم
    message = """
📝 **شكراً لتحقق من المتابعة!**

الآن سننقل معك خطوة بخطوة لملء استمارة التقديم.

**الخطوة 1️⃣: ما اسمك الكامل؟**
    """
    
    await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """الحصول على اسم المستخدم"""
    name = update.message.text
    context.user_data['name'] = name
    
    await update.message.reply_text(f"شكراً {name}! 👋\n\n**الخطوة 2️⃣: ما بريدك الإلكتروني؟**")
    return GET_EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """الحصول على البريد الإلكتروني"""
    email = update.message.text
    context.user_data['email'] = email
    
    await update.message.reply_text(f"ممتاز! ✅\n\n**الخطوة 3️⃣: ما رقم هاتفك؟**")
    return GET_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """الحصول على رقم الهاتف"""
    phone = update.message.text
    context.user_data['phone'] = phone
    
    # أزرار اختيار التخصص
    keyboard = [
        [InlineKeyboardButton("🔬 العلوم والهندسة", callback_data="field_science")],
        [InlineKeyboardButton("📊 الاقتصاد والإدارة", callback_data="field_business")],
        [InlineKeyboardButton("🎓 العلوم الإنسانية", callback_data="field_humanities")],
        [InlineKeyboardButton("💻 تكنولوجيا المعلومات", callback_data="field_it")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "رائع! 🎯\n\n**الخطوة 4️⃣: ما مجال دراستك المفضل؟**",
        reply_markup=reply_markup
    )
    return GET_FIELD

async def get_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """الحصول على مجال الدراسة"""
    query = update.callback_query
    await query.answer()
    
    field_map = {
        'field_science': 'العلوم والهندسة',
        'field_business': 'الاقتصاد والإدارة',
        'field_humanities': 'العلوم الإنسانية',
        'field_it': 'تكنولوجيا المعلومات'
    }
    
    field = field_map.get(query.data, 'غير محدد')
    context.user_data['field'] = field
    
    message = f"""
✅ **تم حفظ بيانات التقديم:**

👤 **الاسم:** {context.user_data['name']}
📧 **البريد:** {context.user_data['email']}
📱 **الهاتف:** {context.user_data['phone']}
🎓 **المجال:** {field}

**الآن سيتم إرسال بيانات التقديم إلى فريقنا للمراجعة.**

شكراً لاختيارك Glovuni! 🎉
سيتواصل معك فريقنا قريباً لمتابعة الخطوات التالية.
    """
    
    # إرسال البيانات إلى Make.com
    await send_to_make(context.user_data)
    
    keyboard = [
        [InlineKeyboardButton("❓ اسأل سؤال", callback_data="ask_question")],
        [InlineKeyboardButton("📋 معلومات عن الخدمات", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def send_to_make(user_data: dict) -> None:
    """إرسال البيانات إلى Make.com"""
    if not MAKE_WEBHOOK_URL:
        logger.warning("MAKE_WEBHOOK_URL غير محدد")
        return
    
    try:
        payload = {
            'name': user_data.get('name'),
            'email': user_data.get('email'),
            'phone': user_data.get('phone'),
            'field': user_data.get('field'),
            'timestamp': str(user_data.get('timestamp', ''))
        }
        
        response = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"تم إرسال البيانات بنجاح: {user_data.get('name')}")
        else:
            logger.error(f"خطأ في إرسال البيانات: {response.status_code}")
    except Exception as e:
        logger.error(f"خطأ في الاتصال مع Make.com: {e}")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """الإجابة على الأسئلة باستخدام AI"""
    query = update.callback_query
    await query.answer()
    
    message = """
❓ **اسأل أي سؤال عن الدراسة بالخارج**

يمكنك السؤال عن:
- 🏫 الجامعات والبرامج
- 💰 التكاليف والمنح
- 📝 متطلبات التقديم
- 🌍 الدول والمدن
- 📚 التخصصات والمسارات الدراسية

اكتب سؤالك الآن:
    """
    
    keyboard = [
        [InlineKeyboardButton("👈 العودة", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    context.user_data['waiting_for_question'] = True

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالجة الأسئلة والإجابة عليها"""
    if not context.user_data.get('waiting_for_question'):
        return
    
    question = update.message.text
    context.user_data['waiting_for_question'] = False
    
    # الإجابة الذكية باستخدام OpenAI مع قاعدة المعرفة
    try:
        # إنشاء سياق من قاعدة المعرفة
        knowledge_context = json.dumps(KNOWLEDGE_BASE, ensure_ascii=False, indent=2)
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"""أنت مساعد متخصص في استشارات التعليم العالي بالخارج لشركة Glovuni.
                    
قاعدة المعرفة:
{knowledge_context}

الإجابة يجب أن تكون:
- مفيدة وشاملة
- باللغة العربية
- مستندة على قاعدة المعرفة
- تشجع المستخدم على التقديم معنا
- تتضمن معلومات عملية وفعلية"""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        
        keyboard = [
            [InlineKeyboardButton("❓ سؤال آخر", callback_data="ask_question")],
            [InlineKeyboardButton("📋 معلومات عن الخدمات", callback_data="services")],
            [InlineKeyboardButton("👈 العودة", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(answer, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"خطأ في OpenAI: {e}")
        await update.message.reply_text("عذراً، حدث خطأ في معالجة سؤالك. يرجى المحاولة مرة أخرى.")

async def services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض معلومات الخدمات"""
    query = update.callback_query
    await query.answer()
    
    message = """
📋 **خدمات Glovuni:**

1️⃣ **استشارات التقديم**
   - تقييم ملفك الأكاديمي
   - اختيار أفضل الجامعات
   - استراتيجية التقديم

2️⃣ **إعداد الملفات**
   - ترجمة الوثائق
   - كتابة خطاب الدافع
   - إعداد السيرة الذاتية

3️⃣ **متابعة الطلب**
   - الرد على استفسارات الجامعات
   - متابعة حالة الطلب
   - دعم مستمر

4️⃣ **دعم اللغة**
   - تحضير اختبارات اللغة
   - دروس تقوية
   - نصائح للنجاح

5️⃣ **المنح الدراسية**
   - البحث عن المنح المتاحة
   - مساعدة في التقديم
   - متابعة النتائج

🎯 **هدفنا:** مساعدتك في تحقيق حلمك الأكاديمي! 🌟
    """
    
    keyboard = [
        [InlineKeyboardButton("📝 ابدأ التقديم", callback_data="start_application")],
        [InlineKeyboardButton("❓ اسأل سؤال", callback_data="ask_question")],
        [InlineKeyboardButton("👈 العودة", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """العودة إلى القائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    
    message = """
🎓 **قائمة Glovuni الرئيسية**

اختر ما تريد:
    """
    
    keyboard = [
        [InlineKeyboardButton("📱 تابعنا على إنستقرام", url="https://www.instagram.com/glovuni")],
        [InlineKeyboardButton("✅ تحقق من المتابعة", callback_data="verify_instagram")],
        [InlineKeyboardButton("❓ اسأل سؤال", callback_data="ask_question")],
        [InlineKeyboardButton("📋 معلومات عن الخدمات", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر المساعدة"""
    help_text = """
🆘 **مساعدة Glovuni Bot**

الأوامر المتاحة:
/start - بدء المحادثة
/help - عرض هذه المساعدة
/services - معلومات الخدمات
/contact - معلومات التواصل

📱 تابعنا على Instagram: @glovuni
💬 أي استفسار؟ اسأل الآن!
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معلومات التواصل"""
    contact_text = """
📞 **معلومات التواصل:**

📱 Instagram: @glovuni
🌐 Website: www.glovuni.com
📧 Email: contact@glovuni.com

🕐 ساعات العمل: 24/7
💬 نحن هنا لمساعدتك!
    """
    await update.message.reply_text(contact_text, parse_mode=ParseMode.MARKDOWN)

def main() -> None:
    """بدء البوت"""
    # إنشاء التطبيق
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # معالج المحادثة
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            VERIFY_INSTAGRAM: [
                CallbackQueryHandler(verify_instagram, pattern="verify_instagram"),
                CallbackQueryHandler(ask_question, pattern="ask_question"),
                CallbackQueryHandler(services, pattern="services"),
            ],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GET_FIELD: [CallbackQueryHandler(get_field, pattern="field_")],
        },
        fallbacks=[
            CallbackQueryHandler(back_to_menu, pattern="back_to_menu"),
            CommandHandler("start", start),
        ],
    )
    
    # إضافة المعالجات
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contact", contact_command))
    application.add_handler(CallbackQueryHandler(start_application, pattern="start_application"))
    application.add_handler(CallbackQueryHandler(ask_question, pattern="ask_question"))
    application.add_handler(CallbackQueryHandler(services, pattern="services"))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="back_to_menu"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    
    # بدء البوت
    logger.info("Telegram Bot Application started")
    application.run_polling()

if __name__ == '__main__':
    main()

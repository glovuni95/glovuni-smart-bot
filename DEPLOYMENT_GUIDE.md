# دليل نشر بوت Glovuni على Heroku

## المتطلبات

1. حساب GitHub
2. حساب Heroku
3. Heroku CLI (اختياري)

---

## الخطوات:

### 1. إنشاء مستودع GitHub

```bash
# إنشاء مجلد جديد
mkdir glovuni-bot
cd glovuni-bot

# تهيئة Git
git init

# إضافة الملفات
git add .
git commit -m "Initial commit: Glovuni Smart Bot"

# إنشاء المستودع على GitHub وإضافة الرابط
git remote add origin https://github.com/YOUR_USERNAME/glovuni-bot.git
git branch -M main
git push -u origin main
```

### 2. ربط Heroku مع GitHub

1. اذهب إلى https://dashboard.heroku.com/
2. اضغط "New" → "Create new app"
3. أدخل اسم التطبيق: `glovuni-bot`
4. اختر المنطقة الأقرب لك
5. اضغط "Create app"

### 3. إضافة متغيرات البيئة (Config Vars)

في لوحة تحكم Heroku، اذهب إلى "Settings" → "Config Vars" وأضف:

```
TELEGRAM_BOT_TOKEN = YOUR_TELEGRAM_BOT_TOKEN

OPENAI_API_KEY = YOUR_OPENAI_API_KEY

GOOGLE_CREDS_JSON = {ضع محتوى ملف Google Credentials هنا}

WHATSAPP_API_URL = https://graph.instagram.com/v18.0/YOUR_PHONE_NUMBER_ID/messages

WHATSAPP_API_TOKEN = YOUR_WHATSAPP_API_TOKEN

HEROKU_APP_NAME = glovuni-bot

PORT = 8443
```

### 4. ربط GitHub مع Heroku

1. في لوحة تحكم Heroku، اذهب إلى "Deploy"
2. اختر "GitHub" كطريقة النشر
3. ابحث عن مستودعك `glovuni-bot`
4. اضغط "Connect"
5. اختر "Enable Automatic Deploys" (اختياري)

### 5. النشر الأول

```bash
# أو اضغط "Deploy Branch" في لوحة تحكم Heroku
```

---

## التحقق من حالة البوت

```bash
# عرض السجلات
heroku logs --tail

# التحقق من حالة التطبيق
heroku apps:info glovuni-bot
```

---

## متغيرات البيئة المطلوبة

| المتغير | الوصف | مثال |
|--------|--------|--------|
| `TELEGRAM_BOT_TOKEN` | توكن بوت Telegram | `7980778146:AAF...` |
| `OPENAI_API_KEY` | مفتاح OpenAI API | `sk-proj-...` |
| `GOOGLE_CREDS_JSON` | بيانات اعتماد Google | `{...json...}` |
| `WHATSAPP_API_URL` | رابط WhatsApp API | `https://graph.instagram.com/...` |
| `WHATSAPP_API_TOKEN` | توكن WhatsApp API | `EAAB...` |
| `HEROKU_APP_NAME` | اسم تطبيق Heroku | `glovuni-bot` |

---

## الملفات المطلوبة

```
glovuni-bot/
├── glovuni_bot_advanced.py    # الكود الرئيسي
├── Procfile                    # إعدادات Heroku
├── requirements.txt            # المكتبات المطلوبة
├── .gitignore                  # الملفات المستثناة من Git
└── README.md                   # توثيق المشروع
```

---

## استكشاف الأخطاء

### البوت لا يستجيب

1. تحقق من توكن Telegram
2. تحقق من السجلات: `heroku logs --tail`
3. تأكد من أن الـ Webhook مُعد بشكل صحيح

### خطأ في Google Sheets

1. تحقق من ملف بيانات اعتماد Google
2. تأكد من أن جدول البيانات موجود وباسم `Glovuni_Database`

### خطأ في OpenAI

1. تحقق من مفتاح API
2. تأكد من أن الحساب له رصيد كافٍ

---

## الدعم والمساعدة

للمزيد من المعلومات، تواصل مع:
- 📧 البريد: info@glovuni.com
- 📱 واتساب: +962781460847

import logging
import os
from threading import Thread

from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# 1. إعداد سيرفر Flask لإرضاء فحص البورت على Render
app = Flask(__name__)


@app.route("/")
def home():
  return "SRT IPA Signer Bot is Running 24/7!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


# تشغيل سيرفر Flask في خيط (Thread) منفصل
Thread(target=run_flask, daemon=True).start()

# 2. إعدادات التسجيل (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# حالات المحادثة
WAITING_P12, WAITING_PROVISION, WAITING_PASSWORD = range(3)

# مسار حفظ الشهادات
CERT_DIR = "certificates"
os.makedirs(CERT_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
      [InlineKeyboardButton("📂 رفع شهادة جديدة", callback_data="upload_cert")],
      [
          InlineKeyboardButton(
              "🔍 فحص الشهادة", callback_data="check_cert"
          ),
          InlineKeyboardButton("🗑️ حذف الشهادة", callback_data="delete_cert"),
      ],
      [InlineKeyboardButton("❓ مساعدة", callback_data="help")],
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  user_id = update.effective_user.id
  p12_exists = os.path.exists(f"{CERT_DIR}/{user_id}.p12")
  prov_exists = os.path.exists(f"{CERT_DIR}/{user_id}.mobileprovision")

  status_msg = f"""
📊 **حالة الشهادة الحالية:**

• ملف `p12`: {'✅ موجود' if p12_exists else '❌ غير موجود'}
• ملف `mobileprovision`: {'✅ موجود' if prov_exists else '❌ غير موجود'}
"""
  if update.message:
    await update.message.reply_text(status_msg, reply_markup=reply_markup)
  else:
    await update.callback_query.edit_message_text(
        status_msg, reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  if query.data == "upload_cert":
    await query.edit_message_text(
        "1️⃣ **الخطوة الأولى:** أرسل الآن ملف الشهادة `p12.` كُمستند."
    )
    return WAITING_P12
  elif query.data == "delete_cert":
    user_id = query.from_user.id
    for ext in [".p12", ".mobileprovision", ".txt"]:
      path = f"{CERT_DIR}/{user_id}{ext}"
      if os.path.exists(path):
        os.remove(path)
    await query.edit_message_text("🗑️ تم حذف الشهادة الخاصة بك بنجاح!")
    return ConversationHandler.END


async def handle_p12(update: Update, context: ContextTypes.DEFAULT_TYPE):
  doc = update.message.document
  if not doc:
    await update.message.reply_text("❌ يرجى إرسال الملف كُمستند.")
    return WAITING_P12

  file_name = doc.file_name.lower() if doc.file_name else ""
  if not file_name.endswith(".p12"):
    await update.message.reply_text(
        "❌ هذا ليس ملف `.p12` صحيح، يرجى إعادة الإرسال."
    )
    return WAITING_P12

  user_id = update.effective_user.id
  file = await context.bot.get_file(doc.file_id)
  await file.download_to_drive(f"{CERT_DIR}/{user_id}.p12")

  await update.message.reply_text(
      "✅ تم حفظ ملف `p12.` بنجاح!\n\n2️⃣ **الخطوة الثانية:** أرسل الآن ملف"
      " `mobileprovision.` كُمستند."
  )
  return WAITING_PROVISION


async def handle_provision(update: Update, context: ContextTypes.DEFAULT_TYPE):
  doc = update.message.document
  if not doc:
    await update.message.reply_text("❌ يرجى إرسال الملف كُمستند.")
    return WAITING_PROVISION

  file_name = doc.file_name.lower() if doc.file_name else ""
  # الفحص المرن يقبل كلا الامتدادين وبدون تدقيق الحروف
  if not (
      file_name.endswith(".mobileprovision") or file_name.endswith(".provision")
  ):
    await update.message.reply_text(
        "❌ هذا ليس ملف `mobileprovision.` صحيح، يرجى التأكد وإعادة الإرسال."
    )
    return WAITING_PROVISION

  user_id = update.effective_user.id
  file = await context.bot.get_file(doc.file_id)
  await file.download_to_drive(f"{CERT_DIR}/{user_id}.mobileprovision")

  await update.message.reply_text(
      "✅ تم حفظ ملف `mobileprovision.` بنجاح!\n\n3️⃣ **الخطوة الثالثة:**"
      " أرسل الآن كلمة سر الشهادة (P12 Password)."
  )
  return WAITING_PASSWORD


async def handle_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
  password = update.message.text
  user_id = update.effective_user.id

  with open(f"{CERT_DIR}/{user_id}.txt", "w") as f:
    f.write(password)

  await update.message.reply_text(
      "🎉 **تمت إضافة الشهادة بنجاح!**\nيمكنك الآن إرسال أي ملف IPA لتوقيعه"
      " مباشرة."
  )
  return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("تم إلغاء العملية.")
  return ConversationHandler.END


def main():
  # استخراج التوكن من متغيرات البيئة
  TOKEN = os.environ.get("BOT_TOKEN", "ضع_التوكن_هنا_إذا_لم_تستخدم_ENV")

  application = Application.builder().token(TOKEN).build()

  cert_handler = ConversationHandler(
      entry_points=[CallbackQueryHandler(button_handler, pattern="^upload_cert$")],
      states={
          WAITING_P12: [
              MessageHandler(filters.Document.ALL, handle_p12)
          ],
          WAITING_PROVISION: [
              MessageHandler(filters.Document.ALL, handle_provision)
          ],
          WAITING_PASSWORD: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, handle_password)
          ],
      },
      fallbacks=[CommandHandler("cancel", cancel)],
      per_message=False,
  )

  application.add_handler(CommandHandler("start", start))
  application.add_handler(cert_handler)
  application.add_handler(CallbackQueryHandler(button_handler))

  print("Bot is running...")
  application.run_polling()


if __name__ == "__main__":
  main()

import logging
import os
import plistlib
import subprocess
import urllib.parse
import zipfile
from threading import Thread

from flask import Flask
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# 1. إعداد سيرفر Flask الداخلي لمنع توقف Render
app = Flask(__name__)


@app.route("/")
def home():
  return "SRT IPA Signer Bot is Live!"


def run_flask():
  port = int(os.environ.get("PORT", 8080))
  app.run(host="0.0.0.0", port=port)


Thread(target=run_flask, daemon=True).start()

# 2. إعداد المتغيرات والمعلومات
TOKEN = os.environ.get(
    "BOT_TOKEN", "8686601094:AAEViStOO6vokqRvEDnFY8Wj2LwtY0eqKHc"
)
CHANNEL_USERNAME = "@srt_ipa7"
CHANNEL_URL = "https://t.me/srt_ipa7"
DEVELOPER = "@evv2g"
GITHUB_PAGES_URL = "https://srtttt7.github.io/Ipa-/index.html"

WAITING_P12, WAITING_PROV, WAITING_PASS, WAITING_IPA = range(4)


def get_ipa_info(ipa_path):
  app_name, bundle_id, app_version = "تطبيق", "com.app.signed", "1.0"
  try:
    with zipfile.ZipFile(ipa_path, "r") as zip_ref:
      for file_name in zip_ref.namelist():
        if file_name.startswith("Payload/") and file_name.endswith(
            ".app/Info.plist"
        ):
          plist_data = zip_ref.read(file_name)
          plist = plistlib.loads(plist_data)
          app_name = plist.get("CFBundleDisplayName") or plist.get(
              "CFBundleName", app_name
          )
          bundle_id = plist.get("CFBundleIdentifier", bundle_id)
          app_version = plist.get("CFBundleShortVersionString") or plist.get(
              "CFBundleVersion", app_version
          )
          break
  except Exception as e:
    print("Error reading IPA:", e)
  return app_name, bundle_id, app_version


def upload_file_catbox(file_path):
  try:
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload"}
    with open(file_path, "rb") as f:
      files = {"fileToUpload": f}
      res = requests.post(url, data=data, files=files)
      if res.status_code == 200:
        return res.text.strip()
  except Exception as e:
    print("Upload Error:", e)
  return None


def make_direct_ota(ipa_url, bundle_id, app_version, app_name, user_dir):
  plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>items</key>
    <array>
        <dict>
            <key>assets</key>
            <array>
                <dict>
                    <key>kind</key>
                    <key>software-package</key>
                    <key>url</key>
                    <string>{ipa_url}</string>
                </dict>
            </array>
            <key>metadata</key>
            <dict>
                <key>bundle-identifier</key>
                <string>{bundle_id}</string>
                <key>bundle-version</key>
                <string>{app_version}</string>
                <key>kind</key>
                <string>software</string>
                <key>title</key>
                <string>{app_name}</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>"""

  plist_path = f"{user_dir}/manifest.plist"
  with open(plist_path, "w", encoding="utf-8") as f:
    f.write(plist_content)

  plist_url = upload_file_catbox(plist_path)
  if os.path.exists(plist_path):
    os.remove(plist_path)

  if plist_url:
    encoded_plist = urllib.parse.quote(plist_url, safe="")
    install_button_url = f"{GITHUB_PAGES_URL}?plist={encoded_plist}"
    return install_button_url, plist_url
  return None, None


async def is_user_subscribed(
    user_id: int, context: ContextTypes.DEFAULT_TYPE
) -> bool:
  try:
    member = await context.bot.get_chat_member(
        chat_id=CHANNEL_USERNAME, user_id=user_id
    )
    return member.status in ["member", "administrator", "creator"]
  except Exception:
    return True


async def check_subscription_guard(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
  user_id = update.effective_user.id
  subscribed = await is_user_subscribed(user_id, context)
  if not subscribed:
    keyboard = [
        [InlineKeyboardButton("📢 انضم للقناة أولاً", url=CHANNEL_URL)],
        [
            InlineKeyboardButton(
                "✅ تحقق من الاشتراك", callback_data="check_sub"
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "⚠️ يجب عليك الاشتراك في القناة أولاً لاستخدام البوت:\n"
        + CHANNEL_USERNAME
    )

    if update.callback_query:
      await update.callback_query.message.reply_text(
          text, reply_markup=reply_markup
      )
    elif update.message:
      await update.message.reply_text(text, reply_markup=reply_markup)
    return False
  return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not await check_subscription_guard(update, context):
    return ConversationHandler.END

  user_id = update.effective_user.id
  user_dir = f"users/{user_id}"
  os.makedirs(user_dir, exist_ok=True)

  keyboard = [
      [
          InlineKeyboardButton(
              "✍️ توقيع تطبيق IPA", callback_data="start_sign"
          )
      ],
      [
          InlineKeyboardButton(
              "📁 رفع شهادة جديدة", callback_data="start_cert_flow"
          )
      ],
      [
          InlineKeyboardButton("🔍 فحص الشهادة", callback_data="check_cert"),
          InlineKeyboardButton("🗑️ حذف الشهادة", callback_data="delete_cert"),
      ],
      [InlineKeyboardButton("❓ مساعدة", callback_data="help")],
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)
  msg_text = (
      "مرحبا في بوت توقيع ملفات ipa 📲\n\n"
      f"👨‍💻 **مطور البوت:** {DEVELOPER}\n\n"
      "إضغط على **'توقيع تطبيق IPA'** لتوقيع ملفاتك مباشرة بعد رفع الشهادة."
  )
  await update.message.reply_text(
      msg_text, reply_markup=reply_markup, parse_mode="Markdown"
  )
  return ConversationHandler.END


async def cert_flow_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  if not await check_subscription_guard(update, context):
    return ConversationHandler.END

  await query.message.reply_text(
      "1️⃣ **الخطوة الأولى:** أرسل الآن ملف الشهادة `.p12` كمستند."
  )
  return WAITING_P12


async def process_p12(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_dir = f"users/{user_id}"
  os.makedirs(user_dir, exist_ok=True)

  doc = update.message.document
  file_name = doc.file_name.lower() if doc and doc.file_name else ""

  if not doc or not file_name.endswith(".p12"):
    await update.message.reply_text(
        "❌ خطأ: يرجى إرسال ملف بصيغة `.p12` فقط!"
    )
    return WAITING_P12

  file = await context.bot.get_file(doc.file_id)
  await file.download_to_drive(f"{user_dir}/cert.p12")

  await update.message.reply_text(
      "✅ تم حفظ ملف `.p12` بنجاح!\n\n2️⃣ **الخطوة الثانية:** أرسل الآن ملف"
      " `.mobileprovision` كمستند."
  )
  return WAITING_PROV


async def process_prov(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_dir = f"users/{user_id}"
  os.makedirs(user_dir, exist_ok=True)

  doc = update.message.document
  file_name = doc.file_name.lower() if doc and doc.file_name else ""

  if not doc or not (
      file_name.endswith(".mobileprovision") or file_name.endswith(".provision")
  ):
    await update.message.reply_text(
        "❌ خطأ: يرجى إرسال ملف بصيغة `.mobileprovision` فقط!"
    )
    return WAITING_PROV

  file = await context.bot.get_file(doc.file_id)
  await file.download_to_drive(f"{user_dir}/cert.mobileprovision")

  await update.message.reply_text(
      "✅ تم حفظ ملف `.mobileprovision` بنجاح!\n\n3️⃣ **الخطوة الثالثة:**"
      " أرسل كلمة سر الشهادة الآن (إذا لم توجد كلمة سر أرسل الرقم 0)."
  )
  return WAITING_PASS


async def process_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = update.effective_user.id
  user_dir = f"users/{user_id}"
  password = update.message.text.strip()

  if password == "0":
    password = ""

  with open(f"{user_dir}/pass.txt", "w") as f:
    f.write(password)

  await update.message.reply_text(
      "🎉 تم حفظ الشهادة بنجاح! إضغط على زر 'توقيع تطبيق IPA' وأرسل تطبيقك."
  )
  return ConversationHandler.END


async def start_sign_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  user_id = update.effective_user.id
  user_dir = os.path.abspath(f"users/{user_id}")
  p12_path = f"{user_dir}/cert.p12"
  prov_path = f"{user_dir}/cert.mobileprovision"

  if not os.path.exists(p12_path) or not os.path.exists(prov_path):
    await query.message.reply_text(
        "❌ يرجى إعداد ورفع الشهادة أولاً بالضغط على 'رفع شهادة جديدة'."
    )
    return ConversationHandler.END

  await query.message.reply_text(
      "📲 **أرسل الآن ملف تطبيق الـ IPA المُراد توقيعه:**"
  )
  return WAITING_IPA


async def handle_ipa_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not await check_subscription_guard(update, context):
    return ConversationHandler.END

  user_id = update.effective_user.id
  user_dir = os.path.abspath(f"users/{user_id}")
  doc = update.message.document

  file_name = doc.file_name.lower() if doc and doc.file_name else ""

  if not doc or not file_name.endswith(".ipa"):
    await update.message.reply_text("❌ يرجى إرسال ملف بصيغة `.ipa` فقط!")
    return WAITING_IPA

  p12_path = f"{user_dir}/cert.p12"
  prov_path = f"{user_dir}/cert.mobileprovision"
  pass_path = f"{user_dir}/pass.txt"

  p12_pass = ""
  if os.path.exists(pass_path):
    with open(pass_path, "r") as f:
      p12_pass = f.read().strip()

  status_msg = await update.message.reply_text("⏳ جاري تنزيل ملف الـ IPA...")
  file = await context.bot.get_file(doc.file_id)

  input_ipa = f"{user_dir}/input.ipa"
  output_ipa = f"{user_dir}/signed_{doc.file_name}"

  if os.path.exists(input_ipa):
    os.remove(input_ipa)
  if os.path.exists(output_ipa):
    os.remove(output_ipa)

  await file.download_to_drive(input_ipa)
  await status_msg.edit_text("✍️ جاري توقيع التطبيق...")

  cmd = f'isign -c "{p12_path}" -k "{p12_pass}" -p "{prov_path}" -o "{output_ipa}" "{input_ipa}"'
  process = subprocess.run(cmd, shell=True, capture_output=True, text=True)

  if process.returncode == 0 and os.path.exists(output_ipa):
    await status_msg.edit_text(
        "⚡ تم التوقيع بنجاح! جاري إعداد زر التثبيت المباشر..."
    )

    app_name, bundle_id, app_version = get_ipa_info(output_ipa)
    ipa_download_url = upload_file_catbox(output_ipa)

    if ipa_download_url:
      install_button_url, plist_url = make_direct_ota(
          ipa_download_url, bundle_id, app_version, app_name, user_dir
      )

      msg_response = (
          "📲 **معلومات التطبيق** 📲\n\n"
          f"• **AppName:** `{app_name}`\n"
          f"• **AppVersion:** `{app_version}`\n"
          f"• **BundleID:** `{bundle_id}`"
      )

      keyboard = [[InlineKeyboardButton("📲 تثبيت", url=install_button_url)]]
      reply_markup = InlineKeyboardMarkup(keyboard)

      await status_msg.edit_text(
          msg_response, reply_markup=reply_markup, parse_mode="Markdown"
      )
    else:
      await status_msg.edit_text(
          "❌ حدث خطأ أثناء رفع الملف لإنشاء رابط التثبيت."
      )

    if os.path.exists(input_ipa):
      os.remove(input_ipa)
    if os.path.exists(output_ipa):
      os.remove(output_ipa)
  else:
    err_out = process.stderr if process.stderr else process.stdout
    err_out_clean = str(err_out)[:500]
    await status_msg.edit_text(
        "❌ حدث خطأ أثناء التوقيع:\n\n`" + err_out_clean + "`", parse_mode="Markdown"
    )

  return ConversationHandler.END


async def callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()

  if query.data == "check_sub":
    if await is_user_subscribed(update.effective_user.id, context):
      await query.message.reply_text("✅ شكراً لاشتراكك! أرسل /start للبدء.")
    else:
      await query.message.reply_text("❌ لم تنضم للقناة بعد.")
    return

  if not await check_subscription_guard(update, context):
    return

  user_id = update.effective_user.id
  user_dir = f"users/{user_id}"

  if query.data == "check_cert":
    p12_exists = (
        "✅ موجود" if os.path.exists(f"{user_dir}/cert.p12") else "❌ غير موجود"
    )
    prov_exists = (
        "✅ موجود"
        if os.path.exists(f"{user_dir}/cert.mobileprovision")
        else "❌ غير موجود"
    )
    pass_exists = (
        "✅ مضافة" if os.path.exists(f"{user_dir}/pass.txt") else "❌ غير مضافة"
    )

    msg = f"📊 **حالة الشهادة الحالية:**\n\n• ملف `.p12`: {p12_exists}\n• ملف `.mobileprovision`: {prov_exists}\n• كلمة سر الشهادة: {pass_exists}"
    await query.message.reply_text(msg, parse_mode="Markdown")

  elif query.data == "delete_cert":
    files_to_remove = [
        f"{user_dir}/cert.p12",
        f"{user_dir}/cert.mobileprovision",
        f"{user_dir}/pass.txt",
    ]
    deleted = False
    for f in files_to_remove:
      if os.path.exists(f):
        os.remove(f)
        deleted = True

    if deleted:
      await query.message.reply_text(
          "🗑️ **تم حذف جميع ملفات الشهادة المرفوقة بنجاح.**",
          parse_mode="Markdown",
      )
    else:
      await query.message.reply_text("ℹ️ لا توجد شهادة مضافة لحذفها.")

  elif query.data == "help":
    await query.message.reply_text(
        "ℹ️ **كيفية الاستخدام:**\n\n1. اضغط على 'رفع شهادة جديدة'.\n2. أرسل"
        " ملف .p12 ثم .mobileprovision ثم كلمة السر.\n3. اضغط على 'توقيع تطبيق"
        " IPA' وأرسل تطبيقك ليتم تثبيته بلمسة واحدة."
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("تم إلغاء العملية.")
  return ConversationHandler.END


if __name__ == "__main__":
  app = ApplicationBuilder().token(TOKEN).build()

  cert_handler = ConversationHandler(
      entry_points=[
          CallbackQueryHandler(cert_flow_start, pattern="^start_cert_flow$"),
          CommandHandler("upload", cert_flow_start),
      ],
      states={
          WAITING_P12: [
              MessageHandler(
                  filters.Document.ALL & ~filters.COMMAND, process_p12
              )
          ],
          WAITING_PROV: [
              MessageHandler(
                  filters.Document.ALL & ~filters.COMMAND, process_prov
              )
          ],
          WAITING_PASS: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, process_pass)
          ],
      },
      fallbacks=[CommandHandler("cancel", cancel)],
      per_message=False,
  )

  sign_handler = ConversationHandler(
      entry_points=[
          CallbackQueryHandler(start_sign_flow, pattern="^start_sign$")
      ],
      states={
          WAITING_IPA: [
              MessageHandler(
                  filters.Document.ALL & ~filters.COMMAND, handle_ipa_file
              )
          ]
      },
      fallbacks=[CommandHandler("cancel", cancel)],
      per_message=False,
  )

  app.add_handler(CommandHandler("start", start))
  app.add_handler(cert_handler)
  app.add_handler(sign_handler)
  app.add_handler(CallbackQueryHandler(callback_handler))

  print("Bot is running...")
  app.run_polling()

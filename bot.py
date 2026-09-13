import logging
from datetime import timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# === আপনার কনফিগারেশন তথ্যসমূহ ===
TOKEN = "8839361164:AAH_Y4F4rKFjWTvsvmiIC_VL2taTxQG9gnc"  # বটের টোকেন
ADMIN_USERNAME = "kawsar123450"  # আপনার টেলিগ্রাম ইউজারনেম (মালিক)

# আপনার প্রাইভেট চ্যানেল আইডি (মুভি চ্যানেল)
PRIVATE_CHANNEL_ID = -1003967128934

# আপনার গ্রুপ আইডি (হিন্দি বাংলা সিনেমা গুরু)
TARGET_GROUP_ID = -1004362653651

# মেমোরি ডাটাবেজ
warnings = {}
videos = {
    "hot": [],
    "bachelor": [],
    "natok": [],
    "hindi": [],
    "cid": [],
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ১. গ্রুপে অটো বাটন পাঠানোর ফাংশন (প্রতি ১ মিনিট পর পর)
async def send_auto_video_menu(context: ContextTypes.DEFAULT_TYPE):
  bot_username = (await context.bot.get_me()).username

  keyboard = [
      [
          InlineKeyboardButton(
              "🔥🔞 হট ভিডিও 🔞🔥", url=f"https://t.me/{bot_username}?start=hot"
          )
      ],
      [
          InlineKeyboardButton(
              "🎭🔥 ব্যাচেলর পয়েন্ট নাটক 🔥🎭",
              url=f"https://t.me/{bot_username}?start=bachelor",
          )
      ],
      [
          InlineKeyboardButton(
              "🎬🍿 বাংলা সিনেমা নাটক 🍿🎬",
              url=f"https://t.me/{bot_username}?start=natok",
          )
      ],
      [
          InlineKeyboardButton(
              "🇮🇳🎥 হিন্দি ড্রামা / মুভি 🎥🇮🇳",
              url=f"https://t.me/{bot_username}?start=hindi",
          )
      ],
      [
          InlineKeyboardButton(
              "🕵️‍♂️🔥 CID নাটক 🔥🕵️‍♂️",
              url=f"https://t.me/{bot_username}?start=cid",
          )
      ],
      [
          InlineKeyboardButton(
              "📁✨ এক ক্লিকে সব গ্রুপ/চ্যানেল ✨📁",
              url="https://t.me/addlist/F5fxxWGnll43MDY1",
          )
      ],
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  try:
    await context.bot.send_message(
        chat_id=TARGET_GROUP_ID,
        text=(
            "🔥 **বিশাল অফার!** 🔥\n\n✨ **যা যা উপভোগ করতে পারবেন:**\n🔹 ব্যাচেলর"
            " পয়েন্ট নাটক\n🔞 হট ভিডিও\n🎬 হিন্দি ড্রামা ও মুভি\n🎞️ বাংলা সিনেমা ও"
            " নাটক\n🕵️ সিআইডি নাটক\n\n👇 **এখনই নিচে দেওয়া বাটনে ক্লিক করে"
            " উপভোগ করুন আপনার পছন্দের ক্যাটাগরি!**"
        ),
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
  except Exception as e:
    print(f"Error sending auto menu: {e}")


# ২. লিংক রিমুভ ও ৩ বার ওয়ার্নিং ও ১ ঘণ্টা মিউট সিস্টেম
async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or not update.message.text:
    return

  message = update.message
  user = message.from_user

  if user.username and user.username.lower() == ADMIN_USERNAME.lower():
    return

  text = message.text
  if "http://" in text or "https://" in text or "t.me/" in text:
    try:
      await message.delete()
    except Exception:
      pass

    user_id = user.id
    warnings[user_id] = warnings.get(user_id, 0) + 1
    count = warnings[user_id]

    if count < 3:
      await context.bot.send_message(
          chat_id=message.chat_id,
          text=(
              f"@{user.username or user.first_name}, গ্রুপে লিংক শেয়ার করা"
              f" নিষিদ্ধ! আপনার ওয়ার্নিং: {count}/3"
          ),
      )
    else:
      try:
        await context.bot.restrict_chat_member(
            chat_id=message.chat_id,
            user_id=user_id,
            permissions={
                "can_send_messages": False,
                "can_send_media_messages": False,
                "can_send_other_messages": False,
            },
            until_date=timedelta(hours=1),
        )
        await context.bot.send_message(
            chat_id=message.chat_id,
            text=(
                f"@{user.username or user.first_name} ৩ বার লিংক শেয়ার করার"
                " কারণে ১ ঘণ্টার জন্য মিউট করা হয়েছে।"
            ),
        )
        warnings[user_id] = 0
      except Exception as e:
        print(f"Error muting user: {e}")


# ৩. প্রাইভেট চ্যানেল থেকে ভিডিও রিসিভ করার ফাংশন
async def receive_channel_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  message = update.channel_post or update.effective_message
  if not message:
    return

  if message.video or message.document:
    caption = message.caption.lower() if message.caption else ""

    if "hot" in caption:
      videos["hot"].append(message.message_id)
      print(f"✅ Hot video saved! Message ID: {message.message_id}")
    elif "bachelor" in caption:
      videos["bachelor"].append(message.message_id)
      print(f"✅ Bachelor video saved! Message ID: {message.message_id}")
    elif "natok" in caption:
      videos["natok"].append(message.message_id)
      print(f"✅ Natok video saved! Message ID: {message.message_id}")
    elif "hindi" in caption:
      videos["hindi"].append(message.message_id)
      print(f"✅ Hindi video saved! Message ID: {message.message_id}")
    elif "cid" in caption:
      videos["cid"].append(message.message_id)
      print(f"✅ CID video saved! Message ID: {message.message_id}")


# ৪. ইউজার ইনবক্সে আসলে ফরোয়ার্ডের বদলে কপি করে ভিডিও পাঠানো (চ্যানেলের নাম হাইড থাকবে)
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  args = context.args

  if not args:
    await update.message.reply_text(
        "🎉 আপনাকে স্বাগতম!\n\n👇 আপনার পছন্দের ক্যাটাগরি নির্বাচন করুন"
    )
    return

  category = args[0].lower()
  target_list = []

  cat_names = {
      "hot": "হট ভিডিও",
      "bachelor": "ব্যাচেলর পয়েন্ট নাটক",
      "natok": "বাংলা সিনেমা নাটক",
      "hindi": "হিন্দি ড্রামা / মুভি",
      "cid": "CID নাটক",
  }

  if category in cat_names:
    await update.message.reply_text(
        f"⏳ একটু অপেক্ষা করুন, আপনার {cat_names[category]} সংগ্রহ করা হচ্ছে..."
    )

  if category == "hot":
    target_list = videos["hot"]
  elif category == "bachelor":
    target_list = videos["bachelor"]
  elif category == "natok":
    target_list = videos["natok"]
  elif category == "hindi":
    target_list = videos["hindi"]
  elif category == "cid":
    target_list = videos["cid"]

  if target_list:
    latest_msg_id = target_list[-1]
    try:
      # forward_message এর বদলে copy_message ব্যবহার করা হয়েছে যাতে চ্যানেলের নাম না দেখায়
      await context.bot.copy_message(
          chat_id=user.id,
          from_chat_id=PRIVATE_CHANNEL_ID,
          message_id=latest_msg_id,
      )
    except Exception as e:
      print(f"Copy message error: {e}")
      await update.message.reply_text(
          "❌ ভিডিও পাঠাতে সমস্যা হয়েছে। দয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
      )
  else:
    await update.message.reply_text(
        "⚠️ এই ক্যাটাগরিতে বর্তমানে কোনো ভিডিও আপলোড করা হয়নি। দয়া করে একটু"
        " পর চেষ্টা করুন।"
    )


# ৫. স্ট্যাটাস চেক করার কমান্ড (/status)
async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  if not user.username or user.username.lower() != ADMIN_USERNAME.lower():
    return

  status_text = (
      f"📊 বটের ডাটাবেজ স্ট্যাটাস:\n"
      f"- হট ভিডিও: {len(videos['hot'])}\n"
      f"- ব্যাচেলর পয়েন্ট: {len(videos['bachelor'])}\n"
      f"- বাংলা সিনেমা নাটক: {len(videos['natok'])}\n"
      f"- হিন্দি ড্রামা/মুভি: {len(videos['hindi'])}\n"
      f"- CID নাটক: {len(videos['cid'])}"
  )
  await update.message.reply_text(status_text)


def main():
  application = ApplicationBuilder().token(TOKEN).build()

  # প্রতি ১ মিনিট পর পর গ্রুপে মেনু পাঠানোর লুপ
  job_queue = application.job_queue
  job_queue.run_repeating(send_auto_video_menu, interval=60, first=5)

  # হ্যান্ডলার রেজিস্ট্রেশন
  application.add_handler(CommandHandler("start", start_handler))
  application.add_handler(CommandHandler("status", admin_status))
  application.add_handler(
      MessageHandler(filters.TEXT & (~filters.COMMAND), check_links)
  )

  application.add_handler(
      MessageHandler(
          filters.VIDEO | filters.Document.ALL, receive_channel_video
      )
  )

  print(
      "Bot is running successfully with clean copy_message feature (No channel"
      " watermark)..."
  )
  application.run_polling()


if __name__ == "__main__":
  main()

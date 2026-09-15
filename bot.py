import asyncio
from datetime import timedelta
import logging
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

# মেমোরি ডাটাবেজ (দীর্ঘ সময় ভিডিও সেভ রাখার জন্য)
warnings = {}
videos = {
    "hot": [],
    "bachelor": [],
    "natok": [],
    "hindi": [],
    "cid": [],
}

# গ্রুপে পাঠানো শেষ মেনু মেসেজ আইডি ট্র্যাক করার জন্য
last_sent_menu_id = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# নির্দিষ্ট সময় পর গ্রুপ থেকে মেসেজ ডিলিট করার ফাংশন
async def delete_message_after_delay(context, chat_id, message_id, delay_seconds):
  await asyncio.sleep(delay_seconds)
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


# ১. গ্রুপে অটো বাটন পাঠানোর ফাংশন (প্রতি ২ মিনিট পর পর, ৩০ সেকেন্ড পর অটো ডিলিট)
async def send_auto_video_menu(context: ContextTypes.DEFAULT_TYPE):
  global last_sent_menu_id
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

  # পূর্বে পাঠানো মেনু মেসেজ থাকলে তা আগে ডিলিট করে দেওয়া
  if last_sent_menu_id:
    try:
      await context.bot.delete_message(
          chat_id=TARGET_GROUP_ID, message_id=last_sent_menu_id
      )
    except Exception:
      pass

  try:
    sent_msg = await context.bot.send_message(
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
    last_sent_menu_id = sent_msg.message_id

    # ৩০ সেকেন্ড পর গ্রুপ থেকে মেসেজটি স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যাবে
    asyncio.create_task(
        delete_message_after_delay(
            context, TARGET_GROUP_ID, sent_msg.message_id, 30
        )
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


# ভিডিও প্রসেস করে ডিকশনারিতে স্থায়ীভাবে সেভ করার ফাংশন
def process_and_store_message(message):
  if message.video or message.document:
    caption = message.caption.lower() if message.caption else ""

    if "hot" in caption:
      if message.message_id not in videos["hot"]:
        videos["hot"].append(message.message_id)
    elif "bachelor" in caption:
      if message.message_id not in videos["bachelor"]:
        videos["bachelor"].append(message.message_id)
    elif "natok" in caption:
      if message.message_id not in videos["natok"]:
        videos["natok"].append(message.message_id)
    elif "hindi" in caption:
      if message.message_id not in videos["hindi"]:
        videos["hindi"].append(message.message_id)
    elif "cid" in caption:
      if message.message_id not in videos["cid"]:
        videos["cid"].append(message.message_id)


# ৩. প্রাইভেট চ্যানেল থেকে নতুন ভিডিও আসলে রিয়েল-টাইমে সেভ করার ফাংশন
async def receive_channel_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  message = update.channel_post or update.effective_message
  if not message:
    return
  process_and_store_message(message)


# পুরনো ভিডিওগুলো স্ক্যান করে ডাটাবেজে স্থায়ীভাবে লোড করার ফাংশন (৩-৪ মাসের পুরনো ভিডিও)
async def load_old_videos_from_channel(bot):
  print("🔄 প্রাইভেট চ্যানেলের পুরনো ভিডিও স্ক্যান ও ডাটাবেজে সংরক্ষণ শুরু...")
  try:
    for msg_id in range(1, 5000):
      try:
        chat_msg = await bot.get_message(
            chat_id=PRIVATE_CHANNEL_ID, message_id=msg_id
        )
        if chat_msg:
          process_and_store_message(chat_msg)
      except Exception:
        pass
    print("✅ স্ক্যান সম্পন্ন! সকল পুরনো ভিডিও ডাটাবেজে নিরাপদে সংরক্ষিত হয়েছে।")
  except Exception as e:
    print(f"Error scanning old messages: {e}")


# ৪. ইউজার ইনবক্সে আসলে কোনো জয়েন করার শর্ত ছাড়াই সরাসরি ভিডিও পাঠানো
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
        "⚠️ এই ক্যাটাগরিতে বর্তমানে কোনো ভিডিও পাওয়া যায়নি। দয়া করে একটু পর"
        " চেষ্টা করুন।"
    )


# ৫. স্ট্যাটাস চেক করার কমান্ড (/status)
async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  if not user.username or user.username.lower() != ADMIN_USERNAME.lower():
    return

  status_text = (
      f"📊 বটের দীর্ঘমেয়াদী ডাটাবেজ স্ট্যাটাস:\n"
      f"- হট ভিডিও: {len(videos['hot'])}\n"
      f"- ব্যাচেলর পয়েন্ট: {len(videos['bachelor'])}\n"
      f"- বাংলা সিনেমা নাটক: {len(videos['natok'])}\n"
      f"- হিন্দি ড্রামা/মুভি: {len(videos['hindi'])}\n"
      f"- CID নাটক: {len(videos['cid'])}"
  )
  await update.message.reply_text(status_text)


def main():
  application = ApplicationBuilder().token(TOKEN).build()

  # বট চালু হওয়ার সাথে সাথে প্রাইভেট চ্যানেলের পুরনো ভিডিও স্ক্যান করে লোড করবে
  async def post_init(app):
    await load_old_videos_from_channel(app.bot)

  application.post_init = post_init

  # প্রতি ২ মিনিট (১২০ সেকেন্ড) পর পর গ্রুপে মেনু পাঠানোর লুপ
  job_queue = application.job_queue
  job_queue.run_repeating(send_auto_video_menu, interval=120, first=5)

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

  print("Bot is running successfully with all requested features!")
  application.run_polling()


if __name__ == "__main__":
  main()

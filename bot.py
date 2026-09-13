import asyncio
from datetime import timedelta
import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# === আপনার কনফিগারেশন তথ্যসমূহ ===
TOKEN = "7971620957:AAH246ssazEKmF-dDvZwHLtX7QZIsA0deuY"  # বটের টোকেন
ADMIN_USERNAME = "kawsar123450"  # আপনার টেলিগ্রাম ইউজারনেম (মালিক)

# আপনার প্রাইভেট চ্যানেল আইডি (মুভি চ্যানেল)
PRIVATE_CHANNEL_ID = -1003967128934

# আপনার ৩টি গ্রুপের আইডি একসাথে এখানে সেট করা হলো
GROUP_IDS = [
    -1004362653651,  # হিন্দি বাংলা সিনেমা গুরু
    -1004300669395,  # সার্ভিস গ্রুপ
    -1003986096637,  # নিউ মুভি chat
]

# আপনার দেওয়া ৮টি চ্যানেল ও গ্রুপের লিংক দিয়ে সাজানো বাটন লিস্ট
CHANNEL_BUTTONS = [
    [
        InlineKeyboardButton(
            "🔗 চ্যানেল/গ্রুপ লিংক ১", url="https://t.me/+YVDafDISqdMxNTVl"
        )
    ],
    [
        InlineKeyboardButton(
            "🕵️‍♂️ CID Season S2", url="https://t.me/CID_Season_S2o"
        )
    ],
    [
        InlineKeyboardButton(
            "📢 মেইন চ্যানেল", url="https://t.me/kawsaralom76410"
        )
    ],
    [
        InlineKeyboardButton(
            "🔗 চ্যানেল/গ্রুপ লিংক ৪", url="https://t.me/+L0o2S0oxgeNlN2Q1"
        )
    ],
    [
        InlineKeyboardButton(
            "🔗 চ্যানেল/গ্রুপ লিংক ৫", url="https://t.me/+wkl-d8aJChtjMGU1"
        )
    ],
    [
        InlineKeyboardButton(
            "🔗 চ্যানেল/গ্রুপ লিংক ৬", url="https://t.me/+Pb8z-Fv8K6o2NjA1"
        )
    ],
    [
        InlineKeyboardButton(
            "👤 অফিশিয়াল আইডি/চ্যানেল", url="https://t.me/kawsar7641"
        )
    ],
    [
        InlineKeyboardButton(
            "🎬 ব্যাকআপ মুভি গ্রুপ", url="https://t.me/Demogroup764"
        )
    ],
]

# মেমোরি ডাটাবেজ
warnings = {}
videos = {
    "hot": [],
    "bachelor": [],
    "natok": [],
    "hindi": [],
    "cid": [],
}
menu_image_id = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ১. ৩টি গ্রুপেই ছবিসহ অটো বাটন পাঠানো এবং ৫০ সেকেন্ড পর ডিলিট করার ফাংশন
async def send_auto_video_menu(context: ContextTypes.DEFAULT_TYPE):
  global menu_image_id
  bot_username = (await context.bot.get_me()).username

  # মূল ক্যাটাগরি মেনু বাটন (ইনবক্সে যাওয়ার জন্য url ব্যবহার করা হয়েছে)
  keyboard = [
      [
          InlineKeyboardButton(
              "🔥🔞 হট ভিডিও তালিকা 🔞🔥",
              url=f"https://t.me/{bot_username}?start=menu_hot",
          )
      ],
      [
          InlineKeyboardButton(
              "🎭🔥 ব্যাচেলর পয়েন্ট নাটক 🔥🎭",
              url=f"https://t.me/{bot_username}?start=menu_bachelor",
          )
      ],
      [
          InlineKeyboardButton(
              "🎬🍿 বাংলা সিনেমা নাটক 🍿🎬",
              url=f"https://t.me/{bot_username}?start=menu_natok",
          )
      ],
      [
          InlineKeyboardButton(
              "🇮🇳🎥 হিন্দি ড্রামা / মুভি 🎥🇮🇳",
              url=f"https://t.me/{bot_username}?start=menu_hindi",
          )
      ],
      [
          InlineKeyboardButton(
              "🕵️‍♂️🔥 CID নাটক তালিকা 🔥🕵️‍♂️",
              url=f"https://t.me/{bot_username}?start=menu_cid",
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

  menu_caption = (
      "🔥 **বিশাল অফার ও বিনোদন জগৎ!** 🔥\n\n✨ **যা যা উপভোগ করতে পারবেন:**\n🔹"
      " ব্যাচেলর পয়েন্ট নাটক\n🔞 হট ভিডিও (সব পর্ব একসাথে)\n🎬 হিন্দি ড্রামা ও মুভি\n🎞️"
      " বাংলা সিনেমা ও নাটক\n🕵️ সিআইডি নাটক (সকল পর্ব)\n\n👇 **বটের ইনবক্সে গিয়ে"
      " এক ক্লিকে সব ভিডিও পেতে যেকোনো একটিতে ক্লিক করুন!**"
  )

  for group_id in GROUP_IDS:
    try:
      if menu_image_id:
        sent_message = await context.bot.copy_message(
            chat_id=group_id,
            from_chat_id=PRIVATE_CHANNEL_ID,
            message_id=menu_image_id,
            caption=menu_caption,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
      else:
        sent_message = await context.bot.send_message(
            chat_id=group_id,
            text=menu_caption,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

      asyncio.create_task(
          delete_menu_after_delay(context, group_id, sent_message.message_id)
      )

    except Exception as e:
      print(f"Error sending auto menu to {group_id}: {e}")


async def delete_menu_after_delay(context, chat_id, message_id):
  await asyncio.sleep(50)
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception as e:
    print(f"Error deleting menu message: {e}")


# ২. নিখুঁত লিংক ও ইউজারনেম ফিল্টার সিস্টেম (গ্রুপের জন্য)
async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message:
    return

  if update.message.chat_id not in GROUP_IDS:
    return

  message = update.message
  user = message.from_user
  is_admin = user.username and user.username.lower() == ADMIN_USERNAME.lower()

  text = message.text or message.caption or ""
  has_link = (
      "http://" in text
      or "https://" in text
      or "t.me/" in text
      or bool(re.search(r"@\w+", text))
  )

  if not is_admin and has_link:
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
              f"@{user.username or user.first_name}, গ্রুপে লিংক বা ইউজারনেম"
              f" শেয়ার করা নিষিদ্ধ! আপনার ওয়ার্নিং: {count}/3"
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
    return

  if not is_admin:
    asyncio.create_task(
        delete_user_message_after_delay(
            context, message.chat_id, message.message_id
        )
    )


async def delete_user_message_after_delay(context, chat_id, message_id):
  await asyncio.sleep(1800)
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


# ৩. প্রাইভেট চ্যানেল থেকে ভিডিও এবং ক্যাপশন সেভ করা
async def receive_channel_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  global menu_image_id
  message = update.channel_post or update.effective_message
  if not message:
    return

  caption = message.caption.lower() if message.caption else ""

  if message.photo and "menu" in caption:
    menu_image_id = message.message_id
    print(f"✅ Menu image updated! Message ID: {menu_image_id}")
    return

  if message.video or message.document or message.photo:
    original_caption = message.caption or "নামবিহীন ভিডিও"
    video_data = {
        "message_id": message.message_id,
        "caption": original_caption,
    }

    if "hot" in caption:
      videos["hot"].append(video_data)
      print(f"✅ Hot video saved: {original_caption}")
    elif "bachelor" in caption:
      videos["bachelor"].append(video_data)
      print(f"✅ Bachelor video saved: {original_caption}")
    elif "natok" in caption:
      videos["natok"].append(video_data)
      print(f"✅ Natok video saved: {original_caption}")
    elif "hindi" in caption:
      videos["hindi"].append(video_data)
      print(f"✅ Hindi video saved: {original_caption}")
    elif "cid" in caption:
      videos["cid"].append(video_data)
      print(f"✅ CID video saved: {original_caption}")


# ৪. ইউজার ইনবক্সে আসলে বা লিংকে ক্লিক করলে এক ক্লিকে সব ভিডিও ৮টি চ্যানেলের লিংক বাটনসহ পাঠিয়ে দেওয়া
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  args = context.args
  chat_id = update.message.chat_id

  cat_display_names = {
      "menu_hot": ("hot", "🔥🔞 হট ভিডিও সমাহার"),
      "menu_bachelor": ("bachelor", "🎭🔥 ব্যাচেলর পয়েন্ট নাটক"),
      "menu_natok": ("natok", "🎬🍿 বাংলা সিনেমা ও নাটক"),
      "menu_hindi": ("hindi", "🇮🇳🎥 হিন্দি ড্রামা ও মুভি"),
      "menu_cid": ("cid", "🕵️‍♂️🔥 CID নাটকের সকল পর্ব"),
  }

  if args and args[0] in cat_display_names:
    cat_key, cat_title = cat_display_names[args[0]]
    target_list = videos.get(cat_key, [])

    if not target_list:
      await update.message.reply_text(
          f"⚠️ এই মুহূর্তে **{cat_title}**-তে কোনো ভিডিও আপলোড করা হয়নি।"
      )
      return

    await update.message.reply_text(
        f"🚀 **{cat_title}**-এর সমস্ত ভিডিও আপনার ইনবক্সে পাঠানো হচ্ছে,"
        " একটু অপেক্ষা করুন..."
    )

    # আপনার ৮টি চ্যানেলের লিংক বাটন প্রস্তুত করা হলো
    video_markup = InlineKeyboardMarkup(CHANNEL_BUTTONS)

    # এক ক্লিকে ওই ক্যাটাগরির আন্ডারে থাকা সব ভিডিও ক্যাপশন ঠিক রেখে ৮টি লিংক বাটনসহ পাঠিয়ে দেওয়া
    for item in target_list:
      try:
        sent_msg = await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=PRIVATE_CHANNEL_ID,
            message_id=item["message_id"],
            reply_markup=video_markup,
        )

        # ইনবক্সে পাঠানো প্রতিটি ভিডিওর ওপর ২০ মিনিটের অটো-ডিলিট টাইমার সেট করা
        asyncio.create_task(
            delete_inbox_video_after_delay(context, chat_id, sent_msg.message_id)
        )
        await asyncio.sleep(0.5)  # টেলিগ্রাম ফ্লাড লিমিট এড়ানোর জন্য সামান্য বিরতি
      except Exception as e:
        print(f"Error sending video: {e}")

    await update.message.reply_text(
        "⏱️ উপরের সমস্ত ভিডিও আপনার ইনবক্সে সফলভাবে পাঠানো হয়েছে। নিরাপত্তা"
        " বা গোপনীয়তার কারণে প্রতিটি ভিডিও ঠিক **২০ মিনিট পর** ইনবক্স থেকে"
        " স্বয়ংক্রিয়ভাবে মুছে যাবে।"
    )
    return

  # সাধারণ স্টার্ট মেসেজ
  await update.message.reply_text(
      "🎉 বটের ইনবক্সে আপনাকে স্বাগতম!\n\nদয়া করে গ্রুপে দেওয়া মেনু থেকে আপনার"
      " পছন্দের ক্যাটাগরিতে ক্লিক করুন।"
  )


# ইনবক্স থেকে ভিডিও ২০ মিনিট পর ডিলিট করার ফাংশন
async def delete_inbox_video_after_delay(context, chat_id, message_id):
  await asyncio.sleep(1200)  # ১২০০ সেকেন্ড = ২০ মিনিট
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


# ৫. স্ট্যাটাস চেক করার কমান্ড (/status)
async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  if not user.username or user.username.lower() != ADMIN_USERNAME.lower():
    return

  status_text = (
      f"📊 বটের ডাটাবেজ স্ট্যাটাস:\n"
      f"- মেনু ছবি সেট?: {'হ্যাঁ' if menu_image_id else 'না'}\n"
      f"- হট ভিডিও মোট: {len(videos['hot'])}\n"
      f"- ব্যাচেলর পয়েন্ট মোট: {len(videos['bachelor'])}\n"
      f"- বাংলা সিনেমা নাটক মোট: {len(videos['natok'])}\n"
      f"- হিন্দি ড্রামা/মুভি মোট: {len(videos['hindi'])}\n"
      f"- CID নাটক মোট: {len(videos['cid'])}"
  )
  await update.message.reply_text(status_text)


def main():
  application = (
      ApplicationBuilder()
      .token(TOKEN)
      .read_timeout(30)
      .write_timeout(30)
      .connect_timeout(30)
      .build()
  )

  job_queue = application.job_queue
  job_queue.run_repeating(send_auto_video_menu, interval=60, first=5)

  application.add_handler(CommandHandler("start", start_handler))
  application.add_handler(CommandHandler("status", admin_status))
  application.add_handler(
      MessageHandler(filters.TEXT & (~filters.COMMAND), check_links)
  )

  application.add_handler(
      MessageHandler(
          filters.VIDEO | filters.Document.ALL | filters.PHOTO,
          receive_channel_video,
      )
  )

  print(
      "Bot is running with 8 Channel Buttons, Original Captions Preserved &"
      " 20-min Auto-Delete!"
  )
  application.run_polling()


if __name__ == "__main__":
  main()

import asyncio
from datetime import timedelta
import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
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
      " ব্যাচেলর পয়েন্ট নাটক\n🔞 হট ভিডিও (পর্বসহ)\n🎬 হিন্দি ড্রামা ও মুভি\n🎞️ বাংলা"
      " সিনেমা ও নাটক\n🕵️ সিআইডি নাটক (সকল পর্ব)\n\n👇 **বটের ইনবক্সে গিয়ে"
      " পছন্দের ক্যাটাগরিতে ক্লিক করুন!**"
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

  # টেক্সট অথবা ক্যাপশন চেক করার জন্য
  text = message.text or message.caption or ""

  # লিংক বা টেলিগ্রাম ইউজারনেম চেনার জন্য প্যাটার্ন (http, https, t.me, @username ইত্যাদি)
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

  # ইউজারদের সাধারণ মেসেজগুলো ৩০ মিনিট পর ডিলিট হবে
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


# ৪. ইউজার ইনবক্সে আসলে বা `/start` কমান্ড দিলে ক্যাটাগরির লিস্ট দেখানো
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  args = context.args

  cat_display_names = {
      "menu_hot": ("hot", "🔥🔞 হট ভিডিও সমাহার"),
      "menu_bachelor": ("bachelor", "🎭🔥 ব্যাচেলর পয়েন্ট নাটক"),
      "menu_natok": ("natok", "🎬🍿 বাংলা সিনেমা ও নাটক"),
      "menu_hindi": ("hindi", "🇮🇳🎥 হিন্দি ড্রামা ও মুভি"),
      "menu_cid": ("cid", "🕵️‍♂️🔥 CID নাটকের সকল পর্ব"),
  }

  # যদি ইউজার গ্রুপ থেকে লিংকে ক্লিক করে সরাসরি কোনো ক্যাটাগরিতে আসে
  if args and args[0] in cat_display_names:
    cat_key, cat_title = cat_display_names[args[0]]
    target_list = videos.get(cat_key, [])

    if not target_list:
      await update.message.reply_text(
          f"⚠️ এই মুহূর্তে **{cat_title}**-তে কোনো ভিডিও আপলোড করা হয়নি।"
      )
      return

    keyboard = []
    for idx, item in enumerate(target_list):
      btn_text = item["caption"].split("\n")[0]
      callback_data = f"getvid_{cat_key}_{idx}"
      keyboard.append(
          [InlineKeyboardButton(btn_text, callback_data=callback_data)]
      )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📂 **{cat_title}**\n\nনিচে আপনার পছন্দের ভিডিও বা পর্বটিতে ক্লিক"
        " করুন, সেটি সরাসরি আপনার ইনবক্সে চলে আসবে! 👇",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return

  # সাধারণ স্টার্ট মেসেজ
  await update.message.reply_text(
      "🎉 বটের ইনবক্সে আপনাকে স্বাগতম!\n\nদয়া করে গ্রুপে দেওয়া মেনু থেকে আপনার"
      " পছন্দের ক্যাটাগরিতে ক্লিক করুন।"
  )


# ৫. ইনবক্সে ইনলাইন বাটন হ্যান্ডেল করা (ক্যাটাগরি লিস্ট দেখানোর জন্য)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  data = query.data
  if not data.startswith("menu_"):
    return

  category = data.split("_")[1]
  target_list = videos.get(category, [])

  cat_display_names = {
      "hot": "🔥🔞 হট ভিডিও সমাহার",
      "bachelor": "🎭🔥 ব্যাচেলর পয়েন্ট নাটক",
      "natok": "🎬🍿 বাংলা সিনেমা ও নাটক",
      "hindi": "🇮🇳🎥 হিন্দি ড্রামা ও মুভি",
      "cid": "🕵️‍♂️🔥 CID নাটকের সকল পর্ব",
  }

  if not target_list:
    await query.message.reply_text(
        f"⚠️ এই মুহূর্তে **{cat_display_names.get(category, 'ক্যাটাগরি')}**-তে কোনো"
        " ভিডিও নেই।"
    )
    return

  keyboard = []
  for idx, item in enumerate(target_list):
    btn_text = item["caption"].split("\n")[0]
    callback_data = f"getvid_{category}_{idx}"
    keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])

  reply_markup = InlineKeyboardMarkup(keyboard)

  await query.message.reply_text(
      f"📂 **{cat_display_names.get(category, 'তালিকা')}**\n\nনিচে আপনার"
      " পছন্দের ভিডিও বা পর্বটিতে ক্লিক করুন, সাথে সাথে ইনবক্সে চলে আসবে! 👇",
      reply_markup=reply_markup,
      parse_mode="Markdown",
  )


# ৬. ইউজার নির্দিষ্ট ভিডিওতে ক্লিক করলে সরাসরি ইনবক্সে পাঠানো এবং ২০ মিনিট পর অটো-ডিলিট করা
async def send_specific_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer("আপনার ভিডিওটি ইনবক্সে পাঠানো হচ্ছে...")

  data = query.data
  if not data.startswith("getvid_"):
    return

  parts = data.split("_")
  category = parts[1]
  index = int(parts[2])

  target_list = videos.get(category, [])
  if index < len(target_list):
    video_item = target_list[index]
    try:
      # সরাসরি ইউজারের ইনবক্সে ভিডিও পাঠানো হচ্ছে
      sent_msg = await context.bot.copy_message(
          chat_id=query.message.chat_id,
          from_chat_id=PRIVATE_CHANNEL_ID,
          message_id=video_item["message_id"],
      )

      # ইনবক্সে পাঠানো ভিডিওটি ঠিক ২০ মিনিট (১২০০ সেকেন্ড) পর অটোমেটিক ডিলিট করার টাস্ক
      asyncio.create_task(
          delete_inbox_video_after_delay(
              context, query.message.chat_id, sent_msg.message_id
          )
      )

      # ইউজারকে একটি ছোট নোটিফিকেশন দেওয়া যে ভিডিওটি ২০ মিনিট পর ডিলিট হবে
      await query.message.reply_text(
          "⏱️ এই ভিডিওটি আপনার ইনবক্সে পাঠানো হয়েছে এবং নিরাপত্তা বা গোপনীয়তার"
          " কারণে ঠিক **২০ মিনিট পর** ইনবক্স থেকে স্বয়ংক্রিয়ভাবে মুছে যাবে।"
      )

    except Exception as e:
      print(f"Error sending video: {e}")
      await query.message.reply_text(
          "❌ ভিডিওটি পাঠাতে সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।"
      )
  else:
    await query.message.reply_text(
        "⚠️ দুঃখিত, এই ভিডিওটি খুঁজে পাওয়া যায়নি।"
    )


# ইনবক্স থেকে ভিডিও ২০ মিনিট পর ডিলিট করার ফাংশন
async def delete_inbox_video_after_delay(context, chat_id, message_id):
  await asyncio.sleep(1200)  # ১২০০ সেকেন্ড = ২০ মিনিট
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


# ৭. স্ট্যাটাস চেক করার কমান্ড (/status)
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
  application = ApplicationBuilder().token(TOKEN).build()

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

  application.add_handler(
      CallbackQueryHandler(button_handler, pattern="^menu_")
  )
  application.add_handler(
      CallbackQueryHandler(send_specific_video, pattern="^getvid_")
  )

  print("Bot is running with Inbox Delivery, 20-min Auto-Delete & Strict Links!")
  application.run_polling()


if __name__ == "__main__":
  main()

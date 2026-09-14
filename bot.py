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
ADMIN_USERNAME = "kawsar123450"  # আপনার টেলিগ্রাম ইউজারনেম (মালিক - ফুল বাইপাস পাবেন)

# আপনার প্রাইভেট চ্যানেল আইডি (মুভি চ্যানেল)
PRIVATE_CHANNEL_ID = -1003967128934

# আপনার ৩টি গ্রুপের আইডি (যেখানে লিংক ও ইউজারনেম ফিল্টার হবে এবং পোস্ট যাবে)
GROUP_IDS = [
    -1004362653651,  # হিন্দি বাংলা সিনেমা গুরু
    -1004300669395,  # সার্ভিস গ্রুপ
    -1003986096637,  # নিউ মুভি chat
]

# আপনার দেওয়া ৫টি টার্গেট চ্যানেল (যেগুলোতে প্রতি ১ মিনিট পর পর অটো পোস্ট যাবে এবং ফোর্স সাবস্ক্রাইব চেক হবে)
TARGET_CHANNELS = [
    {
        "id": -1003067466801,
        "name": "নিউ মুভি",
        "url": "https://t.me/+YVDafDISqdMxNTVl",
    },
    {
        "id": -1004302390586,
        "name": "তানিয়া আক্তার হট ভিডিও",
        "url": "https://t.me/CID_Season_S2o",
    },
    {
        "id": -1004395034930,
        "name": "হট ভিডিও",
        "url": "https://t.me/kawsaralom76410",
    },
    {
        "id": -1004296342087,
        "name": "CID Bangla Season 2",
        "url": "https://t.me/CID_Season_S2o",
    },
    {
        "id": -1004484108921,
        "name": "মুভি সিআইডি ব্যাচালার নাটক",
        "url": "https://t.me/Demogroup764",
    },
]

# আপনার দেওয়া ৮টি চ্যানেল ও গ্রুপের লিংক দিয়ে সাজানো বাটন লিস্ট (ভিডিওর সাথে পাঠানো হবে)
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
    "hot": [],  # হট ভিডিও (কোনো ট্যাগ বা কমান্ড ছাড়াই অটো সেভ হবে)
    "bachelor": [],
    "natok": [],
    "hindi": [],
    "cid": [],
}

# ৫টি আলাদা মেনু পোস্টার (ছবি বা ভিডিও উভয়ই হতে পারে) সেভ করার লিস্ট
menu_items = [None, None, None, None, None]
menu_index = 0

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ১. ফোর্স সাবস্ক্রাইব চেক করার ফাংশন
async def check_user_subscriptions(user_id, bot) -> bool:
  try:
    for ch in TARGET_CHANNELS:
      m = await bot.get_chat_member(chat_id=ch["id"], user_id=user_id)
      if m.status not in ["creator", "administrator", "member"]:
        return False
    return True
  except Exception:
    pass
  return False


# ২. ৫টি পোস্টার (ছবি বা ভিডিও) ঘুরিয়ে ফিরিয়ে প্রতি ১ মিনিট পর পর চ্যানেল ও গ্রুপে পাঠানোর ফাংশন
async def send_auto_video_menu(context: ContextTypes.DEFAULT_TYPE):
  global menu_index
  bot_username = (await context.bot.get_me()).username

  current_item_id = menu_items[menu_index % 5]
  menu_index = (menu_index + 1) % 5

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

  # টার্গেট ৫টি চ্যানেলে অটো পোস্ট
  for ch in TARGET_CHANNELS:
    try:
      if current_item_id:
        await context.bot.copy_message(
            chat_id=ch["id"],
            from_chat_id=PRIVATE_CHANNEL_ID,
            message_id=current_item_id,
            caption=menu_caption,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
      else:
        await context.bot.send_message(
            chat_id=ch["id"],
            text=menu_caption,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    except Exception as e:
      print(f"Error sending menu to channel {ch['id']}: {e}")

  # গ্রুপগুলোতে অটো পোস্ট এবং ৫০ সেকেন্ড পর ডিলিট
  for group_id in GROUP_IDS:
    try:
      if current_item_id:
        sent_message = await context.bot.copy_message(
            chat_id=group_id,
            from_chat_id=PRIVATE_CHANNEL_ID,
            message_id=current_item_id,
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
      print(f"Error sending auto menu to group {group_id}: {e}")


async def delete_menu_after_delay(context, chat_id, message_id):
  await asyncio.sleep(50)
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


# ৩. লিংক ও ইউজারনেম ফিল্টার সিস্টেম (গ্রুপের জন্য)
async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or update.message.chat_id not in GROUP_IDS:
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


# ৪. প্রাইভেট চ্যানেল থেকে ভিডিও ও মেনু ক্যাটাগরি অটো-ডিটেক্ট করে সেভ করা
async def receive_channel_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  global menu_items
  message = update.channel_post or update.effective_message
  if not message:
    return

  caption = message.caption.lower() if message.caption else ""

  # মেনু পোস্টার চেক (menu1 থেকে menu5)
  if message.photo or message.video:
    if "menu1" in caption:
      menu_items[0] = message.message_id
      return
    elif "menu2" in caption:
      menu_items[1] = message.message_id
      return
    elif "menu3" in caption:
      menu_items[2] = message.message_id
      return
    elif "menu4" in caption:
      menu_items[3] = message.message_id
      return
    elif "menu5" in caption:
      menu_items[4] = message.message_id
      return

  # ভিডিও বা ডকুমেন্ট বা ছবি সেভিং লজিক
  if message.video or message.document or message.photo:
    original_caption = message.caption or "নামবিহীন ভিডিও"
    video_data = {
        "message_id": message.message_id,
        "caption": original_caption,
    }

    # নির্দিষ্ট ট্যাগ চেক (ব্যাচেলর, নাটক, হিন্দি, সিআইডি)
    if "bachelor" in caption:
      videos["bachelor"].append(video_data)
      print(f"✅ Bachelor video saved: {original_caption}")
    elif "natok" in caption:
      videos["natok"].append(video_data)
      print(f"✅ Natok video saved: {original_caption}")
    elif "hindi" in caption:
      videos["hindi"].append(video_data)
      print(f"✅ Hindi video saved: {original_caption}")
    elif "cid" in caption or "#cid" in caption:
      videos["cid"].append(video_data)
      print(f"✅ CID video saved: {original_caption}")
    else:
      # হট ভিডিও বা অন্য যেকোনো সাধারণ ভিডিও (যেগুলোতে কোনো ট্যাগ নেই) সরাসরি 'hot'-এ সেভ হবে
      videos["hot"].append(video_data)
      print(f"✅ Hot/Direct video saved: {original_caption}")


# মূল ভিডিও পাঠানোর কোর ফাংশন
async def deliver_videos_to_user(chat_id, cat_key, cat_title, context):
  target_list = videos.get(cat_key, [])
  if not target_list:
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚠️ এই মুহূর্তে **{cat_title}**-তে কোনো ভিডিও আপলোড করা হয়নি।",
    )
    return

  await context.bot.send_message(
      chat_id=chat_id,
      text=(
          f"🚀 **{cat_title}**-এর সমস্ত ভিডিও আপনার ইনবক্সে পাঠানো হচ্ছে,"
          " একটু অপেক্ষা করুন..."
      ),
  )

  video_markup = InlineKeyboardMarkup(CHANNEL_BUTTONS)
  for item in target_list:
    try:
      sent_msg = await context.bot.copy_message(
          chat_id=chat_id,
          from_chat_id=PRIVATE_CHANNEL_ID,
          message_id=item["message_id"],
          reply_markup=video_markup,
      )
      asyncio.create_task(
          delete_inbox_video_after_delay(context, chat_id, sent_msg.message_id)
      )
      await asyncio.sleep(0.5)
    except Exception as e:
      print(f"Error sending video: {e}")

  await context.bot.send_message(
      chat_id=chat_id,
      text=(
          "⏱️ সমস্ত ভিডিও পাঠানো সম্পন্ন হয়েছে। গোপনীয়তার কারণে প্রতিটি ভিডিও"
          " ঠিক **২০ মিনিট পর** ইনবক্স থেকে মুছে যাবে।"
      ),
  )


# ৫. স্টার্ট ও ক্যাটাগরি হ্যান্ডলার (ফোর্স সাবস্ক্রাইব চেকসহ)
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  args = context.args
  chat_id = update.message.chat_id
  is_admin = user.username and user.username.lower() == ADMIN_USERNAME.lower()

  cat_display_names = {
      "menu_hot": ("hot", "🔥🔞 হট ভিডিও সমাহার"),
      "menu_bachelor": ("bachelor", "🎭🔥 ব্যাচেলর পয়েন্ট নাটক"),
      "menu_natok": ("natok", "🎬🍿 বাংলা সিনেমা ও নাটক"),
      "menu_hindi": ("hindi", "🇮🇳🎥 হিন্দি ড্রামা ও মুভি"),
      "menu_cid": ("cid", "🕵️‍♂️🔥 CID নাটকের সকল পর্ব"),
  }

  if args and args[0] in cat_display_names:
    cat_key, cat_title = cat_display_names[args[0]]

    # যদি ইউজার এডমিন না হন, তবে ৫টি চ্যানেলের সাবস্ক্রিপশন চেক করবে
    if not is_admin:
      is_subscribed = await check_user_subscriptions(user.id, context.bot)
      if not is_subscribed:
        join_keyboard = []
        for ch in TARGET_CHANNELS:
          join_keyboard.append(
              [InlineKeyboardButton(f"👉 {ch['name']} এ জয়েন করুন", url=ch["url"])]
          )

        join_keyboard.append([
            InlineKeyboardButton(
                "✅ সাবস্ক্রাইব চেক করুন", callback_data=f"check_{args[0]}"
            )
        ])

        await update.message.reply_text(
            "⚠️ **ভিডিও দেখতে হলে নিচের ৫টি চ্যানেলে অবশ্যই জয়েন করতে হবে!**\n\nদয়া"
            " করে প্রতিটি চ্যানেলে জয়েন করে নিচের **'✅ সাবস্ক্রাইব চেক করুন'**"
            " বাটনে ক্লিক করুন।",
            reply_markup=InlineKeyboardMarkup(join_keyboard),
        )
        return

    # এডমিন অথবা সাবস্ক্রাইব করা থাকলে সরাসরি ভিডিও দিয়ে দেওয়া হবে
    await deliver_videos_to_user(chat_id, cat_key, cat_title, context)
    return

  await update.message.reply_text(
      "🎉 বটের ইনবক্সে আপনাকে স্বাগতম!\n\nদয়া করে গ্রুপে দেওয়া মেনু থেকে আপনার"
      " পছন্দের ক্যাটাগরিতে ক্লিক করুন।"
  )


# ৬. সাবস্ক্রাইব চেক বাটন ক্লিক হ্যান্ডলার (Callback Query)
async def button_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()
  user = query.from_user
  data = query.data

  if data.startswith("check_"):
    cat_arg = data.replace("check_", "")
    is_subscribed = await check_user_subscriptions(user.id, context.bot)

    if is_subscribed:
      await query.message.delete()
      cat_mapping = {
          "menu_hot": ("hot", "🔥🔞 হট ভিডিও সমাহার"),
          "menu_bachelor": ("bachelor", "🎭🔥 ব্যাচেলর পয়েন্ট নাটক"),
          "menu_natok": ("natok", "🎬🍿 বাংলা সিনেমা ও নাটক"),
          "menu_hindi": ("hindi", "🇮🇳🎥 হিন্দি ড্রামা ও মুভি"),
          "menu_cid": ("cid", "🕵️‍♂️🔥 CID নাটকের সকল পর্ব"),
      }
      if cat_arg in cat_mapping:
        cat_key, cat_title = cat_mapping[cat_arg]
        await deliver_videos_to_user(
            query.message.chat_id, cat_key, cat_title, context
        )
    else:
      await query.answer(
          "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি! দয়া করে সবগুলোতে জয়েন"
          " করে আবার চেক করুন।",
          show_alert=True,
      )


async def delete_inbox_video_after_delay(context, chat_id, message_id):
  await asyncio.sleep(1200)  # ২০ মিনিট
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


# ৭. স্ট্যাটাস চেক কমান্ড (/status)
async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  if not user.username or user.username.lower() != ADMIN_USERNAME.lower():
    return

  set_menus = sum(1 for m in menu_items if m is not None)
  status_text = (
      f"📊 বটের ডাটাবেজ স্ট্যাটাস:\n"
      f"- সেট করা মেনু পোস্টার: {set_menus}/5\n"
      f"- হট/ডাইরেক্ট ভিডিও মোট: {len(videos['hot'])}\n"
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
  application.add_handler(CallbackQueryHandler(button_callback_handler))
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
      "Bot is fully configured: Hot videos auto-saved without tag, specific tags"
      " preserved, Force Subscribe active!"
  )
  application.run_polling()


if __name__ == "__main__":
  main()

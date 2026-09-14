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

# === কনফিগারেশন তথ্যসমূহ ===
TOKEN = "7971620957:AAH246ssazEKmF-dDvZwHLtX7QZIsA0deuY"
ADMIN_USERNAME = "kawsar123450"

PRIVATE_CHANNEL_ID = -1003967128934

GROUP_IDS = [
    -1004362653651,
    -1004300669395,
    -1003986096637,
]

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

warnings = {}
videos = {"hot": [], "bachelor": [], "natok": [], "hindi": [], "cid": []}
menu_items = [None, None, None, None, None]
menu_index = 0
is_sending_menu = False

# গ্রুপে আগের পাঠানো বটের মেনু মেসেজ আইডিগুলো মনে রাখার ডিকশনারি
last_sent_menu_ids = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# ১. ফোর্স সাবস্ক্রাইব চেক
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


# ২. অটো মেনু পোস্টার পাঠানোর ফাংশন (আগের মেসেজ নিজে ডিলিট করে তারপর নতুন পাঠাবে)
async def send_auto_video_menu(context: ContextTypes.DEFAULT_TYPE):
  global menu_index, is_sending_menu, last_sent_menu_ids
  if is_sending_menu:
    return
  is_sending_menu = True

  try:
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

    # টার্গেট চ্যানেলগুলোতে পাঠানো
    for ch in TARGET_CHANNELS:
      try:
        chat_id = ch["id"]
        # চ্যানেলে আগের পাঠানো মেনু থাকলে তা ডিলিট করা
        if chat_id in last_sent_menu_ids:
          try:
            await context.bot.delete_message(
                chat_id=chat_id, message_id=last_sent_menu_ids[chat_id]
            )
          except Exception:
            pass

        if current_item_id:
          sent_msg = await context.bot.copy_message(
              chat_id=chat_id,
              from_chat_id=PRIVATE_CHANNEL_ID,
              message_id=current_item_id,
              caption=menu_caption,
              reply_markup=reply_markup,
              parse_mode="Markdown",
          )
        else:
          sent_msg = await context.bot.send_message(
              chat_id=chat_id,
              text=menu_caption,
              reply_markup=reply_markup,
              parse_mode="Markdown",
          )
        last_sent_menu_ids[chat_id] = sent_msg.message_id
        await asyncio.sleep(0.3)
      except Exception as e:
        print(f"Error sending menu to channel: {e}")

    # গ্রুপগুলোতে পাঠানো (আগে নিজের পাঠানো মেসেজ ডিলিট করে তারপর নতুন পাঠাবে)
    for group_id in GROUP_IDS:
      try:
        # গ্রুপে বটের আগের পাঠানো মেনু মেসেজ থাকলে তা তাৎক্ষণিক ডিলিট করা
        if group_id in last_sent_menu_ids:
          try:
            await context.bot.delete_message(
                chat_id=group_id, message_id=last_sent_menu_ids[group_id]
            )
          except Exception:
            pass

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

        # নতুন পাঠানো মেসেজ আইডিও সেভ করে রাখা হলো
        last_sent_menu_ids[group_id] = sent_message.message_id
        await asyncio.sleep(0.3)
      except Exception as e:
        print(f"Error sending auto menu to group: {e}")
  finally:
    is_sending_menu = False


# ৩. গ্রুপ ফিল্টার সিস্টেম
async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or update.message.chat_id not in GROUP_IDS:
    return

  message = update.message
  user = message.from_user
  if not user:
    return

  is_admin = user.username and user.username.lower() == ADMIN_USERNAME.lower()

  text = message.text or message.caption or ""
  has_link = (
      "http://" in text
      or "https://" in text
      or "t.me/" in text
      or bool(re.search(r"@\w+", text))
  )
  has_button = message.reply_markup and message.reply_markup.inline_keyboard
  is_forwarded = (
      message.forward_date is not None
      or message.forward_from is not None
      or message.forward_sender_name is not None
  )

  if not is_admin and (has_link or has_button or is_forwarded):
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
              f"@{user.username or user.first_name}, গ্রুপে লিংক, বাটন বা ফরোয়ার্ড"
              f" মেসেজ পাঠানো নিষিদ্ধ! আপনার ওয়ার্নিং: {count}/3"
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
                f"@{user.username or user.first_name} ৩ বার নিয়ম অমান্য করার"
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


# ভিডিও এবং মেনু প্রসেস করার ফাংশন
def process_and_store_message(message):
  global menu_items
  caption = message.caption.lower() if message.caption else ""

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

  if message.video or message.document or message.photo:
    original_caption = message.caption or "নামবিহীন ভিডিও"
    video_data = {
        "message_id": message.message_id,
        "caption": original_caption,
    }

    target_list = None
    if "bachelor" in caption:
      target_list = videos["bachelor"]
    elif "natok" in caption:
      target_list = videos["natok"]
    elif "hindi" in caption:
      target_list = videos["hindi"]
    elif "cid" in caption or "#cid" in caption:
      target_list = videos["cid"]
    else:
      target_list = videos["hot"]

    if not any(v["message_id"] == message.message_id for v in target_list):
      target_list.append(video_data)


async def receive_channel_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  message = update.channel_post or update.effective_message
  if not message:
    return
  process_and_store_message(message)


# ৪. প্রাইভেট চ্যানেলের পুরনো সব ভিডিও স্ক্যান ও লোড করার সিস্টেম
async def load_old_videos_from_channel(bot):
  print("🔄 প্রাইভেট চ্যানেলের পুরনো ভিডিও স্ক্যান করা হচ্ছে...")
  try:
    for msg_id in range(1, 300):
      try:
        chat_msg = await bot.get_message(
            chat_id=PRIVATE_CHANNEL_ID, message_id=msg_id
        )
        if chat_msg:
          process_and_store_message(chat_msg)
      except Exception:
        pass
    print("✅ পুরনো ভিডিও স্ক্যান ও ডাটাবেজে সংরক্ষণ সফল হয়েছে!")
  except Exception as e:
    print(f"Old load error: {e}")


# ভিডিও ডেলিভারি সিস্টেম
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

    await deliver_videos_to_user(chat_id, cat_key, cat_title, context)
    return

  await update.message.reply_text(
      "🎉 বটের ইনবক্সে আপনাকে স্বাগতম!\n\nদয়া করে গ্রুপে দেওয়া মেনু থেকে আপনার"
      " পছন্দের ক্যাটাগরিতে ক্লিক করুন।"
  )


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
          " করে আবার চেক করুন.",
          show_alert=True,
      )


async def delete_inbox_video_after_delay(context, chat_id, message_id):
  await asyncio.sleep(1200)
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  if not user.username or user.username.lower() != ADMIN_USERNAME.lower():
    return

  set_menus = sum(1 for m in menu_items if m is not None)
  status_text = (
      f"📊 বটের ডাটাবেজ স্ট্যাটাস:\n"
      f"- সেট করা মেনু পোস্টার: {set_menus}/5\n"
      f"- হট/ডাইরেক্ট ভিডিও মোট: len(videos['hot'])\n"
      f"- ব্যাচেলর পয়েন্ট মোট: len(videos['bachelor'])\n"
      f"- বাংলা সিনেমা নাটক মোট: len(videos['natok'])\n"
      f"- হিন্দি ড্রামা/মুভি মোট: len(videos['hindi'])\n"
      f"- CID নাটক মোট: len(videos['cid'])"
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

  async def post_init(app):
    await load_old_videos_from_channel(app.bot)

  application.post_init = post_init

  job_queue = application.job_queue
  # ইন্টারভাল ২ মিনিট (১২০ সেকেন্ড) করা হয়েছে যাতে ডাবল পোস্ট না হয়
  job_queue.run_repeating(send_auto_video_menu, interval=120, first=5)

  application.add_handler(CommandHandler("start", start_handler))
  application.add_handler(CommandHandler("status", admin_status))
  application.add_handler(CallbackQueryHandler(button_callback_handler))

  application.add_handler(
      MessageHandler(
          filters.ALL & (~filters.COMMAND) & (~filters.UpdateType.CHANNEL_POST),
          check_links,
      )
  )

  application.add_handler(
      MessageHandler(
          filters.VIDEO | filters.Document.ALL | filters.PHOTO,
          receive_channel_video,
      )
  )

  print("Bot is running with auto-delete and single-post fixed!")
  application.run_polling()


if __name__ == "__main__":
  main()

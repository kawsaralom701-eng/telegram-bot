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

# আপনার প্রাইভেট চ্যানেল আইডি (যেখান থেকে ভিডিও ও পোস্টার সংগ্রহ করবে)
PRIVATE_CHANNEL_ID = -1003967128934

# ৫টি চ্যানেল এবং ১টি গ্রুপসহ মোট ৬টি টার্গেট আইডি (একযোগে একই সময়ে মেসেজ পাঠানোর জন্য)
TARGET_CHATS = [
    -1004484108921,  # মুভি সিআইডি ব্যাচালার নাটক চ্যানেল
    -1004296342087,  # CID Bangla Season 2
    -1004395034930,  # হট ভিডিও চ্যানেল
    -1004302390586,  # তানিয়া আক্তার হট ভিডিও চ্যানেল
    -1003067466801,  # নিউ মুভি চ্যানেল
    -1004362653651,  # মূল গ্রুপ আইডি
]

TARGET_CHANNELS = [
    {
        "id": -1004484108921,
        "name": "মুভি সিআইডি ব্যাচালার নাটক",
        "url": "https://t.me/Demogroup764",
    },
    {
        "id": -1004296342087,
        "name": "CID Bangla Season 2",
        "url": "https://t.me/CID_Season_S2o",
    },
    {
        "id": -1004395034930,
        "name": "হট ভিডিও চ্যানেল",
        "url": "https://t.me/kawsaralom76410",
    },
    {
        "id": -1004302390586,
        "name": "তানিয়া আক্তার চ্যানেল",
        "url": "https://t.me/CID_Season_S2o",
    },
    {
        "id": -1003067466801,
        "name": "নিউ মুভি",
        "url": "https://t.me/+YVDafDISqdMxNTVl",
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
            "👤 অফিশিয়াল আইডি/চ্যানেল", url="https://t.me/kawsar7641"
        )
    ],
]

warnings = {}
videos = {
    "hot": [],  # ক্যাপশন ছাড়া ভিডিওগুলো এখানে জমা হবে
    "bachelor": [],
    "natok": [],
    "bangla_natok": [],
    "hindi": [],
    "cid": [],
}

menu_poster_ids = []
poster_index = 0
menu_lock = asyncio.Lock()
last_sent_menu_ids = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


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


# ১. ৬টি জায়গায় একসাথে ঠিক ১টি করে মেনু পোস্ট পাঠানোর ফাংশন (প্রতি ১ মিনিট পর পর)
async def send_auto_video_menu(context: ContextTypes.DEFAULT_TYPE):
  global poster_index, last_sent_menu_ids

  if menu_lock.locked():
    return

  async with menu_lock:
    try:
      bot_username = (await context.bot.get_me()).username

      # ১ থেকে ১০০টি পোস্টার ছবি থেকে চক্রাকারে (rotation) একটি করে ছবি নেওয়া
      current_poster_id = None
      if menu_poster_ids:
        current_poster_id = menu_poster_ids[poster_index % len(menu_poster_ids)]
        poster_index = (poster_index + 1) % len(menu_poster_ids)

      # আপনার চাহিদা অনুযায়ী ঠিক ৬টি বাটন
      keyboard = [
          [
              InlineKeyboardButton(
                  "🎭🔥 ব্যাচেলর পয়েন্ট নাটক 🔥🎭",
                  url=f"https://t.me/{bot_username}?start=bachelor",
              )
          ],
          [
              InlineKeyboardButton(
                  "🔥🔞 হট ভিডিও 🔞🔥",
                  url=f"https://t.me/{bot_username}?start=hot",
              )
          ],
          [
              InlineKeyboardButton(
                  "📺🎭 বাংলা নাটক 🎭📺",
                  url=f"https://t.me/{bot_username}?start=bangla_natok",
              )
          ],
          [
              InlineKeyboardButton(
                  "🎬🍿 বাংলা সিনেমা ও নাটক 🍿🎬",
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
      ]
      reply_markup = InlineKeyboardMarkup(keyboard)

      menu_caption = (
          "🔥 **বিশাল অফার ও বিনোদন জগৎ!** 🔥\n\n✨ **যা যা উপভোগ করতে পারবেন:**\n🔹"
          " ব্যাচেলর পয়েন্ট নাটক\n🔞 হট ভিডিও\n🔹 বাংলা নাটক\n🎬 হিন্দি ড্রামা ও"
          " মুভি\n🎞️ বাংলা সিনেমা ও নাটক\n🕵️ সিআইডি নাটক\n\n👇 **বটের ইনবক্সে গিয়ে"
          " পছন্দের ক্যাটাগরিতে ক্লিক করুন!**"
      )

      for chat_id in TARGET_CHATS:
        # আগের পাঠানো মেসেজ ডিলিট করে দেওয়া যাতে ডাবল মেসেজ না হয়
        if chat_id in last_sent_menu_ids:
          old_id = last_sent_menu_ids[chat_id]
          try:
            await context.bot.delete_message(chat_id=chat_id, message_id=old_id)
          except Exception:
            pass

        try:
          if current_poster_id:
            sent_msg = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=PRIVATE_CHANNEL_ID,
                message_id=current_poster_id,
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
          print(f"Error sending menu to {chat_id}: {e}")

    except Exception as e:
      print(f"Loop error: {e}")


# ২. লিংক রিমুভ ও ৩ বার ওয়ার্নিং সিস্টেম
async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if not update.message or update.message.chat_id not in TARGET_CHATS:
    return

  message = update.message
  user = message.from_user
  if not user:
    return

  if user.username and user.username.lower() == ADMIN_USERNAME.lower():
    return

  text = message.text or message.caption or ""
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
              f"@{user.username or user.first_name}, গ্রুপ বা চ্যানেলে লিংক"
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


# ৩. প্রাইভেট চ্যানেল থেকে ভিডিও এবং পোস্টার ছবি রিসিভ ও ফিল্টার করা
async def receive_channel_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  message = update.channel_post or update.effective_message
  if not message:
    return

  caption = message.caption.lower() if message.caption else ""

  # ১০০টি পোস্টার বা ছবি ফিল্টার করা
  if message.photo:
    if (
        "poster" in caption
        or "menu" in caption
        or "pic" in caption
        or not caption
    ):
      if message.message_id not in menu_poster_ids:
        menu_poster_ids.append(message.message_id)
      return

  if message.video or message.document:
    video_data = {
        "message_id": message.message_id,
        "caption": message.caption or "নামবিহীন ভিডিও",
    }

    # যদি ক্যাপশন বা কমান্ড থাকে, তবে সে অনুযায়ী ক্যাটাগরিতে যাবে
    if "bachelor" in caption:
      videos["bachelor"].append(video_data)
    elif "bangla natok" in caption or "বাংলা নাটক" in caption:
      videos["bangla_natok"].append(video_data)
    elif "natok" in caption or "বাংলা সিনেমা" in caption:
      videos["natok"].append(video_data)
    elif "hindi" in caption or "হিন্দি" in caption:
      videos["hindi"].append(video_data)
    elif "cid" in caption:
      videos["cid"].append(video_data)
    else:
      # কোনো কমান্ড বা ক্যাপশন না থাকলে সেটি অটোমেটিক 'হট ভিডিও' হিসেবে রিসিভ হবে
      videos["hot"].append(video_data)


# প্রাইভেট চ্যানেলের পুরনো মেসেজগুলো স্ক্যান করা
async def load_old_videos_from_channel(bot):
  print("🔄 প্রাইভেট চ্যানেল স্ক্যানিং শুরু...")
  try:
    for msg_id in range(1, 500):
      try:
        chat_msg = await bot.get_message(
            chat_id=PRIVATE_CHANNEL_ID, message_id=msg_id
        )
        if chat_msg:
          caption = chat_msg.caption.lower() if chat_msg.caption else ""
          if chat_msg.photo:
            if (
                "poster" in caption
                or "menu" in caption
                or "pic" in caption
                or not caption
            ):
              if chat_msg.message_id not in menu_poster_ids:
                menu_poster_ids.append(chat_msg.message_id)
          elif chat_msg.video or chat_msg.document:
            v_data = {
                "message_id": chat_msg.message_id,
                "caption": chat_msg.caption or "নামবিহীন ভিডিও",
            }
            if "bachelor" in caption and v_data not in videos["bachelor"]:
              videos["bachelor"].append(v_data)
            elif (
                ("bangla natok" in caption or "বাংলা নাটক" in caption)
                and v_data not in videos["bangla_natok"]
            ):
              videos["bangla_natok"].append(v_data)
            elif (
                ("natok" in caption or "বাংলা সিনেমা" in caption)
                and v_data not in videos["natok"]
            ):
              videos["natok"].append(v_data)
            elif ("hindi" in caption or "হিন্দি" in caption) and v_data not in [
                v for v in videos["hindi"]
            ]:
              videos["hindi"].append(v_data)
            elif "cid" in caption and v_data not in videos["cid"]:
              videos["cid"].append(v_data)
            elif not chat_msg.caption and v_data not in videos["hot"]:
              videos["hot"].append(v_data)
      except Exception:
        pass
    print(
        f"✅ স্ক্যান সম্পন্ন! মোট পোস্টার: {len(menu_poster_ids)}, হট ভিডিও:"
        f" {len(videos['hot'])}, ব্যাচেলর: {len(videos['bachelor'])}, বাংলা নাটক:"
        f" {len(videos['bangla_natok'])}, সিনেমা/নাটক: {len(videos['natok'])},"
        f" হিন্দি: {len(videos['hindi'])}, CID: {len(videos['cid'])}"
    )
  except Exception as e:
    print(f"Error scanning: {e}")


async def deliver_videos_to_user(chat_id, cat_key, cat_title, context):
  target_list = videos.get(cat_key, [])
  if not target_list:
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚠️ এই মুহূর্তে **{cat_title}**-তে কোনো ভিডিও নেই।",
    )
    return

  await context.bot.send_message(
      chat_id=chat_id,
      text=f"🚀 **{cat_title}**-এর সমস্ত ভিডিও পাঠানো হচ্ছে...",
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
      print(f"Error: {e}")


# ৪. স্টার্ট কমান্ড ও ক্যাটাগরি হ্যান্ডলার
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.message.from_user
  args = context.args
  chat_id = update.message.chat_id
  is_admin = user.username and user.username.lower() == ADMIN_USERNAME.lower()

  cat_display_names = {
      "bachelor": ("bachelor", "🎭🔥 ব্যাচেলর পয়েন্ট নাটক"),
      "hot": ("hot", "🔥🔞 হট ভিডিও"),
      "natok": ("natok", "🎬🍿 বাংলা সিনেমা ও নাটক"),
      "bangla_natok": ("bangla_natok", "📺🎭 বাংলা নাটক"),
      "hindi": ("hindi", "🇮🇳🎥 হিন্দি ড্রামা ও মুভি"),
      "cid": ("cid", "🕵️‍♂️🔥 CID নাটকের সকল পর্ব"),
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
            "⚠️ **ভিডিও দেখতে হলে নিচের চ্যানেলগুলোতে অবশ্যই জয়েন করতে হবে!**",
            reply_markup=InlineKeyboardMarkup(join_keyboard),
        )
        return

    await deliver_videos_to_user(chat_id, cat_key, cat_title, context)
    return

  await update.message.reply_text(
      "🎉 স্বাগতম! চ্যানেল বা গ্রুপে দেওয়া মেনু থেকে আপনার পছন্দের ক্যাটাগরি বেছে"
      " নিন।"
  )


async def button_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()
  user = query.from_user
  data = query.data

  if data.startswith("check_"):
    cat_arg = data.replace("check_", "", 1)
    is_subscribed = await check_user_subscriptions(user.id, context.bot)

    if is_subscribed:
      await query.message.delete()
      cat_mapping = {
          "bachelor": ("bachelor", "🎭🔥 ব্যাচেলর পয়েন্ট নাটক"),
          "hot": ("hot", "🔥🔞 হট ভিডিও"),
          "natok": ("natok", "🎬🍿 বাংলা সিনেমা ও নাটক"),
          "bangla_natok": ("bangla_natok", "📺🎭 বাংলা নাটক"),
          "hindi": ("hindi", "🇮🇳🎥 হিন্দি ড্রামা ও মুভি"),
          "cid": ("cid", "🕵️‍♂️🔥 CID নাটকের সকল পর্ব"),
      }
      if cat_arg in cat_mapping:
        cat_key, cat_title = cat_mapping[cat_arg]
        await deliver_videos_to_user(
            query.message.chat_id, cat_key, cat_title, context
        )
    else:
      await query.answer("❌ সব চ্যানেলে জয়েন করুন!", show_alert=True)


async def delete_inbox_video_after_delay(context, chat_id, message_id):
  await asyncio.sleep(1200)
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
      f"- সংরক্ষিত পোস্টার ছবি: {len(menu_poster_ids)}\n"
      f"- হট ভিডিও: {len(videos['hot'])}\n"
      f"- ব্যাচেলর পয়েন্ট: {len(videos['bachelor'])}\n"
      f"- বাংলা নাটক: {len(videos['bangla_natok'])}\n"
      f"- বাংলা সিনেমা ও নাটক: {len(videos['natok'])}\n"
      f"- হিন্দি ড্রামা/মুভি: {len(videos['hindi'])}\n"
      f"- CID নাটক: {len(videos['cid'])}"
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
  # প্রতি ১ মিনিট পর পর সমস্ত ৬টি জায়গায় একসাথে ঠিক ১টি করে মেনু পোস্ট আপডেট ও রোটেট হবে
  job_queue.run_repeating(send_auto_video_menu, interval=60, first=5)

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

  print(
      "Bot is running successfully across all 6 targets with 6 buttons and"
      " poster rotation!"
  )
  application.run_polling()


if __name__ == "__main__":
  main()

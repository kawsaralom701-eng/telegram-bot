import asyncio
from datetime import timedelta
import logging
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

# প্রাইভেট চ্যানেল আইডি (যেখান থেকে ভিডিও ও পোস্টার সংগ্রহ করবে)
PRIVATE_CHANNEL_ID = -1003967128934

# টার্গেট চ্যাটসমূহ (যেখানে মেনু পোস্ট পাঠানো হবে)
TARGET_CHATS = [
    -1004484108921,
    -1004296342087,
    -1004395034930,
    -1004302390586,
    -1003067466801,
    -1004362653651,
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

# ভিডিওর নিচের বাটনসমূহ (আপনার দেওয়া নতুন লিঙ্ক সহ)
CHANNEL_BUTTONS = [
    [
        InlineKeyboardButton(
            "📢 আমাদের চ্যানেলে জয়েন করুন", url="https://t.me/+3_mK5H2KK-k0M2E1"
        )
    ],
    [
        InlineKeyboardButton(
            "🎬 নিউ মুভি চ্যানেল", url="https://t.me/+YVDafDISqdMxNTVl"
        )
    ],
    [
        InlineKeyboardButton(
            "🕵️‍♂️ CID Bangla Season 2", url="https://t.me/CID_Season_S2o"
        )
    ],
    [
        InlineKeyboardButton(
            "🔥 হট ভিডিও চ্যানেল", url="https://t.me/kawsaralom76410"
        )
    ],
    [
        InlineKeyboardButton(
            "👥 মূল গ্রুপ", url="https://t.me/kawsaralom76410"
        )
    ],
]

warnings = {}
videos = {
    "hot": [],
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


# নির্দিষ্ট সময় পর মেসেজ ডিলিট করার ফাংশন
async def delete_message_after_delay(context, chat_id, message_id, delay_seconds):
  await asyncio.sleep(delay_seconds)
  try:
    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
  except Exception:
    pass


# প্রতি ২ মিনিট (১২০ সেকেন্ড) পর পর মেনু পোস্ট পাঠানোর এবং ২০ সেকেন্ড পর ডিলিট করার লজিক
async def send_auto_video_menu(context: ContextTypes.DEFAULT_TYPE):
  global poster_index, last_sent_menu_ids

  if menu_lock.locked():
    return

  async with menu_lock:
    try:
      bot_username = (await context.bot.get_me()).username

      current_poster_id = None
      if menu_poster_ids:
        current_poster_id = menu_poster_ids[poster_index % len(menu_poster_ids)]
        poster_index = (poster_index + 1) % len(menu_poster_ids)

      # সিঙ্গেল ও পরিচ্ছন্ন বাটন লেআউট (নতুন চ্যানেল লিঙ্ক সহ)
      keyboard = [
          [
              InlineKeyboardButton(
                  "📢 আমাদের চ্যানেলে জয়েন করুন",
                  url="https://t.me/+3_mK5H2KK-k0M2E1",
              )
          ],
          [
              InlineKeyboardButton(
                  "🔥 হট ভিডিও জোন",
                  url=f"https://t.me/{bot_username}?start=hot",
              )
          ],
          [
              InlineKeyboardButton(
                  "🎭 ব্যাচেলর পয়েন্ট নাটক",
                  url=f"https://t.me/{bot_username}?start=bachelor",
              )
          ],
          [
              InlineKeyboardButton(
                  "📺 বাংলা নাটক",
                  url=f"https://t.me/{bot_username}?start=bangla_natok",
              )
          ],
          [
              InlineKeyboardButton(
                  "🎬 বাংলা সিনেমা ও নাটক",
                  url=f"https://t.me/{bot_username}?start=natok",
              )
          ],
          [
              InlineKeyboardButton(
                  "🇮🇳 হিন্দি ড্রামা ও মুভি",
                  url=f"https://t.me/{bot_username}?start=hindi",
              )
          ],
          [
              InlineKeyboardButton(
                  "🕵️‍♂️ CID নাটকের সকল পর্ব",
                  url=f"https://t.me/{bot_username}?start=cid",
              )
          ],
          [
              InlineKeyboardButton(
                  "🔵 মূল ভিডিও চ্যানেল", url="https://t.me/kawsaralom76410"
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
        if chat_id in last_sent_menu_ids:
          old_msg_id = last_sent_menu_ids[chat_id]
          try:
            await context.bot.delete_

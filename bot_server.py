from flask import Flask
import threading
import telebot
import instaloader
import os
import uuid
import shutil
from telebot import types
from moviepy.editor import VideoFileClip

# Flask server
app = Flask(__name__)

@app.route("/")
def home():
    return "Instagram Video + Audio Bot ishlayapti ✅", 200

# Telegram bot
TOKEN = "7359713313:AAGbK1Bj_k1dRt259fRkUM0fn4g_Gau79_8"
bot = telebot.TeleBot(TOKEN)

# Instaloader (faqat video kerak, qolgan narsalarni yuklamaslik uchun)
loader = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    download_pictures=False,
    download_video_thumbnails=False,
    save_metadata=False,
    compress_json=False,
    post_metadata_txt_pattern="",
    filename_pattern="{shortcode}"
)

# /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Assalomu alaykum! 😊\n\n"
        "Instagram Reels, Post yoki IGTV linkini yuboring – men sizga video + audioni chiqarib beraman 🎵\n\n"
        "Masalan:\nhttps://www.instagram.com/reel/C1234567890/"
    )

# Har qanday matn kelsa – Instagram link deb qaraymiz
@bot.message_handler(func=lambda message: True)
def handle_instagram_link(message):
    url = message.text.strip()

    if "instagram.com" not in url:
        bot.reply_to(message, "❌ Iltimos, faqat Instagram link yuboring!")
        return

    # Shortcode olish (reel/, p/, tv/ uchun ham ishlaydi)
    try:
        if "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0].split("?")[0]
        elif "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0].split("?")[0]
        elif "/tv/" in url:
            shortcode = url.split("/tv/")[1].split("/")[0].split("?")[0]
        else:
            bot.reply_to(message, "❌ To‘g‘ri Instagram link yuboring!")
            return
    except:
        bot.reply_to(message, "❌ Link formati noto‘g‘ri!")
        return

    status = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")

    # Har bir foydalanuvchi uchun alohida papka
    folder_name = f"temp_{uuid.uuid4().hex[:10]}"
    os.makedirs(folder_name, exist_ok=True)

    video_path = None

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=folder_name)

        # .mp4 faylni topish
        for file in os.listdir(folder_name):
            if file.endswith(".mp4"):
                video_path = os.path.join(folder_name, file)
                break

        if not video_path or not os.path.exists(video_path):
            raise Exception("Video topilmadi")

        # Video yuborish + tugma qo‘shish
        with open(video_path, "rb") as video_file:
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("🔊 Audioni olish", callback_data=f"audio_{folder_name}")
            markup.add(btn)
            bot.send_video(message.chat.id, video_file, caption="✅ Video tayyor!", reply_markup=markup)

        bot.delete_message(message.chat.id, status.message_id)

    except Exception as e:
        bot.delete_message(message.chat.id, status.message_id)
        bot.reply_to(message, f"Xatolik yuz berdi 😔\n\n{str(e)}")
    finally:
        # Agar xato bo‘lsa ham papkani o‘chirib tashlash
        if os.path.exists(folder_name) and os.path.isdir(folder_name):
            shutil.rmtree(folder_name, ignore_errors=True)

# Audio so‘ralganda
@bot.callback_query_handler(func=lambda call: call.data.startswith("audio_"))
def send_audio(call):
    folder_name = call.data.split("_", 1)[1]
    
    if not os.path.exists(folder_name):
        bot.answer_callback_query(call.id, text="❌ Video o‘chirilgan yoki muddati o‘tgan")
        return

    bot.answer_callback_query(call.id, text="🔄 Audio tayyorlanyapti...")
    bot.send_message(call.message.chat.id, "⏳ Audio chiqarilmoqda...")

    video_path = None
    for file in os.listdir(folder_name):
        if file.endswith(".mp4"):
            video_path = os.path.join(folder_name, file)
            break

    if not video_path:
        bot.send_message(call.message.chat.id, "❌ Video topilmadi")
        return

    try:
        video = VideoFileClip(video_path)
        audio_path = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video.close()

        with open(audio_path, "rb") as audio_file:
            bot.send_audio(call.message.chat.id, audio_file, title="Instagram dan audio 🎵")

        os.remove(audio_path)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"Audio chiqarishda xato: {e}")
    finally:
        # Har doim temp papkani tozalash
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name, ignore_errors=True)

# Botni alohida thread’da ishga tushirish
def run_bot():
    print("Bot ishga tushdi...")
    bot.infinity_polling(none_stop=True, interval=0)

# Asosiy ishga tushirish
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    # Ko‘p platformalarda PORT muhit o‘zgaruvchisi bo‘ladi
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
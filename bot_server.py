from flask import Flask
import threading
import telebot
import instaloader
import os
import uuid
import shutil
from telebot import types
from moviepy.editor import VideoFileClip

app = Flask(__name__)

@app.route("/")
def home():
    return "Instagram Downloader Bot – 100% ishlayapti ✅", 200

# ==================== CONFIG ====================
TOKEN = "7359713313:AAGbK1Bj_k1dRt259fRkUM0fn4g_Gau79_8"
bot = telebot.TeleBot(TOKEN)

# SIZNING INSTAGRAM LOGIININGIZ (allaqachon qoʻyib qoʻyildi)
INSTA_USER = "djdnsnnmamsd"
INSTA_PASS = "Abdulatif7"

L = instaloader.Instaloader(
    download_pictures=False,
    download_video_thumbnails=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    quiet=True,
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)

# Login (har safar ishga tushganda avto-login)
try:
    L.login(INSTA_USER, INSTA_PASS)
    print("Instagram login muvaffaqiyatli – bloklanish deyarli yoʻq!")
except Exception as e:
    print(f"Login xatosi: {e}")

# ==================== HANDLERS ====================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "Assalomu alaykum! 😊\n\n"
        "Instagram Reels, Post yoki IGTV linkini yuboring — video + audio chiqarib beraman 🎵\n\n"
        "Masalan: https://www.instagram.com/reel/C123abcDEF/"
    )

@bot.message_handler(func=lambda m: True)
def handle_link(message):
    url = message.text.strip()
    if "instagram.com" not in url:
        return bot.reply_to(message, "❌ Faqat Instagram link yuboring!")

    # Shortcode ajratib olish
    try:
        part = url.split("instagram.com/")[1]
        shortcode = part.split("/")[1].split("?")[0].rstrip("/")
    except:
        return bot.reply_to(message, "❌ Link notoʻgʻri formatda")

    status = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")

    temp_dir = f"temp_{uuid.uuid4().hex[:12]}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=temp_dir)

        video_path = None
        for f in os.listdir(temp_dir):
            if f.endswith(".mp4"):
                video_path = os.path.join(temp_dir, f)
                break

        if not video_path:
            raise Exception("Video topilmadi")

        with open(video_path, "rb") as vid:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔊 Audioni olish", callback_data=f"audio|{temp_dir}"))
            bot.send_video(message.chat.id, vid, caption="✅ Video tayyor!", reply_markup=markup)

        bot.delete_message(message.chat.id, status.message_id)

    except instaloader.exceptions.LoginRequiredException:
        bot.delete_message(message.chat.id, status.message_id)
        bot.reply_to(message, "Instagram login yangilanishi kerak. Botni qayta ishga tushiraman...")
    except instaloader.exceptions.ConnectionException as e:
        if "wait a few minutes" in str(e) or "401" in str(e):
            bot.delete_message(message.chat.id, status.message_id)
            bot.reply_to(message, "🚫 Instagram vaqtincha blokladi. 10-15 daqiqa kuting.")
        else:
            bot.reply_to(message, f"Xatolik: {str(e)}")
    except Exception as e:
        bot.reply_to(message, f"Xatolik: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("audio|"))
def get_audio(call):
    temp_dir = call.data.split("|", 1)[1]
    if not os.path.exists(temp_dir):
        return bot.answer_callback_query(call.id, "Fayl oʻchirildi", show_alert=True)

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "⏳ Audio tayyorlanyapti...")

    video_path = None
    for f in os.listdir(temp_dir):
        if f.endswith(".mp4"):
            video_path = os.path.join(temp_dir, f)
            break

    if not video_path:
        return bot.send_message(call.message.chat.id, "Video topilmadi")

    try:
        clip = VideoFileClip(video_path)
        audio_path = f"audio_{uuid.uuid4().hex[:8]}.mp3"
        clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
        clip.close()

        with open(audio_path, "rb") as audio:
            bot.send_audio(call.message.chat.id, audio, title="Instagram Audio 🎵")

        os.remove(audio_path)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"Audio xatosi: {e}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

# ==================== RUN ====================
def run_bot():
    print("Telegram bot ishga tushdi...")
    bot.infinity_polling(none_stop=True, interval=0)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

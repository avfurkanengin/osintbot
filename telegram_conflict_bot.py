from keep_alive import keep_alive
keep_alive()

from telethon.sync import TelegramClient
from googletrans import Translator
import os
import re
import requests
import hashlib
import time

# TELEGRAM API bilgileri
api_id = 29513510
api_hash = 'd6e8e45dfd50bcfea2b5f3721f013ac6'

# ✅ Takip edilecek Telegram kanalları ve kullanıcı filtreleri
channel_usernames = {
    'conflict_tr': {
        'lang': 'tr',
        'allowed_senders': ['ConflictTR']
    },
    'ww3media': {
        'lang': 'tr',
        'allowed_senders': ['3. Dünya Savaşı']
    },
    'ateobreaking': {
        'lang': 'ru',
        'allowed_senders': ['Ateo Breaking']
    }
}

# GİZLİ DEĞİŞKENLER (Replit veya .env içinde)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Hashtag'leri temizle
def remove_hashtags(text):
    return re.sub(r"#\S+\s*", "", text)

# Metni İngilizce’ye çevir
def translate_text(text, src_lang='auto'):
    try:
        translator = Translator()
        result = translator.translate(text, src=src_lang, dest='en')
        return result.text
    except Exception as e:
        print("❌ Çeviri hatası:", e)
        return text

# Telegram botuna mesaj gönder (fotoğraf ve video destekli)
def send_to_telegram(text, media_path=None, is_video=False):
    try:
        if media_path:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo" if is_video else f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(media_path, 'rb') as media_file:
                files = {'video' if is_video else 'photo': media_file}
                data = {"chat_id": CHAT_ID, "caption": text}
                response = requests.post(url, data=data, files=files)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {"chat_id": CHAT_ID, "text": text}
            response = requests.post(url, data=data)

        if response.status_code == 200:
            print("✅ Mesaj gönderildi.")
        else:
            print("❌ Gönderim hatası:", response.text)
    except Exception as e:
        print("❌ Telegram API hatası:", e)

# Gönderilmiş içeriklerin hash'lerini sakla
def get_sent_hashes():
    try:
        with open("sent_hashes.txt", "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_sent_hash(content_hash):
    with open("sent_hashes.txt", "a") as f:
        f.write(content_hash + "\n")

# 🎉 Filtrelenecek emoji karakterleri
BLOCKED_EMOJIS = ['🎉', '🎁', '🎊', '🎈', '🎂', '🎇', '🎆', '🥳', '🎀', '🎟']

# 🚫 Yasaklı anahtar kelimeler
BLOCKED_KEYWORDS = [
    'advertiser', 'sponsor', 'telegram premium',
    'dem parti', 'dem partisi', 'özgür özel', 'chp', 'akp', 'imamoğlu', 'imamoglu', "conflicttr", "ww3media", "ateobreaking", "dunyadantr", "dunyadantr", "dunyadan_tr",
]

# 🔁 Sonsuz döngü (5 dakikada bir)
while True:
    try:
        with TelegramClient('multi_session', api_id, api_hash) as client:
            print("[INFO] Kanallar kontrol ediliyor...\n")

            sent_hashes = get_sent_hashes()
            new_messages = 0

            for channel, info in channel_usernames.items():
                lang = info['lang']
                allowed_senders = info['allowed_senders']
                print(f"[INFO] Kanal: {channel}")

                for message in client.iter_messages(channel, limit=4):
                    if not message.text or not message.sender:
                        continue

                    try:
                        if hasattr(message.sender, 'first_name') and message.sender.first_name:
                            sender_name = message.sender.first_name
                        elif hasattr(message.sender, 'title') and message.sender.title:
                            sender_name = message.sender.title
                        else:
                            sender_name = ""
                    except:
                        sender_name = ""

                    if sender_name not in allowed_senders:
                        print(f"[SKIP] Filtreden geçmedi: {sender_name}")
                        continue

                    raw_text = message.text.strip()
                    lower_text = raw_text.lower()

                    if any(keyword in lower_text for keyword in BLOCKED_KEYWORDS):
                        print("[SKIP] Yasaklı içerik, atlanıyor.")
                        continue

                    if re.search(r"https?://\S+", raw_text):
                        print("[SKIP] Link içeren mesaj, atlanıyor.")
                        continue

                    if any(emoji in raw_text for emoji in BLOCKED_EMOJIS):
                        print("[SKIP] Kutlama emojisi içeriyor, atlanıyor.")
                        continue

                    current_hash = hashlib.md5((channel + raw_text).encode()).hexdigest()
                    if current_hash in sent_hashes:
                        print("[DUPLICATE] Zaten gönderilmiş, atlanıyor.")
                        continue

                    cleaned = remove_hashtags(raw_text)
                    translated = translate_text(cleaned, src_lang=lang)

                    final_message = (
                        "🚨 Breaking\n\n"
                        f"{translated}\n\n"
                        "Follow us on X: @PulseofGlobe"
                    )

                    media_path = None
                    is_video = False

                    if message.video:
                        try:
                            media_path = client.download_media(message.video)
                            is_video = True
                        except Exception as e:
                            print("[WARN] Video indirilemedi:", e)

                    elif message.photo:
                        try:
                            media_path = client.download_media(message.photo)
                        except Exception as e:
                            print("[WARN] Fotoğraf indirilemedi:", e)

                    print("[SEND] Gönderiliyor:\n", final_message)
                    send_to_telegram(final_message, media_path, is_video=is_video)
                    save_sent_hash(current_hash)
                    new_messages += 1
                    time.sleep(20)

            if new_messages == 0:
                print("[INFO] Yeni mesaj bulunamadı.")
    except Exception as e:
        print("❌ Genel hata:", e)

    print("[WAIT] 5 dakika bekleniyor...\n")
    time.sleep(300)

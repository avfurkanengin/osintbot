from telethon.sync import TelegramClient
import openai
import os
import re
import requests
import hashlib
import time
from PIL import Image
import numpy as np
import csv
from datetime import datetime
import functools
import base64
import traceback

print = functools.partial(print, flush=True)

# Environment variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
openai.api_key = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CSV_FILE = "gpt_full_log.csv"

print("\n✅ Değişkenler alınıyor:")
print(f"🔑 API_ID: {api_id}")
print(f"🔑 API_HASH: {'VAR' if api_hash else 'YOK'}")
print(f"🔑 OPENAI_API_KEY: {'VAR' if openai.api_key else 'YOK'}")
print(f"🔑 BOT_TOKEN: {'VAR' if BOT_TOKEN else 'YOK'}")
print(f"🔑 CHAT_ID: {CHAT_ID}\n")

# Session setup
if not os.path.exists("multi_session.session"):
    print("📦 Session dosyası bulunamadı, base64'ten yazılıyor...")
    session_b64 = os.getenv("SESSION_B64")
    if session_b64:
        print("✅ SESSION_B64 değişkeni bulundu, decode ediliyor.")
        with open("multi_session.session", "wb") as f:
            f.write(base64.b64decode(session_b64))
    else:
        print("❌ SESSION_B64 bulunamadı, oturum dosyası oluşturulamaz!")

# Temizlik: railway yeniden başlatıldığında bazen lock kalıyor
try:
    os.remove("multi_session.session-journal")
except FileNotFoundError:
    pass

telegram_client = TelegramClient("multi_session", api_id, api_hash)

print("📡 Telegram bağlantısı kuruluyor...")
if not telegram_client.is_connected():
    telegram_client.connect()

if not telegram_client.is_user_authorized():
    print("❌ Telegram istemcisi yetkili değil! Railway üzerinde numara girilemez.")
    exit()
print("✅ Telegram oturumu aktif.\n")

channel_usernames = {
    'conflict_tr': {'lang': 'tr', 'allowed_senders': ['ConflictTR']},
    'ww3media': {'lang': 'tr', 'allowed_senders': ['3. Dünya Savaşı']},
    'ateobreaking': {'lang': 'ru', 'allowed_senders': ['Ateo Breaking']}
}

BLOCKED_EMOJIS = ['🎉', '🎁', '🎊', '🎈', '🎂', '🎇', '🎆', '🥳', '🎀', '🎟']
BLOCKED_KEYWORDS = [
    'advertiser', 'sponsor', 'sponsored', 'promotion', 'telegram premium',
    'reklam', 'sponsor', 'sponsorlu', 'taksit', 'indirim', 'kampanya',
    'dem parti', 'dem partisi', 'özgür özel', 'chp', 'akp', 'ımamoğlu', 'imamoglu',
    'conflicttr', 'ww3media', 'ateobreaking', 'dunyadantr', 'dunyadan_tr',
]

def log_gpt_interaction(stage, date, channel, text, sent, usage):
    try:
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Tarih", "Aşama", "Kanal", "Özet",
                    "Telegram’a Gönderildi mi?", "Prompt Tokens", "Completion Tokens", "Toplam Tokens"
                ])
            writer.writerow([
                date, stage, channel, text[:100],
                "Evet" if sent else "Hayır",
                getattr(usage, 'prompt_tokens', '-') if usage else '-',
                getattr(usage, 'completion_tokens', '-') if usage else '-',
                getattr(usage, 'total_tokens', '-') if usage else '-'
            ])
    except Exception as e:
        print("[LOG ERROR] CSV yazma hatası:", e)

def remove_hashtags(text):
    return re.sub(r"#\S+\s*", "", text)

def translate_if_geopolitical(text):
    prompt = (
        "You will receive a news post.\n\n"
        "1. If the content is NOT about international politics, global affairs, or geopolitical events, respond ONLY with: \"SKIP\".\n"
        "2. If it IS geopolitical, translate or rewrite the content into fluent, concise English suitable for a Twitter audience. "
        "Keep it under 280 characters. Stay neutral. Use 1–2 relevant hashtags and one emoji. Begin with a flag emoji if clearly appropriate.\n\n"
        "Return only the translated version or the word 'SKIP'."
    )
    try:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        output = response.choices[0].message.content.strip()
        return output, response.usage
    except Exception as e:
        print("[GPT TRANSLATE ERROR]", e)
        return "", None

def get_sent_hashes():
    try:
        with open("sent_hashes.txt", "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_sent_hash(content_hash):
    with open("sent_hashes.txt", "a") as f:
        f.write(content_hash + "\n")

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

def is_image_red_or_black_heavy(image_path, threshold=0.7):
    try:
        image = Image.open(image_path).convert('RGB')
        image = image.resize((100, 100))
        data = np.array(image)
        total_pixels = data.shape[0] * data.shape[1]
        red_pixels = np.sum((data[:,:,0] > 150) & (data[:,:,1] < 80) & (data[:,:,2] < 80))
        black_pixels = np.sum((data[:,:,0] < 50) & (data[:,:,1] < 50) & (data[:,:,2] < 50))
        ratio = (red_pixels + black_pixels) / total_pixels
        return ratio >= threshold
    except Exception as e:
        print(f"[COLOR FILTER ERROR] {e}")
        return False

def main():
    print("🚀 Bot çalışmaya başladı. Kanallar taranıyor...\n")
    while True:
        try:
            print("[INFO] Kanallar kontrol ediliyor...")
            sent_hashes = get_sent_hashes()
            new_messages = 0

            for channel, info in channel_usernames.items():
                allowed_senders = info['allowed_senders']
                print(f"[INFO] Kanal: {channel}")

                for message in telegram_client.iter_messages(channel, limit=4):
                    if not message.text or not message.sender:
                        continue

                    sender_name = getattr(message.sender, 'first_name', '') or getattr(message.sender, 'title', '')
                    if sender_name not in allowed_senders:
                        print(f"[SKIP] Filtreden geçmedi: {sender_name}")
                        continue

                    raw_text = message.text.strip()
                    lower_text = raw_text.lower()

                    if any(keyword in lower_text for keyword in BLOCKED_KEYWORDS):
                        print("[SKIP] Yasaklı içerik, atlanıyor.")
                        continue

                    if re.search(r"https?://\S+", raw_text) or any(e in raw_text for e in BLOCKED_EMOJIS):
                        print("[SKIP] Uygunsuz içerik, atlanıyor.")
                        continue

                    current_hash = hashlib.md5((channel + raw_text).encode()).hexdigest()
                    if current_hash in sent_hashes:
                        print("[DUPLICATE] Zaten gönderilmiş, atlanıyor.")
                        continue

                    cleaned = remove_hashtags(raw_text)
                    translated, usage = translate_if_geopolitical(cleaned)
                    if translated.upper() == "SKIP":
                        print("[SKIP] GPT 'SKIP' dedi.")
                        log_gpt_interaction("Translate & Filter", datetime.now().strftime("%Y-%m-%d %H:%M"), channel, cleaned, False, usage)
                        continue

                    tweet_url = "https://twitter.com/intent/tweet?text=" + requests.utils.quote(translated)
                    final_message = f"{translated}\n\n🔗 Post on Twitter: {tweet_url}"

                    media_path = None
                    is_video = False

                    if message.video:
                        try:
                            media_path = telegram_client.download_media(message.video)
                            is_video = True
                        except Exception as e:
                            print("[WARN] Video indirilemedi:", e)
                    elif message.photo:
                        try:
                            media_path = telegram_client.download_media(message.photo)
                            if is_image_red_or_black_heavy(media_path):
                                print("[SKIP] Görselde kırmızı/siyah baskın. Atlanıyor.")
                                continue
                        except Exception as e:
                            print("[WARN] Fotoğraf indirilemedi:", e)

                    print("[SEND] Gönderiliyor:\n", final_message)
                    send_to_telegram(final_message, media_path, is_video=is_video)
                    save_sent_hash(current_hash)
                    log_gpt_interaction("Final", datetime.now().strftime("%Y-%m-%d %H:%M"), channel, cleaned, True, usage)

                    new_messages += 1
                    time.sleep(20)

            if new_messages == 0:
                print("[INFO] Yeni mesaj bulunamadı.")
        except Exception as e:
            print("❌ Genel hata:", e)
            traceback.print_exc()

        print("[WAIT] 5 dakika bekleniyor...\n")
        time.sleep(300)

if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    main()
# GPT-4o entegreli versiyon

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
import tweepy
import os

client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_CONSUMER_KEY"),
    consumer_secret=os.getenv("TWITTER_CONSUMER_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
)

def send_to_twitter(text, media_path=None):
    try:
        if media_path:
            print("⚠️ Medya içerik çıkarıldı, sadece metinle tweet atılıyor.")

        response = client.create_tweet(text=text)
        print(f"✅ Tweet atıldı: https://twitter.com/user/status/{response.data['id']}")
    except Exception as e:
        print("❌ Tweet gönderim hatası:", e)

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

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

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CSV_FILE = "gpt_full_log.csv"

def log_gpt_interaction(stage, date, channel, text, importance, sent, usage):
    try:
        file_exists = os.path.isfile(CSV_FILE)

        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Tarih", "Aşama", "Kanal", "Özet", "Önem Derecesi",
                    "Telegram’a Gönderildi mi?", "Prompt Tokens", "Completion Tokens", "Toplam Tokens"
                ])
            writer.writerow([
                date,
                stage,
                channel,
                text[:100],
                importance,
                "Evet" if sent else "Hayır",
                getattr(usage, 'prompt_tokens', '-') if usage else '-',
                getattr(usage, 'completion_tokens', '-') if usage else '-',
                getattr(usage, 'total_tokens', '-') if usage else '-'
            ])
        if usage:
            print(f"[LOG] {stage} kaydedildi ({usage.total_tokens} token).")
        else:
            print(f"[LOG] {stage} kaydedildi (token verisi yok).")
    except Exception as e:
        print("[LOG ERROR]", e)

def remove_hashtags(text):
    return re.sub(r"#\S+\s*", "", text)

def is_geopolitical_news(text, channel_name=None):
    prompt = (
        "Analyze the following news post. Is it about international politics, geopolitical events, or global affairs?\n"
        "Answer only with 'YES' or 'NO'.\n\n"
        f"Text: {text}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5,
        )
        usage = response.usage
        print(f"[TOKENS] Geo Filter - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")

        # ✅ CSV'ye logla
        if channel_name:
            log_gpt_interaction(
                "Geo Filter",
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                channel_name,
                text,
                "-",  # Önem derecesi yok
                False,
                usage
            )

        result = response.choices[0].message.content.strip().upper()
        return result == "YES"
    except Exception as e:
        print("[GPT FILTER ERROR]", e)
        return False

def get_importance_score(text):
    prompt = (
        "Aşağıdaki haberin uluslararası jeopolitik önemini değerlendir.\n"
        "Yanıtın sadece şu 5 kategoriden biri olsun:\n"
        "'Çok Önemli', 'Önemli', 'Orta', 'Az Önemli', 'Önemsiz'\n\n"
        f"Metin: {text}"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        result = response.choices[0].message.content.strip()
        print(f"[IMPORTANCE] Bu içerik: {result}")
        return result, response.usage
    except Exception as e:
        print("[IMPORTANCE ERROR]", e)
        return "Bilinmiyor", None

def gpt4o_translate(text):
    prompt = (
        "Translate or rewrite the following news post into fluent, concise English for a geopolitical OSINT Twitter audience. "
        "Keep it tweet-ready, under 280 characters. "
        "Remain neutral, regardless of whether the source is Turkish, Russian, English, or partisan. "
        "Add brief context only if it helps international readers. "
        "Use up to 2 relevant hashtags and 1 emoji. "
        "Start with a country flag emoji if clearly appropriate. "
        "Avoid literal or overly localized translation."
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
        usage = response.usage
        print(f"[TOKENS] Translation - Prompt: {usage.prompt_tokens}, Completion: {usage.completion_tokens}, Total: {usage.total_tokens}")
        return response.choices[0].message.content.strip(), usage
    except Exception as e:
        print("[GPT TRANSLATE ERROR]", e)
        return "", None

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

def get_sent_hashes():
    try:
        with open("sent_hashes.txt", "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_sent_hash(content_hash):
    with open("sent_hashes.txt", "a") as f:
        f.write(content_hash + "\n")

BLOCKED_EMOJIS = ['🎉', '🎁', '🎊', '🎈', '🎂', '🎇', '🎆', '🥳', '🎀', '🎟']
BLOCKED_KEYWORDS = [
    'advertiser', 'sponsor', 'sponsored', 'promotion', 'telegram premium',
    'reklam', 'sponsor', 'sponsorlu', 'taksit', 'indirim', 'kampanya',
    'dem parti', 'dem partisi', 'özgür özel', 'chp', 'akp', 'ımamoğlu', 'imamoglu',
    'conflicttr', 'ww3media', 'ateobreaking', 'dunyadantr', 'dunyadan_tr',
]

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
    while True:
        try:
            with TelegramClient('multi_session', api_id, api_hash) as telegram_client:
                print("[INFO] Kanallar kontrol ediliyor...\n")

                sent_hashes = get_sent_hashes()
                new_messages = 0

                for channel, info in channel_usernames.items():
                    lang = info['lang']
                    allowed_senders = info['allowed_senders']
                    print(f"[INFO] Kanal: {channel}")

                    for message in telegram_client.iter_messages(channel, limit=4):
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

                        if not is_geopolitical_news(cleaned, channel):
                            print("[SKIP] Yerel haber, atlanıyor.")
                            continue

                        importance, imp_usage = get_importance_score(cleaned)
                        if importance == "Önemsiz":
                            print("[SKIP] GPT tarafından önemsiz bulundu. Çeviri yapılmıyor.")
                            log_gpt_interaction(
                                "Importance Score",
                                datetime.now().strftime("%Y-%m-%d %H:%M"),
                                channel,
                                cleaned,
                                importance,
                                False,
                                imp_usage
                            )
                            continue

                        translated, trans_usage = gpt4o_translate(cleaned)
                        final_message = translated

                        log_gpt_interaction(
                            "Translation",
                            datetime.now().strftime("%Y-%m-%d %H:%M"),
                            channel,
                            cleaned,
                            importance,
                            True,
                            trans_usage
                        )

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

                        if importance in ["Çok Önemli", "Önemli"]:
                            try:
                                send_to_twitter(final_message, media_path)
                            except Exception as e:
                                print("[WARN] Twitter gönderim hatası:", e)

                        save_sent_hash(current_hash)
                        log_gpt_interaction(
                            "Final",
                            datetime.now().strftime("%Y-%m-%d %H:%M"),
                            channel,
                            cleaned,
                            importance,
                            True,
                            usage=None
                        )

                        new_messages += 1
                        time.sleep(20)

                if new_messages == 0:
                    print("[INFO] Yeni mesaj bulunamadı.")
        except Exception as e:
            print("❌ Genel hata:", e)

        print("[WAIT] 5 dakika bekleniyor...\n")
        time.sleep(300)

if __name__ == "__main__":
    from keep_alive import keep_alive
    keep_alive()
    main()

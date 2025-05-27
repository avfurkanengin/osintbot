import feedparser
import os
import time
import requests
import re
from bs4 import BeautifulSoup
from googletrans import Translator

# 🔐 GİZLİ DEĞİŞKENLER (.env veya Replit Secrets kısmında tanımlı)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📡 Takip edilecek Telegram RSS kanalları ve dilleri
RSS_FEEDS = {
    "conflict_tr": {
        "url": "https://rsshub.app/telegram/channel/conflict_tr",
        "lang": "tr"
    },
    "ww3media": {
        "url": "https://rsshub.app/telegram/channel/ww3media",
        "lang": "tr"

    },
    "ww3media": {
        "url": "https://rsshub.app/telegram/channel/dunyadantr",
        "lang": "tr"
    },
    "ateobreaking": {
        "url": "https://rsshub.app/telegram/channel/ateobreaking",
        "lang": "ru"
    }
}

# ⏱ Kontrol aralığı (saniye)
CHECK_INTERVAL = 300  # 5 dakika

# 🧹 Hashtag ve bağlı kelimeyi temizle (örnek: "#Suriye saldırısı" → "saldırısı" da gider)
def remove_hashtags(text):
    return re.sub(r"#\S+\s*", "", text)

# ✅ Çeviri fonksiyonu (TR veya RU → EN)
def translate_text(text, lang_code):
    try:
        translator = Translator()
        result = translator.translate(text, src=lang_code, dest='en')
        return result.text
    except Exception as e:
        print("❌ Google Çeviri hatası:", e)
        return "Translation failed."

# ✅ Telegram’a mesaj gönder
def send_to_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Telegram gönderim hatası:", e)

# 💾 En son gönderilen mesajın ID’sini sakla
def get_last_saved(feed_name):
    filename = f"last_{feed_name}.txt"
    try:
        with open(filename, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last(feed_name, entry_id):
    filename = f"last_{feed_name}.txt"
    with open(filename, "w") as f:
        f.write(entry_id)

# 🔁 Her kanal için işlem
def process_feed(feed_name, feed_info):
    print(f"🔄 {feed_name} kontrol ediliyor...")

    url = feed_info["url"]
    lang = feed_info["lang"]

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"
    }
    response = requests.get(url, headers=headers)
    feed = feedparser.parse(response.content)

    if not feed.entries:
        print(f"❌ {feed_name} için veri yok.")
        return

    latest_entry = feed.entries[0]
    last_saved = get_last_saved(feed_name)

    if latest_entry.id != last_saved:
        title = latest_entry.title
        summary = BeautifulSoup(latest_entry.summary, "html.parser").get_text()
        combined = f"{title}\n\n{summary}"

        clean_text = remove_hashtags(combined)
        translated = translate_text(clean_text, lang)

        final_message = f"{translated}\n\nFollow us on X: @PulseofGlobe"
        send_to_telegram(final_message)

        save_last(feed_name, latest_entry.id)
        print(f"✅ {feed_name} yeni mesaj gönderildi!")
    else:
        print(f"🔁 {feed_name} için yeni mesaj yok.")

# 🔁 Ana döngü
def main():
    for feed_name, feed_info in RSS_FEEDS.items():
        process_feed(feed_name, feed_info)

if __name__ == "__main__":
    while True:
        main()
        time.sleep(CHECK_INTERVAL)

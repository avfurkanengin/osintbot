import feedparser
import os
import time
import requests
from bs4 import BeautifulSoup
from googletrans import Translator  # Google Translate API (ücretsiz)

# 🔐 GİZLİ DEĞİŞKENLER
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 📡 RSS FEED URL
RSS_URL = "https://rsshub.app/telegram/channel/conflict_tr"
CHECK_INTERVAL = 300  # saniye (5 dakika)

# ✅ Çeviri Fonksiyonu (Google Translate ile)
def translate_text(text):
    try:
        translator = Translator()
        result = translator.translate(text, src='tr', dest='en')
        return result.text
    except Exception as e:
        print("❌ Google Çeviri hatası:", e)
        return "Translation failed."

# 📬 Telegram'a mesaj gönderme
def send_to_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Telegram gönderim hatası:", e)

# 💾 Son görülen mesajı sakla / kontrol et
def get_last_saved():
    try:
        with open("last.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last(entry_id):
    with open("last.txt", "w") as f:
        f.write(entry_id)

# 🔁 Ana döngü
def main():
    print("🔄 Telegram RSS kontrol ediliyor...")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RSSBot/1.0)"
    }
    response = requests.get(RSS_URL, headers=headers)
    feed = feedparser.parse(response.content)

    if not feed.entries:
        print("❌ Feed boş.")
        return

    latest_entry = feed.entries[0]
    last_saved = get_last_saved()

    if latest_entry.id != last_saved:
        title = latest_entry.title
        summary = BeautifulSoup(latest_entry.summary, "html.parser").get_text()
        combined = f"{title}\n\n{summary}"
        translated = translate_text(combined)

        mesaj = f"📢 Yeni Mesaj (ConflictTR):\n\n🗣 {title}\n\n📘 Çeviri:\n{translated}"
        send_to_telegram(mesaj)
        save_last(latest_entry.id)
        print("✅ Yeni mesaj gönderildi!")
    else:
        print("🔁 Yeni mesaj yok.")

# ⏱ Sürekli çalıştır
if __name__ == "__main__":
    while True:
        main()
        time.sleep(CHECK_INTERVAL)

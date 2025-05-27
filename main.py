import feedparser
import openai
import os
import time
import requests

# GİZLİ DEĞİŞKENLER
openai.api_key = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# RSS FEED
RSS_URL = "https://rsshub.app/telegram/channel/conflict_tr"
CHECK_INTERVAL = 300  # 5 dakika

def get_last_saved():
    try:
        with open("last.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last(entry_id):
    with open("last.txt", "w") as f:
        f.write(entry_id)

def translate_text(text):
    try:
        prompt = f"Translate this Turkish news post to English:\n\n{text}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Çeviri hatası:", e)
        return "Translation failed."

def send_to_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram gönderim hatası:", e)

def main():
    print("🔄 Telegram RSS kontrol ediliyor...")
    feed = feedparser.parse(RSS_URL)
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

if __name__ == "__main__":
    while True:
        main()
        time.sleep(CHECK_INTERVAL)

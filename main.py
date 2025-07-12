import os
import base64
import time
import traceback
from telethon.sync import TelegramClient
from config import *
from bot import process_channel
from keep_alive import keep_alive  # Assuming keep_alive.py exists; otherwise integrate
from utils import get_sent_hashes

# Session setup - Use SESSION_FILE from config which handles Railway deployment
session_path = SESSION_FILE.replace('.session', '')  # Remove .session extension for TelegramClient

# Clean up lock files that might remain from previous runs
try:
    os.remove(f"{session_path}.session-journal")
except (FileNotFoundError, OSError):
    pass

try:
    os.remove(f"{session_path}.session-wal")
except (FileNotFoundError, OSError):
    pass

try:
    os.remove(f"{session_path}.session-shm")
except (FileNotFoundError, OSError):
    pass

client = TelegramClient(session_path, API_ID, API_HASH)

print("📡 Telegram bağlantısı kuruluyor...")
client.start()

if not client.is_user_authorized():
    print("❌ Telegram istemcisi yetkili değil! Railway üzerinde numara girilemez.")
    exit()
print("✅ Telegram oturumu aktif.\n")

def main():
    keep_alive()
    print("🚀 Bot çalışmaya başladı. Kanallar taranıyor...\n")
    while True:
        try:
            print("[INFO] Kanallar kontrol ediliyor...")
            sent_hashes = get_sent_hashes()
            new_messages = 0

            with client:
                for channel, info in CHANNELS.items():
                    if process_channel(client, channel, info, sent_hashes):
                        new_messages += 1

            if new_messages == 0:
                print("[INFO] Yeni mesaj bulunamadı.")
        except Exception as e:
            print("❌ Genel hata:", e)
            traceback.print_exc()

        # In main loop, calculate sleep based on priorities
        sleep_time = LOOP_INTERVAL if new_messages == 0 else LOOP_INTERVAL / 2  # Example adaptive
        print(f"[WAIT] {LOOP_INTERVAL / 60} dakika bekleniyor...\n")
        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    main()
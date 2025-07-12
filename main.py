import os
import base64
import time
import traceback
import tempfile
from telethon.sync import TelegramClient
from config import *
from bot import process_channel
from keep_alive import keep_alive  # Assuming keep_alive.py exists; otherwise integrate
from utils import get_sent_hashes

# Force session loading from repository files
def load_session_from_files():
    """Load session from repository files and return session path"""
    print("🔍 Loading session from repository files...")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📋 Files available: {os.listdir('.')}")
    
    session_parts = []
    for i in range(1, 10):
        part_file = f"session_part_{i}.txt"
        if os.path.exists(part_file):
            print(f"✅ Found {part_file}")
            with open(part_file, 'r') as f:
                content = f.read().strip()
                session_parts.append(content)
                print(f"✅ Loaded {len(content)} characters from {part_file}")
        else:
            print(f"❌ {part_file} not found")
            break
    
    if session_parts:
        session_b64 = ''.join(session_parts)
        print(f"✅ Total session length: {len(session_b64)} characters")
        
        try:
            session_data = base64.b64decode(session_b64)
            temp_session = tempfile.NamedTemporaryFile(delete=False, suffix='.session')
            temp_session.write(session_data)
            temp_session.close()
            print(f"✅ Created session file: {temp_session.name}")
            return temp_session.name.replace('.session', '')
        except Exception as e:
            print(f"❌ Error decoding session: {e}")
    
    print("❌ No valid session found, using default")
    return SESSION_FILE.replace('.session', '')

# Session setup - Force load from repository files
session_path = load_session_from_files()

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
    
    # Add a startup delay to prevent immediate processing
    print("[STARTUP] Waiting 10 seconds before first scan...")
    time.sleep(10)
    
    while True:
        try:
            print("[INFO] Kanallar kontrol ediliyor...")
            sent_hashes = get_sent_hashes()
            print(f"[DEBUG] Loaded {len(sent_hashes)} sent hashes")
            new_messages = 0

            with client:
                for channel, info in CHANNELS.items():
                    if process_channel(client, channel, info, sent_hashes):
                        new_messages += 1
                        # Add delay between channels to prevent rapid processing
                        print(f"[WAIT] Processed channel {channel}, waiting 10 seconds...")
                        time.sleep(10)

            if new_messages == 0:
                print("[INFO] Yeni mesaj bulunamadı.")
        except Exception as e:
            print("❌ Genel hata:", e)
            traceback.print_exc()
            # Add delay on error to prevent rapid retries
            print("[ERROR] Waiting 60 seconds before retry...")
            time.sleep(60)

        # In main loop, calculate sleep based on priorities
        sleep_time = LOOP_INTERVAL if new_messages == 0 else LOOP_INTERVAL / 2  # Example adaptive
        print(f"[WAIT] {LOOP_INTERVAL / 60} dakika bekleniyor...\n")
        time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    main()
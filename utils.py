import hashlib
import csv
import os
from datetime import datetime
import requests
from PIL import Image
import numpy as np
import re

def get_sent_hashes(file_path="sent_hashes.txt"):
    try:
        with open(file_path, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_sent_hash(content_hash, file_path="sent_hashes.txt"):
    with open(file_path, "a") as f:
        f.write(content_hash + "\n")

def get_content_similarity_hash(text):
    """Create a hash for similar content detection"""
    # Remove common words, punctuation, and normalize
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = text.split()
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'has', 'have', 'had'}
    filtered_words = [w for w in words if w not in common_words and len(w) > 2]
    # Sort words to catch similar content regardless of order
    filtered_words.sort()
    similarity_text = ' '.join(filtered_words[:10])  # Take first 10 significant words
    return hashlib.md5(similarity_text.encode()).hexdigest()

def is_similar_content(text, sent_hashes):
    """Check if content is similar to already sent content"""
    similarity_hash = get_content_similarity_hash(text)
    return similarity_hash in sent_hashes

def log_gpt_interaction(csv_file, stage, date, channel, text, sent, usage):
    try:
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
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

def send_to_telegram(bot_token, chat_id, text, media_path=None, is_video=False):
    try:
        if media_path:
            url = f"https://api.telegram.org/bot{bot_token}/sendVideo" if is_video else f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            with open(media_path, 'rb') as media_file:
                files = {'video' if is_video else 'photo': media_file}
                data = {"chat_id": chat_id, "caption": text}
                response = requests.post(url, data=data, files=files)
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
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

def remove_hashtags(text):
    import re
    return re.sub(r"#\S+\s*", "", text) 
import openai
import hashlib
import time
import traceback
import os
from datetime import datetime
from telethon.sync import TelegramClient
from config import *
from utils import *
import re
from urllib.parse import quote
import requests
from database import DatabaseManager

# Configure OpenAI client properly for newer versions
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Disable any proxy settings that might cause issues
os.environ['NO_PROXY'] = '*'

# Initialize database
db = DatabaseManager()

def calculate_content_quality(text, sender_name="", channel=""):
    """Calculate content quality score based on various factors"""
    score = 0.5  # Base score
    
    # Length factor (optimal around 100-200 chars)
    length = len(text)
    if 50 <= length <= 300:
        score += 0.2
    elif length > 300:
        score -= 0.1
    
    # Official source indicators
    official_terms = ['breaking', 'urgent', 'confirmed', 'official', 'statement', 'announces']
    if any(term in text.lower() for term in official_terms):
        score += 0.2
    
    # Geopolitical relevance
    geo_terms = ['government', 'military', 'president', 'minister', 'embassy', 'border', 'sanctions']
    geo_count = sum(1 for term in geo_terms if term in text.lower())
    score += min(geo_count * 0.1, 0.3)
    
    # Reduce score for promotional content
    promo_terms = ['subscribe', 'follow', 'join', 'channel', 'link']
    if any(term in text.lower() for term in promo_terms):
        score -= 0.2
    
    return min(max(score, 0), 1)  # Clamp between 0 and 1

def calculate_bias_score(text):
    """Calculate bias score (0 = neutral, 1 = highly biased)"""
    bias_terms = [
        'puppet', 'regime', 'terrorist', 'fascist', 'evil', 'destroy', 'crush',
        'zionist', 'propaganda', 'fake', 'lies', 'corrupt', 'dictator'
    ]
    
    bias_count = sum(1 for term in bias_terms if term in text.lower())
    return min(bias_count * 0.2, 1)  # Max bias score of 1

def translate_if_geopolitical(text):
    prompt = (
        "You will receive a news post.\n\n"
        "1. If the content is NOT about international politics, global affairs, or geopolitical events, respond ONLY with: \"SKIP\".\n"
        "2. If it IS geopolitical, translate or rewrite the content into fluent, concise English suitable for a Twitter audience. "
        "Keep it under 280 characters. Stay strictly neutral and objective. Do not use hashtags. "
        "Begin with a country flag emoji if the news is related to a specific country, or use a globe emoji 🌍 if it's global news.\n\n"
        "IMPORTANT: Remove any heavily biased language or propaganda terms. "
        "Focus on factual reporting. Avoid inflammatory terms like 'zionist', 'puppet government', 'evil empire', etc. "
        "Use neutral terms like 'government', 'officials', 'authorities', 'reported', 'according to sources'. "
        "However, standard news terms like 'regime', 'breaking news', 'urgent', 'destroy', 'crush' are acceptable when factually accurate.\n\n"
        "Return only the translated/rewritten version or the word 'SKIP'."
    )
    try:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        output = (response.choices[0].message.content or '').strip()
        return output, response.usage
    except Exception as e:
        print(f"[GPT TRANSLATE ERROR] {type(e).__name__}: {e}")
        print(f"[GPT TRANSLATE ERROR] Full traceback: {traceback.format_exc()}")
        return "", None

def process_channel(client, channel, info, sent_hashes):
    allowed_senders = info['allowed_senders']
    print(f"[INFO] Kanal: {channel}")

    # Add more detailed logging for debugging
    print(f"[DEBUG] Processing channel {channel} with {MESSAGE_LIMIT} message limit")
    print(f"[DEBUG] Current sent_hashes count: {len(sent_hashes)}")

    for message in client.iter_messages(channel, limit=MESSAGE_LIMIT):
        if not message.text or not message.sender:
            continue

        sender_name = getattr(message.sender, 'first_name', '') or getattr(message.sender, 'title', '')
        
        # If allowed_senders is empty, allow all senders (for discovering sender names)
        if allowed_senders and sender_name not in allowed_senders:
            print(f"[SKIP] Filtreden geçmedi: {sender_name}")
            continue
        
        # Log sender name for new channels to help identify actual sender names
        if not allowed_senders:
            print(f"[INFO] Gönderen: {sender_name} (kanal: {channel})")

        raw_text = message.text.strip()
        lower_text = raw_text.lower()

        if any(keyword in lower_text for keyword in BLOCKED_KEYWORDS):
            print("[SKIP] Yasaklı içerik, atlanıyor.")
            continue

        if re.search(r"https?://\S+", raw_text) or any(e in raw_text for e in BLOCKED_EMOJIS):
            print("[SKIP] Uygunsuz içerik, atlanıyor.")
            continue

        current_hash = hashlib.md5((channel + raw_text).encode()).hexdigest()
        print(f"[DEBUG] Processing message {message.id} from {channel}, hash: {current_hash[:8]}...")
        
        if current_hash in sent_hashes:
            print(f"[DUPLICATE] Hash {current_hash[:8]}... already in sent_hashes, skipping.")
            continue
            
        # Also check database for duplicates before processing
        message_id = f"{channel}_{message.id}"
        existing_post = db.get_post_by_message_id(message_id)
        if existing_post:
            print(f"[DUPLICATE] Post already exists in database: {message_id}")
            continue

        # Check if message is too recent (within last 5 minutes) to prevent rapid processing
        message_date = message.date
        if message_date:
            time_diff = datetime.now() - message_date
            if time_diff.total_seconds() < 300:  # 5 minutes
                print(f"[SKIP] Message too recent ({time_diff.total_seconds():.0f}s ago), skipping to prevent duplicates")
                continue

        cleaned = remove_hashtags(raw_text)
        
        # Calculate quality and bias scores
        quality_score = calculate_content_quality(cleaned, sender_name, channel)
        bias_score = calculate_bias_score(cleaned)
        
        # Create message ID for database
        message_id = f"{channel}_{message.id}"
        
        # Determine media type and path
        media_type = None
        media_path = None
        is_video = False
        
        if message.video:
            media_type = "video"
            try:
                media_path = client.download_media(message.video, file="media/")
                is_video = True
            except Exception as e:
                print("[WARN] Video indirilemedi:", e)
        elif message.photo:
            media_type = "photo"
            try:
                media_path = client.download_media(message.photo, file="media/")
                if is_image_red_or_black_heavy(media_path, MEDIA_THRESHOLD):
                    print("[SKIP] Görselde kırmızı/siyah baskın. Atlanıyor.")
                    continue
            except Exception as e:
                print("[WARN] Fotoğraf indirilemedi:", e)
        
        # Translate and check if geopolitical
        translated, usage = translate_if_geopolitical(cleaned)
        
        # Check if translation failed or returned empty
        if not translated or translated.upper() == "SKIP":
            print("[SKIP] GPT 'SKIP' dedi veya çeviri başarısız.")
            log_gpt_interaction(CSV_FILE, "Translate & Filter", datetime.now().strftime("%Y-%m-%d %H:%M"), channel, cleaned, False, usage)
            
            # Still save to database as rejected content
            post_data = {
                'message_id': message_id,
                'channel_name': channel,
                'sender_name': sender_name,
                'original_text': cleaned,
                'translated_text': None,
                'media_type': media_type,
                'media_path': media_path,
                'classification': 'non_geopolitical',
                'quality_score': quality_score,
                'bias_score': bias_score,
                'status': 'rejected',
                'content_hash': current_hash,
                'similarity_hash': hashlib.md5(cleaned.encode()).hexdigest(),
                'priority': info.get('priority', 1),
                'telegram_url': f"https://t.me/{channel}/{message.id}"
            }
            db.add_post(post_data)
            
            # Save hash for rejected posts too to prevent reprocessing
            save_sent_hash(current_hash)
            continue

        # Validate translated content before creating message
        if len(translated.strip()) < 10:
            print("[SKIP] Çeviri çok kısa veya boş.")
            continue

        # Create X (Twitter) URL
        tweet_url = "https://x.com/intent/tweet?text=" + quote(translated)
        final_message = f"{translated}\n\n🔗 Post on X: {tweet_url}"

        # Save to database as pending
        post_data = {
            'message_id': message_id,
            'channel_name': channel,
            'sender_name': sender_name,
            'original_text': cleaned,
            'translated_text': translated,
            'media_type': media_type,
            'media_path': media_path,
            'classification': 'geopolitical',
            'quality_score': quality_score,
            'bias_score': bias_score,
            'status': 'pending',
            'content_hash': current_hash,
            'similarity_hash': hashlib.md5(cleaned.encode()).hexdigest(),
            'priority': info.get('priority', 1),
            'telegram_url': f"https://t.me/{channel}/{message.id}"
        }
        
        post_id = db.add_post(post_data)
        
        if post_id:
            print(f"[DATABASE] Saved post {post_id} to database")
            
            # Save hash BEFORE sending to prevent duplicates on restart
            save_sent_hash(current_hash)
            
            # For now, still auto-post to Telegram (can be disabled later)
            print("[SEND] Gönderiliyor:\n", final_message)
            send_to_telegram(BOT_TOKEN, CHAT_ID, final_message, media_path, is_video=is_video)
            
            # Update status to posted
            db.update_post_status(post_id, 'posted')
            
            log_gpt_interaction(CSV_FILE, "Final", datetime.now().strftime("%Y-%m-%d %H:%M"), channel, cleaned, True, usage)

            # Add longer delay to prevent rapid duplicate processing
            print("[WAIT] Waiting 30 seconds before processing next message...")
            time.sleep(30)
            return True  # Indicate a new message was processed
        else:
            print("[WARN] Failed to save post to database or duplicate detected")
            
    return False 
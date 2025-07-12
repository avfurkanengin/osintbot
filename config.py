import os
from dotenv import load_dotenv
import base64
import tempfile

load_dotenv()

# Railway deployment: Handle base64 encoded session
def get_session_file():
    """Get session file path, handling Railway deployment"""
    session_b64 = os.getenv('SESSION_B64')
    
    # Try to get split session data (for very long sessions)
    if not session_b64:
        session_parts = []
        for i in range(1, 10):  # Check SESSION_B64_1, SESSION_B64_2, etc.
            part = os.getenv(f'SESSION_B64_{i}')
            if part:
                session_parts.append(part)
            else:
                break
        if session_parts:
            session_b64 = ''.join(session_parts)
            print(f"✅ Reconstructed session from {len(session_parts)} parts")
    
    # Check if we're in Railway deployment (SESSION_B64 exists and is valid)
    if session_b64 and len(session_b64) > 100:  # Base64 should be long
        # Decode base64 session for Railway deployment
        try:
            session_data = base64.b64decode(session_b64)
            # Create temporary session file
            temp_session = tempfile.NamedTemporaryFile(delete=False, suffix='.session')
            temp_session.write(session_data)
            temp_session.close()
            print(f"✅ Using Railway session file: {temp_session.name}")
            return temp_session.name
        except Exception as e:
            print(f"❌ Error decoding Railway session: {e}")
            print("🔄 Falling back to local session file")
    
    # Local development - use the existing session file
    local_session = "multi_session.session"
    if os.path.exists(local_session):
        print(f"✅ Using local session file: {local_session}")
        return local_session
    else:
        print(f"❌ Local session file not found: {local_session}")
        print("🔄 Will create new session file when bot starts")
        return local_session

# Load sensitive data from environment variables
api_id_str = os.getenv("API_ID")
if api_id_str is None:
    raise ValueError("API_ID is missing")
API_ID = int(api_id_str)
api_hash = os.getenv("API_HASH")
if api_hash is None:
    raise ValueError("API_HASH is missing")
API_HASH = api_hash
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key is None:
    raise ValueError("OPENAI_API_KEY is missing")
OPENAI_API_KEY = openai_key
bot_token = os.getenv("BOT_TOKEN")
if bot_token is None:
    raise ValueError("BOT_TOKEN is missing")
BOT_TOKEN = bot_token
chat_id = os.getenv("CHAT_ID")
if chat_id is None:
    raise ValueError("CHAT_ID is missing")
CHAT_ID = chat_id
CSV_FILE = os.getenv("CSV_FILE", "gpt_full_log.csv")

# Hardcoded configurations (non-sensitive)
CHANNELS = {
    'conflict_tr': {'lang': 'tr', 'allowed_senders': ['ConflictTR'], 'priority': 1},
    'ww3media': {'lang': 'tr', 'allowed_senders': ['3. Dünya Savaşı'], 'priority': 1},
    'ateobreaking': {'lang': 'ru', 'allowed_senders': ['Ateo Breaking'], 'priority': 1},
    # New channels - allow all senders initially to discover actual sender names
    'firstreportsnews': {'lang': 'en', 'allowed_senders': [], 'priority': 2},
    # 'IranintlTV': {'lang': 'en', 'allowed_senders': [], 'priority': 2},
    # 'lebanonNewsNow': {'lang': 'en', 'allowed_senders': [], 'priority': 2},
    # 'DDGeopolitics': {'lang': 'en', 'allowed_senders': [], 'priority': 2},
}

BLOCKED_EMOJIS = ['🎉', '🎁', '🎊', '🎈', '🎂', '🎇', '🎆', '🥳', '🎀', '🎟']
BLOCKED_KEYWORDS = [
    'advertiser', 'sponsor', 'sponsored', 'promotion', 'telegram premium',
    'reklam', 'sponsor', 'sponsorlu', 'taksit', 'indirim', 'kampanya',
    'dem parti', 'dem partisi', 'özgür özel', 'chp', 'akp', 'ımamoğlu', 'imamoglu',
    'conflicttr', 'ww3media', 'ateobreaking', 'dunyadantr', 'dunyadan_tr',
    # Specific bias terms
    'zionist', 'siyonist', 'zionism', 'siyonizm', 'zionist regime', 'sionist',
]

# Enhanced filtering for biased language
BIAS_KEYWORDS = [
    'zionist', 'siyonist', 'zionism', 'siyonizm', 'zionist regime', 'sionist',
    'puppet government', 'puppet regime', 'puppet state',
    'evil empire', 'axis of evil'
]

SESSION_NAME = "multi_session"
SESSION_FILE = get_session_file()  # Use dynamic session file path
MESSAGE_LIMIT = 4
LOOP_INTERVAL = 300  # 5 minutes
MEDIA_THRESHOLD = 0.7  # For image color filter 
#!/usr/bin/env python3
"""
Script to create a valid Telegram session file for the OSINT bot
Run this locally to authenticate with Telegram and create the session file
"""

import os
import base64
from telethon.sync import TelegramClient
from config import API_ID, API_HASH

def create_session():
    """Create a new Telegram session file"""
    print("🔐 Creating Telegram session...")
    print("📱 You will need to enter your phone number and verification code")
    
    # Create session file
    session_name = "multi_session"
    client = TelegramClient(session_name, API_ID, API_HASH)
    
    print("📡 Connecting to Telegram...")
    client.start()
    
    if client.is_user_authorized():
        print("✅ Successfully authenticated with Telegram!")
        print(f"✅ Session file created: {session_name}.session")
        
        # Test channel access
        print("\n🔍 Testing channel access...")
        try:
            with client:
                # Test access to one of your channels
                entity = client.get_entity('conflict_tr')
                print(f"✅ Can access channel: {entity.title}")
        except Exception as e:
            print(f"⚠️ Warning: Could not access channel 'conflict_tr': {e}")
            print("Make sure you're a member of all the channels you want to monitor")
        
        # Create base64 encoded version for Railway
        session_file = f"{session_name}.session"
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                session_data = f.read()
            
            session_b64 = base64.b64encode(session_data).decode('utf-8')
            
            print(f"\n📋 Base64 encoded session (copy this to Railway):")
            print("=" * 50)
            print(session_b64)
            print("=" * 50)
            
            # Save to file for easy copying
            with open('session_b64.txt', 'w') as f:
                f.write(session_b64)
            print(f"✅ Base64 session saved to: session_b64.txt")
            
            print(f"\n🚀 Next steps:")
            print("1. Copy the base64 string above")
            print("2. Go to your Railway dashboard")
            print("3. Add environment variable: SESSION_B64")
            print("4. Paste the base64 string as the value")
            print("5. Redeploy your Railway app")
            
        else:
            print("❌ Session file not found after creation")
    else:
        print("❌ Failed to authenticate with Telegram")
    
    client.disconnect()

if __name__ == "__main__":
    create_session() 
#!/usr/bin/env python3
"""
Script to check if there's an existing valid Telegram session file
"""

import os
import base64
from telethon.sync import TelegramClient
from config import API_ID, API_HASH

def check_existing_session():
    """Check if there's an existing valid session file"""
    session_files = [
        "multi_session.session",
        "osint_bot.session", 
        "telegram_session.session",
        "bot.session"
    ]
    
    print("🔍 Checking for existing session files...")
    
    for session_file in session_files:
        if os.path.exists(session_file):
            size = os.path.getsize(session_file)
            print(f"📁 Found: {session_file} ({size} bytes)")
            
            if size > 0:
                print(f"✅ Testing session file: {session_file}")
                
                # Test the session file
                session_name = session_file.replace('.session', '')
                client = TelegramClient(session_name, API_ID, API_HASH)
                
                try:
                    client.connect()
                    if client.is_user_authorized():
                        print(f"✅ Valid session found: {session_file}")
                        
                        # Create base64 version
                        with open(session_file, 'rb') as f:
                            session_data = f.read()
                        
                        session_b64 = base64.b64encode(session_data).decode('utf-8')
                        
                        print(f"\n📋 Base64 encoded session for Railway:")
                        print("=" * 50)
                        print(session_b64)
                        print("=" * 50)
                        
                        # Save to file
                        with open('session_b64.txt', 'w') as f:
                            f.write(session_b64)
                        print(f"✅ Base64 session saved to: session_b64.txt")
                        
                        client.disconnect()
                        return True
                    else:
                        print(f"❌ Session file exists but not authorized: {session_file}")
                except Exception as e:
                    print(f"❌ Error testing session {session_file}: {e}")
                finally:
                    client.disconnect()
            else:
                print(f"❌ Empty session file: {session_file}")
        else:
            print(f"❌ Not found: {session_file}")
    
    print("\n🔐 No valid session files found.")
    print("💡 You need to create a new session file using create_session.py")
    return False

if __name__ == "__main__":
    check_existing_session() 
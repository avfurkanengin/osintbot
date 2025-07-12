#!/usr/bin/env python3
"""
Script to split a long SESSION_B64 string into multiple Railway environment variables.
Railway has a 32,768 character limit per variable.
"""

def split_session_string(session_b64, max_length=32000):
    """Split a long session string into multiple parts"""
    if len(session_b64) <= max_length:
        print(f"✅ Session string is {len(session_b64)} characters - no splitting needed!")
        print(f"Just use: SESSION_B64={session_b64}")
        return
    
    print(f"📏 Session string is {len(session_b64)} characters - splitting needed!")
    print(f"🔪 Max length per variable: {max_length}")
    
    # Split the string into chunks
    chunks = []
    for i in range(0, len(session_b64), max_length):
        chunk = session_b64[i:i+max_length]
        chunks.append(chunk)
    
    print(f"✂️ Split into {len(chunks)} parts")
    print("\n🚀 Add these variables to Railway:")
    print("="*60)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"SESSION_B64_{i}={chunk}")
        print(f"   (Length: {len(chunk)} characters)")
        print()
    
    print("="*60)
    print("📝 Instructions:")
    print("1. Remove the original SESSION_B64 variable from Railway")
    print("2. Add each SESSION_B64_1, SESSION_B64_2, etc. as separate variables")
    print("3. Deploy your app")
    print("4. The config.py will automatically reconstruct the session")

if __name__ == "__main__":
    print("🔧 Railway Session String Splitter")
    print("="*50)
    
    # Get the session string from user
    session_string = input("📋 Paste your SESSION_B64 string here: ").strip()
    
    if not session_string:
        print("❌ No session string provided!")
        exit(1)
    
    # Split the session string
    split_session_string(session_string) 
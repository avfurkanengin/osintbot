#!/usr/bin/env python3
"""
Simple script to split the SESSION_B64 string for Railway deployment
"""

# Read the session string from the file
with open('session_b64.txt', 'r') as f:
    session_string = f.read().strip()

print(f"📏 Session string is {len(session_string)} characters")

# Split into chunks of 32000 characters (Railway limit is 32768)
max_length = 32000
chunks = []

for i in range(0, len(session_string), max_length):
    chunk = session_string[i:i+max_length]
    chunks.append(chunk)

print(f"✂️ Split into {len(chunks)} parts")
print("\n🚀 Add these variables to Railway:")
print("="*60)

for i, chunk in enumerate(chunks, 1):
    print(f"\nSESSION_B64_{i}:")
    print(f"Length: {len(chunk)} characters")
    print(f"Value: {chunk}")
    print("-" * 40)

print("="*60)
print("\n📝 Instructions:")
print("1. Go to Railway dashboard")
print("2. Remove any existing SESSION_B64 variable")
print("3. Add each SESSION_B64_1, SESSION_B64_2, etc. as separate variables")
print("4. Copy the exact value for each variable (without quotes)")
print("5. Deploy your app")
print("6. The config.py will automatically reconstruct the session") 
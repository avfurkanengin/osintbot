from database import DatabaseManager
from datetime import datetime

db = DatabaseManager()
posts = db.get_posts(status='posted', limit=5)

print('Recent posted posts:')
for p in posts:
    created = datetime.fromisoformat(p['created_at'].replace('Z', '+00:00'))
    print(f'{created}: {p["original_text"][:50]}...')

print('\nChecking all posts by status:')
all_posts = db.get_posts()
status_counts = {}
for p in all_posts:
    status = p['status']
    status_counts[status] = status_counts.get(status, 0) + 1

for status, count in status_counts.items():
    print(f'{status}: {count}') 
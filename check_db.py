from database import DatabaseManager

db = DatabaseManager()
posts = db.get_posts()  # Get all posts without status filter

print(f'Total posts: {len(posts)}')

confirmed = [p for p in posts if p['status'] == 'posted']
rejected = [p for p in posts if p['status'] == 'rejected']
pending = [p for p in posts if p['status'] == 'pending']

print(f'Confirmed: {len(confirmed)}')
print(f'Rejected: {len(rejected)}')
print(f'Pending: {len(pending)}')

print('\nRecent posts:')
for p in posts[-10:]:
    print(f"{p['status']}: {p['original_text'][:50]}...") 
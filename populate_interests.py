"""
Script to populate Interest data in the database
Run with: python manage.py shell < populate_interests.py
"""
from api.models import Interest

interests_data = [
    {"interest_id": "technology", "name": "Technology", "image": "https://example.com/images/technology.jpg"},
    {"interest_id": "art", "name": "Art", "image": "https://example.com/images/art.jpg"},
    {"interest_id": "travel", "name": "Travel", "image": "https://example.com/images/travel.jpg"},
    {"interest_id": "music", "name": "Music", "image": "https://example.com/images/music.jpg"},
    {"interest_id": "sports", "name": "Sports", "image": "https://example.com/images/sports.jpg"},
    {"interest_id": "food", "name": "Food", "image": "https://example.com/images/food.jpg"},
    {"interest_id": "photography", "name": "Photography", "image": "https://example.com/images/photography.jpg"},
    {"interest_id": "fashion", "name": "Fashion", "image": "https://example.com/images/fashion.jpg"},
    {"interest_id": "fitness", "name": "Fitness", "image": "https://example.com/images/fitness.jpg"},
    {"interest_id": "diy", "name": "DIY", "image": "https://example.com/images/diy.jpg"},
]

print("Populating interests...")
for item in interests_data:
    interest, created = Interest.objects.get_or_create(**item)
    if created:
        print(f"✅ Created: {interest.name}")
    else:
        print(f"⚠️  Already exists: {interest.name}")

print(f"\n✅ Total interests in database: {Interest.objects.count()}")

#!/usr/bin/env python3
"""
Test script for Google Geocoding API integration
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.auth_views import get_location_details

def test_google_geocoding():
    """Test the Google Geocoding API with various coordinates"""

    test_cases = [
        # Mumbai coordinates (from previous test)
        {'lat': '19.0760', 'long': '72.8777', 'expected_city': 'Mumbai'},
        # Delhi coordinates
        {'lat': '28.6139', 'long': '77.2090', 'expected_city': 'New Delhi'},
        # Bangalore coordinates
        {'lat': '12.9716', 'long': '77.5946', 'expected_city': 'Bengaluru'},
        # Invalid coordinates
        {'lat': '91.0', 'long': '0.0', 'expected_city': 'Invalid Coordinates'},
        # Invalid format
        {'lat': 'invalid', 'long': '72.8777', 'expected_city': 'Invalid Format'},
    ]

    print("🗺️  Testing Google Geocoding API Integration")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        lat = test_case['lat']
        long = test_case['long']
        expected = test_case['expected_city']

        print(f"\nTest {i}: lat={lat}, long={long}")
        print("-" * 30)

        try:
            result = get_location_details(lat, long)
            print(f"Result: {result}")
            print(f"Expected city: {expected}")
            print(f"Match: {'✅' if result['city'] == expected else '❌'}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("Testing complete!")

if __name__ == "__main__":
    test_google_geocoding()
import re

# Read the file
with open('api/feed_views.py', 'r') as f:
    content = f.read()

# Find the CreatePostView's media_url assignment followed by '# Create the post'
# We need to be careful to match only in CreatePostView, not SavePostView
# Let's use a more specific pattern that includes the class context

# Pattern to match in CreatePostView: the media_url assignment followed by '# Create the post'
# and make sure it's in CreatePostView by checking for the PUT method before it
pattern = r'(PUT /create-post - Returns the UI schema for the create post screen.*?media_url = \'https://via.placeholder.com/1x1/ffffff/ffffff\'  # Placeholder for text posts\n\n            # Create the post)'

replacement = r'\1\n\n            # Update user\'s PIN codes if necessary\n            # When a user creates a post with a specific pincode_id (e.g., pincode_home_560001),\n            # automatically add that PIN code to their profile so they can see their own posts\n            try:\n                pincode_parts = pincode_id.split(\'_\')\n                if len(pincode_parts) >= 3 and pincode_parts[0] == \'pincode\':\n                    pincode_type = pincode_parts[1]  # \'home\', \'office\', etc.\n                    \n                    # Update the appropriate PIN code field in user profile\n                    if pincode_type == \'home\' and not current_user.home_pincode:\n                        current_user.home_pincode = pincode\n                        current_user.save()\n                    elif pincode_type == \'office\' and not current_user.office_pincode:\n                        current_user.office_pincode = pincode\n                        current_user.save()\n                    elif pincode_type not in [\'home\', \'office\']:\n                        # For other types or if no specific type, add to additional_pincodes if not already there\n                        if pincode not in (current_user.additional_pincodes or []):\n                            additional = list(current_user.additional_pincodes or [])\n                            additional.append(pincode)\n                            current_user.additional_pincodes = additional\n                            current_user.save()\n            except (IndexError, AttributeError):\n                # If pincode_id parsing fails, continue without updating profile\n                pass\n\n            # Create the post'

# Use re.DOTALL to match across newlines
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('api/feed_views.py', 'w') as f:
    f.write(new_content)

print('Replacement completed')

        # Step 2: Fetch posts for the home feed
        # Get posts ordered by timestamp (newest first)
        posts = Post.objects.all().order_by('-timestamp')[:50]  # Limit to 50 posts for performance

        # Format posts for the feed
        feed_posts = []
        for post in posts:
            # Get user profile for the post author
            try:
                post_user = UserProfile.objects.get(userId=post.userId)
                author_name = post_user.name or f"User {post.userId[:8]}"
            except UserProfile.DoesNotExist:
                author_name = f"User {post.userId[:8]}"

            feed_posts.append({
                'postId': post.postId,
                'author': {
                    'userId': post.userId,
                    'name': author_name
                },
                'content': post.description or '',
                'mediaType': post.mediaType,
                'mediaURL': post.mediaURL,
                'pincode': post.pincode,
                'timestamp': post.timestamp.isoformat(),
                'location': post.location or {}
            })

        return Response({
            'results': [{
                'type': 'HOME_FEED_V1',
                'home_feed_v1': {
                    'posts': feed_posts,
                    'total_count': len(feed_posts)
                }
            }]
        }, status=status.HTTP_200_OK)

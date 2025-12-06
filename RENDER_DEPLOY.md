# Render Deployment Guide

## Quick Deploy Instructions

### 1. Render Configuration

**Build Command:**
```bash
pip install -r requirements.txt && python3 manage.py collectstatic --noinput
```

**Start Command:**
```bash
python3 manage.py migrate && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT
```

### 2. Required Environment Variables

Set these in Render Dashboard (Settings → Environment):

```
DJANGO_SECRET_KEY=<generate-a-strong-random-key>
DEBUG=False
ALLOWED_HOSTS=.onrender.com
SubaseUrl=https://qzhfqngedeadnyeqtoqp.supabase.co
SUPABASE_DB_PASSWORD=955Fp4x0TrLoWjha
ANON_PUBLIC=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF6aGZxbmdlZGVhZG55ZXF0b3FwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1MjA2NjEsImV4cCI6MjA3ODA5NjY2MX0.lv4JuwrEpnmkuoaW4fXSoM5NNInMiZ4zxjeS1NFdieA
SERVICE_ROLE=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF6aGZxbmdlZGVhZG55ZXF0b3FwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjUyMDY2MSwiZXhwIjoyMDc4MDk2NjYxfQ.pFOKMOixmCn3bzEjXFL6TJofc1Su6ChUNaLqttEjTSc
```

**Generate SECRET_KEY:**
```python
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Service Settings

- **Name:** `Social_Media_Platform_Backend`
- **Region:** Oregon (US West) or closest to your users
- **Branch:** `main`
- **Root Directory:** (leave blank)
- **Instance Type:** Free for testing, Starter+ for production

### 4. Deploy

1. Push changes to GitHub
2. Render will auto-deploy
3. Check logs for any errors
4. Visit your service URL to verify

### Troubleshooting

**Common Issues:**

1. **`python: not found`** → Use `python3` in commands
2. **`gunicorn: not found`** → Add `gunicorn` to requirements.txt (✅ Fixed)
3. **Static files 404** → Run `collectstatic` in build command (✅ Fixed)
4. **Database connection errors** → Verify Supabase env vars are set correctly
5. **500 errors** → Set `DEBUG=False` and check logs

**Health Check:**
Add this endpoint to test the service is running:
```python
# In api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def health_check(request):
    return Response({'status': 'healthy'})
```

Then add to urls.py:
```python
path('health/', health_check, name='health'),
```

### Post-Deploy Commands

Run these in Render Shell (if needed):

```bash
# Create superuser
python3 manage.py createsuperuser

# Run migrations manually
python3 manage.py migrate

# Collect static files
python3 manage.py collectstatic --noinput
```

### Production Checklist

- [x] `gunicorn` added to requirements.txt
- [x] `whitenoise` for static files
- [x] `SECRET_KEY` from environment variable
- [x] `DEBUG=False` in production
- [x] `ALLOWED_HOSTS` configured
- [x] Static files configured
- [ ] Set all environment variables in Render
- [ ] Test all API endpoints after deploy
- [ ] Monitor logs for errors
- [ ] Set up custom domain (optional)

## Additional Resources

- [Render Python Docs](https://render.com/docs/deploy-django)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Supabase Connection Guide](./SUPABASE_CONNECTION_GUIDE.md)

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone

try:
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    print(f"Total Registered Users: {User.objects.count()}")
    print(f"Active Logged-in Sessions: {active_sessions.count()}")

    for session in active_sessions:
        data = session.get_decoded()
        uid = data.get('_auth_user_id')
        if uid:
            try:
                user = User.objects.get(id=uid)
                print(f"- Logged in user: {user.username}")
            except User.DoesNotExist:
                pass
except Exception as e:
    print(f"Error checking DB: {str(e)}")

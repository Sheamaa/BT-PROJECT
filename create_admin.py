import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hpap.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = "admin"
password = "admin"
email = "admin@gmail.com"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )

print("Admin created or already exists")
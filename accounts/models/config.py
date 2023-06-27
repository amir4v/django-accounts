from django.conf import settings

USERNAME_MIN_LENGTH = getattr(settings, 'USERNAME_MIN_LENGTH', 6)
USERNAME_MAX_LENGTH = getattr(settings, 'USERNAME_MAX_LENGTH', 32)

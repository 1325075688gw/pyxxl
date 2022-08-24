from django.conf import settings


def test_print_settings():
    print(hasattr(settings, "A"))

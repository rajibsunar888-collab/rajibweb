from django.conf import settings

from .models import SiteProfile


def site_context(request):
    """Makes `profile` and the Turnstile key available in every template."""
    try:
        profile = SiteProfile.load()
    except Exception:  # e.g. before the first migration
        profile = None
    return {
        "profile": profile,
        "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
    }

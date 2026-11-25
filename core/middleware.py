from django.utils import timezone

from .models import PageView

SKIP_PREFIXES = ("/admin", "/static", "/media", "/contact", "/quote/send", "/testimonials",
                 "/subscribe", "/analytics", "/favicon")
BOT_WORDS = ("bot", "crawl", "spider", "slurp", "preview", "monitor", "curl", "wget")


class PageViewMiddleware:
    """Counts page views per path per day. Stores no IPs or personal data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if (
                request.method == "GET"
                and response.status_code == 200
                and not request.path.startswith(SKIP_PREFIXES)
                and not request.path.startswith("/cv")
                and not (getattr(request, "user", None) and request.user.is_staff)
                and not any(w in request.META.get("HTTP_USER_AGENT", "").lower() for w in BOT_WORDS)
                and "text/html" in response.get("Content-Type", "")
            ):
                from django.db.models import F
                obj, _ = PageView.objects.get_or_create(
                    path=request.path[:200], day=timezone.localdate())
                PageView.objects.filter(pk=obj.pk).update(count=F("count") + 1)
        except Exception:
            pass  # analytics must never break a page
        return response

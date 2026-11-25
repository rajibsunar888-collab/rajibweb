import json
import logging
import urllib.parse
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import F, Sum
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ContactForm, QuoteForm, SubscribeForm, TestimonialForm
from .models import (
    BlogPost, ContactMessage, GalleryImage, PageView, Project, QuoteRequest, Service,
    SiteProfile, Skill, SkillArea, Subscriber, Testimonial,
)
from .youtube import latest_videos

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ pages
def home(request):
    return render(request, "index.html", {
        "skills": Skill.objects.all(),
        "projects": Project.objects.filter(published=True, featured=True)[:3],
        "services": Service.objects.filter(published=True, show_on_home=True)[:4],
        "gallery": GalleryImage.objects.filter(published=True)[:5],
        "project_total": Project.objects.filter(published=True).count(),
        "videos": latest_videos(SiteProfile.load().youtube_channel_id),
        "testimonials": Testimonial.objects.filter(approved=True)[:6],
        "posts": BlogPost.objects.filter(published=True)[:3],
    })


def about(request):
    return render(request, "about.html")


def skills(request):
    return render(request, "skill.html", {"areas": SkillArea.objects.all()})


def projects(request):
    items = Project.objects.filter(published=True)
    return render(request, "project.html", {"projects": items, "project_total": items.count()})


def services(request):
    return render(request, "service.html", {"services": Service.objects.filter(published=True)})


# ------------------------------------------------------------------ CV download
def download_cv(request):
    profile = SiteProfile.load()
    SiteProfile.objects.filter(pk=profile.pk).update(cv_downloads=F("cv_downloads") + 1)
    if profile.cv_file:
        return FileResponse(profile.cv_file.open("rb"), as_attachment=True,
                            filename="Rajib_Sunar_CV.pdf")
    from django.contrib.staticfiles import finders
    path = finders.find("files/rajibcv.pdf")
    if not path:
        raise Http404("CV not found")
    return FileResponse(open(path, "rb"), as_attachment=True, filename="Rajib_Sunar_CV.pdf")


# ------------------------------------------------------------------ contact form
def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _turnstile_ok(token, ip):
    """Verify a Cloudflare Turnstile token. Returns True when Turnstile is not configured."""
    if not settings.TURNSTILE_SECRET_KEY:
        return True
    if not token:
        return False
    data = urllib.parse.urlencode({
        "secret": settings.TURNSTILE_SECRET_KEY, "response": token, "remoteip": ip or "",
    }).encode()
    try:
        req = urllib.request.Request(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify", data=data)
        with urllib.request.urlopen(req, timeout=8) as resp:
            return bool(json.load(resp).get("success"))
    except Exception:
        logger.exception("Turnstile verification failed")
        return False


def _notify(msg):
    body = (
        f"New message from your portfolio website\n\n"
        f"Name: {msg.name}\nEmail: {msg.email}\nSubject: {msg.subject}\n\n{msg.message}\n"
    )
    mail = EmailMessage(
        subject=f"[Portfolio] {msg.subject}",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_NOTIFY_EMAIL],
        reply_to=[msg.email],
    )
    try:
        mail.send()
        return True
    except Exception:
        logger.exception("Could not send contact notification email")
        return False


@require_POST
def contact(request):
    ip = _client_ip(request)

    window_start = timezone.now() - timedelta(minutes=settings.CONTACT_RATE_WINDOW_MINUTES)
    recent = ContactMessage.objects.filter(ip_address=ip, created__gte=window_start).count()
    if recent >= settings.CONTACT_RATE_LIMIT:
        return JsonResponse(
            {"ok": False, "error": "Too many messages from your network. Please try again later."},
            status=429,
        )

    form = ContactForm(request.POST)
    if not form.is_valid():
        if "website" in form.errors:  # honeypot tripped: pretend success to the bot
            return JsonResponse({"ok": True})
        first = next(iter(form.errors.values()))[0]
        return JsonResponse({"ok": False, "error": first, "errors": form.errors}, status=400)

    if not _turnstile_ok(request.POST.get("cf-turnstile-response"), ip):
        return JsonResponse(
            {"ok": False, "error": "Human verification failed. Please try again."}, status=400)

    msg = form.save(commit=False)
    msg.ip_address = ip
    msg.save()
    msg.email_sent = _notify(msg)
    msg.save(update_fields=["email_sent"])
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ shared helpers for new forms
def _owner_mail(subject, body, reply_to=None):
    mail = EmailMessage(
        subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.CONTACT_NOTIFY_EMAIL], reply_to=[reply_to] if reply_to else None,
    )
    try:
        mail.send()
        return True
    except Exception:
        logger.exception("Could not send notification email")
        return False


def _guard(request, model, form):
    """Common spam protection. Returns (JsonResponse or None, ip)."""
    ip = _client_ip(request)
    window_start = timezone.now() - timedelta(minutes=settings.CONTACT_RATE_WINDOW_MINUTES)
    if model.objects.filter(ip_address=ip, created__gte=window_start).count() >= settings.CONTACT_RATE_LIMIT:
        return JsonResponse(
            {"ok": False, "error": "Too many requests from your network. Please try again later."},
            status=429), ip
    if not form.is_valid():
        if "website" in form.errors:  # honeypot tripped: pretend success to the bot
            return JsonResponse({"ok": True}), ip
        first = next(iter(form.errors.values()))[0]
        return JsonResponse({"ok": False, "error": first, "errors": form.errors}, status=400), ip
    return None, ip


def _captcha_failed(request, ip):
    if _turnstile_ok(request.POST.get("cf-turnstile-response"), ip):
        return None
    return JsonResponse({"ok": False, "error": "Human verification failed. Please try again."}, status=400)


# ------------------------------------------------------------------ quote request
def quote_page(request):
    return render(request, "quote.html", {
        "services": Service.objects.filter(published=True),
        "budgets": QuoteRequest.BUDGETS,
        "preselect": request.GET.get("service", ""),
    })


@require_POST
def quote_submit(request):
    form = QuoteForm(request.POST)
    early, ip = _guard(request, QuoteRequest, form)
    if early:
        return early
    failed = _captcha_failed(request, ip)
    if failed:
        return failed
    d = form.cleaned_data
    q = QuoteRequest.objects.create(
        name=d["name"], email=d["email"], service=d["service"], budget=d["budget"],
        deadline=d["deadline"], details=d["details"], ip_address=ip,
    )
    q.email_sent = _owner_mail(
        f"[Portfolio] Quote request: {q.service or 'General'} from {q.name}",
        f"New quote request\n\nName: {q.name}\nEmail: {q.email}\nService: {q.service or '-'}\n"
        f"Budget: {q.get_budget_display()}\nDeadline: {q.deadline or '-'}\n\n{q.details}\n",
        reply_to=q.email,
    )
    q.save(update_fields=["email_sent"])
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ testimonials
@require_POST
def testimonial_submit(request):
    form = TestimonialForm(request.POST)
    early, ip = _guard(request, Testimonial, form)
    if early:
        return early
    failed = _captcha_failed(request, ip)
    if failed:
        return failed
    d = form.cleaned_data
    t = Testimonial.objects.create(
        name=d["name"], role=d["role"], rating=d["rating"], text=d["text"], ip_address=ip)
    _owner_mail(
        f"[Portfolio] New review waiting for approval from {t.name}",
        f"{t.name} ({t.role or 'no role'}) rated you {t.rating}/5:\n\n{t.text}\n\n"
        f"Approve it in the admin panel under Testimonials.",
    )
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ newsletter
@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    early, ip = _guard(request, Subscriber, form)
    if early:
        return early
    email = form.cleaned_data["email"].lower()
    sub, created = Subscriber.objects.get_or_create(email=email, defaults={"ip_address": ip})
    if not created and not sub.active:
        sub.active = True
        sub.save(update_fields=["active"])
    return JsonResponse({"ok": True})


# ------------------------------------------------------------------ blog
def blog_list(request):
    return render(request, "blog_list.html", {"posts": BlogPost.objects.filter(published=True)})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    BlogPost.objects.filter(pk=post.pk).update(views=F("views") + 1)
    others = BlogPost.objects.filter(published=True).exclude(pk=post.pk)[:3]
    return render(request, "blog_detail.html", {"post": post, "others": others})


# ------------------------------------------------------------------ analytics (staff only)
@staff_member_required
def analytics(request):
    today = timezone.localdate()

    def total(days):
        since = today - timedelta(days=days - 1)
        return PageView.objects.filter(day__gte=since).aggregate(n=Sum("count"))["n"] or 0

    since30 = today - timedelta(days=29)
    top_pages = (PageView.objects.filter(day__gte=since30).values("path")
                 .annotate(n=Sum("count")).order_by("-n")[:10])
    daily = (PageView.objects.filter(day__gte=today - timedelta(days=13)).values("day")
             .annotate(n=Sum("count")).order_by("day"))
    daily_map = {d["day"]: d["n"] for d in daily}
    series = []
    for i in range(14):
        day = today - timedelta(days=13 - i)
        series.append({"day": day, "n": daily_map.get(day, 0)})
    peak = max([x["n"] for x in series] + [1])
    for x in series:
        x["pct"] = round(x["n"] * 100 / peak)

    context = {
        "title": "Analytics",
        "views_today": total(1), "views_7": total(7), "views_30": total(30),
        "top_pages": top_pages, "series": series,
        "cv_downloads": SiteProfile.load().cv_downloads,
        "messages_total": ContactMessage.objects.count(),
        "messages_unread": ContactMessage.objects.filter(is_read=False).count(),
        "quotes_total": QuoteRequest.objects.count(),
        "quotes_new": QuoteRequest.objects.filter(status="new").count(),
        "subscribers": Subscriber.objects.filter(active=True).count(),
        "reviews_pending": Testimonial.objects.filter(approved=False).count(),
        "top_posts": BlogPost.objects.order_by("-views")[:5],
    }
    return render(request, "admin/analytics.html", context)

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, Project, SiteProfile

VALID = {
    "name": "Test User",
    "email": "test@example.com",
    "subject": "Website project",
    "message": "I would like a portfolio website for my business.",
}


class PagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_data", verbosity=0)

    def test_all_pages_render(self):
        for name in ["home", "about", "skills", "projects", "services"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_projects_page_lists_database_projects(self):
        Project.objects.create(title="Brand New Thing", category="TEST", description="d", repo_url="https://github.com/x/y")
        resp = self.client.get(reverse("projects"))
        self.assertContains(resp, "Brand New Thing")
        self.assertContains(resp, "12 PROJECTS")

    def test_unpublished_project_hidden(self):
        Project.objects.create(title="Secret Draft", category="X", description="d", published=False)
        self.assertNotContains(self.client.get(reverse("projects")), "Secret Draft")

    def test_home_shows_profile_details(self):
        resp = self.client.get(reverse("home"))
        self.assertContains(resp, SiteProfile.load().email)
        self.assertContains(resp, 'name="csrfmiddlewaretoken"')
        self.assertContains(resp, 'name="website"')  # honeypot

    def test_cv_download_counts(self):
        resp = self.client.get(reverse("download_cv"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp["Content-Disposition"])
        self.assertEqual(SiteProfile.load().cv_downloads, 1)


@override_settings(CONTACT_RATE_LIMIT=3, TURNSTILE_SECRET_KEY="")
class ContactTests(TestCase):
    def test_valid_message_saved_and_emailed(self):
        resp = self.client.post(reverse("contact"), VALID)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        msg = ContactMessage.objects.get()
        self.assertTrue(msg.email_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ["test@example.com"])

    def test_invalid_email_rejected(self):
        resp = self.client.post(reverse("contact"), {**VALID, "email": "nope"})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(ContactMessage.objects.exists())

    def test_short_message_rejected(self):
        resp = self.client.post(reverse("contact"), {**VALID, "message": "hi"})
        self.assertEqual(resp.status_code, 400)

    def test_honeypot_silently_discards(self):
        resp = self.client.post(reverse("contact"), {**VALID, "website": "http://spam.example"})
        self.assertTrue(resp.json()["ok"])
        self.assertFalse(ContactMessage.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit(self):
        for _ in range(3):
            self.assertEqual(self.client.post(reverse("contact"), VALID).status_code, 200)
        self.assertEqual(self.client.post(reverse("contact"), VALID).status_code, 429)
        self.assertEqual(ContactMessage.objects.count(), 3)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse("contact")).status_code, 405)

    def test_csrf_enforced(self):
        from django.test import Client
        c = Client(enforce_csrf_checks=True)
        self.assertEqual(c.post(reverse("contact"), VALID).status_code, 403)

    @override_settings(TURNSTILE_SECRET_KEY="secret")
    def test_missing_captcha_token_rejected_when_enabled(self):
        resp = self.client.post(reverse("contact"), VALID)
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(ContactMessage.objects.exists())

    def test_email_failure_does_not_lose_message(self):
        from unittest import mock
        with mock.patch("core.views.EmailMessage.send", side_effect=OSError("smtp down")):
            resp = self.client.post(reverse("contact"), VALID)
        self.assertTrue(resp.json()["ok"])
        self.assertFalse(ContactMessage.objects.get().email_sent)


# ====================================================== new features
from datetime import timedelta  # noqa: E402
from unittest import mock  # noqa: E402

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.utils import timezone  # noqa: E402

from .models import BlogPost, PageView, QuoteRequest, Subscriber, Testimonial  # noqa: E402
from .youtube import latest_videos, parse_feed  # noqa: E402

QUOTE = {
    "name": "Client", "email": "client@example.com", "service": "Web Design",
    "budget": "200-500", "deadline": "", "details": "I need a small business website with 5 pages.",
}

FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
 <entry><yt:videoId>abc123</yt:videoId><title>First video</title><published>2026-11-01T10:00:00+00:00</published></entry>
 <entry><yt:videoId>def456</yt:videoId><title>Second video</title><published>2026-10-20T10:00:00+00:00</published></entry>
</feed>"""


@override_settings(CONTACT_RATE_LIMIT=3, TURNSTILE_SECRET_KEY="")
class QuoteTests(TestCase):
    def test_page_renders_with_preselected_service(self):
        call_command("seed_data", verbosity=0)
        resp = self.client.get(reverse("quote") + "?service=Logo%20Design")
        self.assertContains(resp, 'value="Logo Design" selected')

    def test_valid_quote_saved_and_emailed(self):
        resp = self.client.post(reverse("quote_submit"), QUOTE)
        self.assertTrue(resp.json()["ok"])
        q = QuoteRequest.objects.get()
        self.assertEqual(q.status, "new")
        self.assertTrue(q.email_sent)
        self.assertIn("Quote request", mail.outbox[0].subject)

    def test_past_deadline_rejected(self):
        past = (timezone.localdate() - timedelta(days=2)).isoformat()
        self.assertEqual(self.client.post(reverse("quote_submit"), {**QUOTE, "deadline": past}).status_code, 400)

    def test_future_deadline_accepted(self):
        future = (timezone.localdate() + timedelta(days=20)).isoformat()
        self.assertEqual(self.client.post(reverse("quote_submit"), {**QUOTE, "deadline": future}).status_code, 200)
        self.assertEqual(QuoteRequest.objects.get().deadline.isoformat(), future)

    def test_bad_budget_rejected(self):
        self.assertEqual(self.client.post(reverse("quote_submit"), {**QUOTE, "budget": "free"}).status_code, 400)

    def test_honeypot_and_rate_limit(self):
        r = self.client.post(reverse("quote_submit"), {**QUOTE, "website": "x"})
        self.assertTrue(r.json()["ok"])
        self.assertFalse(QuoteRequest.objects.exists())
        for _ in range(3):
            self.client.post(reverse("quote_submit"), QUOTE)
        self.assertEqual(self.client.post(reverse("quote_submit"), QUOTE).status_code, 429)

    @override_settings(TURNSTILE_SECRET_KEY="secret")
    def test_captcha_required_when_enabled(self):
        self.assertEqual(self.client.post(reverse("quote_submit"), QUOTE).status_code, 400)
        self.assertFalse(QuoteRequest.objects.exists())


@override_settings(CONTACT_RATE_LIMIT=5, TURNSTILE_SECRET_KEY="")
class TestimonialTests(TestCase):
    DATA = {"name": "Happy Client", "role": "Shop owner", "rating": "5",
            "text": "Fast, clear and the website looks great."}

    def test_submission_needs_approval(self):
        self.assertTrue(self.client.post(reverse("testimonial_submit"), self.DATA).json()["ok"])
        t = Testimonial.objects.get()
        self.assertFalse(t.approved)
        self.assertNotContains(self.client.get(reverse("home")), "Fast, clear and the website")
        self.assertIn("waiting for approval", mail.outbox[0].subject)
        t.approved = True
        t.save()
        self.assertContains(self.client.get(reverse("home")), "Fast, clear and the website")

    def test_rating_out_of_range_rejected(self):
        self.assertEqual(self.client.post(reverse("testimonial_submit"), {**self.DATA, "rating": "9"}).status_code, 400)

    def test_html_is_escaped(self):
        Testimonial.objects.create(name="<b>x</b>", text="<script>alert(1)</script> hello there", rating=5, approved=True)
        html = self.client.get(reverse("home")).content.decode()
        self.assertNotIn("<script>alert(1)</script>", html)


@override_settings(CONTACT_RATE_LIMIT=5)
class NewsletterTests(TestCase):
    def test_subscribe_and_dedupe(self):
        for _ in range(2):
            self.assertTrue(self.client.post(reverse("subscribe"), {"email": "Fan@Example.com"}).json()["ok"])
        self.assertEqual(Subscriber.objects.count(), 1)
        self.assertEqual(Subscriber.objects.get().email, "fan@example.com")

    def test_invalid_email(self):
        self.assertEqual(self.client.post(reverse("subscribe"), {"email": "nope"}).status_code, 400)


class BlogTests(TestCase):
    def setUp(self):
        self.post = BlogPost.objects.create(title="Learn Django", slug="learn-django",
                                            excerpt="A short intro.", body="Line one.\n\nLine two <b>bold</b>")
        BlogPost.objects.create(title="Draft", slug="draft", excerpt="x", body="x", published=False)

    def test_list_hides_drafts(self):
        resp = self.client.get(reverse("blog"))
        self.assertContains(resp, "Learn Django")
        self.assertNotContains(resp, "Draft")

    def test_detail_counts_views_and_escapes(self):
        resp = self.client.get(reverse("blog_detail", args=["learn-django"]))
        self.assertContains(resp, "&lt;b&gt;bold&lt;/b&gt;")
        self.assertContains(resp, 'name="description" content="A short intro."')
        self.client.get(reverse("blog_detail", args=["learn-django"]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 2)

    def test_unpublished_is_404(self):
        self.assertEqual(self.client.get(reverse("blog_detail", args=["draft"])).status_code, 404)

    def test_home_shows_latest_posts(self):
        self.assertContains(self.client.get(reverse("home")), "Learn Django")


class AnalyticsTests(TestCase):
    def test_page_views_counted_per_day(self):
        self.client.get(reverse("about"))
        self.client.get(reverse("about"))
        pv = PageView.objects.get(path="/about/")
        self.assertEqual(pv.count, 2)

    def test_excludes_bots_admin_and_posts(self):
        self.client.get(reverse("about"), HTTP_USER_AGENT="Googlebot/2.1")
        self.client.get("/admin/login/")
        self.client.post(reverse("subscribe"), {"email": "a@b.com"})
        self.assertFalse(PageView.objects.exists())

    def test_staff_views_not_counted(self):
        User = get_user_model()
        User.objects.create_superuser("boss", "b@b.com", "pw12345!")
        self.client.login(username="boss", password="pw12345!")
        self.client.get(reverse("about"))
        self.assertFalse(PageView.objects.exists())

    def test_dashboard_requires_staff(self):
        resp = self.client.get(reverse("analytics"))
        self.assertEqual(resp.status_code, 302)
        User = get_user_model()
        User.objects.create_superuser("boss", "b@b.com", "pw12345!")
        self.client.login(username="boss", password="pw12345!")
        PageView.objects.create(path="/about/", day=timezone.localdate(), count=7)
        resp = self.client.get(reverse("analytics"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "/about/")

    def test_admin_index_has_analytics_link(self):
        User = get_user_model()
        User.objects.create_superuser("boss", "b@b.com", "pw12345!")
        self.client.login(username="boss", password="pw12345!")
        self.assertContains(self.client.get("/admin/"), reverse("analytics"))


class YouTubeTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_parse_feed(self):
        v = parse_feed(FEED, limit=3)
        self.assertEqual([x["id"] for x in v], ["abc123", "def456"])
        self.assertEqual(v[0]["url"], "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(v[0]["published"], "2026-11-01")

    def test_invalid_channel_id_skips_network(self):
        with mock.patch("core.youtube.urllib.request.urlopen") as m:
            self.assertEqual(latest_videos(""), [])
            self.assertEqual(latest_videos("not-a-channel"), [])
            m.assert_not_called()

    def test_network_failure_returns_empty_and_does_not_raise(self):
        with mock.patch("core.youtube.urllib.request.urlopen", side_effect=OSError("offline")):
            self.assertEqual(latest_videos("UCabc"), [])

    def test_home_shows_videos_when_channel_set(self):
        profile = SiteProfile.load()
        profile.youtube_channel_id = "UCtest123"
        profile.save()
        resp_obj = mock.MagicMock()
        resp_obj.__enter__.return_value.read.return_value = FEED
        with mock.patch("core.youtube.urllib.request.urlopen", return_value=resp_obj):
            html = self.client.get(reverse("home")).content.decode()
        self.assertIn("First video", html)
        self.assertIn("i.ytimg.com/vi/abc123", html)

    def test_home_without_channel_has_no_videos_section(self):
        self.assertNotContains(self.client.get(reverse("home")), 'id="videos"')

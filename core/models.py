from django.db import models
from django.templatetags.static import static


class SiteProfile(models.Model):
    """Single row holding your personal details. Edit it in the admin panel."""

    name = models.CharField(max_length=100, default="Rajib Sunar")
    email = models.EmailField(default="rajibsunar888@gmail.com")
    phone = models.CharField(max_length=30, default="+977 9701728571")
    location = models.CharField(max_length=100, default="Pokhara, Nepal")
    available_for_work = models.BooleanField(default=True)

    github_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_channel_id = models.CharField(
        max_length=40, blank=True,
        help_text="Starts with UC... Shows your latest videos on the home page. "
                  "Find it in YouTube Studio > Settings > Channel > Advanced settings.",
    )

    cv_file = models.FileField(
        upload_to="cv/", blank=True,
        help_text="Upload a new CV here. If empty, the bundled static/files/rajibcv.pdf is used.",
    )
    cv_downloads = models.PositiveIntegerField(default=0, editable=False)

    stat_projects = models.CharField("Projects shipped", max_length=10, default="7+")
    stat_clients = models.CharField("Happy clients", max_length=10, default="3+")
    stat_disciplines = models.CharField("Disciplines", max_length=10, default="2")

    class Meta:
        verbose_name = "Site profile"
        verbose_name_plural = "Site profile"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.pk = 1  # keep it a singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def phone_href(self):
        return "+" + "".join(ch for ch in self.phone if ch.isdigit())


class Skill(models.Model):
    """Skill bar shown on the home page."""

    name = models.CharField(max_length=60)
    level = models.PositiveSmallIntegerField(default=80, help_text="0-100")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.name} ({self.level}%)"


class SkillArea(models.Model):
    """Card on the dedicated Skills page."""

    title = models.CharField(max_length=80)
    description = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Project(models.Model):
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=40, help_text="Short label, e.g. GAME, FINANCE, AI")
    description = models.TextField()
    tech_tags = models.CharField(
        max_length=200, blank=True, help_text="Comma separated, e.g. Python, Django, HTML"
    )
    repo_url = models.URLField("GitHub repository", blank=True)
    live_url = models.URLField("Live demo", blank=True)
    featured = models.BooleanField(default=False, help_text="Show on the home page (keep to about 3)")
    published = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def tags(self):
        return [t.strip() for t in self.tech_tags.split(",") if t.strip()]


class Service(models.Model):
    ACCENTS = [
        ("web", "Blue"), ("software", "Green"), ("graphic", "Orange"),
        ("logo", "Purple"), ("content", "Pink"), ("video", "Sky blue"),
    ]

    title = models.CharField(max_length=80)
    tag = models.CharField(max_length=20, blank=True, help_text="Optional small label, e.g. WEB")
    description = models.TextField()
    features = models.TextField(blank=True, help_text="One bullet per line")
    accent = models.CharField(max_length=10, choices=ACCENTS, default="web")
    icon_svg = models.TextField(
        blank=True, help_text="Inner SVG shapes (paths) for the card icon. Optional."
    )
    show_on_home = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    @property
    def feature_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]


class GalleryImage(models.Model):
    title = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="gallery/", blank=True)
    static_path = models.CharField(
        max_length=200, blank=True,
        help_text="Fallback path inside static/, e.g. img/12.png (used when no image is uploaded)",
    )
    order = models.PositiveSmallIntegerField(default=0)
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title or f"Image {self.pk}"

    @property
    def url(self):
        if self.image:
            return self.image.url
        if self.static_path:
            return static(self.static_path)
        return ""


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name}: {self.subject}"


class QuoteRequest(models.Model):
    BUDGETS = [
        ("under-200", "Under $200"),
        ("200-500", "$200 - $500"),
        ("500-1000", "$500 - $1,000"),
        ("1000-plus", "$1,000+"),
        ("not-sure", "Not sure yet"),
    ]
    STATUSES = [("new", "New"), ("replied", "Replied"), ("won", "Won"), ("closed", "Closed")]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    service = models.CharField(max_length=80, blank=True)
    budget = models.CharField(max_length=20, choices=BUDGETS, default="not-sure")
    deadline = models.DateField(null=True, blank=True)
    details = models.TextField()
    status = models.CharField(max_length=10, choices=STATUSES, default="new")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False, editable=False)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} - {self.service or 'General'}"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField("Role / company", max_length=100, blank=True)
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    approved = models.BooleanField(default=False, help_text="Only approved reviews appear on the site")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.rating}/5)"

    @property
    def stars(self):
        return "\u2605" * self.rating + "\u2606" * (5 - self.rating)


class BlogPost(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=170, unique=True)
    excerpt = models.CharField(max_length=300, help_text="Short summary, also used for search engines")
    body = models.TextField(help_text="Plain text. A blank line starts a new paragraph.")
    cover = models.ImageField(upload_to="blog/", blank=True)
    video_url = models.URLField("YouTube link", blank=True, help_text="Optional related video")
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("blog_detail", args=[self.slug])

    @property
    def read_minutes(self):
        return max(1, round(len(self.body.split()) / 200))


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.email


class PageView(models.Model):
    """Daily view counter per page (no personal data stored)."""

    path = models.CharField(max_length=200)
    day = models.DateField()
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("path", "day")
        ordering = ["-day", "-count"]

    def __str__(self):
        return f"{self.path} {self.day}: {self.count}"

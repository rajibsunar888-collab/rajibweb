import csv

from django.contrib import admin
from django.db.models import Sum
from django.http import HttpResponse

from .models import (
    BlogPost, ContactMessage, GalleryImage, PageView, Project, QuoteRequest, Service,
    SiteProfile, Skill, SkillArea, Subscriber, Testimonial,
)

admin.site.site_header = "Rajib Sunar - Portfolio admin"
admin.site.site_title = "Portfolio admin"
admin.site.index_title = "Manage your portfolio"


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    readonly_fields = ("cv_downloads",)

    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "order")
    list_editable = ("level", "order")


@admin.register(SkillArea)
class SkillAreaAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "featured", "published", "order")
    list_editable = ("featured", "published", "order")
    list_filter = ("category", "featured", "published")
    search_fields = ("title", "description", "tech_tags")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "accent", "show_on_home", "published", "order")
    list_editable = ("show_on_home", "published", "order")


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("__str__", "published", "order")
    list_editable = ("published", "order")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created", "is_read", "email_sent")
    list_filter = ("is_read", "email_sent", "created")
    list_editable = ("is_read",)
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "ip_address", "created", "email_sent")

    def has_add_permission(self, request):
        return False


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "service", "budget", "deadline", "status", "created")
    list_filter = ("status", "budget", "service", "created")
    list_editable = ("status",)
    search_fields = ("name", "email", "details")
    readonly_fields = ("name", "email", "service", "budget", "deadline", "details",
                       "ip_address", "created", "email_sent")

    def has_add_permission(self, request):
        return False


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "rating", "approved", "created")
    list_filter = ("approved", "rating")
    list_editable = ("approved",)
    search_fields = ("name", "text")
    actions = ["approve_selected"]

    @admin.action(description="Approve selected reviews")
    def approve_selected(self, request, queryset):
        queryset.update(approved=True)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "published", "views", "created")
    list_editable = ("published",)
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")
    readonly_fields = ("views",)


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "active", "created")
    list_filter = ("active",)
    list_editable = ("active",)
    search_fields = ("email",)
    actions = ["export_csv"]

    @admin.action(description="Export selected subscribers as CSV")
    def export_csv(self, request, queryset):
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="subscribers.csv"'
        w = csv.writer(resp)
        w.writerow(["email", "active", "subscribed"])
        for s in queryset:
            w.writerow([s.email, s.active, s.created.isoformat()])
        return resp


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ("path", "day", "count")
    list_filter = ("day",)
    search_fields = ("path",)
    date_hierarchy = "day"

    def has_add_permission(self, request):
        return False

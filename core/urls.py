from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("skills/", views.skills, name="skills"),
    path("projects/", views.projects, name="projects"),
    path("services/", views.services, name="services"),
    path("contact/", views.contact, name="contact"),
    path("cv/", views.download_cv, name="download_cv"),
    path("quote/", views.quote_page, name="quote"),
    path("quote/send/", views.quote_submit, name="quote_submit"),
    path("testimonials/send/", views.testimonial_submit, name="testimonial_submit"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("blog/", views.blog_list, name="blog"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
    path("analytics/", views.analytics, name="analytics"),
]

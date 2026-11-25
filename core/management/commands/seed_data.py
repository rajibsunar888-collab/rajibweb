"""Fill the database with the content that was hard-coded in the original HTML pages.

Run once:  python manage.py seed_data
Safe to re-run: it only seeds tables that are still empty.
"""
from django.core.management.base import BaseCommand

from core.models import GalleryImage, Project, Service, SiteProfile, Skill, SkillArea

GH = "https://github.com/rajibsunar888-collab/"

SKILLS = [
    ("HTML", 95), ("CSS", 92), ("Python Django", 88), ("React", 80),
    ("Figma", 85), ("Photography", 90), ("Capcut", 78), ("GitHub", 83),
]

SKILL_AREAS = [
    ("Graphic Designer", "Creative in making designs that attract users and speak visually. Expert in Photoshop and Illustrator."),
    ("Photography", "Passionate about capturing moments that matter. Skilled in editing and composition."),
    ("Web Designing", "Building interactive and responsive websites with modern design and great UX."),
    ("Content Creation", "Expert in making creative video and blog content that engages audience effectively."),
]

# title, category, description, tags, repo, featured
PROJECTS = [
    ("Life Manager", "APPLICATION",
     "A productivity-oriented application designed to organize everyday activities and help users manage different aspects of daily life.",
     "APP, PRODUCTIVITY", "life-manager", False),
    ("Project", "DEVELOPMENT",
     "A development project maintained in our GitHub collection for experimentation, learning and software development.",
     "SOFTWARE, DEV", "project", False),
    ("Personal Expense Tracker", "FINANCE",
     "A financial tracking application focused on organizing personal expenses and monitoring spending information.",
     "Python, FINANCE, TRACKER", "personal-expense-tracker", True),
    ("Geolocation Tracker", "TRACKING",
     "A real-time geo-location tracker that helps users view, track, and manage locations accurately using GPS technology.",
     "GEOLOCATION, TRACKING", "Geolocationtracker", True),
    ("Memory Puzzle Game", "GAME",
     "An interactive memory puzzle designed around gameplay, user interaction and problem solving.",
     "GAME, PUZZLE", "memory-puzzle-game", False),
    ("Hangmn", "GAME",
     "A classic word-based guessing game developed as an interactive programming project.",
     "GAME, WORD", "hangmn", False),
    ("Basic Chatbot", "AI",
     "A conversational project exploring basic chatbot interaction and artificial intelligence concepts.",
     "AI, CHATBOT", "basic-chatbot", False),
    ("Hangam", "GAME",
     "An additional interactive game project included in the team's development repository.",
     "GAME, INTERACTIVE", "hangam", False),
    ("Stock Portfolio Tracker", "FINANCE",
     "A project focused on tracking and organizing stock portfolio information.",
     "Python, STOCK, PORTFOLIO", "stockportfoliotracker1", True),
    ("Banking", "BANKING",
     "A banking application project focused on financial operations and digital banking concepts.",
     "BANKING, FINANCE", "banking", False),
    ("Banking 1", "BANKING",
     "An additional banking project maintained in the development repository collection.",
     "BANKING, APPLICATION", "banking1", False),
]

SVG = {
    "web": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3c2.5 2.5 3.8 5.8 3.8 9S14.5 18.5 12 21c-2.5-2.5-3.8-5.8-3.8-9S9.5 5.5 12 3Z"/>',
    "software": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m8 10-3 2 3 2"/><path d="m16 10 3 2-3 2"/><path d="m14 8-4 8"/>',
    "graphic": '<path d="M4 20 16 8"/><path d="M14 6 18 2l4 4-4 4"/><path d="M4 4h6"/><path d="M4 8h4"/><path d="M4 12h5"/>',
    "logo": '<path d="M4 20c6-1 11-5 14-12"/><path d="M14 4c2-2 5-1 6 1 1 2 0 4-2 5"/><path d="M5 19c-1-3 0-6 3-8"/>',
    "content": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="m10 9 5 3-5 3V9Z"/>',
    "video": '<rect x="3" y="5" width="13" height="14" rx="2"/><path d="m16 10 5-3v10l-5-3"/>',
    "camera": '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>',
}

# title, tag, description, features, accent, icon, home, order
SERVICES = [
    ("Web Design", "[ WEB ]", "Fast, responsive and modern websites designed around your brand and goals.",
     "Responsive website\nModern UI design\nSEO friendly\nE-commerce website", "web", True),
    ("Software Development", "", "Custom applications and software built around your exact requirements.",
     "Custom software\nWeb applications\nDesktop applications\nDatabase solutions", "software", True),
    ("Graphic Design", "", "Creative visual designs that help your business communicate clearly.",
     "Banner & poster\nSocial media design\nBrochure & pamphlet\nCreative designs", "graphic", False),
    ("Logo Design", "", "Memorable visual identities designed to make your brand recognizable.",
     "Business logo\nBrand identity\nMinimal modern logo\nUnlimited revision", "logo", False),
    ("Content Creation", "", "Creative content for social platforms, brands and digital campaigns.",
     "YouTube content\nSocial media posts\nCreative ideas\nEngaging content", "content", True),
    ("Video Editing", "", "Professional video editing for YouTube, social media and personal projects.",
     "Video cutting\nTransitions & effects\nYouTube video\nProfessional editing", "video", False),
    ("Photography", "", "Portrait, product, and event photography with a clean, editorial edit style.",
     "Portrait photography\nProduct photography\nEvent coverage\nEditorial photo editing", "camera", True),
]

GALLERY = ["img/12.png", "img/13.png", "img/14.png", "img/16.png"]


class Command(BaseCommand):
    help = "Seed the database with the portfolio content from the original static site."

    def handle(self, *args, **options):
        profile = SiteProfile.load()
        if not profile.github_url:
            profile.github_url = "https://github.com/rajibsunar888-collab"
            profile.instagram_url = "https://www.instagram.com/sunar.444"
            profile.youtube_url = "https://www.youtube.com/@Rajibsunar-fv8it"
            profile.facebook_url = "https://www.facebook.com/share/1BwEYseoHi/"
            profile.linkedin_url = "https://www.linkedin.com/in/rajib-s-4b482530b"
            profile.save()

        if not Skill.objects.exists():
            for i, (name, level) in enumerate(SKILLS):
                Skill.objects.create(name=name, level=level, order=i)
        if not SkillArea.objects.exists():
            for i, (t, d) in enumerate(SKILL_AREAS):
                SkillArea.objects.create(title=t, description=d, order=i)
        if not Project.objects.exists():
            for i, (t, c, d, tags, repo, feat) in enumerate(PROJECTS):
                Project.objects.create(title=t, category=c, description=d, tech_tags=tags,
                                       repo_url=GH + repo, featured=feat, order=i)
        if not Service.objects.exists():
            for i, (t, tag, d, f, accent, home) in enumerate(SERVICES):
                Service.objects.create(title=t, tag=tag, description=d, features=f, accent=accent,
                                       icon_svg=SVG[accent if accent in SVG else "web"],
                                       show_on_home=home, order=i)
        if not GalleryImage.objects.exists():
            for i, path in enumerate(GALLERY):
                GalleryImage.objects.create(title=f"Gallery photo {i + 1}", static_path=path, order=i)

        self.stdout.write(self.style.SUCCESS("Seed data ready."))

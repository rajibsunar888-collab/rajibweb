"""Latest-videos feed from a public YouTube channel RSS (no API key needed)."""
import logging
import urllib.request
import xml.etree.ElementTree as ET

from django.core.cache import cache

logger = logging.getLogger(__name__)

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}
CACHE_SECONDS = 60 * 60


def parse_feed(xml_bytes, limit=3):
    root = ET.fromstring(xml_bytes)
    videos = []
    for entry in root.findall("a:entry", NS)[:limit]:
        vid = entry.findtext("yt:videoId", default="", namespaces=NS)
        title = entry.findtext("a:title", default="", namespaces=NS)
        if not vid:
            continue
        videos.append({
            "id": vid,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "published": (entry.findtext("a:published", default="", namespaces=NS) or "")[:10],
        })
    return videos


def latest_videos(channel_id, limit=3):
    """Return a list of video dicts, or [] when unavailable. Never raises."""
    channel_id = (channel_id or "").strip()
    if not channel_id.startswith("UC"):
        return []
    key = f"yt-feed:{channel_id}:{limit}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            videos = parse_feed(resp.read(), limit)
    except Exception:
        logger.warning("Could not load YouTube feed for %s", channel_id, exc_info=True)
        videos = []
    # cache failures briefly so a slow YouTube doesn't slow every page load
    cache.set(key, videos, CACHE_SECONDS if videos else 300)
    return videos

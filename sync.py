import json
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlunsplit, urljoin
from html.parser import HTMLParser

RSS_URL = "https://the-french-tangerine-blog.squarespace.com/blog?format=rss"
BLOG_DOMAIN = "www.thefrenchtangerine.com"
POST_LIMIT = 6

HEADERS = {"User-Agent": "Mozilla/5.0"}

namespaces = {
    "media": "http://search.yahoo.com/mrss/"
}


class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = {}

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            attrs = dict(attrs)
            key = attrs.get("property") or attrs.get("name")
            if key in ("og:image", "twitter:image"):
                self.images[key] = attrs.get("content", "")


def get_featured_image(url):
    try:
        request = urllib.request.Request(url, headers=HEADERS)

        with urllib.request.urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")

        parser = ImageParser()
        parser.feed(html)

        image = (
            parser.images.get("og:image")
            or parser.images.get("twitter:image")
            or ""
        )

        return urljoin(url, image) if image else ""

    except Exception as error:
        print(f"Image lookup failed: {error}")
        return ""


request = urllib.request.Request(RSS_URL, headers=HEADERS)

with urllib.request.urlopen(request, timeout=30) as response:
    root = ET.fromstring(response.read())

posts = []

for item in root.findall("./channel/item")[:POST_LIMIT]:
    title = item.findtext("title", "")
    link = item.findtext("link", "")
    image = ""

    # First, check the RSS feed for an image.
    for tag in ["media:content", "media:thumbnail"]:
        for element in item.findall(".//" + tag, namespaces):
            if element.get("url"):
                image = element.get("url")
                break
        if image:
            break

    if not image:
        enclosure = item.find("enclosure")
        if enclosure is not None:
            if enclosure.get("type", "").startswith("image/"):
                image = enclosure.get("url", "")

    # If no RSS image exists, visit the blog post.
    if not image and link:
        image = get_featured_image(link)

    # Use the branded blog domain for Shopify links.
    if link:
        parts = urlsplit(link)
        link = urlunsplit((
            "https",
            BLOG_DOMAIN,
            parts.path,
            parts.query,
            parts.fragment
        ))

    posts.append({
        "title": title,
        "url": link,
        "image": image,
        "date": item.findtext("pubDate", "")
    })

if not posts:
    raise RuntimeError("No blog posts found in RSS feed.")

with open("posts.json", "w", encoding="utf-8") as file:
    json.dump(posts, file, indent=2, ensure_ascii=False)

print(f"Successfully synced {len(posts)} blog posts.")

for post in posts:
    print(post["title"])
    print(f"Image: {post['image'] or 'NOT FOUND'}")

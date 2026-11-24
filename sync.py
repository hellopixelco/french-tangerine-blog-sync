import json
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlunsplit

RSS_URL = "https://the-french-tangerine-blog.squarespace.com/blog?format=rss"
BLOG_DOMAIN = "www.thefrenchtangerine.com"
POST_LIMIT = 6

namespaces = {
    "media": "http://search.yahoo.com/mrss/"
}

request = urllib.request.Request(
    RSS_URL,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    root = ET.fromstring(response.read())

posts = []

for item in root.findall("./channel/item")[:POST_LIMIT]:
    title = item.findtext("title", "")
    link = item.findtext("link", "")
    image = ""

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
    if not post["image"]:
        print("Warning: Featured image not found.")

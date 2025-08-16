# main.py
from flask import Flask, request, Response, abort
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import html, time

app = Flask(__name__)
DEFAULT_UA = "rssify/1.1"
CACHE_TTL = 300
_cache = {}

def httpdate(ts=None):
    ts = ts if ts else time.gmtime()
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", ts)

def make_rss(title, link, items):
    now = httpdate()
    parts = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<rss version="2.0"><channel>',
        f'<title>{html.escape(title)}</title>',
        f'<link>{html.escape(link)}</link>',
        f'<description>Generated feed for {html.escape(link)}</description>',
        f'<lastBuildDate>{now}</lastBuildDate>',
    ]
    for it in items:
        parts += ['<item>',
                  f'<title>{html.escape(it.get("title","(no title)"))}</title>']
        if it.get("link"):
            parts += [
                f'<link>{html.escape(it["link"])}</link>',
                f'<guid isPermaLink="true">{html.escape(it["link"])}</guid>'
            ]
        if it.get("description"):
            parts.append(f'<description><![CDATA[{it["description"]}]]></description>')
        parts.append('</item>')
    parts.append('</channel></rss>')
    return "\n".join(parts)

def fetch(url, ua=None):
    headers = {"User-Agent": ua or DEFAULT_UA}
    r = requests.get(url, timeout=20, headers=headers)
    r.raise_for_status()
    return r.text

def extract_items(html_text, base_url, selector, limit=30):
    soup = BeautifulSoup(html_text, "html.parser")
    nodes = soup.select(selector)
    items = []
    for n in nodes[:limit]:
        it = {}
        a = n.select_one("a[href]")
        it["title"] = a.get_text(strip=True) if a else n.get_text(strip=True)
        it["link"] = urljoin(base_url, a["href"]) if a else None
        it["description"] = str(n)
        items.append(it)
    return items

@app.route("/feed")
def feed():
    target = request.args.get("url")
    selector = request.args.get("selector")
    limit = min(max(1, request.args.get("limit", default=30, type=int)), 100)
    if not target or not selector:
        return abort(400, "required params: url and selector")
    cache_key = f"{target}|{selector}|{limit}"
    now = time.time()
    if cache_key in _cache and _cache[cache_key][0] > now:
        return Response(_cache[cache_key][1], mimetype="application/rss+xml; charset=utf-8")
    try:
        html_text = fetch(target)
        items = extract_items(html_text, target, selector, limit)
        rss = make_rss(f"Feed for {target}", target, items)
        _cache[cache_key] = (now + CACHE_TTL, rss)
        return Response(rss, mimetype="application/rss+xml; charset=utf-8")
    except Exception as e:
        return abort(500, f"Error: {e}")

@app.route("/health")
def health():
    return {"ok": True, "ts": httpdate()}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 5000)))

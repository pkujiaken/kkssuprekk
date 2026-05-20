"""Fetch articles from RSS sources over the last 24h."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

SOURCES = {
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Hacker News": "https://hnrss.org/frontpage",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "NYT Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
}

MAX_PER_SOURCE = 15
LOOKBACK_HOURS = 24


def fetch_all():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    articles = []
    for name, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[warn] {name} failed: {e}", file=sys.stderr)
            continue
        count = 0
        for entry in feed.entries[:MAX_PER_SOURCE * 2]:
            published_struct = entry.get("published_parsed") or entry.get("updated_parsed")
            if published_struct:
                pub_dt = datetime(*published_struct[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue
            summary = entry.get("summary", "") or entry.get("description", "")
            articles.append({
                "source": name,
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "summary": summary[:600],
                "published": entry.get("published", "") or entry.get("updated", ""),
            })
            count += 1
            if count >= MAX_PER_SOURCE:
                break
        print(f"[ok] {name}: {count} articles")
    return articles


if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    articles = fetch_all()
    with open("data/raw.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"Total: {len(articles)} articles")

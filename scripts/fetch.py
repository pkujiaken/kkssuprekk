"""Fetch articles from RSS sources over the last 24h."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser

SOURCES = {
    # === 一手大佬观点 ===
    "Sam Altman Blog": "https://blog.samaltman.com/posts.atom",
    "Stratechery (Ben Thompson)": "https://stratechery.com/feed/",
    "Marginal Revolution (Tyler Cowen)": "https://marginalrevolution.com/feed",
    "Aswath Damodaran": "https://aswathdamodaran.blogspot.com/feeds/posts/default",
    "A Wealth of Common Sense (Ben Carlson)": "https://awealthofcommonsense.com/feed/",
    "a16z": "https://a16z.com/feed/",
    "Calculated Risk (Bill McBride)": "https://www.calculatedriskblog.com/feeds/posts/default",

    # === 美联储 / 监管一手 ===
    "Federal Reserve Press": "https://www.federalreserve.gov/feeds/press_all.xml",
    "SEC Press": "https://www.sec.gov/news/pressreleases.rss",

    # === 投资 / 金融市场新闻 ===
    "NYT Business": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    "NYT Economy": "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
    "NYT DealBook": "https://rss.nytimes.com/services/xml/rss/nyt/DealBook.xml",
    "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "MarketWatch Top Stories": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "MarketWatch Real-Time": "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
    "CNBC Business": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
    "CNBC Finance": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",

    # === 科技 / AI ===
    "Hacker News Top": "https://hnrss.org/frontpage?points=200",  # 高分门槛，过滤掉垃圾
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "MIT Tech Review": "https://www.technologyreview.com/feed/",

    # === 中国 / A股 ===
    "Caixin Global": "https://www.caixinglobal.com/rss/",
    "SCMP Business": "https://www.scmp.com/rss/92/feed",
}

MAX_PER_SOURCE = 10
LOOKBACK_HOURS = 36  # 拉宽到 36h，因为有些博客不是每天更新


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
                "summary": summary[:800],
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

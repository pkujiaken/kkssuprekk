"""Render processed news data into a mobile-friendly HTML page."""
import json
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

BJT = timezone(timedelta(hours=8))

SECTIONS = [
    ("macro", "💰 宏观与金融"),
    ("tech", "🚀 科技 & AI"),
    ("us_stocks", "📈 美股"),
    ("a_stocks", "🇨🇳 A 股 / 中国"),
    ("business", "🏢 商业"),
    ("overlooked", "🌐 你今天没看的角落"),
]


def render_item(item):
    title = escape(item.get("title", ""))
    summary = escape(item.get("summary", ""))
    src_parts = []
    for s in item.get("sources", []):
        name = escape(s.get("name", "源"))
        url = escape(s.get("url", "#"))
        src_parts.append(f'<a href="{url}" target="_blank" rel="noopener">{name}</a>')
    sources_html = " · ".join(src_parts) if src_parts else ""
    return f"""<div class="item">
  <div class="item-title">{title}</div>
  <div class="item-summary">{summary}</div>
  <div class="sources">{sources_html}</div>
</div>"""


def render_html(data):
    now = datetime.now(BJT)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]

    top5_html = "".join(render_item(it) for it in data.get("top5", []))

    sections_html = ""
    for key, title in SECTIONS:
        items = data.get(key, []) or []
        if not items:
            continue
        cls = "overlooked" if key == "overlooked" else ""
        sections_html += f'<h2>{title}</h2>\n<div class="section {cls}">\n'
        sections_html += "".join(render_item(it) for it in items)
        sections_html += "</div>\n"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="每日简报">
<meta name="theme-color" content="#fafafa">
<title>每日简报 · {date_str}</title>
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='22' fill='%231a1a1a'/%3E%3Ctext x='50' y='66' font-size='52' text-anchor='middle' fill='white' font-family='-apple-system'%3E📰%3C/text%3E%3C/svg%3E">
<style>
  * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", sans-serif;
    background: #fafafa;
    color: #1a1a1a;
    line-height: 1.6;
    padding: env(safe-area-inset-top) 16px env(safe-area-inset-bottom) 16px;
    max-width: 720px;
    margin: 0 auto;
  }}
  header {{
    padding: 24px 0 8px;
  }}
  h1 {{
    font-size: 28px;
    font-weight: 700;
    margin: 0 0 4px;
    letter-spacing: -0.5px;
  }}
  .meta {{
    color: #8a8a8a;
    font-size: 13px;
    margin-bottom: 8px;
  }}
  .tagline {{
    color: #c0c0c0;
    font-size: 12px;
    margin-bottom: 20px;
  }}
  h2 {{
    font-size: 17px;
    font-weight: 600;
    margin: 28px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e8e8e8;
  }}
  .item {{
    background: #fff;
    padding: 14px 16px;
    margin: 8px 0;
    border-radius: 10px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  }}
  .item-title {{
    font-weight: 600;
    font-size: 15px;
    margin-bottom: 6px;
    color: #1a1a1a;
  }}
  .item-summary {{
    font-size: 14px;
    color: #444;
  }}
  .sources {{
    font-size: 12px;
    color: #9a9a9a;
    margin-top: 8px;
  }}
  .sources a {{
    color: #2c7be5;
    text-decoration: none;
    margin-right: 4px;
  }}
  .top5 .item {{ border-left: 3px solid #d9534f; }}
  .overlooked .item {{ border-left: 3px solid #5cb85c; }}
  footer {{
    margin: 40px 0 24px;
    text-align: center;
    color: #b0b0b0;
    font-size: 12px;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #000; color: #f0f0f0; }}
    h2 {{ border-bottom-color: #2a2a2a; }}
    .item {{ background: #161616; box-shadow: none; }}
    .item-title {{ color: #f0f0f0; }}
    .item-summary {{ color: #c0c0c0; }}
    .sources {{ color: #6a6a6a; }}
    .sources a {{ color: #5ba3ff; }}
    .meta, .tagline {{ color: #6a6a6a; }}
  }}
</style>
</head>
<body>
<header>
  <h1>每日简报</h1>
  <div class="meta">{date_str} {weekday} · 更新于 {time_str} (北京)</div>
  <div class="tagline">客观 · 全面 · 反算法</div>
</header>

<h2>🌍 今日 5 件大事</h2>
<div class="section top5">
{top5_html}
</div>

{sections_html}

<footer>不依赖推荐算法 · 强制呈现多元视角</footer>
</body>
</html>
"""


if __name__ == "__main__":
    with open("data/processed.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    html = render_html(data)
    Path("docs").mkdir(exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote docs/index.html ({len(html)} bytes)")

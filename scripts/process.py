"""Use Gemini to translate, cluster, and categorize articles into a Chinese brief."""
import json
import os
import sys
from pathlib import Path

import google.generativeai as genai

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
    sys.exit(1)

genai.configure(api_key=API_KEY)

MODEL = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={"response_mime_type": "application/json"},
)

PROMPT_TEMPLATE = """你是一个客观、全面、反信息茧房的全球新闻编辑。

下面是过去 24 小时来自多个英文媒体的新闻原始数据。请你完成以下工作：

1. **翻译**：所有标题和摘要翻译为中文。
2. **聚类**：识别同一事件的不同报道，合并为一条，把多个 source 都列出来。
3. **分类**：把每条新闻分到下面 6 个类别之一：
   - top5（今日全球最重要的 5 件大事）
   - macro（宏观经济、央行、利率、汇率、地缘政治）
   - tech（科技、AI、互联网）
   - us_stocks（美股、美国公司财报、商业）
   - a_stocks（A 股、中国市场、中国公司）—— 如果没有就空数组
   - business（商业、消费、能源、医疗等其他领域）
   - overlooked（重要但非热门的"被忽略角落"，2-3 条，比如非洲、拉美、能源、气候、新兴市场）
4. **摘要风格**：每条 80-150 字，客观陈述事实，不要煽动性词汇。
5. **排序**：每个类别内部按重要性排序。

⚠️ 严格要求：
- 必须输出合法 JSON
- top5 必须恰好 5 条
- 每个其他类别 3-6 条（除非原始数据不够）
- 不要编造原文没有的信息

输出格式：
{{
  "top5": [
    {{
      "title": "中文标题",
      "summary": "中文摘要 80-150 字",
      "sources": [{{"name": "BBC", "url": "https://..."}}, ...]
    }}
  ],
  "macro": [...],
  "tech": [...],
  "us_stocks": [...],
  "a_stocks": [...],
  "business": [...],
  "overlooked": [...]
}}

原始新闻数据：
{articles_json}
"""


def process(articles):
    if not articles:
        return {"top5": [], "macro": [], "tech": [], "us_stocks": [],
                "a_stocks": [], "business": [], "overlooked": []}

    prompt = PROMPT_TEMPLATE.format(
        articles_json=json.dumps(articles, ensure_ascii=False)
    )
    response = MODEL.generate_content(prompt)
    text = response.text.strip()
    # Defensive: strip code fences if model added them despite JSON mime type
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    return json.loads(text)


if __name__ == "__main__":
    with open("data/raw.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    print(f"Processing {len(articles)} articles with Gemini...")
    result = process(articles)
    Path("data").mkdir(exist_ok=True)
    with open("data/processed.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in result.values() if isinstance(v, list))
    print(f"Done. {total} items across {len(result)} sections.")

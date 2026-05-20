"""Use Gemini to translate, cluster, and categorize articles into a Chinese brief."""
import json
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY not set", file=sys.stderr)
    sys.exit(1)

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash"
MAX_ARTICLES = 60

PROMPT_TEMPLATE = """你是一个为高净值投资者服务的全球新闻编辑。读者是关注**投资、宏观经济、科技商业、美股、A股**的专业人士，每天只有 5-10 分钟看简报。

下面是过去 36 小时来自多个高质量英文媒体的原始文章。请按以下要求处理：

## ⚠️ 严格过滤（直接扔掉）
- 体育、娱乐、明星八卦、犯罪、灾难、地方新闻
- 与投资/宏观/科技商业无关的人物花边
- 营销文章、产品评测（非战略层面）
- 标题党 listicle（"10 个......"）
- 重复事件的边角报道

## 🎯 保留并加重
- 央行政策、利率、通胀、就业数据
- 公司财报、并购、IPO、监管行动
- 半导体、AI、云、平台战略
- 中美科技/贸易/资本流向
- 大宗、能源、汇率、加密
- 顶级投资人/CEO/学者的**原话观点**

## 📑 输出结构（JSON）

```
{{
  "top5": [               // 今日全球最重要 5 件大事（投资/宏观/科技角度）
    {{
      "title": "中文标题（不要标题党）",
      "summary": "中文 100-180 字。客观陈述事实+影响，给出'为什么重要'的判断",
      "sources": [{{"name": "源名", "url": "..."}}]
    }}
  ],
  "people": [             // 大佬今日观点（最重要的一节！）
    {{
      "name": "Elon Musk / Sam Altman / Warren Buffett / Howard Marks / Ben Thompson / Tyler Cowen / Jensen Huang / Powell 等具名人物",
      "title": "他说了什么的中文概括",
      "summary": "中文 80-150 字。如果是直接引语，标注 '原话：「...」'。如果只是间接观点，标 '观点：...'",
      "sources": [{{"name": "...", "url": "..."}}]
    }}
  ],
  "macro": [...],          // 宏观/央行/利率/通胀/汇率
  "tech": [...],           // 科技/AI/半导体的战略层面
  "us_stocks": [...],      // 美股/美国公司财报/并购
  "a_stocks": [...],       // A股/中国市场/中国公司，没有就空
  "business": [...],       // 其他重要商业事件（能源、医药、消费等）
  "overlooked": [...]      // 重要但容易被忽略的（新兴市场、长尾资产、结构性变化），2-3 条
}}
```

## 数量约束
- top5: 必须 5 条
- people: 3-6 条（如果原文里没有大佬观点，就放该领域**最被引用的专业评论员观点**，比如 Ben Thompson、Tyler Cowen、Damodaran 等）
- macro/tech/us_stocks/business: 各 3-5 条
- a_stocks: 0-4 条（看素材）
- overlooked: 2-3 条

## 风格要求
- 客观、专业、无煽动
- 给"为什么重要"的判断，不只是事实复述
- 不重复 top5 已经讲过的事情（其他类别要互补）
- 不要编造原文没有的信息

原始文章数据：
{articles_json}
"""

EMPTY_RESULT = {
    "top5": [], "people": [], "macro": [], "tech": [],
    "us_stocks": [], "a_stocks": [], "business": [], "overlooked": [],
}


def call_gemini(prompt, max_retries=4):
    config = types.GenerateContentConfig(response_mime_type="application/json")
    last_err = None
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=MODEL, contents=prompt, config=config,
            )
        except genai_errors.ClientError as e:
            last_err = e
            msg = str(e)
            if "retry_delay" in msg or "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                wait = 30 + attempt * 20
                print(f"[retry {attempt+1}/{max_retries}] rate-limited, sleeping {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except genai_errors.ServerError as e:
            last_err = e
            wait = 10 + attempt * 10
            print(f"[retry {attempt+1}/{max_retries}] server error, sleeping {wait}s...", file=sys.stderr)
            time.sleep(wait)
    raise last_err


def process(articles):
    if not articles:
        return EMPTY_RESULT.copy()
    if len(articles) > MAX_ARTICLES:
        articles = articles[:MAX_ARTICLES]
        print(f"[info] capped input to {MAX_ARTICLES} articles")

    prompt = PROMPT_TEMPLATE.format(
        articles_json=json.dumps(articles, ensure_ascii=False)
    )
    response = call_gemini(prompt)
    text = (response.text or "").strip()

    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()

    return json.loads(text)


if __name__ == "__main__":
    with open("data/raw.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    print(f"Processing {len(articles)} articles with Gemini ({MODEL})...")
    result = process(articles)
    Path("data").mkdir(exist_ok=True)
    with open("data/processed.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    total = sum(len(v) for v in result.values() if isinstance(v, list))
    print(f"Done. {total} items across {len(result)} sections.")

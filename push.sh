#!/bin/bash
# 一键把本地 /Users/kk/kkssuprekk/ 推送到 GitHub，覆盖远程乱七八糟的状态
set -e

cd "$(dirname "$0")"

echo ""
echo "==> 准备推送到 https://github.com/pkujiaken/kkssuprekk"
echo ""
echo "请粘贴你的 GitHub Personal Access Token (PAT)："
echo "（粘贴后看不到字符是正常的，安全考虑隐藏了。粘贴完按回车）"
echo ""
read -s TOKEN
echo ""

if [ -z "$TOKEN" ]; then
  echo "❌ Token 为空，退出"
  exit 1
fi

# 初始化 git（如果还没初始化）
if [ ! -d .git ]; then
  git init -b main
fi

# 配置一次性身份（仅本仓库，不影响全局）
git config user.email "pkujiaken@users.noreply.github.com"
git config user.name "pkujiaken"

# 强制 HTTP/1.1（绕开 macOS git 偶发的 HTTP2 framing 错误）
git config http.version HTTP/1.1
git config http.postBuffer 524288000

# 加入所有文件
git add -A
git commit -m "clean initial push" || echo "(no changes to commit)"

# 设置远程并强制推送
git remote remove origin 2>/dev/null || true
git remote add origin "https://pkujiaken:${TOKEN}@github.com/pkujiaken/kkssuprekk.git"

echo ""
echo "==> 推送中..."
git push -u origin main --force

echo ""
echo "✅ 推送成功！"
echo ""
echo "下一步："
echo "1. 立刻去 https://github.com/settings/tokens 撤销刚才的 token（安全起见）"
echo "2. 去 https://github.com/pkujiaken/kkssuprekk/actions 手动跑一次 Daily Brief"

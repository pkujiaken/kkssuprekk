#!/bin/bash
# 从剪贴板读 token，避免输入错误
set -e
cd "$(dirname "$0")"

echo ""
echo "==> 准备推送到 https://github.com/pkujiaken/kkssuprekk"
echo ""

# 从剪贴板读 token
TOKEN=$(pbpaste | tr -d '[:space:]')

if [ -z "$TOKEN" ]; then
  echo "❌ 剪贴板是空的，请先复制 token 再跑"
  exit 1
fi

# 验证 token 格式
if [[ ! "$TOKEN" =~ ^(ghp_|github_pat_) ]]; then
  echo "❌ 剪贴板里不像是 GitHub token"
  echo "   读到的前 30 个字符: ${TOKEN:0:30}"
  echo "   应该以 'ghp_' 或 'github_pat_' 开头"
  echo "   请重新去 GitHub 复制 token，再跑一次"
  exit 1
fi

LEN=${#TOKEN}
echo "✓ 从剪贴板读到 token: ${TOKEN:0:7}...${TOKEN: -4}（长度 $LEN）"
echo ""

# 初始化 git
if [ ! -d .git ]; then
  git init -b main
fi

# 配置（仅本仓库）
git config user.email "pkujiaken@users.noreply.github.com"
git config user.name "pkujiaken"
git config http.version HTTP/1.1
git config http.postBuffer 524288000

# 提交所有改动
git add -A
git commit -m "clean push" 2>/dev/null || echo "(无新改动)"

# 设置远程
git remote remove origin 2>/dev/null || true
git remote add origin "https://pkujiaken:${TOKEN}@github.com/pkujiaken/kkssuprekk.git"

echo ""
echo "==> 推送中..."
git push -u origin main --force

echo ""
echo "✅ 推送成功！"
echo ""
echo "下一步："
echo "1. 立刻去 https://github.com/settings/tokens 撤销刚才的 token"
echo "2. 去 https://github.com/pkujiaken/kkssuprekk/actions 跑一次 Daily Brief"

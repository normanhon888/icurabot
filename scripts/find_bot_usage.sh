#!/usr/bin/env bash
set -euo pipefail

TARGET="bot.nzinsure.co.nz"
SEARCH_DIRS=(
  "/opt/icurabot"       # 主应用目录
  "/opt/icura"          # 旧目录（若已清理可能不存在）
  "/etc/nginx/conf.d"   # Nginx 配置
  "/var/www/h5"         # H5 前端页面
)

echo "🔍 开始扫描 '$TARGET' 的引用..."

for dir in "${SEARCH_DIRS[@]}"; do
  if [[ -d "$dir" ]]; then
    echo -e "\n📂 检查目录: $dir"
    grep -R --color=always -n "$TARGET" "$dir" || echo "✅ 未发现引用"
  else
    echo -e "\n⚠️ 目录不存在: $dir"
  fi
done

echo -e "\n🎉 扫描完成"

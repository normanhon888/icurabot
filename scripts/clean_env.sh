#!/usr/bin/env bash
set -euo pipefail

echo "🧹 开始清理并统一 icurabot 环境..."

# 1. 停止所有 gunicorn
echo "⛔ 停止所有 gunicorn 进程..."
sudo pkill -9 -f gunicorn || true

# 2. 备份旧目录
TS=$(date +%Y%m%d_%H%M%S)
for dir in /opt/icura /opt/icura/.venv; do
  if [[ -d "$dir" ]]; then
    echo "📦 备份 $dir 到 ${dir}_bak_$TS"
    sudo mv "$dir" "${dir}_bak_$TS"
  fi
done

# 3. 确保主目录存在
if [[ ! -d /opt/icurabot/app ]]; then
  echo "❌ /opt/icurabot/app 不存在，请确认代码已放在这里"
  exit 1
fi

# 4. 确保 Supervisor 配置
CONF="/etc/supervisor/conf.d/icurabot.conf"
if [[ -f "$CONF" ]]; then
  echo "✅ 已找到 Supervisor 配置: $CONF"
else
  echo "⚠️ 未找到 $CONF，请手动创建配置"
fi

# 5. 重载 Supervisor
echo "🔄 重启 icurabot 服务..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart icurabot || true

# 6. 重启 Nginx
echo "🌐 重载 Nginx..."
sudo nginx -t && sudo systemctl reload nginx

# 7. 验证
echo "🧪 本地健康检查:"
curl -s -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:8000/healthz || true
curl -s -o /dev/null -w "version: %{http_code}\n" http://127.0.0.1:8000/version || true

echo "🎉 环境清理完成，只保留 /opt/icurabot 作为主目录"

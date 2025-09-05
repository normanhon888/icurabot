#!/usr/bin/env bash
set -euo pipefail

echo "🔍 iCura 环境检测开始..."

# 1. 检查目录结构
echo -e "\n📂 目录检查:"
for dir in /opt/icura /opt/icura/.venv /opt/icurabot; do
  if [[ -d "$dir" ]]; then
    echo "✅ 存在: $dir"
  else
    echo "❌ 不存在: $dir"
  fi
done

# 2. 检查 Gunicorn 进程
echo -e "\n🐍 Gunicorn 进程:"
ps -ef | grep gunicorn | grep -v grep || echo "❌ 未找到 gunicorn 进程"

# 3. 检查端口监听
echo -e "\n🌐 端口监听:"
sudo lsof -nP -i:8000 || echo "❌ 8000 端口未被监听"

# 4. 检查 Supervisor 配置
echo -e "\n⚙️  Supervisor 配置:"
CONF="/etc/supervisor/conf.d/icurabot.conf"
if [[ -f "$CONF" ]]; then
  echo "✅ 已找到 $CONF"
  grep command $CONF
else
  echo "❌ 未找到 $CONF"
fi

# 5. 检查 Supervisor 状态
echo -e "\n📡 Supervisor 服务状态:"
sudo supervisorctl status icurabot || echo "❌ icurabot 未由 Supervisor 管理"

# 6. 检查 Nginx 配置
echo -e "\n🌐 Nginx 配置检查:"
grep -R "proxy_pass" /etc/nginx/conf.d/ | grep 8000 || echo "❌ Nginx 未配置 proxy_pass 到 8000"

# 7. 健康检查
echo -e "\n🧪 健康检查:"
curl -s -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:8000/healthz || true
curl -s -o /dev/null -w "version: %{http_code}\n" http://127.0.0.1:8000/version || true

echo -e "\n🎉 检测完成"

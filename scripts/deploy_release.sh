#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/icurabot/app"
VENV="/opt/icurabot/venv"
LOG_ERR="/var/log/icurabot/gunicorn.error.log"
TARGET_USER="azureuser"
TARGET_GROUP="www-data"

echo "📂 当前工作目录: $APP_DIR"

# 0) 确保 venv 权限正确
echo "🔧 检查并修复虚拟环境权限..."
if [[ -d "$VENV" ]]; then
  sudo chown -R "$TARGET_USER":"$TARGET_GROUP" "$VENV"
  sudo chmod -R 775 "$VENV"
  ls -ld "$VENV"
else
  echo "⚠️ 未找到虚拟环境目录: $VENV，将在后续步骤创建"
fi

# 1) 虚拟环境
echo "📦 检查/创建虚拟环境..."
python3 -m venv "$VENV" || true
"$VENV/bin/pip" install --upgrade pip wheel setuptools

# 2) 安装依赖
if [[ -f "$APP_DIR/requirements.txt" ]]; then
  echo "📚 安装 Python 依赖..."
  "$VENV/bin/pip" install -r "$APP_DIR/requirements.txt"
else
  echo "⚠️ 未找到 $APP_DIR/requirements.txt，跳过依赖安装"
fi

# 3) 重启 Supervisor 管理的 icurabot
echo "🔄 重启 icurabot 服务..."
sudo supervisorctl reread || true
sudo supervisorctl update || true
sudo supervisorctl restart icurabot

# 4) 健康检查（本地）
echo "🧪 本地健康检查..."
sleep 2
HC=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/healthz || true)
if [[ "$HC" != "200" ]]; then
  echo "❌ 本地 healthz 检查失败 (HTTP $HC)"
  echo "=== 最近 Gunicorn 错误日志 ==="
  sudo tail -n 50 "$LOG_ERR" || true
  exit 1
else
  echo "✅ 本地健康检查通过"
fi

# 5) 外部健康检查
echo "🌐 外部健康检查..."
for url in \
  "https://api.nzinsure.co.nz/healthz" \
  "https://api.nzinsure.co.nz/version" \
  "https://h5.nzinsure.co.nz/"; do
  code=$(curl -sk -o /dev/null -w "%{http_code}" "$url")
  echo "$url => $code"
  if [[ "$code" != "200" ]]; then
    echo "❌ 外部检查失败: $url"
    exit 1
  fi
done

# 6) 验证并重载 Nginx
echo "🔁 检查并重载 Nginx..."
sudo nginx -t
sudo systemctl reload nginx

echo "✅ 部署完成"


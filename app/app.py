from flask import Flask
from health import bp as health_bp
from hubspot_routes import bp as hubspot_bp
from version import bp as version_bp   # ✅ 新增导入

app = Flask(__name__)
app.register_blueprint(health_bp)
app.register_blueprint(hubspot_bp)
app.register_blueprint(version_bp)     # ✅ 注册 version blueprint

wsgi_app = app  # gunicorn app:wsgi_app


import importlib
try:
    import app.patch_register  # 触发自动注册蓝图
except Exception as e:
    print("wsgi_icura: patch_register import failed:", e)
_real = importlib.import_module("app.wsgi")
app = getattr(_real, "app", None) or getattr(_real, "application", None)
if app is None and hasattr(_real, "create_app"):
    app = _real.create_app()
if app is None:
    raise RuntimeError("wsgi_icura: cannot resolve Flask app from app.wsgi")

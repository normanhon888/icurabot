"""
Auto-register zz_health_bp blueprint onto the running Flask app,
and wrap create_app factory if present.
"""
try:
    try:
        from app.zz_health_bp import bp as __zz_bp
    except Exception:
        from zz_health_bp import bp as __zz_bp
except Exception as e:
    print("patch_register: cannot import zz_health_bp:", e)
    __zz_bp = None

def _register_on(obj):
    if not __zz_bp or obj is None:
        return
    try:
        obj.register_blueprint(__zz_bp)
        print("patch_register: zz_health_bp registered on", getattr(obj, "name", obj))
    except Exception as e:
        print("patch_register: register on object failed:", e)

# 情况 1：全局 app / application 已经存在（wsgi:app / wsgi:application）
g = globals()
for name in ("app", "application"):
    if name in g:
        _register_on(g[name])

# 情况 2：工厂模式 create_app()
if "create_app" in g:
    _old_factory = g["create_app"]
    def create_app(*a, **kw):
        app = _old_factory(*a, **kw)
        _register_on(app)
        return app
    g["create_app"] = create_app

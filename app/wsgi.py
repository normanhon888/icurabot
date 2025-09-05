import sys, traceback
from dotenv import load_dotenv
try:
    load_dotenv('/opt/icurabot/.env')
except Exception as e:
    sys.stderr.write(f"[dotenv] warning: {e}\n")

try:
    from app.health import app as real_app
    app = real_app
except Exception:
    sys.stderr.write("[bootstrap] failed to import app.health:\n" + traceback.format_exc() + "\n")
    from flask import Flask, jsonify
    app = Flask(__name__)
    @app.route("/ping")
    def ping():
        return jsonify({"ok": True, "fallback": True}), 200
    @app.route("/version")
    def version():
        return jsonify({"ok": False, "bootstrap": "fallback"}), 500
# --- auto-register zz_health_bp (do not remove) ---
try:
    try:
        from app.zz_health_bp import bp as __zz_bp
    except Exception:
        from zz_health_bp import bp as __zz_bp

    # 全局 app/application
    try:
        if "app" in globals():
            globals()["app"].register_blueprint(__zz_bp)
        if "application" in globals():
            globals()["application"].register_blueprint(__zz_bp)
    except Exception as e:
        print("zz_health_bp register on global object failed:", e)

    # 工厂模式
    if "create_app" in globals():
        __old_create = globals()["create_app"]
        def create_app(*a, **kw):
            __app = __old_create(*a, **kw)
            try:
                __app.register_blueprint(__zz_bp)
            except Exception as e:
                print("zz_health_bp register in factory failed:", e)
            return __app
        globals()["create_app"] = create_app
except Exception as e:
    print("zz_health_bp wiring error:", e)
# --- end auto-register ---

# auto-register zz_health_bp
import app.patch_register  # noqa

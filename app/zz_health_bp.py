from flask import Blueprint, request, jsonify
import os

# 显式加载 .env（不依赖外部环境）
try:
    from dotenv import load_dotenv
    load_dotenv("/opt/icurabot/.env")
except Exception:
    pass

bp = Blueprint("zz_health", __name__)

@bp.get("/version")
def version():
    return jsonify({
        "app": "icurabot",
        "build": os.getenv("ICURABOT_BUILD", "20250818"),
        "model_default": os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4o-mini"),
        "model_upgrade": os.getenv("OPENAI_MODEL_UPGRADE", "gpt-4o"),
        "ok": True
    }), 200

def _get_client():
    from openai import OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("missing OPENAI_API_KEY")
    kw = {"api_key": api_key}
    base_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
    if base_url:
        kw["base_url"] = base_url
    api_version = os.getenv("OPENAI_API_VERSION")
    if api_version:
        kw["default_query"] = {"api-version": api_version}
    return OpenAI(**kw)

def _as_int(x, d=0):
    try:
        return int(x) if x is not None else d
    except Exception:
        return d

@bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip() or "Hello!"
    model = data.get("model") or os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4o-mini")
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content":"You are a helpful assistant."},
                {"role":"user","content":user_msg}
            ],
        )
        choice = resp.choices[0]
        content = (getattr(choice, "message", None).content
                   if hasattr(choice, "message") and getattr(choice, "message") else
                   getattr(choice, "text", ""))

        usage = getattr(resp, "usage", None)
        usage_dict = None
        if usage:
            if isinstance(usage, dict):
                usage_dict = {
                    "prompt_tokens": _as_int(usage.get("prompt_tokens")),
                    "completion_tokens": _as_int(usage.get("completion_tokens")),
                    "total_tokens": _as_int(usage.get("total_tokens")),
                }
            else:
                usage_dict = {
                    "prompt_tokens": _as_int(getattr(usage, "prompt_tokens", None)),
                    "completion_tokens": _as_int(getattr(usage, "completion_tokens", None)),
                    "total_tokens": _as_int(getattr(usage, "total_tokens", None)),
                }

        result = {"ok": True, "model": getattr(resp, "model", model), "message": content}
        if usage_dict:
            result["usage"] = usage_dict
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

import os, time
from urllib.parse import quote
import requests
from flask import Blueprint, request, jsonify

bp = Blueprint("hubspot", __name__)

def _token():
    t = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or os.getenv("HUBSPOT_ACCESS_TOKEN")
    if not t:
        raise RuntimeError("HUBSPOT token missing")
    return t

def _extract_properties(data: dict):
    if not isinstance(data, dict):
        return {}
    lower = { (k.lower() if isinstance(k,str) else k): v for k,v in data.items() }
    mapping = {"first_name":"firstname", "last_name":"lastname"}
    props = {}
    for k in ("email","firstname","lastname","phone","company","jobtitle","website","lifecyclestage"):
        v = lower.get(k) if k in lower else lower.get(mapping.get(k,"__no__"))
        if v:
            props[k] = v
    return props

@bp.route("/lead/create", methods=["OPTIONS"])
def lead_create_options():
    return ("", 204)

@bp.route("/lead/create", methods=["POST"])
def lead_create():
    secret = os.getenv("WEBHOOK_SHARED_SECRET")
    if secret and request.headers.get("X-Webhook-Token") != secret:
        return jsonify({"ok": False, "status": 401, "error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    props = _extract_properties(data)
    email = (props.get("email") or "").strip().lower()
    if not email:
        return jsonify({"ok": False, "status": 400, "error": "email required"}), 400

    t0 = time.time()
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
    }

    # ✅ 策略：先 PATCH by email（idProperty=email）→ 不存在就 POST 创建
    patch_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{quote(email, safe='')}"
    try:
        r = requests.patch(patch_url, headers=headers, params={"idProperty":"email"},
                           json={"properties": props}, timeout=12)
    except Exception as e:
        return jsonify({"ok": False, "status": 500, "error": f"patch_error: {e}"}), 500

    if r.status_code == 404:
        # 新建
        try:
            create_url = "https://api.hubapi.com/crm/v3/objects/contacts"
            r2 = requests.post(create_url, headers=headers, json={"properties": props}, timeout=12)
            ok2 = 200 <= r2.status_code < 300
            out = {
                "ok": ok2,
                "status": r2.status_code,
                "mode": "create",
                "took_ms": int((time.time() - t0) * 1000),
            }
            try:
                j = r2.json()
                out["hubspot"] = j
                rid = (j.get("id") or (j.get("results",[{}])[0].get("id") if isinstance(j.get("results"), list) and j["results"] else None))
                if rid: out["hubspot_id"] = rid
            except Exception:
                out["hubspot_raw"] = r2.text[:800]
            return jsonify(out), (200 if ok2 else r2.status_code)
        except Exception as e:
            return jsonify({"ok": False, "status": 500, "error": f"create_error: {e}"}), 500

    # PATCH 成功或其他非 404
    ok = 200 <= r.status_code < 300
    out = {
        "ok": ok,
        "status": r.status_code,
        "mode": "patch",
        "took_ms": int((time.time() - t0) * 1000),
    }
    try:
        j = r.json()
        out["hubspot"] = j
        rid = (j.get("id") or (j.get("results",[{}])[0].get("id") if isinstance(j.get("results"), list) and j["results"] else None))
        if rid: out["hubspot_id"] = rid
    except Exception:
        out["hubspot_raw"] = r.text[:800]
    return jsonify(out), (200 if ok else r.status_code)

# 诊断路由，确认当前部署的策略
@bp.get("/lead/_diag")
def lead_diag():
    return jsonify({"strategy":"patch_then_create", "idProperty":"email"}), 200

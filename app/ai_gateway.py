import os, time
from typing import Dict, Any

USE_AZURE = os.getenv("USE_AZURE_OPENAI","").lower() in ("1","true","yes")
DEFAULT_MODEL = os.getenv("MODEL_DEFAULT", "gpt-4o-mini")
UPGRADE_MODEL  = os.getenv("MODEL_UPGRADE",  "gpt-4o")

if USE_AZURE:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION","2024-02-15-preview"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
else:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def _choose_model(prompt: str, force: str|None) -> str:
    hard = ("条款","Business Interruption","赔付","等待期","费率","计算","保费")
    if force == "complex" or len(prompt) > 350 or any(k.lower() in prompt.lower() for k in hard):
        return UPGRADE_MODEL
    return DEFAULT_MODEL

def _usage_simple(u) -> Dict[str, Any] | None:
    if not u: return None
    try:
        if hasattr(u, "model_dump"):
            d = u.model_dump()
            return {
                "prompt_tokens": d.get("prompt_tokens"),
                "completion_tokens": d.get("completion_tokens"),
                "total_tokens": d.get("total_tokens"),
            }
    except Exception:
        pass
    return {
        "prompt_tokens": getattr(u, "prompt_tokens", None),
        "completion_tokens": getattr(u, "completion_tokens", None),
        "total_tokens": getattr(u, "total_tokens", None),
    }

def _build_result(r, model, t0):
    usage = _usage_simple(getattr(r, "usage", None))
    content = r.choices[0].message.content if getattr(r, "choices", None) else ""
    return {"ok": True, "model": model, "content": content, "usage": usage,
            "latency_ms": int((time.time()-t0)*1000)}

def chat(prompt: str, force: str|None=None, system: str|None=None) -> Dict[str, Any]:
    model = _choose_model(prompt, force)
    msgs = [{"role":"system","content":system}] if system else []
    msgs.append({"role":"user","content":prompt})
    t0 = time.time()
    try:
        r = client.chat.completions.create(model=model, messages=msgs, temperature=0.3)
        return _build_result(r, model, t0)
    except Exception as e:
        if model != UPGRADE_MODEL:
            try:
                r = client.chat.completions.create(model=UPGRADE_MODEL, messages=msgs, temperature=0.3)
                return _build_result(r, UPGRADE_MODEL, t0)
            except Exception as e2:
                return {"ok": False, "error": str(e2)}
        return {"ok": False, "error": str(e)}

import os, requests
from typing import Optional, Dict, Any
BASE = "https://api.hubapi.com"
TOKEN = os.getenv("HUBSPOT_API_KEY")

def _headers() -> Dict[str,str]:
    if not TOKEN: raise RuntimeError("HUBSPOT_API_KEY is not set")
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def find_contact_by_email(email: str) -> Optional[Dict[str, Any]]:
    url = f"{BASE}/crm/v3/objects/contacts/search"
    data = {"filterGroups":[{"filters":[{"propertyName":"email","operator":"EQ","value":email}]}],
            "properties":["email","firstname","lastname","phone"]}
    r = requests.post(url, headers=_headers(), json=data, timeout=15); r.raise_for_status()
    items = r.json().get("results", []); return items[0] if items else None

def create_or_update_contact(props: Dict[str, Any]) -> Dict[str, Any]:
    email = props.get("email");  assert email, "email is required"
    ex = find_contact_by_email(email)
    if ex:
        r = requests.patch(f"{BASE}/crm/v3/objects/contacts/{ex['id']}", headers=_headers(), json={"properties":props}, timeout=15)
        r.raise_for_status();  return {"action":"updated","id":ex["id"]}
    r = requests.post(f"{BASE}/crm/v3/objects/contacts", headers=_headers(), json={"properties":props}, timeout=15)
    r.raise_for_status();  return {"action":"created","id":r.json()["id"]}

def create_deal(props: Dict[str, Any]) -> str:
    data = {"properties":{"dealname": props.get("dealname") or "iCurabot Deal",
                          "amount": props.get("amount"),
                          "pipeline": props.get("pipeline") or "default",
                          "dealstage": props.get("dealstage") or "appointmentscheduled"}}
    r = requests.post(f"{BASE}/crm/v3/objects/deals", headers=_headers(), json=data, timeout=15)
    r.raise_for_status();  return r.json()["id"]

def associate_deal_contact(deal_id: str, contact_id: str) -> None:
    data = {"inputs":[{"from":{"id":deal_id},"to":{"id":contact_id},"type":"deal_to_contact"}]}
    r = requests.post(f"{BASE}/crm/v4/associations/deals/contacts/batch/create", headers=_headers(), json=data, timeout=15)
    r.raise_for_status()

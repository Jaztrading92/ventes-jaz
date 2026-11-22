import os
import json
import datetime
import urllib.request
import urllib.parse

KEY = os.environ["CHARIOW_KEY"].strip()
API = "https://api.chariow.com/v1/sales"
PAID = ("completed", "settled")
DAYS = 90


def get(params):
    req = urllib.request.Request(
        API + "?" + urllib.parse.urlencode(params),
        headers={"Authorization": "Bearer " + KEY, "Accept": "application/json", "User-Agent": "jaz-ventes/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch(status, frm):
    out, cursor = [], None
    while True:
        p = {"per_page": 100, "status": status, "from": frm}
        if cursor:
            p["cursor"] = cursor
        j = get(p)
        out.extend(j.get("data") or [])
        cursor = (j.get("pagination") or {}).get("next_cursor")
        if not cursor:
            return out


frm = (datetime.date.today() - datetime.timedelta(days=DAYS)).isoformat()
items, seen, sales = [], set(), []
for st in PAID:
    items.extend(fetch(st, frm))
for s in items:
    sid = s.get("id")
    if not sid or sid in seen:
        continue
    seen.add(sid)
    amt = float((s.get("amount") or {}).get("value") or 0)
    if amt <= 0:
        continue
    orig = float((s.get("original_amount") or {}).get("value") or amt)
    sales.append({"id": sid, "t": s.get("created_at"), "prix": orig, "paye": amt, "p": (s.get("product") or {}).get("name", "")})
sales.sort(key=lambda x: x["t"] or "", reverse=True)

data = {"day": datetime.date.today().isoformat(), "sales": sales}
old = None
try:
    with open("ventes.json", encoding="utf-8") as f:
        old = json.load(f)
except Exception:
    pass
if old != data:
    with open("ventes.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("ventes.json mis a jour (" + str(len(sales)) + " ventes)")
else:
    print("aucun changement")

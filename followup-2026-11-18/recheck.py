#!/usr/bin/env python3
"""Recheck the 125 JPL close-approach (CAD) row pairs that shared one time (op2 CADALL-SE; Chief ruling BC3).
For each pair in shared_time_pairs_125.csv, take the CURRENT CAD rows of that object within +-2 days of the old shared time
for the two bodies of the pair, and report whether the two rows still carry the same time.
Times are compared as numbers (Decimal), never as text (July lesson: equal times can differ by a trailing zero).
Modes:
  live    OUTDIR         query https://ssd-api.jpl.nasa.gov/cad.api once per pair (serial, 2 s apart, generic client),
                         save every reply under OUTDIR/raw/, then classify. Run ONLY on the Chief's order, after JPL's recompute.
  offline TABLE.json     classify against a saved CAD table (same JSON shape as cad.api body=ALL) — used for the self-test.
Per pair: STILL_SHARED, CHANGED (both rows present, times now differ; which row moved and by how many minutes),
ROW_MISSING (one or both body rows absent within +-2 days and dist-max 0.2 au). Totals at the end.
Claim authority NONE. Contacts no one; schedules nothing.
usage: python3 -I this.py PAIRS.csv MODE (OUTDIR|TABLE.json) REPORT.json"""
import sys, os, csv, json, time, hashlib, datetime as dt, urllib.request, urllib.parse
from decimal import Decimal

PAIRS, MODE, ARG, REPORT = sys.argv[1:5]
UA = "generic-research-client/1.0"
WIN = Decimal(2)                                  # days around the old shared time
BODY = {"Earth": "Earth", "Moon": "Moon", "Venus": "Venus", "Mars": "Mars", "Mercury": "Merc"}


def jd_to_date(jd):
    return (dt.datetime(2000, 1, 1, 12) + dt.timedelta(days=float(jd) - 2451545.0))


def rows_live(des, jd, rawdir):
    d0 = (jd_to_date(jd - WIN)).strftime("%Y-%m-%d"); d1 = (jd_to_date(jd + WIN) + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    q = urllib.parse.urlencode({"des": des, "body": "ALL", "date-min": d0, "date-max": d1, "dist-max": "0.2", "fullname": "true"})
    url = "https://ssd-api.jpl.nasa.gov/cad.api?" + q
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r: body = r.read()
    fn = os.path.join(rawdir, des.replace(" ", "_").replace("/", "_") + ".json"); open(fn, "wb").write(body)
    j = json.loads(body); F = j.get("fields", [])
    return [dict(zip(F, v)) for v in j.get("data", [])], {"url": url, "file": fn, "sha256": hashlib.sha256(body).hexdigest()}


TABLE = None


def rows_offline(des, jd):
    global TABLE
    if TABLE is None:
        s = json.load(open(ARG)); F = s["fields"]; TABLE = {}
        for v in s["data"]:
            r = dict(zip(F, v)); TABLE.setdefault(r["des"], []).append(r)
    return [r for r in TABLE.get(des, []) if abs(Decimal(r["jd"]) - jd) <= WIN], None


def classify(p, rows):
    jd = Decimal(p["shared_time_jd"]); bodies = [BODY.get(b, b) for b in p["bodies"].split("+")]
    pick = {}
    for b in bodies:
        c = [r for r in rows if r.get("body", "Earth") == b and abs(Decimal(r["jd"]) - jd) <= WIN]
        if c: pick[b] = min(c, key=lambda r: abs(Decimal(r["jd"]) - jd))
    out = {"designation": p["designation"], "bodies": p["bodies"], "old_shared_jd": p["shared_time_jd"], "old_wrong_row": p.get("row_with_wrong_time", ""),
           "rows_now": {b: {"jd": r["jd"], "cd": r.get("cd"), "dist": r.get("dist"), "orbit_id": r.get("orbit_id")} for b, r in pick.items()}}
    if len(pick) < 2:
        out["status"] = "ROW_MISSING"; out["missing"] = [b for b in bodies if b not in pick]; return out
    a, b = (Decimal(pick[x]["jd"]) for x in bodies)
    if a == b:
        out["status"] = "STILL_SHARED"
    else:
        out["status"] = "CHANGED"
        out["moved_min"] = {x: float((Decimal(pick[x]["jd"]) - jd) * 1440) for x in bodies}
        out["rows_now_differ_min"] = float(abs(a - b) * 1440)
    return out


pairs = list(csv.DictReader(open(PAIRS)))
res, prov = [], []
if MODE == "live":
    rawdir = os.path.join(ARG, "raw"); os.makedirs(rawdir, exist_ok=True)
for i, p in enumerate(pairs):
    jd = Decimal(p["shared_time_jd"])
    if MODE == "live":
        try:
            rows, pv = rows_live(p["designation"], jd, rawdir); prov.append(pv)
        except Exception as ex:
            res.append({"designation": p["designation"], "status": "FETCH_FAILED", "error": str(ex)[:200]}); time.sleep(2); continue
        time.sleep(2)
    else:
        rows, _ = rows_offline(p["designation"], jd)
    res.append(classify(p, rows))
tot = {}
for r in res: tot[r["status"]] = tot.get(r["status"], 0) + 1
rep = {"claim_authority": "NONE", "mode": MODE, "source": ARG if MODE == "offline" else "https://ssd-api.jpl.nasa.gov/cad.api",
       "run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
       "pairs_file": PAIRS, "pairs_sha256": hashlib.sha256(open(PAIRS, "rb").read()).hexdigest(),
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "n_pairs": len(pairs), "totals": tot,
       "by_old_wrong_row": {}, "pairs": res, "fetch_provenance": prov}
for r in res:
    k = (r.get("old_wrong_row") or "?") + ":" + r["status"]; rep["by_old_wrong_row"][k] = rep["by_old_wrong_row"].get(k, 0) + 1
json.dump(rep, open(REPORT, "w"), indent=1)
print(json.dumps({k: rep[k] for k in ("mode", "n_pairs", "totals", "by_old_wrong_row")}, indent=1))

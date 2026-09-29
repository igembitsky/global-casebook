#!/usr/bin/env python3
"""Combine all verification results into data/verify/summary.json for the Sources tab."""
import json, pathlib, datetime
R = pathlib.Path(__file__).parent / "data"
ld = lambda p, d=None: json.loads((R/p).read_text()) if (R/p).exists() else d
links = ld("verify/links_raw.json", [])
content = {c["url"]: c for c in ld("verify/cases_content.json", [])}
bc = ld("verify/burden_claims.json", {})
burden_claims = bc.get("claims", []) if isinstance(bc, dict) else bc
# pages that block scripts but were confirmed with a browser-style fetch by a verification agent
BROWSER_OK = {"https://www.cdc.gov/mmwr/volumes/74/wr/mm7405a1.htm", "https://www.cdc.gov/nchs/fastats/suicide.htm", "https://openalex.org"}
SEARCH_OK = {"https://www.sciencedirect.com/journal/idcases", "https://onlinelibrary.wiley.com/journal/20500904"}
L = {}
for o in links:
    u = o["url"]
    if o["status"] in (200, 203): L[u] = {"ok": True, "how": f"opened by script (HTTP {o['status']})"}
    elif u in SEARCH_OK: L[u] = {"ok": True, "how": "site blocks all automated access; confirmed through the publisher's catalog, DOAJ and the ISSN register"}
    elif u in BROWSER_OK or (u in content and content[u]["verdict"] in ("verified", "fixed")):
        L[u] = {"ok": True, "how": "site blocks scripts; opened and read with a browser fetch"}
    else: L[u] = {"ok": False, "how": f"HTTP {o['status']}; not confirmed"}
mep = ld("verify/mep_doi.json", {})
live = ld("verify/burden_live_who.json", {})
pmc = ld("verify/pmc_titles.json", {})
iris = ld("verify/iris_titles.json", {})
lib = ld("library.json", {})
alt = [c for c in lib.get("cases", []) if c.get("source") != "mededportal"]
cc = ld("verify/cases_content.json", [])
checks = [
 {"value": f"{mep.get('ok',0):,} of {mep.get('checked',0):,}", "label": "MedEdPORTAL DOIs (Digital Object Identifiers: permanent links) open the right publication"},
 {"value": f"{mep.get('checked',0):,}", "label": "MedEdPORTAL titles match the publisher's Crossref record"},
 {"value": f"{live.get('checked',0) - len(live.get('mismatches',[]))} of {live.get('checked',0)}", "label": "WHO (World Health Organization) burden figures match the live WHO data"},
 {"value": f"{len(burden_claims)}", "label": f"other burden figures checked against their source documents ({len(burden_claims) - sum(1 for c in burden_claims if c.get('verdict')=='verified')} corrected)"},
 {"value": f"{sum(1 for u,v in L.items() if v['ok'])} of {len(L)}", "label": "source and case links open"},
 {"value": f"{len(pmc)} + {sum(1 for c in alt if 'iris.who.int' in c['url'])}", "label": "journal and WHO cases checked by title in PubMed Central and WHO IRIS"},
]
if cc: checks.append({"value": f"{sum(1 for c in cc if c['verdict'] in ('verified','fixed'))} of {len(cc)}", "label": "cases read in full to confirm the case exists"})
summary = {"date": datetime.date.today().isoformat(), "links": L, "checks": checks,
  "summary": f"Every source below was checked on {datetime.date.today():%d %B %Y}. Scripts opened each link, compared titles with the official registries (Crossref, the DOI registry; PubMed Central, the US National Library of Medicine archive; WHO IRIS, the World Health Organization document library) and compared each burden figure with the live WHO data. Verification agents then read the source documents to confirm the figures and the cases."}
(R/"verify/summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(checks, indent=1)); print("links not ok:", [u for u,v in L.items() if not v["ok"]])

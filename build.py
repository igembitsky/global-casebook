#!/usr/bin/env python3
"""Merge research data into data/library.json and render index.html from template.html."""
import json, re, glob, datetime, pathlib, sys
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT / "data"))
from conditions import CONDITIONS
from glossary import GLOSSARY

_ABBR = sorted(GLOSSARY, key=len, reverse=True)
_ABBR_RE = re.compile(r"(?<![\w/&-])(" + "|".join(re.escape(a) for a in _ABBR) + r")('s)?(?![\w/&-])")
def expand(text, skip=()):
    """Write 'ABBR (meaning)' at the first use of each abbreviation in this text."""
    if not text: return text
    done = set(skip)
    def rep(m):
        a = m.group(1); key = a
        poss = m.group(2) or ""
        if key in done: return a + poss
        done.add(key)
        if a.endswith("s") and a[:-1] in GLOSSARY: done.add(a[:-1])
        elif a + "s" in GLOSSARY: done.add(a + "s")
        mean = GLOSSARY[a]
        after = text[m.end():m.end()+2]
        if after.startswith(" (") or mean.split(":")[0].lower() in text.lower(): return a + poss
        return f"{a}{poss} ({mean})"
    return _ABBR_RE.sub(rep, text)

def load(p, default=None):
    p = ROOT / p
    return json.loads(p.read_text()) if p.exists() else default

# key aliases: merge near-duplicate keys the classifiers invented
ALIAS = {"pneumonia":"lower-respiratory-infection","acute-coronary-syndrome":"ischemic-heart-disease","myocardial-infarction":"ischemic-heart-disease",
 "copd-exacerbation":"copd","dka":"diabetes","diabetic-ketoacidosis":"diabetes","hypoglycemia":"diabetes","postpartum-hemorrhage":"maternal-hemorrhage",
 "pph":"maternal-hemorrhage","eclampsia":"preeclampsia-eclampsia","preeclampsia":"preeclampsia-eclampsia","septic-shock":"sepsis","hiv":"hiv-aids",
 "tb":"tuberculosis","substance-use-disorder":"opioid-use-disorder","alcohol-use-disorder":"substance-use-alcohol","alcohol-withdrawal":"substance-use-alcohol",
 "suicide":"self-harm-suicide","suicidal-ideation":"self-harm-suicide","dementia":"alzheimer-dementia","child-abuse":"interpersonal-violence",
 "intimate-partner-violence":"interpersonal-violence","neonatal-resuscitation":"neonatal-encephalopathy-asphyxia","birth-asphyxia":"neonatal-encephalopathy-asphyxia",
 "prematurity":"neonatal-preterm-birth","preterm-birth":"neonatal-preterm-birth","dvt":"venous-thromboembolism","appendicitis":"acute-abdomen",
 "atrial-fibrillation":"arrhythmia","smoking-cessation":"tobacco-use","palliative-care":"end-of-life-palliative","end-of-life":"end-of-life-palliative",
 "overdose":"poisoning-overdose","poisoning":"poisoning-overdose","status-epilepticus":"seizure-epilepsy","seizure":"seizure-epilepsy","ptsd":"anxiety",
 "severe-acute-malnutrition":"malnutrition","cholera":"diarrheal-disease","gastroenteritis":"diarrheal-disease","dehydration":"diarrheal-disease",
 "hepatitis-b":"hepatitis","hepatitis-c":"hepatitis","sti":"sexually-transmitted-infection","syphilis":"sexually-transmitted-infection",
 "traumatic-brain-injury":"trauma-general","head-injury":"trauma-general","hemorrhagic-shock":"trauma-general","motor-vehicle-collision":"road-injury",
 "bronchiolitis":"lower-respiratory-infection","hip-fracture":"falls","enteric-fever":"typhoid","rheumatic-fever":"rheumatic-heart-disease",
 "diabetes-mellitus":"diabetes","type-2-diabetes":"diabetes","type-1-diabetes":"diabetes","cardiac-arrest-acls":"cardiac-arrest","chf":"heart-failure",
 "sickle-cell":"sickle-cell-disease","envenomation":"snakebite","neonatal-jaundice":"neonatal-jaundice","epilepsy":"seizure-epilepsy","febrile-seizure":"seizure-epilepsy","psychosis":"schizophrenia-psychosis"}
def canon(k):
    k = (k or "").strip().lower().replace(" ","-").replace("_","-")
    return ALIAS.get(k, k)

burden = load("data/burden.json", {"source_primary":{"name":"pending"},"countries":[]})
for c in burden["countries"]:
    for x in c["conditions"]: x["key"] = canon(x["key"])

# ---- MedEdPORTAL ----
meta = {}
for r in json.loads((ROOT/"data/mededportal_meta.json").read_text()):
    m = re.search(r"\.(\d+)$", r["doi"] or "")
    if m: meta.setdefault(m.group(1), r)
def authors(a):
    if not a: return ""
    last = lambda n: n.split()[-1] if n else ""
    return f"{last(a[0])} et al." if len(a) > 2 else " and ".join(last(x) for x in a)
cases = []; seen = set(); excluded = 0
for f in sorted(glob.glob(str(ROOT/"data/classification/b*.json"))):
    for o in json.loads(pathlib.Path(f).read_text()):
        if not o.get("include"): excluded += 1; continue
        i = str(o["id"]); r = meta.get(i)
        if not r or i in seen: continue
        if re.search(r"out of print|retired", r["title"], re.I): excluded += 1; continue
        seen.add(i)
        doi = r["doi"]
        cases.append({"id":"mep-"+i, "source":"mededportal", "source_id":"mededportal", "title":r["title"], "year":r["year"], "authors":authors(r["authors"]),
          "doi":doi, "url":"https://www.mededportal.org/doi/"+doi, "format":o.get("format"), "sp_ready":o.get("sp_ready"), "n_cases":o.get("n_cases"),
          "diagnoses":o.get("diagnoses") or [], "presentations":o.get("presentations") or [], "conditions":sorted({canon(k) for k in o.get("conditions") or [] if k}),
          "specialty":o.get("specialty"), "learners":o.get("learners"), "brief":o.get("brief",""), "license":"Free for teaching; each publication states its license (most are Creative Commons)"})

# umbrella keys: a case tagged with a child also counts for the parent
GROUP = {"maternal-conditions": ["maternal-hemorrhage","preeclampsia-eclampsia","ectopic-pregnancy","shoulder-dystocia","obstructed-labor","maternal-sepsis","pregnancy-prenatal-care","precipitous-delivery","miscarriage"],
         "poisoning-overdose": ["pesticide-poisoning"]}
# related keys: shown under the condition as related cases, not counted as coverage
RELATED = {"road-injury":["trauma-general"],"hypertensive-heart-disease":["hypertension","heart-failure"],"liver-cancer":["cirrhosis-liver-disease","hepatitis"],
 "falls":["trauma-general"],"interpersonal-violence":["trauma-general"],"chronic-kidney-disease":["acute-kidney-injury"],"neonatal-preterm-birth":["neonatal-encephalopathy-asphyxia","neonatal-sepsis"],
 "neonatal-sepsis":["pediatric-fever","sepsis"],"malaria":["pediatric-fever"],"dengue":["pediatric-fever"],"typhoid":["pediatric-fever"],"hypertension":["hypertensive-heart-disease"],
 "stroke":["hypertension"],"cervical-cancer":["sexually-transmitted-infection"],"self-harm-suicide":["depression"],"opioid-use-disorder":["poisoning-overdose"],
 "diarrheal-disease":["malnutrition"],"malnutrition":["diarrheal-disease"],"copd":["tobacco-use"],"lung-cancer":["tobacco-use","cancer-other"],"hepatitis":["cirrhosis-liver-disease"]}

# ---- alternative sources ----
alt_sources = load("data/alt_sources.json", [])
alt_cases = load("data/alt_cases.json", [])
for a in alt_cases:
    a["source"] = a.get("source_id") or "other"
    a["conditions"] = sorted({canon(k) for k in a.get("conditions") or [] if k})
    a.setdefault("diagnoses", [])
    a.setdefault("learners", a.get("learner"))
    a["id"] = "alt-" + a["id"]
    cases.append(a)
sources = [{"id":"mededportal","name":"MedEdPORTAL","publisher":"Association of American Medical Colleges (AAMC)","url":"https://www.mededportal.org",
  "type":"journal","access":"open","license":"CC BY-NC-SA 4.0 or CC BY (per publication)","sp_ready":"yes",
  "trust_note":"Peer-reviewed, PubMed-indexed open-access journal of teaching materials. Each publication ships the facilitator guide, SP case and checklists.",
  "brief":"The largest free, peer-reviewed library of standardized patient cases, OSCE stations and simulation scenarios. Written mostly for US programs.","best_for":[]}] + alt_sources

# ---- plain-language expansion of abbreviations (not applied to official titles) ----
for c in cases:
    c["brief"] = expand(c.get("brief", ""))
    c["diagnoses"] = [expand(d) for d in c.get("diagnoses", [])]
    if c.get("learners"): c["learners"] = expand(c["learners"])
for co in burden["countries"]:
    co["source_note"] = expand(co.get("source_note", ""))
    for x in co["conditions"]:
        x["why"] = expand(x["why"], skip={"DALYs", "DALY"})
        if x["name"] in ("HIV/AIDS",) or x["name"].startswith("HIV"): x["name"] = expand(x["name"])
for s_ in sources:
    for f in ("brief", "trust_note", "authority", "used_for"):
        if s_.get(f): s_[f] = expand(s_[f])

# ---- conditions ----
for c in cases:
    for parent, kids in GROUP.items():
        if set(kids) & set(c["conditions"]): c["conditions"] = sorted(set(c["conditions"]) | {parent})
used = {k for c in cases for k in c["conditions"]} | {x["key"] for c in burden["countries"] for x in c["conditions"]}
conds = []
for k in sorted(used):
    name, syn = CONDITIONS.get(k, (k.replace("-"," ").capitalize(), []))
    names_from_burden = [x["name"] for c in burden["countries"] for x in c["conditions"] if x["key"]==k and x["name"]!=name]
    extra = sorted({d for c in cases if k in c["conditions"] for d in c.get("diagnoses",[]) if len(d) < 40})[:25]
    syn = list(dict.fromkeys(syn + names_from_burden + [e for e in extra if e.lower()!=name.lower()]))
    conds.append({"key":k, "name":name, "synonyms":syn, "related":RELATED.get(k, []), "includes":GROUP.get(k, [])})
gap_notes = load("data/gap_notes.json", {})
for c in conds:
    if c["key"] in gap_notes: c["gap_note"] = expand(gap_notes[c["key"]])

about = (ROOT/"about.html").read_text() if (ROOT/"about.html").exists() else "<p>Method notes pending.</p>"
data_sources = load("data/data_sources.json", [])
for s_ in data_sources:
    for f in ("brief", "authority", "used_for"): s_[f] = expand(s_.get(f, ""))
about = expand(about)
lib_extra = {"data_sources": data_sources, "verification": load("data/verify/summary.json", {})}
lib = {**lib_extra, "built": datetime.date.today().isoformat(), "burden": burden, "conditions": conds, "sources": sources, "cases": cases, "about_html": about,
       "counts": {"mededportal_screened": len(meta), "excluded": excluded}}
(ROOT/"data/library.json").write_text(json.dumps(lib, ensure_ascii=False, indent=1))
html = (ROOT/"template.html").read_text().replace("/*DATA*/", json.dumps(lib, ensure_ascii=False).replace("</", "<\\/"))
(ROOT/"index.html").write_text(html)
print(f"cases {len(cases)} (mep {sum(c['source']=='mededportal' for c in cases)}), sources {len(sources)}, conditions {len(conds)}, html {len(html)//1024} KB")

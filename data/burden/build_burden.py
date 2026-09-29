#!/usr/bin/env python3
"""Build ../../burden.json from the raw WHO pulls in this folder.

Ranked items: WHO Global Health Estimates 2021 (GHE_FULL_DD, all ages, both sexes),
rankable causes only, ordered by DALYs, COVID-19 removed, low-acuity disability-only
causes skipped. Priority items: hand-curated below, each with a verified source.
Re-run: python3 build_burden.py
"""
import csv
import json
import os
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "burden.json"))

API = "https://xmart-api-public.who.int/DEX_CMS/GHE_FULL_DD"
COVID = "395"
# Rankable GHE causes left out of the "serious conditions" list (mostly disability-only, low acuity).
SKIP = {
    "1380": "back and neck pain",
    "1080": "hearing loss",
    "1330": "skin diseases",
    "1050": "refractive errors",
    "1470": "oral conditions",
    "1320": "gynecological diseases",
    "990": "migraine",
    "880": "anxiety disorders",
}
N_RANKED = 10

# GHE cause code -> (canonical key, clinician-facing name)
CAUSES = {
    "1130": ("ischemic-heart-disease", "Ischemic heart disease"),
    "1140": ("stroke", "Stroke"),
    "680": ("lung-cancer", "Lung cancer"),
    "800": ("diabetes", "Diabetes mellitus"),
    "830": ("depression", "Depressive disorders"),
    "390": ("lower-respiratory-infection", "Pneumonia and other lower respiratory infections"),
    "1530": ("road-injury", "Road traffic injury"),
    "1120": ("hypertensive-heart-disease", "Hypertensive heart disease"),
    "700": ("breast-cancer", "Breast cancer"),
    "1180": ("copd", "Chronic obstructive pulmonary disease (COPD)"),
    "100": ("hiv-aids", "HIV/AIDS"),
    "30": ("tuberculosis", "Tuberculosis"),
    "500": ("neonatal-preterm-birth", "Preterm birth complications"),
    "110": ("diarrheal-disease", "Diarrheal disease"),
    "1400": ("congenital-anomalies", "Congenital anomalies"),
    "510": ("neonatal-encephalopathy-asphyxia", "Birth asphyxia and birth trauma"),
    "1620": ("interpersonal-violence", "Interpersonal violence (assault and homicide)"),
    "580": ("anemia", "Iron-deficiency anemia"),
    "1550": ("falls", "Falls"),
    "1270": ("chronic-kidney-disease", "Chronic kidney disease"),
    "1230": ("cirrhosis-liver-disease", "Cirrhosis of the liver"),
    "660": ("liver-cancer", "Liver cancer"),
    "1610": ("self-harm-suicide", "Self-harm and suicide"),
    "220": ("malaria", "Malaria"),
    "950": ("alzheimer-dementia", "Alzheimer disease and other dementias"),
    "870": ("opioid-use-disorder", "Drug use disorders (mainly opioid use disorder)"),
    "550": ("malnutrition", "Protein-energy malnutrition"),
}

COUNTRIES = [
    ("ARM", "Armenia", "\U0001F1E6\U0001F1F2", "Europe and Central Asia", "051"),
    ("BWA", "Botswana", "\U0001F1E7\U0001F1FC", "Sub-Saharan Africa", "072"),
    ("DOM", "Dominican Republic", "\U0001F1E9\U0001F1F4", "Latin America and Caribbean", "214"),
    ("IND", "India", "\U0001F1EE\U0001F1F3", "South Asia", "356"),
    ("JAM", "Jamaica", "\U0001F1EF\U0001F1F2", "Latin America and Caribbean", "388"),
    ("PHL", "Philippines", "\U0001F1F5\U0001F1ED", "Southeast Asia", "608"),
    ("THA", "Thailand", "\U0001F1F9\U0001F1ED", "Southeast Asia", "764"),
    ("UGA", "Uganda", "\U0001F1FA\U0001F1EC", "Sub-Saharan Africa", "800"),
    ("VNM", "Vietnam", "\U0001F1FB\U0001F1F3", "Southeast Asia", "704"),
    ("ZWE", "Zimbabwe", "\U0001F1FF\U0001F1FC", "Sub-Saharan Africa", "716"),
    ("USA", "United States (including Puerto Rico)", "\U0001F1FA\U0001F1F8", "North America", "840"),
]

# Source URLs for supplementary WHO series
URL_TB = "https://www.who.int/teams/global-programme-on-tuberculosis-and-lung-health/data"
URL_MALARIA = "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/estimated-number-of-malaria-cases"
URL_HIV = "https://www.who.int/data/gho/data/themes/hiv-aids"
URL_MMR = "https://www.who.int/data/gho/data/indicators/indicator-details/GHO/maternal-mortality-ratio-(per-100-000-live-births)"
# Indicator group page: lists both the prevalence and the controlled-hypertension indicators.
# (The old per-indicator "...-age-standardized" URL returns 404.)
URL_HTN = "https://www.who.int/data/gho/data/themes/topics/indicator-groups/indicator-group-details/GHO/blood-pressure"


def cap(t):
    return t[:1].upper() + t[1:]


def whole(v):
    """GHO display value like '1 500 000 [1 400 000 - 1 700 000]' -> '1,500,000'."""
    return v.split(" [")[0].replace(" ", ",")


def ordinal(n):
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def fmt(x):
    return f"{round(x):,}"


def api_url(iso3):
    q = (f"DIM_COUNTRY_CODE eq '{iso3}' and DIM_YEAR_CODE eq '2021' "
         f"and DIM_AGEGROUP_CODE eq 'ALLAges' and DIM_SEX_CODE eq 'BTSX'")
    return API + "?$filter=" + urllib.parse.quote(q)


def load_tb():
    rows = list(csv.DictReader(open(os.path.join(HERE, "who_tb_estimates.csv"), encoding="utf-8-sig")))
    year = max(r["year"] for r in rows)
    cur = [r for r in rows if r["year"] == year]
    by = {r["iso3"]: r for r in cur}
    # Denominator is WHO's published global estimate (GHO TB_e_inc_num, GLOBAL), not the sum of
    # country rows: the country file has a blank e_inc_num for PRK, so the sum runs about 1.4% low.
    glob = json.load(open(os.path.join(HERE, "gho_TB_e_inc_num_global.json")))["value"]
    total = [r["NumericValue"] for r in glob if str(r["TimeDim"]) == year][0]
    return year, total, by


def gho_latest(name, iso3):
    d = json.load(open(os.path.join(HERE, name)))["value"]
    rs = [r for r in d if r["SpatialDim"] == iso3 and r.get("Dim1") in (None, "SEX_BTSX")]
    rs.sort(key=lambda r: r["TimeDim"])
    return rs[-1] if rs else None


TB_YEAR, TB_TOTAL, TB = load_tb()


def tb_fact(iso3):
    r = TB[iso3]
    share = 100 * float(r["e_inc_num"]) / TB_TOTAL
    s = f"WHO estimates {r['e_inc_100k']} new TB cases per 100,000 in {TB_YEAR}"
    if share >= 1:
        s += f" ({share:.1f}% of the global total)"
    if float(r["e_tbhiv_prct"] or 0) >= 20:
        s += f", {r['e_tbhiv_prct']}% of them in people with HIV"
    return s


def hiv_fact(iso3):
    plhiv = gho_latest("gho_HIV_0000000001.json", iso3)
    art = gho_latest("gho_HIV_ARTCOVERAGE.json", iso3)
    return (f"about {whole(plhiv['Value'])} people living with HIV in {plhiv['TimeDim']}, "
            f"{whole(art['Value'])}% on antiretroviral therapy (WHO/UNAIDS estimates)")


def mal_fact(iso3):
    d = json.load(open(os.path.join(HERE, "gho_malaria_est_cases.json")))["value"]
    y = max(r["TimeDim"] for r in d)
    glob = [r for r in d if r["TimeDim"] == y and r["SpatialDimType"] == "GLOBAL"][0]["NumericValue"]
    c = [r for r in d if r["TimeDim"] == y and r["SpatialDim"] == iso3][0]["NumericValue"]
    return f"an estimated {c/1e6:.1f} million malaria cases in {y}, {100*c/glob:.1f}% of the global total (WHO World Malaria Report estimates)"


def htn_fact(iso3):
    p = gho_latest("gho_NCD_HYP_PREVALENCE_A.json", iso3)
    c = gho_latest("gho_NCD_HYP_CONTROL_A.json", iso3)
    return (f"{p['Value'].split(' [')[0]}% of adults aged 30 to 79 have hypertension and only "
            f"{c['Value'].split(' [')[0]}% have it controlled ({p['TimeDim']}, WHO age-standardized estimate)")


def mmr_fact(iso3):
    r = gho_latest("gho_mmr.json", iso3)
    return f"maternal mortality ratio of {r['Value'].split(' [')[0]} per 100,000 live births in {r['TimeDim']} (WHO/UN MMEIG)"


# Extra country-specific facts appended to ranked items: (iso3, cause) -> text
EXTRA = {
    ("UGA", "220"): lambda: mal_fact("UGA"),
    ("IND", "30"): lambda: tb_fact("IND"),
    ("PHL", "30"): lambda: tb_fact("PHL"),
    ("BWA", "30"): lambda: tb_fact("BWA"),
    ("ZWE", "30"): lambda: tb_fact("ZWE"),
    ("UGA", "30"): lambda: tb_fact("UGA"),
    ("BWA", "100"): lambda: hiv_fact("BWA"),
    ("ZWE", "100"): lambda: hiv_fact("ZWE"),
    ("UGA", "100"): lambda: hiv_fact("UGA"),
    ("JAM", "100"): lambda: hiv_fact("JAM"),
    ("DOM", "100"): lambda: hiv_fact("DOM"),
    ("THA", "100"): lambda: hiv_fact("THA"),
}
EXTRA_URL = {"220": URL_MALARIA, "30": URL_TB, "100": URL_HIV}

# Priority items (kind = priority). Every number here was read from the cited source.
# Fact-checked 2026-09-29 against each live source (results: ../../verify/burden_claims.json).
# The THA/VNM "high TB burden" phrase rests on the WHO list document, not on URL_TB:
# https://iris.who.int/server/api/core/bitstreams/69a887d5-9f87-474a-b3ea-3b4f78a504e6/content
# "Strongly linked to HIV" (cervical cancer) rests on the WHO cervical cancer fact sheet
# (women with HIV are 6 times more likely to develop it), not on the GLOBOCAN fact sheet.
PRIORITY = {
    "ARM": [
        dict(key="hypertension", name="Hypertension",
             why=lambda: cap(htn_fact("ARM")) + "; hypertensive heart disease is already the 8th item above",
             source_url=URL_HTN),
    ],
    "BWA": [
        dict(key="cervical-cancer", name="Cervical cancer",
             why=lambda: "Most common cancer and leading cause of cancer death: 502 new cases (17.3% of all cancers) and 331 deaths in 2024 (IARC GLOBOCAN), strongly linked to HIV",
             source_url="https://gco.iarc.who.int/media/globocan/factsheets/populations/72-botswana-fact-sheet.pdf"),
        dict(key="maternal-conditions", name="Maternal complications of pregnancy and childbirth",
             why=lambda: cap(mmr_fact("BWA")),
             source_url=URL_MMR),
        dict(key="hypertension", name="Hypertension",
             why=lambda: cap(htn_fact("BWA")),
             source_url=URL_HTN),
    ],
    "DOM": [
        dict(key="dengue", name="Dengue",
             why=lambda: "9,153 suspected cases in epidemiological weeks 1 to 34 of 2024 (83 per 100,000), 65 severe and 9 deaths (PAHO); WHO GHE ranks dengue only 101st by DALYs",
             source_url="https://www.paho.org/sites/default/files/2024-10/2024-oct-07-phe-epi-alert-dengue-final.pdf"),
        dict(key="maternal-conditions", name="Maternal complications of pregnancy and childbirth",
             why=lambda: cap(mmr_fact("DOM")),
             source_url=URL_MMR),
        dict(key="hypertension", name="Hypertension",
             why=lambda: cap(htn_fact("DOM")),
             source_url=URL_HTN),
    ],
    "IND": [
        dict(key="snakebite", name="Snakebite envenoming",
             why=lambda: "About 58,000 snakebite deaths per year (1.2 million from 2000 to 2019), mostly in low-lying farming areas and during the rainy season (Million Death Study, reported by WHO)",
             source_url="https://www.who.int/news/item/10-07-2020-study-estimates-more-than-one-million-indians-died-from-snakebite-envenoming-over-past-two-decades"),
        dict(key="hypertension", name="Hypertension",
             why=lambda: cap(htn_fact("IND")),
             source_url=URL_HTN),
    ],
    "JAM": [
        dict(key="sickle-cell-disease", name="Sickle cell disease",
             why=lambda: "Newborn screening of 66,833 babies found sickle cell syndromes in 407 (about 1 in 164 births) and sickle cell trait in 9.8% (Serjeant et al., J Community Genet 2017, with the Ministry of Health)",
             source_url="https://pubmed.ncbi.nlm.nih.gov/27796853/"),
        dict(key="prostate-cancer", name="Prostate cancer",
             why=lambda: "Most common cancer and leading cause of cancer death: 1,394 new cases (18.5% of all cancers) and 809 deaths in 2024 (IARC GLOBOCAN)",
             source_url="https://gco.iarc.who.int/media/globocan/factsheets/populations/388-jamaica-fact-sheet.pdf"),
        dict(key="hypertension", name="Hypertension",
             why=lambda: cap(htn_fact("JAM")),
             source_url=URL_HTN),
    ],
    "PHL": [
        dict(key="dengue", name="Dengue",
             why=lambda: "167,355 cases and 575 deaths reported from 1 January to 7 December 2023 (WHO Disease Outbreak News); WHO GHE ranks dengue only 59th by DALYs",
             source_url="https://www.who.int/emergencies/disease-outbreak-news/item/2023-DON498"),
        dict(key="hiv-aids", name="HIV/AIDS",
             why=lambda: "New HIV infections rose more than sixfold, from about 4,600 in 2010 to 30,000 in 2024, and only 40% of people with HIV were on treatment in 2024 (WHO/UNAIDS estimates)",
             source_url=URL_HIV),
    ],
    "THA": [
        dict(key="tuberculosis", name="Tuberculosis",
             why=lambda: tb_fact("THA") + "; Thailand is on the WHO 2021 to 2025 list of 30 high TB burden countries",
             source_url=URL_TB),
        dict(key="dengue", name="Dengue",
             why=lambda: "136,655 cases and 147 deaths in 2023 (to 22 November), up from 46,678 cases in 2022 (WHO Disease Outbreak News)",
             source_url="https://www.who.int/emergencies/disease-outbreak-news/item/2023-DON498"),
    ],
    "UGA": [
        dict(key="sickle-cell-disease", name="Sickle cell disease",
             why=lambda: "National survey of 97,631 HIV-exposed infants found sickle cell trait in 13.3% and sickle cell disease in 0.7%, up to 1.5% in East Central region (Uganda Sickle Surveillance Study, with the Ministry of Health)",
             source_url="https://pubmed.ncbi.nlm.nih.gov/26833239/"),
        dict(key="maternal-conditions", name="Maternal complications of pregnancy and childbirth",
             why=lambda: cap(mmr_fact("UGA")),
             source_url=URL_MMR),
        dict(key="hypertension", name="Hypertension",
             why=lambda: cap(htn_fact("UGA")),
             source_url=URL_HTN),
    ],
    "VNM": [
        dict(key="tuberculosis", name="Tuberculosis",
             why=lambda: tb_fact("VNM") + "; Viet Nam is on the WHO 2021 to 2025 list of 30 high TB burden countries",
             source_url=URL_TB),
        dict(key="dengue", name="Dengue",
             why=lambda: "149,557 cases and 36 deaths reported from 1 January to 7 December 2023 (WHO Disease Outbreak News)",
             source_url="https://www.who.int/emergencies/disease-outbreak-news/item/2023-DON498"),
        dict(key="hepatitis", name="Chronic hepatitis B (and C)",
             why=lambda: "More than 7 million people live with hepatitis B or C (1 in 15), and these viruses cause 90% of liver cancer, the leading cause of cancer death (WHO Western Pacific, 2025)",
             source_url="https://www.who.int/westernpacific/newsroom/feature-stories/item/don-t-wait-for-symptoms---get-checked-for-hepatitis--say-liver-cancer-patient-and-experts-in-viet-nam-ahead-of-world-hepatitis-day"),
    ],
    "ZWE": [
        dict(key="maternal-conditions", name="Maternal complications of pregnancy and childbirth",
             why=lambda: cap(mmr_fact("ZWE")),
             source_url=URL_MMR),
        dict(key="cervical-cancer", name="Cervical cancer",
             why=lambda: "Most common cancer and leading cause of cancer death: 5,194 new cases (20.7% of all cancers) and 3,118 deaths in 2024 (IARC GLOBOCAN), strongly linked to HIV",
             source_url="https://gco.iarc.who.int/media/globocan/factsheets/populations/716-zimbabwe-fact-sheet.pdf"),
        dict(key="malaria", name="Malaria",
             why=lambda: "An estimated 148,833 malaria cases in 2024 (WHO World Malaria Report estimates)",
             source_url=URL_MALARIA),
    ],
    "USA": [
        dict(key="dengue", name="Dengue (Puerto Rico)",
             why=lambda: "Puerto Rico declared a dengue public health emergency in March 2024: 6,291 confirmed cases that year, 52.3% hospitalized, 264 severe, 11 deaths (CDC MMWR 2025)",
             source_url="https://www.cdc.gov/mmwr/volumes/74/wr/mm7405a1.htm"),
        dict(key="self-harm-suicide", name="Self-harm and suicide",
             why=lambda: "48,824 suicide deaths in 2024 (CDC NCHS); 13th leading cause of DALYs in WHO GHE 2021",
             source_url="https://www.cdc.gov/nchs/fastats/suicide.htm"),
    ],
}

COUNTRY_NOTES = {
    "USA": "WHO GHE covers the 50 states only; Puerto Rico is not a WHO member state and has no separate GHE estimate, so Puerto Rico appears through the CDC-sourced dengue priority item.",
    "UGA": "US3 measured 0.7% disease prevalence; the study background notes an older, commonly cited figure of 20,000 babies per year born with sickle cell disease that lacked accurate data.",
}


def build_country(iso3, name, flag, region, num):
    rows = json.load(open(os.path.join(HERE, f"who_ghe_{iso3}.json")))["value"]
    rank = [r for r in rows if r["FLAG_RANKABLE"] == 1 and r["DIM_GHECAUSE_CODE"] != COVID]
    by_daly = sorted(rank, key=lambda r: -r["VAL_DALY_COUNT_NUMERIC"])
    by_death = sorted(rank, key=lambda r: -r["VAL_DTHS_COUNT_NUMERIC"])
    daly_rank = {r["DIM_GHECAUSE_CODE"]: i + 1 for i, r in enumerate(by_daly)}
    death_rank = {r["DIM_GHECAUSE_CODE"]: i + 1 for i, r in enumerate(by_death)}
    covid = [r for r in rows if r["DIM_GHECAUSE_CODE"] == COVID][0]

    conditions, skipped = [], []
    for r in by_daly:
        code = r["DIM_GHECAUSE_CODE"]
        if code in SKIP:
            if daly_rank[code] <= 12:
                skipped.append(f"{SKIP[code]} (#{daly_rank[code]})")
            continue
        if len(conditions) == N_RANKED:
            break
        key, cname = CAUSES[code]
        why = (f"{ordinal(daly_rank[code])} leading cause of DALYs in 2021 "
               f"({fmt(r['VAL_DALY_RATE100K_NUMERIC'])} per 100,000; {r['VAL_PROP_DALY_PERCENT']:.1f}% of all DALYs)")
        dr = death_rank[code]
        if r["VAL_DTHS_COUNT_NUMERIC"] > 0:
            why += f"; {ordinal(dr)} cause of death"
        extra = EXTRA.get((iso3, code))
        if extra:
            why += "; " + extra()
        conditions.append(dict(rank=len(conditions) + 1, key=key, name=cname, kind="ranked",
                               why=why, source_url=api_url(iso3),
                               _code=code))
    ranked_keys = {c["key"] for c in conditions}
    for p in PRIORITY.get(iso3, []):
        if p["key"] in ranked_keys:
            raise SystemExit(f"{iso3}: priority {p['key']} duplicates a ranked item")
        conditions.append(dict(rank=len(conditions) + 1, key=p["key"], name=p["name"], kind="priority",
                               why=p["why"](), source_url=p["source_url"]))
    for c in conditions:
        c.pop("_code", None)

    covid_rank = 1 + sum(1 for r in rank if r["VAL_DALY_COUNT_NUMERIC"] > covid["VAL_DALY_COUNT_NUMERIC"])
    note = (f"WHO GHE 2021, all ages, both sexes. COVID-19 removed from ranking "
            f"(it would have been #{covid_rank} by DALYs, {covid['VAL_PROP_DALY_PERCENT']:.1f}% of all DALYs). ")
    if skipped:
        note += "Skipped as low-acuity, disability-only causes: " + ", ".join(skipped) + ". "
    note += "Ranks in 'why' are WHO ranks among rankable causes with COVID-19 removed; 'rank' is list position."
    if iso3 in COUNTRY_NOTES:
        note += " " + COUNTRY_NOTES[iso3]
    n = len(conditions)
    assert 8 <= n <= 13, (iso3, n)
    return dict(iso3=iso3, name=name, flag=flag, region=region,
                source_url=f"https://data.who.int/countries/{num}",
                source_note=note, conditions=conditions)


def main():
    out = dict(
        source_primary=dict(
            name="WHO Global Health Estimates 2021: disease burden (DALYs) by cause and country",
            year=2021,
            url="https://www.who.int/data/global-health-estimates",
            metric="DALYs",
            notes=("Pulled from the WHO public API (" + API + "), all ages, both sexes, "
                   "the same data behind data.who.int country pages. Ranked items are WHO 'rankable' causes "
                   "ordered by total DALYs. COVID-19 is excluded as a ranked item because 2021 is "
                   "pandemic-distorted. Low-acuity, disability-only causes (back and neck pain, hearing loss, "
                   "skin diseases, refractive errors, oral conditions, gynecological diseases, migraine, anxiety) "
                   "are skipped so the list holds serious conditions; depression and self-harm are kept. "
                   "Priority items come from WHO TB, malaria, HIV, hypertension and maternal mortality series "
                   "(WHO GHO API and the WHO Global TB Programme estimates), IARC GLOBOCAN, PAHO, CDC and "
                   "national surveys; each carries its own source_url. Known conflict: WHO GHE assigns dengue "
                   "very few DALYs (rank 59 or lower in PHL, VNM, THA, DOM), while national surveillance shows "
                   "very large case and hospital loads, so dengue is added as a priority item where surveillance "
                   "supports it. Supplementary series use later years (TB 2024, malaria 2024, HIV 2025 (Philippines trend to 2024), maternal "
                   "mortality 2023, hypertension 2019) than GHE 2021. IHME GBD 2021 was not used; its cause list "
                   "and methods differ, so ranks can differ from these. Ranked items whose 'why' adds a TB, HIV or "
                   "malaria figure draw it from " + URL_TB + ", " + URL_HIV + " and " + URL_MALARIA + "."),
        ),
        countries=[build_country(*c) for c in COUNTRIES],
    )
    text = json.dumps(out, ensure_ascii=False, indent=2)
    for bad in ("–", "—"):
        assert bad not in text, "dash found"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()

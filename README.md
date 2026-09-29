# Global Casebook

**Open the library: https://igembitsky.github.io/global-casebook/**

A free, searchable library of practice patient cases for standardized patient (SP) encounters, OSCEs (Objective Structured Clinical Examinations) and simulation. Each case is matched to the conditions with the highest disease burden in the eleven partner countries of the [Majid Sadigh MD Global Health Academy](https://www.theglobalhealthacademy.org): Armenia, Botswana, Dominican Republic, India, Jamaica, Philippines, Thailand, Uganda, Vietnam, Zimbabwe and the United States (including Puerto Rico).

- 1,422 cases: 1,124 from MedEdPORTAL and 298 from 65 other free sources (WHO training courses, simulation journals, open-access case reports and others).
- Search by condition, browse by country, or see where cases are missing.
- Every link, title and figure was checked on 29 September 2026. The Sources tab in the page shows how.

Built for the 5th Annual Global Health Conference, Southbury, Connecticut, September 2026.

## How it is built

| File | What it is |
|---|---|
| `index.html` | The library. One self-contained file. Open it in any browser, online or offline. |
| `build.py` | Merges the data and writes `index.html` from `template.html`. Run `python3 build.py`. |
| `data/burden.json` | Top conditions per country: WHO Global Health Estimates 2021 by DALYs (disability-adjusted life years), plus sourced local priorities. |
| `data/mededportal_meta.json` | Title, year and authors of every MedEdPORTAL publication (from OpenAlex). |
| `data/classification/` | For each MedEdPORTAL publication: kept or not, format, conditions and a short summary. The rules are in `CLASSIFY.md`. |
| `data/alt_sources.json`, `data/alt_cases.json` | The other trusted sources and their cases. |
| `data/data_sources.json` | Every data source, why it is authoritative, and what it was used for. |
| `data/conditions.py`, `data/glossary.py` | Condition names and search synonyms, and plain meanings of abbreviations. |
| `data/verify/` | The results of every check: DOIs, titles, links, live WHO data, and source documents. |
| `verify_links.py`, `verify_summary.py` | The link check and the verification summary. |
| `data/burden/build_burden.py` | The script that built `burden.json` from the WHO data. It needs the raw WHO downloads, which are not stored here. |

## Add or correct a case

Open an issue with the case title, a link, the license and the conditions it teaches. Or edit `data/alt_cases.json`, run `python3 build.py`, and send a pull request.

## Licenses

- The code is under the MIT License (see `LICENSE`).
- The summaries, condition tags and burden notes written for this library are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- The cases belong to their authors and publishers. This library links to them and does not copy them. Use each case under the license its publisher gives, and credit the authors.
- WHO data is used under the WHO terms of use, with credit to WHO.

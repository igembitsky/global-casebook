# Classify MedEdPORTAL publications for a standardized patient case library

Input: a JSON array of MedEdPORTAL publications: {id, doi, year, title, abstract}.
Goal: decide which publications contain a usable CLINICAL PATIENT CASE that an educator can run as a standardized patient (SP) encounter, OSCE station, role-play, or simulation scenario, and describe each one.

## Include (include: true) when the publication provides at least one patient case with a clinical problem, for example:
- SP cases, OSCE stations, simulated patient encounters, role-plays with a patient.
- Mannequin or high-fidelity simulation scenarios about a patient with a condition (these can be adapted for SPs).
- Virtual patient cases and structured case-based sessions that give a full patient story (history, exam, workup).
- Communication cases (breaking bad news, goals of care, disclosure) when a patient with a clinical condition is portrayed. Also include pure communication or counseling SP cases with no disease (e.g. interpreter use, tobacco counseling, sexual history) and set conditions to the best topic key or [].

## Exclude (include: false) when there is no patient case:
- Procedural task-trainer skills only (suturing, laparoscopy box, IV insertion on a pad, ultrasound phantom) with no patient scenario.
- Curricula, lectures, faculty development, assessment tools, surveys, program descriptions, games, with no patient case.
- Give a 3 to 8 word exclude_reason.

## Output fields for every input item (one output object per input item, same order):
```
{"id": "...", "include": true,
 "format": "sp-case|osce-station|role-play|simulation-scenario|virtual-patient|case-based-session",
 "sp_ready": "yes|partial|no",   // yes = SP script or SP case materials provided; partial = mannequin/case scenario an educator could adapt to an SP; no = not practical for an SP
 "n_cases": 1,                   // number of distinct patient cases in the publication, best estimate from abstract
 "diagnoses": ["Acute pericarditis"],  // clinician-facing diagnosis names, specific
 "presentations": ["chest pain"],      // chief complaints
 "conditions": ["ischemic-heart-disease"],  // canonical keys, see list below; map each diagnosis to the closest key(s); may be []
 "specialty": "internal medicine|emergency medicine|pediatrics|obstetrics & gynecology|surgery|psychiatry|family medicine|neurology|geriatrics|palliative care|interprofessional|other",
 "learners": "medical students|residents|nurses|pharmacy|interprofessional|...",
 "brief": "Two plain sentences: who the patient is and what the learner practices. No jargon beyond standard clinical terms.",
 "exclude_reason": ""}
```
For excluded items output only {"id": "...", "include": false, "exclude_reason": "..."}.

## Canonical condition keys (prefer these; add a new lowercase-hyphenated key only when nothing fits, e.g. "pulmonary-embolism", "appendicitis", "anaphylaxis", "trauma-general")
ischemic-heart-disease (includes acute coronary syndrome, MI, angina), stroke (includes TIA), copd, asthma, lower-respiratory-infection (pneumonia, bronchiolitis), tuberculosis, hiv-aids, malaria, diarrheal-disease (includes pediatric dehydration, gastroenteritis), diabetes (includes DKA, hypoglycemia), hypertension, hypertensive-heart-disease, chronic-kidney-disease (includes AKI? no: use acute-kidney-injury), cirrhosis-liver-disease, hepatitis, lung-cancer, breast-cancer, cervical-cancer, colorectal-cancer, stomach-cancer, liver-cancer, prostate-cancer, oral-cancer, neonatal-preterm-birth, neonatal-encephalopathy-asphyxia (includes neonatal resuscitation), neonatal-sepsis, congenital-anomalies, maternal-hemorrhage (postpartum hemorrhage), preeclampsia-eclampsia, road-injury (motor vehicle trauma), falls, interpersonal-violence (intimate partner violence, child abuse, assault), self-harm-suicide, depression, anxiety, substance-use-alcohol, opioid-use-disorder, alzheimer-dementia (includes delirium? no: use delirium), dengue, sickle-cell-disease, malnutrition, anemia, meningitis, sepsis (includes septic shock), heart-failure, rheumatic-heart-disease, snakebite, typhoid, low-back-pain, headache-migraine, sexually-transmitted-infection, contraception-family-planning, pregnancy-prenatal-care, cancer-other, end-of-life-palliative, tobacco-use, obesity, cardiac-arrest, arrhythmia, anaphylaxis, pulmonary-embolism, acute-abdomen, trauma-general, burns, poisoning-overdose, delirium, schizophrenia-psychosis, bipolar-disorder, eating-disorder, thyroid-disease, urinary-tract-infection, acute-kidney-injury, seizure-epilepsy, pediatric-fever, gi-bleeding, pancreatitis, venous-thromboembolism.

## Rules
- Base everything on the title and abstract only. Do not invent details.
- Write the brief in plain English, 2 sentences, max 45 words. No em dashes or en dashes.
- Output a valid JSON array to the output path given in your task. Validate it with python3 -c "import json;json.load(open(PATH))" before finishing. Every input id must appear exactly once.
- Work in chunks (e.g. 40 items at a time, append to a list, write file at end or incrementally). Use python only for reading input and writing output; the judgments are yours.

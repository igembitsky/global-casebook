#!/usr/bin/env python3
"""Open every source and case URL. Record HTTP status and whether the case title appears in the page text."""
import json, re, subprocess, tempfile, urllib.request, concurrent.futures as cf, pathlib, datetime, html as H
ROOT = pathlib.Path(__file__).parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
def load(p, d): p = ROOT/p; return json.loads(p.read_text()) if p.exists() else d
def text_of(body, ctype):
    if b"%PDF" in body[:1024] or "pdf" in ctype:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(body); f.flush()
            try: return subprocess.run(["pdftotext", "-l", "400", f.name, "-"], capture_output=True, timeout=120).stdout.decode("utf-8", "ignore")
            except Exception: return ""
    t = body.decode("utf-8", "ignore")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    return H.unescape(re.sub(r"<[^>]+>", " ", t))
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
STOP = set("a an the of and or for in on with to by case scenario simulation module part session station".split())
def fetch(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"}), timeout=60)
        return r.status, r.read(60_000_000), r.headers.get("Content-Type", ""), r.url
    except urllib.error.HTTPError as e: return e.code, b"", "", url
    except Exception as e: return 0, str(e).encode(), "", url
cache = {}
def check(item):
    url, title = item
    if url not in cache: cache[url] = fetch(url)
    st, body, ct, final = cache[url]
    res = {"url": url, "status": st, "final": final}
    if st == 200 and title:
        words = [w for w in norm(title).split() if len(w) > 3 and w not in STOP][:8]
        page = norm(text_of(body, ct))
        hit = sum(1 for w in words if w in page)
        res["title_words"] = len(words); res["title_hits"] = hit
    return res
if __name__ == "__main__":
    ds = load("data/data_sources.json", []); src = load("data/alt_sources.json", []); cases = load("data/alt_cases.json", [])
    items = [(s["url"], None) for s in ds + src] + [(c["url"], c["title"]) for c in cases]
    # one fetch per URL first, then title checks reuse the cache
    urls = sorted({u for u, _ in items})
    with cf.ThreadPoolExecutor(8) as ex:
        for u, r in zip(urls, ex.map(fetch, urls)): cache[u] = r
    out = [check(i) for i in items]
    (ROOT/"data/verify/links_raw.json").write_text(json.dumps(out, indent=1))
    bad = [o for o in out if o["status"] != 200]
    weak = [o for o in out if o.get("title_words") and o["title_hits"] < max(1, o["title_words"] // 2)]
    print(f"urls {len(urls)} items {len(out)} non200 {len(bad)} weak-title {len(weak)}")
    for o in bad: print("  STATUS", o["status"], o["url"])
    for o in weak: print("  TITLE", o["title_hits"], "/", o["title_words"], o["url"])

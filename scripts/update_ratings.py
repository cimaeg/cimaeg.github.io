"""يحدّث تقييمات IMDb والسينما.كوم لكل الأفلام في data/films.json.
يعمل أسبوعيًا عبر GitHub Actions. إن فشل جلب تقييم فيلم، يُترك تقييمه السابق كما هو."""
import json, re, sys, time, html, urllib.parse
import requests

DATA = "data/films.json"
DEBUG = "--debug" in sys.argv
S = requests.Session()
S.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
})

def get(url):
    for i in range(3):
        try:
            r = S.get(url, timeout=25)
            if r.status_code == 200:
                return r.text
            print(f"  ! {r.status_code} {url}")
        except Exception as e:
            print(f"  ! {e} {url}")
        time.sleep(2 + i * 3)
    return None

def norm(s):
    s = re.sub(r"[ً-ْـ«»\"()]", "", s or "")
    return re.sub(r"\s+", " ", s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")).strip()

# ——— IMDb ———
def imdb_rating(tid):
    page = get(f"https://www.imdb.com/title/{tid}/")
    if not page:
        return None
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            d = json.loads(block)
        except Exception:
            continue
        ar = d.get("aggregateRating") if isinstance(d, dict) else None
        if ar and ar.get("ratingValue"):
            return {"score": round(float(ar["ratingValue"]), 1), "votes": int(ar.get("ratingCount") or 0)}
    if DEBUG:
        print("  imdb: no JSON-LD rating found")
    return None

def imdb_find(f):
    """يبحث عن رقم الفيلم في IMDb بالعنوان الإنجليزي (title_en) والسنة."""
    q = f.get("title_en")
    if not q:
        return None
    url = "https://v3.sg.media-imdb.com/suggestion/x/" + urllib.parse.quote(q.lower()) + ".json"
    page = get(url)
    if not page:
        return None
    for it in json.loads(page).get("d", []):
        if it.get("id", "").startswith("tt") and abs((it.get("y") or 0) - f["year"]) <= 1:
            return it["id"]
    return None

# ——— السينما.كوم ———
def elc_rating(wid):
    page = get(f"https://elcinema.com/work/{wid}/")
    if not page:
        return None
    m = re.search(r'"ratingValue"\s*:\s*"?([\d.]+)', page)
    if not m:
        m = re.search(r'class="[^"]*legend[^"]*"[^>]*>\s*([\d.]+)\s*<', page)
    if not m:
        m = re.search(r'<span[^>]*>\s*(\d\.\d|10)\s*</span>\s*</div>\s*<div[^>]*>\s*(?:[^<]*)?(?:التقييم|Rating)', page)
    if DEBUG and not m:
        i = page.find("rating")
        print("  elc snippet:", re.sub(r"\s+", " ", page[max(0, i - 600): i + 600]))
    return {"score": round(float(m.group(1)), 1)} if m else None

def elc_find(f):
    """يبحث في السينما.كوم بالعنوان العربي، ويختار العمل الذي تطابق سنته سنة الفيلم."""
    page = get("https://elcinema.com/search/?s=" + urllib.parse.quote(f["title"]))
    if not page:
        return None
    want = norm(f["title"])
    hits = []
    for m in re.finditer(r'href="/(?:en/)?work/(\d+)/?"[^>]*>(.*?)</a>', page, re.S):
        wid, text = m.group(1), html.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip()
        around = page[m.end(): m.end() + 400]
        y = re.search(r"\b(1[89]\d\d|20\d\d)\b", around)
        hits.append((wid, text, int(y.group(1)) if y else None))
    if DEBUG:
        print("  elc hits:", hits[:6])
    for wid, text, y in hits:
        if y == f["year"] and (norm(text) == want or want in norm(text)):
            return wid
    for wid, text, y in hits:
        if y == f["year"]:
            return wid
    return None

def main():
    films = json.load(open(DATA, encoding="utf-8"))
    changed = 0
    for f in films:
        print(f"• {f['title']} ({f['year']})")
        r = f.setdefault("ratings", {})
        im = r.get("imdb") or {}
        if not im.get("id"):
            tid = imdb_find(f)
            if tid:
                im["id"] = tid
        if im.get("id"):
            got = imdb_rating(im["id"])
            if got:
                im.update(got)
                if not im.get("votes"):
                    im.pop("votes", None)
            r["imdb"] = im
            print("  IMDb:", im)
        el = r.get("elcinema") or {}
        if not el.get("id"):
            wid = elc_find(f)
            if wid:
                el["id"] = wid
        if el.get("id"):
            got = elc_rating(el["id"])
            if got:
                el.update(got)
            if el.get("score"):
                r["elcinema"] = el
            print("  elCinema:", el)
        time.sleep(1)
    with open(DATA, encoding="utf-8") as fp:
        before = fp.read()
    after = "[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in films) + "\n]\n"
    if after != before:
        open(DATA, "w", encoding="utf-8").write(after)
        print("updated")
    else:
        print("no changes")

if __name__ == "__main__":
    main()

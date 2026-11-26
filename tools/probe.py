import requests, re
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "ar,en;q=0.8"})
def get(u):
    r = S.get(u, timeout=30); t = r.text
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>|<head>.*?</head>", "", t, flags=re.S)
    return r.status_code, r.url, re.sub(r"\s+", " ", t)
for u in ["https://elcinema.com/index/work/release_year/1946/",
          "https://elcinema.com/index/work/release_year/1946/?page=2",
          "https://elcinema.com/index/work/country/eg/?year=1946",
          "https://elcinema.com/index/work/country/eg/1946/",
          "https://elcinema.com/index/work/category/1/country/eg/release_year/1946/",
          "https://elcinema.com/en/index/work/release_year/1946/"]:
    try:
        c, url, t = get(u)
    except Exception as e:
        print("ERR", u, e); continue
    works = re.findall(r'href="/(?:en/)?work/(\d+)/"[^>]*>([^<]{2,})<', t)
    pages = sorted(set(re.findall(r'[?&]page=(\d+)', t)), key=int)
    print("\n###", u, c, url, "works:", len(set(w for w, _ in works)), "pages:", pages[-5:])
    print("  sample:", list(dict.fromkeys(works))[:12])
    m = re.search(r'href="/(?:en/)?work/(\d+)/"', t)
    if m:
        i = m.start(); print("  ctx:", t[max(0, i-300): i+1200])
    for k in ["نتيجة", "عدد", "results"]:
        mm = re.search(k, t)
        if mm: print("  [", k, "]", t[max(0, mm.start()-200): mm.end()+200])

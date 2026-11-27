"""يقرأ بلد الإنتاج وطاقم التمثيل من صفحات السينما.كوم. الناتج للقراءة فقط، لا يُنشر."""
import json, re, sys, time, html, requests
MODE = sys.argv[1] if len(sys.argv) > 1 else "run"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
SKIP = int(sys.argv[3]) if len(sys.argv) > 3 else 0
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36", "Accept-Language": "ar"})
def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
if MODE == "debug":
    for e in sys.argv[2:]:
        t = S.get(f"https://elcinema.com/work/{e}/", timeout=30).text
        for k in ("country", "الدولة", "بلد"):
            for m in re.finditer(k, t):
                print("CTX", e, k, repr(t[max(0, m.start()-200):m.start()+300]))
                break
        c = S.get(f"https://elcinema.com/work/{e}/cast", timeout=30).text
        i = c.find("/person/")
        print("CAST", e, repr(c[max(0, i-1500):i+2500]))
    sys.exit()
films = json.load(open("data/films.json"))
todo = []
for f in films:
    e = ((f.get("ratings") or {}).get("elcinema") or {}).get("id")
    if not e: continue
    if f.get("src") == "elcinema" or (f.get("src") == "wikidata" and len(f.get("cast") or []) <= 2):
        todo.append((f, e))
todo = todo[SKIP:SKIP + N]
for f, e in todo:
    o = {"id": f["id"], "e": e}
    try:
        t = S.get(f"https://elcinema.com/work/{e}/", timeout=30).text
        o["country"] = sorted(set(re.findall(r"/index/work/country/([a-z]{2})", t)))
        if f.get("src") == "wikidata":
            c = S.get(f"https://elcinema.com/work/{e}/cast", timeout=30).text
            seg = c.split("الممثلين", 1)[-1] if "الممثلين" in c else c
            names = []
            for pid, nm in re.findall(r'href="/person/(\d+)/?"[^>]*>([^<]+)</a>', seg):
                nm = clean(nm)
                if nm and nm not in names: names.append(nm)
            o["cast"] = names[:10]
    except Exception as ex:
        o["err"] = str(ex)
    print("META", json.dumps(o, ensure_ascii=False), flush=True)
    time.sleep(0.4)

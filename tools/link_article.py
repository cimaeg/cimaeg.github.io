"""أداة تحرير «الجريدة».
scan  FILE.md          : يعرض الأفلام والأسماء المرشّحة في النص مع ما يشبهها، للتحقق اليدوي قبل الربط
apply FILE.md MAP.json : يربط أول ظهور فقط لكل عبارة في MAP ({"العبارة": "#film-id" أو "#p-الاسم"})
                         ويطبع قائمتي films و people لإضافتهما إلى data/articles.json
"""
import json, re, sys
F = json.load(open("data/films.json", encoding="utf-8"))
nz = lambda s: s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
pn = lambda n: re.sub(r"\s*\(.*?\)", "", n or "").strip()
def people():
    s = {}
    for f in F:
        for n in (f.get("cast") or []) + [f.get("director")]:
            n = pn(n)
            if n: s.setdefault(n, []).append(f["year"])
    return s
def find(text, phrase):
    """مواضع العبارة بحدود كلمات (مع السماح بالسوابق: و ب ل ف ك ال)"""
    t, p = nz(text), nz(phrase)
    return [m.start(1) for m in re.finditer(r"(?:(?<=[\s«\"'(،.:؛\-])|^)(?:[وبلفك]{0,2})(" + re.escape(p) + r")(?=[\s»\"')،.:؛!؟\-]|$)", t)]
def scan(path):
    text = open(path, encoding="utf-8").read()
    by_title = {}
    for f in F: by_title.setdefault(nz(f["title"]), []).append(f)
    quoted = set(nz(q.strip()) for q in re.findall(r"«([^»]{2,60})»", text))
    print("— أفلام —")
    for k, fs in sorted(by_title.items(), key=lambda kv: -len(kv[0])):
        pos = find(text, fs[0]["title"])
        if not pos: continue
        if k not in quoted and len(k.split()) < 2 and len(k) < 8: continue  # كلمة عامة غير مقتبسة: تُهمل
        print(("«مقتبس» " if k in quoted else "         ") + fs[0]["title"], "×", len(pos), "→", " | ".join(f'{f["id"]} ({f["year"]}، {f.get("director") or "؟"}، {"، ".join((f.get("cast") or [])[:2])})' for f in fs))
    for q in quoted - set(by_title):
        print("«مقتبس غير موجود في الأرشيف»", q)
    print("— أسماء —")
    P = people()
    for n, ys in sorted(P.items(), key=lambda kv: -len(kv[0])):
        pos = find(text, n)
        if pos:
            sim = [m for m in P if m != n and (nz(n) in nz(m))]
            print(n, "×", len(pos), f"({len(ys)} فيلمًا، {min(ys)}–{max(ys)})", ("يشبه: " + "، ".join(sim[:5])) if sim else "")
def apply(path, mp):
    text = open(path, encoding="utf-8").read()
    links = json.load(open(mp, encoding="utf-8"))
    taken = []  # مقاطع صارت روابط
    for ph in sorted(links, key=len, reverse=True):
        # لا نربط داخل رابط قائم
        spans = [(m.start(), m.end()) for m in re.finditer(r"\[[^\]]*\]\([^)]*\)", text)]
        ok = [p for p in find(text, ph) if not any(a <= p < b for a, b in spans)]
        if not ok: print("! لم يُعثر على:", ph); continue
        p = ok[0]; L = len(nz(ph))
        text = text[:p] + "[" + text[p:p + L] + "](" + links[ph].replace(" ", "%20") + ")" + text[p + L:]
    open(path, "w", encoding="utf-8").write(text)
    fl = list(dict.fromkeys(v[6:] for v in links.values() if v.startswith("#film-")))
    pl = list(dict.fromkeys(v[3:] for v in links.values() if v.startswith("#p-")))
    print(json.dumps({"films": fl, "people": pl}, ensure_ascii=False))
if __name__ == "__main__":
    {"scan": lambda: scan(sys.argv[2]), "apply": lambda: apply(sys.argv[2], sys.argv[3])}[sys.argv[1]]()

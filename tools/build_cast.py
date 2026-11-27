"""يبني ملفات الطاقم الكامل من ناتج fetch_cast.py.
python3 tools/build_cast.py cast-*.jsonl
- data/cast/<film-id>.json : [[الاسم, الدور], ...] بترتيب السينما.كوم
- data/credits/<n>.json    : {الاسم: [[film-id, الدور], ...]} موزّعة على 32 ملفًا (n = shard(الاسم))
يوحَّد الشخص برقمه في السينما.كوم؛ ويُستعمل الاسم المكتوب في الأرشيف إن طابقه، ويُميَّز المتشابهون بوسم بين قوسين.
"""
import json, re, sys, os, glob, collections
NS = 32
def shard(n):
    h = 0
    for ch in n: h = (h * 31 + ord(ch)) % 1000003
    return h % NS
def key(n):
    n = re.sub(r"\s*\(.*?\)", "", n)
    n = re.sub("[أإآ]", "ا", n).replace("ة", "ه").replace("ى", "ي").replace("ـ", "")
    return re.sub(r"\s+", "", n)
pn = lambda n: re.sub(r"\s*\((?!ممثل|مخرج|[0-9٠-٩])[^)]*\)", "", n or "").strip()
F = json.load(open("data/films.json", encoding="utf-8")); FI = {f["id"]: f for f in F}
recs = {}
for path in sys.argv[1:]:
    for l in open(path, encoding="utf-8"):
        r = json.loads(l)
        if r.get("secs") is not None and r["id"] in FI: recs[r["id"]] = r
# أسماء الأرشيف الحالية
known = collections.Counter(pn(n) for f in F for n in (f.get("cast") or []) + [f.get("director") or ""] if pn(n))
kidx = collections.defaultdict(list)
for n in known: kidx[key(n)].append(n)
# 1) أصوات: رقم الشخص ← اسم في الأرشيف ورد في طاقم الفيلم نفسه
votes = collections.defaultdict(collections.Counter); ename = {}; credits = collections.Counter()
for fid, r in recs.items():
    main = {key(pn(n)): pn(n) for n in FI[fid].get("cast") or []}
    for rows in r["secs"].values():
        for pid, name, role in rows:
            ename.setdefault(pid, name); credits[pid] += 1
            if key(name) in main: votes[pid][main[key(name)]] += 1
# 2) الاسم المعتمد لكل رقم
canon = {}
for pid, name in ename.items():
    if votes[pid]: canon[pid] = votes[pid].most_common(1)[0][0]
    elif len(kidx.get(key(name), [])) == 1: canon[pid] = kidx[key(name)][0]
    else: canon[pid] = re.sub(r"(^|\s)عبد(?=\S)", r"\1عبد ", name.strip())
# 3) أرقام مختلفة بالاسم نفسه: الأكثر ارتباطًا بالأرشيف يبقى بالاسم، والباقون بوسم سنوات نشاطهم
ar = lambda x: str(x).translate(str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩"))
years = collections.defaultdict(list)
for fid, r in recs.items():
    for rows in r["secs"].values():
        for pid, _, _ in rows: years[pid].append(FI[fid]["year"])
byname = collections.defaultdict(list)
for pid, n in canon.items(): byname[n].append(pid)
for n, pids in byname.items():
    if len(pids) < 2: continue
    pids.sort(key=lambda p: (-sum(votes[p].values()), -credits[p]))
    used = set()
    for p in pids[1:]:
        y0, y1 = min(years[p]), max(years[p])
        t = ar(y0) if y0 == y1 else f"{ar(y0)}–{ar(y1)}"
        k = 2
        while t in used: t = f"{t} {ar(k)}"; k += 1
        used.add(t); canon[p] = f"{n} ({t})"
# 4) الكتابة
os.makedirs("data/cast", exist_ok=True); os.makedirs("data/credits", exist_ok=True)
for p in glob.glob("data/cast/*.json") + glob.glob("data/credits/*.json"): os.remove(p)
cred = [dict() for _ in range(NS)]
for fid, r in recs.items():
    rows = [(canon[pid], role) for sec in r["secs"].values() for pid, _, role in sec]
    seen, out = set(), []
    for n, role in rows:
        if n in seen: continue
        seen.add(n); out.append([n, role])
    if not out: continue
    json.dump(out, open(f"data/cast/{fid}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for n, role in out: cred[shard(n)].setdefault(n, []).append([fid, role])
for i, d in enumerate(cred):
    json.dump(d, open(f"data/credits/{i}.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
dups = {n: len(p) for n, p in byname.items() if len(p) > 1}
print("films", len(recs), "people", len(set(canon.values())), "matched", sum(1 for p in canon if canon[p] in known), "dups", len(dups))
print("أمثلة تشابه:", list(dups.items())[:15])
# 5) توحيد أسماء الأبطال في الملف الرئيسي مع الطاقم الكامل (حين يكون الاسم لشخص موسوم)
fixmap = {}
for fid, r in recs.items():
    rows = {key(name): canon[pid] for sec in r["secs"].values() for pid, name, _ in sec}
    for n in FI[fid].get("cast") or []:
        c = rows.get(key(pn(n)))
        if c and c != pn(n) and "(" in c: fixmap[(fid, n)] = c
def rewrite(path, getcast, setcast):
    lines = open(path, encoding="utf-8").read().split("\n"); ch = 0
    for i, l in enumerate(lines):
        if not l.startswith("{"): continue
        o = json.loads(l.rstrip(","))
        c = getcast(o); nc = [fixmap.get((o["id"], n), n) for n in c]
        if nc != c: setcast(o, nc); lines[i] = json.dumps(o, ensure_ascii=False) + ("," if l.endswith(",") else ""); ch += 1
    open(path, "w", encoding="utf-8").write("\n".join(lines)); return ch
print("main-cast fixes", rewrite("data/films.json", lambda o: o.get("cast") or [], lambda o, c: o.__setitem__("cast", c)))
ce = json.load(open("data/cast_extra.json", encoding="utf-8")); n = 0
for fid, c in ce.items():
    nc = [fixmap.get((fid, x), x) for x in c]
    if nc != c: ce[fid] = nc; n += 1
json.dump(ce, open("data/cast_extra.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0); print("extra fixes", n)

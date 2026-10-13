"""把总览页里人工提交的证据（共享库 evup）整理成 events 分支的 manual.json，供证据包流程使用。
用法：python3 tools/manual_export.py <evup 目录> <输出 manual.json>
<evup 目录> 是 ArtifactData list evup 时 out_dir 下的 evup/ 文件夹：每个提交人一份 <uid>.json = {name, m:{id: 条目}}，
所有者的审核结论在 _review.json = {m:{"<uid>:<id>": {status, note}}}。

公开原则（manual.json 在公开仓库里）：
- 所有条目都公开文件指纹（SHA-256）和提交时间，这样每条都能被 OpenTimestamps 存证；
- 只有所有者标为“已采信”的条目才公开标题、时间、地点、来源、链接和说明；
- 提交人的名字、账号、上传文件本身都不公开（文件只存在总览页里）。"""
import hashlib, json, os, sys

src, out = sys.argv[1], sys.argv[2]
rv = {}
p = os.path.join(src, "_review.json")
if os.path.exists(p):
    rv = (json.load(open(p)) or {}).get("m", {})
items = []
for f in sorted(os.listdir(src)) if os.path.isdir(src) else []:
    if not f.endswith(".json") or f.startswith("_"):
        continue
    uid = f[:-5]
    d = json.load(open(os.path.join(src, f)))
    for k, v in (d.get("m") or {}).items():
        st = (rv.get(f"{uid}:{k}") or {}).get("status", "pending")
        if st not in ("pending", "accepted", "rejected"):
            st = "pending"
        # mid 不暴露账号：用账号和条目号的哈希
        mid = hashlib.sha256(f"{uid}:{k}".encode()).hexdigest()[:16]
        it = {"mid": mid, "ev": v.get("ev") or "", "kind": v.get("kind") or "", "sha256": v.get("sha256"),
              "submitted": v.get("t"), "status": st}
        if st == "accepted":
            for x in ("title", "when", "place", "src", "url", "desc", "fname", "mime", "size"):
                if v.get(x) not in (None, ""):
                    it[x] = v[x]
            note = (rv.get(f"{uid}:{k}") or {}).get("note")
            if note:
                it["review_note"] = note
        items.append(it)
items.sort(key=lambda i: (i.get("submitted") or "", i["mid"]))
new = {"items": items}
old = None
if os.path.exists(out):
    try:
        old = json.load(open(out))
    except Exception:
        old = None
if old and old.get("items") == items:
    print("unchanged", len(items))
    sys.exit(0)
new["updated"] = max([i.get("submitted") or "" for i in items] + [""])
json.dump(new, open(out, "w"), ensure_ascii=False, indent=1)
print("changed", len(items))

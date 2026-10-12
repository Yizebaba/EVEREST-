#!/usr/bin/env python3
"""一次性调查：EVEC（珠峰 Pyramid DORIS 信标）在公开数据里最新到哪天。只读 IGN 匿名 FTP。"""
import ftplib, io, json, gzip, re, subprocess, os, datetime as dt, sys
out = {"t": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "sat": {}, "products": {}, "errors": []}
def ftp():
    f = ftplib.FTP("doris.ign.fr", timeout=60); f.login(); return f
def mlsd(f, path):
    try: return [(n, fa) for n, fa in f.mlsd(path) if n not in (".", "..")]
    except Exception:
        return [(n.rsplit("/", 1)[-1], {}) for n in f.nlst(path)]
try:
    f = ftp()
    top = mlsd(f, "/pub/doris/data")
    out["data_dirs"] = sorted(n for n, _ in top)
    for sat in out["data_dirs"]:
        try:
            ys = sorted(n for n, fa in mlsd(f, f"/pub/doris/data/{sat}") if re.fullmatch(r"\d{4}", n))
            if not ys or int(ys[-1]) < 2025: out["sat"][sat] = {"years": ys[-2:]}; continue
            files = sorted(mlsd(f, f"/pub/doris/data/{sat}/{ys[-1]}"), key=lambda x: x[0])
            files = [x for x in files if x[0][0] != "."]
            newest = files[-3:]
            info = {"year": ys[-1], "n_files": len(files), "newest": [(n, fa.get("modify")) for n, fa in newest]}
            # 下载最新一个文件，看头里有没有 EVEC，统计它的观测条数
            name = newest[-1][0]
            buf = io.BytesIO(); f.retrbinary(f"RETR /pub/doris/data/{sat}/{ys[-1]}/{name}", buf.write)
            raw = buf.getvalue(); open("/tmp/x" + name[-2:], "wb").write(raw)
            if name.endswith(".Z"):
                txt = subprocess.run(["uncompress", "-c"], input=raw, capture_output=True).stdout.decode("latin1", "replace")
            elif name.endswith(".gz"):
                txt = gzip.decompress(raw).decode("latin1", "replace")
            else:
                txt = raw.decode("latin1", "replace")
            head, _, body = txt.partition("END OF HEADER")
            st = [l for l in head.splitlines() if "STATION REFERENCE" in l]
            ev = [l for l in st if "EVE" in l]
            info["stations_in_file"] = len(st)
            info["evec_header"] = ev[:2]
            if ev:
                sid = ev[0].split()[0]
                info["evec_obs_lines"] = sum(1 for l in body.splitlines() if l.startswith(sid) or (" " + sid + " ") in l[:12])
            info["first_obs"] = next((l[:40] for l in body.splitlines() if l.startswith(">")), None)
            out["sat"][sat] = info
        except Exception as e:
            out["errors"].append(f"{sat}: {e!r}"[:200])
    for p in ("stcd", "sinex_series"):
        try:
            ents = mlsd(f, f"/pub/doris/products/{p}")
            out["products"][p] = {"entries": sorted(n for n, _ in ents)[:40]}
        except Exception as e:
            out["errors"].append(f"{p}: {e!r}"[:200])
    # STCD：找含 evec 的文件
    try:
        hits = []
        for d, _ in mlsd(f, "/pub/doris/products/stcd"):
            try:
                for n, fa in mlsd(f, f"/pub/doris/products/stcd/{d}"):
                    if "eve" in n.lower(): hits.append((f"{d}/{n}", fa.get("modify"), fa.get("size")))
            except Exception: pass
        out["stcd_eve"] = hits[-20:]
        if hits:
            last = sorted(hits, key=lambda h: h[1] or "")[-1][0]
            buf = io.BytesIO(); f.retrbinary(f"RETR /pub/doris/products/stcd/{last}", buf.write)
            raw = buf.getvalue()
            try: txt = gzip.decompress(raw).decode("latin1")
            except Exception:
                txt = subprocess.run(["uncompress", "-c"], input=raw, capture_output=True).stdout.decode("latin1") or raw.decode("latin1")
            lines = [l for l in txt.splitlines() if l.strip()]
            out["stcd_last_file"] = {"name": last, "head": lines[:6], "tail": lines[-4:]}
    except Exception as e:
        out["errors"].append(f"stcd scan: {e!r}"[:200])
    f.quit()
except Exception as e:
    out["errors"].append(repr(e)[:300])
json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: v for k, v in out.items() if k != "products"}, ensure_ascii=False)[:3000])

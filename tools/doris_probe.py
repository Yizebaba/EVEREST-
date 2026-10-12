#!/usr/bin/env python3
"""一次性调查第 3 步：NRT 目录最新文件多新、里面有没有 EVEC、观测类型。只读 IGN 匿名 FTP。"""
import ftplib, io, json, gzip, re, subprocess, datetime as dt, sys
out = {"t": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "nrt": {}, "errors": []}
f = ftplib.FTP("doris.ign.fr", timeout=60); f.login()
def get(path):
    b = io.BytesIO(); f.retrbinary("RETR " + path, b.write); raw = b.getvalue()
    if path.endswith(".Z"): return subprocess.run(["uncompress", "-c"], input=raw, capture_output=True).stdout.decode("latin1", "replace"), len(raw)
    if path.endswith(".gz"): return gzip.decompress(raw).decode("latin1", "replace"), len(raw)
    return raw.decode("latin1", "replace"), len(raw)
for sat in ("ja3", "s6a", "s3a", "swo", "h2c", "srl"):
    try:
        base = f"/pub/doris/data/{sat}/NRT"
        names = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(base))
        sub = [n for n in names if re.fullmatch(r"\d{4}", n)]
        if sub:
            yd = base + "/" + sub[-1]; inner = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(yd))
            dd = [n for n in inner if re.fullmatch(r"\d{3}", n)]
            if dd: yd = yd + "/" + dd[-1]; inner = sorted(n.rsplit("/", 1)[-1] for n in f.nlst(yd))
            files = [yd + "/" + n for n in inner]
        else:
            files = [base + "/" + n for n in names]
        files = [x for x in files if "MEP" in x]
        info = {"n": len(files), "newest": [x.rsplit("/", 1)[-1] for x in files[-3:]]}
        txt, size = get(files[-1])
        head, _, body = txt.partition("END OF HEADER")
        info["bytes"] = size
        info["obs_types"] = [l[:60].strip() for l in head.splitlines() if "OBS TYPES" in l][:3]
        st = [l for l in head.splitlines() if "STATION REFERENCE" in l]
        ev = [l for l in st if "EVEC" in l]
        info["stations"] = len(st); info["evec"] = ev[:1]
        epochs = [l for l in body.splitlines() if l.startswith(">")]
        info["first_epoch"] = epochs[0][:32] if epochs else None; info["last_epoch"] = epochs[-1][:32] if epochs else None
        if ev:
            sid = ev[0].split()[0]
            # 找含 EVEC 的最后一个历元
            last = None; cur = None
            for l in body.splitlines():
                if l.startswith(">"): cur = l[:32]
                elif l.startswith(sid): last = cur
            info["evec_last_epoch"] = last
            info["evec_sample"] = [l[:120] for l in body.splitlines() if l.startswith(sid)][:2]
        out["nrt"][sat] = info
    except Exception as e:
        out["errors"].append(f"{sat}: {e!r}"[:200])
f.quit()
json.dump(out, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)

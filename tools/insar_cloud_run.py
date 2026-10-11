#!/usr/bin/env python3
"""用仓库 main 分支的 cloud_insar_pipeline.py 跑真实云端干涉（哥白尼 openEO），并取回已完成任务的结果。
不改 main；产物写到 OUT 目录（之后推到 insar-out 分支）。只写预览图、统计、元数据，不保存大文件。"""
import sys, os, json, time, datetime as dt, pathlib, traceback
sys.path.insert(0, sys.argv[1])            # main 分支代码目录
OUT = pathlib.Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
import openeo, cloud_insar_pipeline as cip
log = {"t": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "steps": []}
def step(k, **v): v["k"] = k; v["t"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"); log["steps"].append(v); print(json.dumps(v, ensure_ascii=False), flush=True)
c = openeo.connect("https://openeo.dataspace.copernicus.eu"); c.authenticate_oidc_refresh_token()
def jobs():
    return [{"id": j["id"], "title": j.get("title"), "status": j.get("status"), "created": j.get("created"), "updated": j.get("updated"),
             "costs": j.get("costs"), "usage": j.get("usage")} for j in c.list_jobs() if (j.get("title") or "").startswith("Everest_InSAR_")]
J = jobs(); step("jobs_before", jobs=J)
# 1 最新影像对：按仓库代码的规则选（23790 条带，相隔 12 天）
pair, _ = cip.discover(); step("discover", pair=pair)
title = "Everest_InSAR_" + "_".join(d.replace("-", "") for d in pair)
mine = [j for j in J if j["title"] == title]
if mine:
    job = c.job(max(mine, key=lambda j: j["created"] or "")["id"])
else:
    graph = {"interferogram": {"process_id": "sentinel1_sar_interferogram", "namespace": cip.NAMESPACE,
             "arguments": {"InSAR_pairs": [pair], "burst_id": 23790, "sub_swath": "IW1", "polarization": "VV",
                           "coherence_window_az": 2, "coherence_window_rg": 10, "n_az_looks": 1, "n_rg_looks": 4}, "result": True}}
    job = c.create_job(process_graph=graph, title=title); step("created", id=job.job_id)
st = job.describe()["status"]
if st == "created": job.start(); step("started", id=job.job_id)
# 2 等待（最多 45 分钟）
t0 = time.time()
while True:
    st = job.describe()["status"]
    if st in ("finished", "error", "canceled") or time.time() - t0 > 45 * 60: break
    time.sleep(60)
step("latest_job", id=job.job_id, title=title, status=st, waited_min=round((time.time() - t0) / 60, 1))
# 3 导出：最新任务（若完成）+ 最近一个已完成的旧任务
def export_v2(tif, od, p, jid):
    """自己的导出（不依赖仓库 export 的波段顺序假设）：按波段描述识别，NaN 安全统计，修正预览拉伸。"""
    import numpy as np, rasterio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    with rasterio.open(tif) as ds:
        desc = [ds.descriptions[i] or "" for i in range(ds.count)]
        arr = [ds.read(i + 1).astype("float32") for i in range(ds.count)]
        nod = ds.nodata
        info = {"count": ds.count, "descriptions": desc, "dtype": ds.dtypes[0], "nodata": nod, "crs": str(ds.crs), "bounds": list(ds.bounds), "shape": [ds.height, ds.width]}
    bands = []
    for i, a in enumerate(arr):
        if nod is not None: a[a == nod] = np.nan
        f = a[np.isfinite(a)]
        bands.append({"i": i + 1, "desc": desc[i], "finite": int(f.size),
                      "q": [round(float(x), 4) for x in np.percentile(f, [0, 2, 50, 98, 100])] if f.size else None})
    def pick(keys, fallback):
        for b in bands:
            if any(k in b["desc"].lower() for k in keys): return b["i"] - 1
        return fallback
    ic = pick(["coh"], 2); iu = pick(["unw"], 1); iw = pick(["wrap", "phase_w", "ifg", "phase"], 0)
    if iw == iu: iw = 0 if iu != 0 else 1
    coh, unw, wr = arr[ic], arr[iu], arr[iw]
    ok = np.isfinite(coh) & np.isfinite(unw) & (coh >= 0.3) & (coh <= 1)
    los = np.where(ok, unw * (-0.055465 * 1000 / (4 * np.pi)), np.nan)
    cf = coh[np.isfinite(coh)]
    stats = {"coh_mean": round(float(cf.mean()), 3) if cf.size else None, "coh_ge_0_3": round(float((cf >= 0.3).mean()), 3) if cf.size else None,
             "valid_los_pixels": int(ok.sum()), "los_q_mm": [round(float(x), 1) for x in np.nanpercentile(los, [2, 50, 98])] if ok.any() else None}
    # 预览（降采样）
    k = max(1, int(max(coh.shape) / 1400))
    fig, ax = plt.subplots(3, 1, figsize=(10, 7.2), dpi=110)
    ext = [info["bounds"][0], info["bounds"][2], info["bounds"][1], info["bounds"][3]]
    for a, data, t, cm, vr in ((ax[0], coh[::k, ::k], "相干性 Coherence (0–1)", "gray", (0, 1)),
                               (ax[1], wr[::k, ::k], "缠绕相位 Wrapped phase", "twilight", (np.nanpercentile(wr, 1), np.nanpercentile(wr, 99))),
                               (ax[2], los[::k, ::k], "视线向位移（未参考，mm）Unreferenced LOS", "RdBu", tuple(np.nanpercentile(los, [2, 98])) if ok.any() else (0, 1))):
        im = a.imshow(data, cmap=cm, vmin=vr[0], vmax=vr[1], extent=ext, interpolation="nearest"); a.set_title(t, fontsize=9); a.tick_params(labelsize=7)
        a.plot(86.925, 27.988, marker="^", color="k", ms=6); fig.colorbar(im, ax=a, shrink=.8, pad=.01)
    fig.suptitle(f"Sentinel-1 {p[0]} → {p[1]} · burst 23790 IW1 VV · ▲ Everest", fontsize=10); fig.tight_layout()
    fig.savefig(od / "preview.png"); plt.close(fig)
    prod = {"pair": p, "job_id": jid, "exported": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "tif": info, "bands": bands,
            "used": {"coherence": ic + 1, "unwrapped": iu + 1, "wrapped": iw + 1}, "stats": stats,
            "status": "UNREFERENCED_NOT_FOR_HAZARD_DECISIONS"}
    (od / "product_v2.json").write_text(json.dumps(prod, ensure_ascii=False, indent=1), encoding="utf-8")
    return prod

def export_job(jid, ttl):
    d = ttl.replace("Everest_InSAR_", ""); a, b = d.split("_"); p = [a[:4] + "-" + a[4:6] + "-" + a[6:], b[:4] + "-" + b[4:6] + "-" + b[6:]]
    od = OUT / d
    if (od / "product_v2.json").exists(): step("export_skip", pair=p); return
    od.mkdir(parents=True, exist_ok=True)
    r = c.job(jid).get_results(); md = r.get_metadata()
    names = [n for n in md.get("assets", {}) if n.endswith(".tif")]
    if len(names) != 1: step("export_fail", pair=p, why="assets", names=list(md.get("assets", {}))[:6]); return
    tif = pathlib.Path("/tmp") / names[0]
    if not tif.exists(): r.get_asset(names[0]).download(tif)
    pr = export_v2(tif, od, p, jid)
    (od / "provenance.json").write_text(json.dumps(cip.safe_metadata(md), indent=1), encoding="utf-8")
    step("exported", pair=p, stats=pr["stats"], bands=pr["bands"], used=pr["used"])

J = jobs(); log["jobs_after"] = J
fin = sorted([j for j in J if j["status"] == "finished"], key=lambda j: j["title"], reverse=True)
for j in fin[:3]:
    try: export_job(j["id"], j["title"])
    except Exception as e: step("export_error", title=j["title"], err=repr(e)[:300])
for j in J:
    if j["status"] == "error" and j["title"] == title:
        try: step("job_error_logs", logs=[str(x.get("message"))[:200] for x in list(c.job(j["id"]).logs())[-5:]])
        except Exception as e: step("log_fail", err=repr(e)[:200])
prods = sorted(p.name for p in OUT.iterdir() if (p / "product_v2.json").exists())
if prods: (OUT / "latest.json").write_text((OUT / prods[-1] / "product_v2.json").read_text(), encoding="utf-8")
log["products"] = prods
(OUT / "run.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")

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
def export_job(jid, ttl):
    d = ttl.replace("Everest_InSAR_", ""); a, b = d.split("_"); p = [a[:4] + "-" + a[4:6] + "-" + a[6:], b[:4] + "-" + b[4:6] + "-" + b[6:]]
    od = OUT / d
    if (od / "product.json").exists(): step("export_skip", pair=p); return
    od.mkdir(parents=True, exist_ok=True)
    r = c.job(jid).get_results(); md = r.get_metadata()
    names = [n for n in md.get("assets", {}) if n.endswith(".tif")]
    if len(names) != 1: step("export_fail", pair=p, why="assets", names=list(md.get("assets", {}))[:6]); return
    tif = pathlib.Path("/tmp") / names[0]; r.get_asset(names[0]).download(tif)
    s = cip.export(tif, od, p, jid)
    (od / "provenance.json").write_text(json.dumps(cip.safe_metadata(md), indent=1), encoding="utf-8")
    for f in ("los_unreferenced_mm.npy", "coherence.npy"):
        if (od / f).exists(): (od / f).unlink()   # 大文件不保存
    step("exported", pair=p, pixels=s["valid_phase_pixels"], coh=round(s["coherence_mean"], 3))
J = jobs(); log["jobs_after"] = J
fin = sorted([j for j in J if j["status"] == "finished"], key=lambda j: j["title"], reverse=True)
for j in fin[:2]:
    try: export_job(j["id"], j["title"])
    except Exception as e: step("export_error", title=j["title"], err=repr(e)[:300])
for j in J:
    if j["status"] == "error" and j["title"] == title:
        try: step("job_error_logs", logs=[str(x.get("message"))[:200] for x in list(c.job(j["id"]).logs())[-5:]])
        except Exception as e: step("log_fail", err=repr(e)[:200])
prods = sorted(p.name for p in OUT.iterdir() if (p / "product.json").exists())
if prods: (OUT / "latest.json").write_text((OUT / prods[-1] / "product.json").read_text(), encoding="utf-8")
log["products"] = prods
(OUT / "run.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")

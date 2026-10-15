"""按 MiroFish 后端 API（backend/app/api/*.py）的顺序跑一次完整推演，保存全部产物。

  1. POST /api/graph/ontology/generate   上传种子材料 + 模拟需求 → project_id、本体
  2. POST /api/graph/build               用 Zep 构建知识图谱 → task_id，轮询 /api/graph/task/<id>
  3. POST /api/simulation/create         → simulation_id（推特 + Reddit 两个平台）
  4. POST /api/simulation/prepare        生成智能体人设和模拟配置 → 轮询 /api/simulation/prepare/status
  5. POST /api/simulation/start          max_rounds 截断轮数 → 轮询 /api/simulation/<id>/run-status
  6. POST /api/report/generate           ReportAgent 写报告 → 轮询 /api/report/generate/status
  7. GET  /api/report/<id>/download      报告 Markdown；另存图谱、人设、配置、时间线、帖子、智能体统计

用法：python3 tools/mirofish_run.py <种子目录（mirofish_seed.py 的输出）> <输出目录> [max_rounds]
"""
import json, os, sys, time, urllib.request, urllib.error, uuid

BASE = os.environ.get("MIROFISH_API", "http://127.0.0.1:5001")
IN, OUT = sys.argv[1], sys.argv[2]
ROUNDS = int(sys.argv[3]) if len(sys.argv) > 3 else 20
os.makedirs(OUT, exist_ok=True)
LOG = []


def log(*a):
    s = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)


def call(method, path, body=None, raw=False, timeout=600):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"content-type": "application/json", "accept-language": "zh"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: b = r.read()
    except urllib.error.HTTPError as e:
        b = e.read(); log("HTTP", e.code, path, b[:400]); raise
    return b if raw else json.loads(b)


def upload(path, files, fields):
    bd = "----mf" + uuid.uuid4().hex; parts = []
    for k, v in fields.items():
        parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for fp in files:
        parts.append(f'--{bd}\r\nContent-Disposition: form-data; name="files"; filename="{os.path.basename(fp)}"\r\nContent-Type: text/markdown\r\n\r\n'.encode() + open(fp, "rb").read() + b"\r\n")
    parts.append(f"--{bd}--\r\n".encode())
    req = urllib.request.Request(BASE + path, data=b"".join(parts), method="POST", headers={"content-type": f"multipart/form-data; boundary={bd}", "accept-language": "zh"})
    try:
        with urllib.request.urlopen(req, timeout=1800) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        b = e.read(); log("HTTP", e.code, path, b[:400]); raise


def save(name, obj):
    p = os.path.join(OUT, name)
    if isinstance(obj, (bytes, str)): open(p, "wb").write(obj if isinstance(obj, bytes) else obj.encode())
    else: json.dump(obj, open(p, "w"), ensure_ascii=False, indent=1)


def poll(fn, done, fail, every=15, limit=3 * 3600, what=""):
    t0 = time.time(); last = None
    while time.time() - t0 < limit:
        d = fn(); st = done(d)
        msg = json.dumps({k: d.get(k) for k in ("status", "progress", "message", "runner_status", "current_round", "total_rounds", "total_actions_count") if k in d}, ensure_ascii=False)
        if msg != last: log(what, msg); last = msg
        if st: return d
        if fail(d): raise RuntimeError(f"{what} 失败：{json.dumps(d, ensure_ascii=False)[:600]}")
        time.sleep(every)
    raise TimeoutError(what + " 超时")


status = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "max_rounds": ROUNDS, "steps": {}}
try:
    seeds = sorted(os.path.join(IN, "seed", f) for f in os.listdir(os.path.join(IN, "seed")))
    req = open(os.path.join(IN, "requirement.txt")).read(); ctx = open(os.path.join(IN, "context.txt")).read()
    # 1 本体
    r = upload("/api/graph/ontology/generate", seeds, {"simulation_requirement": req, "project_name": "EVEREST 证据链推演 " + time.strftime("%Y-%m-%d"), "additional_context": ctx})
    if not r.get("success"): raise RuntimeError("本体生成失败：" + json.dumps(r, ensure_ascii=False)[:500])
    pid = r["data"]["project_id"]; save("01_ontology.json", r["data"]); status["steps"]["ontology"] = pid; log("project", pid)
    # 2 图谱
    r = call("POST", "/api/graph/build", {"project_id": pid, "graph_name": "EVEREST evidence graph"})
    tid = r["data"]["task_id"]
    t = poll(lambda: call("GET", f"/api/graph/task/{tid}")["data"], lambda d: d.get("status") == "completed", lambda d: d.get("status") == "failed", what="图谱")
    proj = call("GET", f"/api/graph/project/{pid}")["data"]; gid = proj.get("graph_id"); status["steps"]["graph"] = gid; log("graph", gid)
    try: save("02_graph.json", call("GET", f"/api/graph/data/{gid}")["data"])
    except Exception as e: log("图谱数据导出失败", e)
    # 3 模拟
    r = call("POST", "/api/simulation/create", {"project_id": pid, "graph_id": gid, "enable_twitter": True, "enable_reddit": True})
    sid = r["data"]["simulation_id"]; status["steps"]["simulation"] = sid; log("simulation", sid)
    # 4 准备
    r = call("POST", "/api/simulation/prepare", {"simulation_id": sid, "use_llm_for_profiles": True, "parallel_profile_count": 5})
    ptid = (r.get("data") or {}).get("task_id")
    poll(lambda: call("POST", "/api/simulation/prepare/status", {"task_id": ptid, "simulation_id": sid})["data"],
         lambda d: d.get("status") in ("completed", "ready") or d.get("already_prepared"), lambda d: d.get("status") == "failed", what="准备")
    for name, path in (("03_profiles.json", f"/api/simulation/{sid}/profiles"), ("04_config.json", f"/api/simulation/{sid}/config")):
        try: save(name, call("GET", path)["data"])
        except Exception as e: log(name, "导出失败", e)
    # 5 运行
    call("POST", "/api/simulation/start", {"simulation_id": sid, "platform": "parallel", "max_rounds": ROUNDS, "enable_graph_memory_update": True})
    # MiroFish 的模拟脚本跑完所有轮次后进入“等待命令模式”（供采访用），进程不退出，runner_status 一直是 running。
    # 两个平台都报完成后，发 close-env 让它优雅退出；10 分钟还没退出就 /stop。之后等到 completed/stopped 才能生成报告。
    ENDS = {"closed": 0.0, "stopped": False}

    def run_status():
        d = call("GET", f"/api/simulation/{sid}/run-status")["data"]
        if d.get("runner_status") == "running" and d.get("twitter_completed") and d.get("reddit_completed"):
            if not ENDS["closed"]:
                ENDS["closed"] = time.time(); log("两个平台都已跑完，发送 close-env")
                try: log("close-env", json.dumps(call("POST", "/api/simulation/close-env", {"simulation_id": sid, "timeout": 120}, timeout=300), ensure_ascii=False)[:300])
                except Exception as e: log("close-env 出错", e)
            elif not ENDS["stopped"] and time.time() - ENDS["closed"] > 600:
                ENDS["stopped"] = True; log("close-env 后 10 分钟仍未退出，发送 stop")
                try: log("stop", json.dumps(call("POST", "/api/simulation/stop", {"simulation_id": sid}, timeout=300), ensure_ascii=False)[:300])
                except Exception as e: log("stop 出错", e)
        return d
    rs = poll(run_status, lambda d: d.get("runner_status") in ("completed", "stopped"),
              lambda d: d.get("runner_status") == "failed", every=30, what="运行")
    status["steps"]["run_end"] = rs.get("runner_status"); status["steps"]["actions"] = rs.get("total_actions_count")
    save("05_run_status.json", rs)
    for name, path in (("06_timeline.json", f"/api/simulation/{sid}/timeline"), ("07_agent_stats.json", f"/api/simulation/{sid}/agent-stats"),
                       ("08_posts.json", f"/api/simulation/{sid}/posts?limit=500"), ("09_comments.json", f"/api/simulation/{sid}/comments?limit=500"),
                       ("10_actions.json", f"/api/simulation/{sid}/actions?limit=2000")):
        try: save(name, call("GET", path)["data"])
        except Exception as e: log(name, "导出失败", e)
    # 6 报告
    for i in range(40):  # 图谱写入未排空时后端返回 409，最多等 20 分钟
        try: r = call("POST", "/api/report/generate", {"simulation_id": sid}); break
        except urllib.error.HTTPError as e:
            if e.code != 409 or i == 39: raise
            time.sleep(30)
    rtid = r["data"].get("task_id"); rid = r["data"].get("report_id")
    poll(lambda: call("POST", "/api/report/generate/status", {"task_id": rtid, "simulation_id": sid})["data"],
         lambda d: d.get("status") == "completed", lambda d: d.get("status") == "failed", every=20, what="报告")
    rep = call("GET", f"/api/report/by-simulation/{sid}"); rid = (rep.get("data") or {}).get("report_id") or rid
    save("11_report_meta.json", rep.get("data"))
    save("REPORT.md", call("GET", f"/api/report/{rid}/download", raw=True))
    status["steps"]["report"] = rid; status["ok"] = True; log("完成", rid)
except Exception as e:
    status["ok"] = False; status["error"] = str(e)[:1000]; log("失败", e)
finally:
    status["finished"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); save("status.json", status); save("run.log", "\n".join(LOG))
sys.exit(0 if status.get("ok") else 1)

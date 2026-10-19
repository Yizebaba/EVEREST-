#!/usr/bin/env bash
# 把 mf_out/ 现有的产物推到 events 分支 <目录>/，并让 mirofish/LATEST 指向它。运行中每 10 分钟一次，结束时再一次。
# 日志里的密钥先抹掉。用法：bash tools/mirofish_checkpoint.sh mirofish/<UTC> "<说明>"
set -u
D="$1"; MSG="${2:-checkpoint}"
for f in mf_out/backend.log mf_out/run.log; do [ -f "$f" ] && for k in "${LLM_API_KEY:-}" "${ZEP_API_KEY:-}"; do [ -n "$k" ] && sed -i "s|$k|***|g" "$f" || true; done; done
W=$(mktemp -d); git config --global user.name "mirofish"; git config --global user.email "actions@users.noreply.github.com"
git fetch -q origin events && git worktree add -q -f "$W" origin/events || exit 0
T="${D%%/*}"   # mirofish（珠峰）或 mirofish-bri（一带一路）
mkdir -p "$W/$D" && cp -r mf_out/. "$W/$D/" && printf '%s\n' "$D" > "$W/$T/LATEST"
# 推演记录索引（网页读它）：mirofish/index.json
python3 - "$W" "$D" <<'PY' || true
import json, os, sys
W, D = sys.argv[1], sys.argv[2]; p = os.path.join(W, D.split("/")[0], "index.json")
idx = json.load(open(p)) if os.path.exists(p) else {"runs": []}
rq = json.load(open(os.path.join(W, D, "request.json"))) if os.path.exists(os.path.join(W, D, "request.json")) else {}
st = json.load(open(os.path.join(W, D, "status.json"))) if os.path.exists(os.path.join(W, D, "status.json")) else {}
e = {"dir": D, "id": rq.get("id", ""), "project": rq.get("project", "everest"), "scope": rq.get("scope", ""), "title": rq.get("title", ""), "requirement": (rq.get("requirement") or "")[:400], "started": rq.get("started") or st.get("started"),
     "finished": st.get("finished"), "ok": st.get("ok"), "error": st.get("error") or st.get("upstream_hint") or "", "has_report": os.path.exists(os.path.join(W, D, "REPORT.md")), "run_url": rq.get("run_url", "")}
idx["runs"] = [e] + [r for r in idx["runs"] if r.get("dir") != D]
json.dump(idx, open(p, "w"), ensure_ascii=False, indent=1)
PY
( cd "$W" && git add "$T" && git commit -qm "mirofish $D ($MSG)" && for i in 1 2 3; do git pull -q --rebase origin events && git push -q origin HEAD:events && break; sleep 3; done ) || true
git worktree remove -f "$W" || true

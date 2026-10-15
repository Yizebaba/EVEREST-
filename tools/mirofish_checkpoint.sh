#!/usr/bin/env bash
# 把 mf_out/ 现有的产物推到 events 分支 <目录>/，并让 mirofish/LATEST 指向它。运行中每 10 分钟一次，结束时再一次。
# 日志里的密钥先抹掉。用法：bash tools/mirofish_checkpoint.sh mirofish/<UTC> "<说明>"
set -u
D="$1"; MSG="${2:-checkpoint}"
for f in mf_out/backend.log mf_out/run.log; do [ -f "$f" ] && for k in "${LLM_API_KEY:-}" "${ZEP_API_KEY:-}"; do [ -n "$k" ] && sed -i "s|$k|***|g" "$f" || true; done; done
W=$(mktemp -d); git config --global user.name "mirofish"; git config --global user.email "actions@users.noreply.github.com"
git fetch -q origin events && git worktree add -q -f "$W" origin/events || exit 0
mkdir -p "$W/$D" && cp -r mf_out/. "$W/$D/" && printf '%s\n' "$D" > "$W/mirofish/LATEST"
( cd "$W" && git add mirofish && git commit -qm "mirofish $D ($MSG)" && for i in 1 2 3; do git pull -q --rebase origin events && git push -q origin HEAD:events && break; sleep 3; done ) || true
git worktree remove -f "$W" || true

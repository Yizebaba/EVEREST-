"""IO.EVN（珠峰南坡 Pyramid 宽频带地震仪，GEOFON）最近 24 小时的 1–5 Hz 包络图，替换总览页里写死的 10-12 示例波形。
方法与证据包相同：BHZ，1–5 Hz 带通，60 秒均方根，相对窗口中位数（背景）；没有数据的分钟留空，不画成 0。
用法：python3 tools/evn_plot.py <输出目录>  →  evn_24h.png、evn_24h.json（latest 最新样本时间、start、cover 覆盖率、bg）
"""
import io, json, os, sys, urllib.request
from datetime import datetime, timedelta, timezone

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
now = datetime.now(timezone.utc).replace(second=0, microsecond=0); a = now - timedelta(hours=24)
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S")
meta = {"generated": iso(now) + "Z", "start": iso(a) + "Z", "station": "IO.EVN BHZ", "source": "GEOFON FDSN dataselect"}
try:
    u = f"https://geofon.gfz.de/fdsnws/dataselect/1/query?net=IO&sta=EVN&cha=BHZ&starttime={iso(a)}&endtime={iso(now)}"
    raw = urllib.request.urlopen(urllib.request.Request(u, headers={"user-agent": "everest-evn-plot"}), timeout=180).read()
    if not raw: raise RuntimeError("GEOFON 最近 24 小时没有返回数据")
    import numpy as np
    from obspy import read
    st = read(io.BytesIO(raw)); st.merge(fill_value=None)
    tr = st[0]; meta["latest"] = tr.stats.endtime.datetime.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    st = st.split(); st.detrend("demean"); st.filter("bandpass", freqmin=1, freqmax=5, corners=4, zerophase=True)
    nmin = int((now - a).total_seconds() // 60); env = np.full(nmin, np.nan)
    for t in st:
        sr = t.stats.sampling_rate; n = int(60 * sr); x = t.data.astype(float)
        i0 = int((t.stats.starttime.datetime.replace(tzinfo=timezone.utc) - a).total_seconds() // 60)
        m = len(x) // n
        if m <= 0: continue
        e = np.sqrt((x[:m * n].reshape(m, n) ** 2).mean(axis=1))
        j0, j1 = max(0, i0), min(nmin, i0 + m)
        if j1 > j0: env[j0:j1] = e[j0 - i0:j1 - i0]
    ok = np.isfinite(env) & (env > 0); bg = float(np.median(env[ok])) if ok.any() else 0
    meta["cover"] = round(100 * ok.sum() / nmin); meta["bg"] = bg
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 2.3), dpi=80)
    ts = [a + timedelta(minutes=i) for i in range(nmin)]
    ax.plot(ts, np.where(ok, env / bg if bg else np.nan, np.nan), lw=0.7, color="#d9822b")
    ax.set_yscale("log"); ax.axhline(1, color="#999", lw=0.5); ax.axhline(5, color="#c33", lw=0.4, ls=":")
    ax.set_ylabel("x bg", fontsize=7); ax.tick_params(labelsize=7)
    ax.set_title(f"IO.EVN (Everest Pyramid) 1-5 Hz, 60 s RMS, last 24 h to {iso(now)[:16]} UTC  |  coverage {meta['cover']}%  |  red dotted = 5x background", fontsize=8, loc="left")
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(os.path.join(out, "evn_24h.png")); plt.close(fig)
    meta["ok"] = True
except Exception as e:
    meta["ok"] = False; meta["error"] = str(e)[:300]
json.dump(meta, open(os.path.join(out, "evn_24h.json"), "w"), ensure_ascii=False)
print(json.dumps(meta, ensure_ascii=False))

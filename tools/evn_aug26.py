#!/usr/bin/env python3
"""一次性核查：8 月 26 日吉隆冰岩崩（USGS us7000tbwb，M5.2 landslide，02:52:10 UTC）时，
珠峰 Pyramid 的意大利地震台 IO.EVN 有没有记录到。对照尼泊尔 KKN（NK 网，EarthScope）。"""
import json, math, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
T0 = UTCDateTime("2026-08-26T02:52:10"); EV = (28.271, 85.515)
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(x))
out = {"event": "us7000tbwb M5.2 landslide 2026-08-26T02:52:10Z", "stations": {}}
fig, ax = plt.subplots(4, 1, figsize=(12, 9), dpi=110)
for k, (cli, net, sta, cha, lat, lon) in enumerate([("GEOFON", "IO", "EVN", "HHZ", 27.95865, 86.811651), ("IRIS", "NK", "KKN", "BHZ", None, None)]):
    info = {}
    try:
        c = Client(cli)
        if lat is None:
            inv = c.get_stations(network=net, station=sta, level="station"); s0 = inv[0][0]; lat, lon = s0.latitude, s0.longitude
        info["dist_km"] = round(km(EV[0], EV[1], lat, lon))
        st = c.get_waveforms(net, sta, "*", cha, T0 - 1800, T0 + 4 * 3600)
        info["traces"] = [(str(tr.stats.starttime), str(tr.stats.endtime), tr.stats.sampling_rate) for tr in st]
        st.merge(fill_value=np.nan if False else 0); tr = st[0]
        tr.detrend("demean"); tr.filter("bandpass", freqmin=1.0, freqmax=8.0)
        t = tr.times(reftime=T0); d = tr.data.astype(float)
        env = np.abs(d); w = int(tr.stats.sampling_rate * 10)
        sm = np.convolve(env, np.ones(w) / w, mode="same")
        pre = np.median(sm[(t > -1700) & (t < -60)])
        win = (t > 0) & (t < 300)
        pk = sm[win].max(); tpk = t[win][sm[win].argmax()]
        info.update(pre_bg=float(pre), peak_10s_mean=float(pk), ratio=round(float(pk / pre), 1), peak_after_s=round(float(tpk)),
                    flood_ratio_40_120min=round(float(np.median(sm[(t > 2400) & (t < 7200)]) / pre), 2))
        ax[2 * k].plot(t / 60, d, lw=.3, color="#2f6f9f"); ax[2 * k].set_title(f"{net}.{sta}.{cha}  {info['dist_km']} km  1–8 Hz", fontsize=9)
        ax[2 * k + 1].semilogy(t / 60, sm / pre, lw=.8, color="#c0504d"); ax[2 * k + 1].set_ylabel("× background", fontsize=8)
        for a in (ax[2 * k], ax[2 * k + 1]): a.axvline(0, color="k", lw=.6, ls="--"); a.set_xlim(-30, 240)
    except Exception as e:
        info["err"] = repr(e)[:300]
    out["stations"][f"{net}.{sta}"] = info
ax[-1].set_xlabel("minutes after 02:52:10 UTC (USGS M5.2 landslide)")
fig.suptitle("2026-08-26 Gyirong ice-rock avalanche — seismic records", fontsize=10); fig.tight_layout(); fig.savefig("evn_aug26.png")
json.dump(out, open("evn_aug26.json", "w"), indent=1); print(json.dumps(out, indent=1))

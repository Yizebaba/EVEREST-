#!/usr/bin/env python3
"""取 IO.EVN（意大利 OGS，珠峰金字塔实验室）最近的真实波形，画两张图：最近 1 小时波形、最近 24 小时“鼓记录”（dayplot）。"""
import datetime as dt, os
from obspy.clients.fdsn import Client
from obspy import UTCDateTime
os.makedirs("data/evn", exist_ok=True)
c = Client("GEOFON")
now = UTCDateTime()
st = c.get_waveforms("IO", "EVN", "*", "HHZ", now - 3600, now)
st.merge(fill_value=0)
last = st[0].stats.endtime
st.plot(outfile="data/evn/evn_last_hour.png", size=(1400, 380), color="#2f6f9f", tick_format="%H:%M",
        title=f"IO.EVN.HHZ  Everest Pyramid 5010 m  last hour, latest sample {last.strftime('%Y-%m-%d %H:%M:%S')} UTC (raw counts)")
st24 = c.get_waveforms("IO", "EVN", "*", "BHZ", now - 86400, now)
st24.merge(fill_value=0)
st24.filter("bandpass", freqmin=1.0, freqmax=8.0)
st24.plot(type="dayplot", interval=60, outfile="data/evn/evn_24h_dayplot.png", size=(1400, 1500), one_tick_per_line=True,
          title=f"IO.EVN.BHZ last 24 h, 1-8 Hz, one line = 60 min (UTC), up to {st24[0].stats.endtime.strftime('%Y-%m-%d %H:%M')} UTC")
open("data/evn/latest.txt", "w").write(f"checked {now.isoformat()}Z\nlatest_sample {last.isoformat()}Z\n")
print("latest sample", last, "now", now, "lag_s", round(now - last))

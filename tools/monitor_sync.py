"""把 Cloudflare 实时采集（facet-live 分支的 rt.json）转换成「现场设备维护台」用的在线状态文档。

用法：
  python3 tools/monitor_sync.py rt.json monitor.json [assets.json]
输出 monitor.json：写入维护台数据库 monitor/latest 的文档。
给了第三个参数时，额外输出外部台站的设备文档列表（只在第一次建台账时用）。

判定规则（只看数据是否在来，不判断设备好坏）：
  水位站（BIPAD）：最后一条数据距 rt.json 汇总时间不超过 6 小时算在线
  地震台 IO.EVN：最近 20 分钟有数据算在线
  DORIS 信标 EVEC：12 小时内被卫星跟踪到算在线
"""
import json
import sys
from datetime import datetime, timezone

BIPAD_H = 6
DORIS_H = 12


def ts(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if d else None


def build(rt):
    now = ts(rt["updated"])
    S = rt["sources"]
    items = {}
    b = S.get("bipad") or {}
    for sid, st in ((b.get("v") or {}).get("st") or {}).items():
        m = st.get("meta") or {}
        last = ts(m.get("last_on"))
        on = bool(last and (now - last).total_seconds() <= BIPAD_H * 3600)
        note = "" if on else ("超过 %d 小时没有新数据" % BIPAD_H)
        if m.get("status") and m["status"] != "BELOW WARNING LEVEL":
            note = (note + "；" if note else "") + "站点状态 " + m["status"]
        items["bipad:" + sid] = {"name": m.get("name") or m.get("title") or sid, "online": on, "last": iso(last), "note": note,
                                 "lat": m.get("lat"), "lon": m.get("lon"), "title": m.get("title")}
    e = S.get("evn") or {}
    if e:
        v = e.get("v") or {}
        on = bool(e.get("ok") and (v.get("completeness") or 0) > 0)
        items["evn"] = {"name": "IO.EVN 地震台（Pyramid）", "online": on, "last": v.get("last_sample"),
                        "note": "" if on else (v.get("note") or e.get("err") or "最近 20 分钟没有数据")}
    d = S.get("doris") or {}
    if d:
        lp = (d.get("v") or {}).get("last_pass")
        last = ts(lp["last"]) if lp else None
        on = bool(last and (now - last).total_seconds() <= DORIS_H * 3600)
        items["doris"] = {"name": "DORIS 信标 EVEC", "online": on, "last": iso(last),
                          "note": "" if on else ("%d 小时内没有被卫星跟踪到" % DORIS_H)}
    return {"updated": rt["updated"], "source": "EVEREST Cloudflare 实时采集 rt.json", "items": items}


def external_assets(mon):
    out = []
    for k, it in mon["items"].items():
        if k.startswith("bipad:"):
            sid = k.split(":", 1)[1]
            out.append({"id": "ext-bipad-" + sid, "name": it["name"], "site": "外部 · 尼泊尔水文气象局水位站", "type": "水位计",
                        "model": "", "serial": "BIPAD " + sid, "location": "%.4fN %.4fE" % (it["lat"], it["lon"]) if it.get("lat") else "",
                        "owner": "外部", "status": "正常", "intervalDays": None, "lastServiced": None, "monitorKey": k,
                        "notes": (it.get("title") or "") + "。设备归尼泊尔水文气象局（DHM）所有，本台账只记录在线状态。"})
    if "evn" in mon["items"]:
        out.append({"id": "ext-evn", "name": "IO.EVN 宽频带地震仪", "site": "外部 · 珠峰 Pyramid 观测站", "type": "地震仪", "model": "",
                    "serial": "IO.EVN", "location": "27.959N 86.813E，海拔约 5050 m", "owner": "外部", "status": "正常",
                    "intervalDays": None, "lastServiced": None, "monitorKey": "evn",
                    "notes": "OGS / Ev-K2-CNR 运营，数据经 GEOFON 公开。本台账只记录在线状态。"})
    if "doris" in mon["items"]:
        out.append({"id": "ext-evec", "name": "DORIS 地面信标 EVEC", "site": "外部 · 珠峰 Pyramid 观测站", "type": "DORIS 信标", "model": "",
                    "serial": "EVEC", "location": "Pyramid 观测站", "owner": "外部", "status": "正常",
                    "intervalDays": None, "lastServiced": None, "monitorKey": "doris",
                    "notes": "IGN / CNES / IDS 网络，2024-10 由 EVEB 更换为 EVEC。本台账只记录在线状态。"})
    for a in out:
        a["createdAt"] = a["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return out


if __name__ == "__main__":
    rt = json.load(open(sys.argv[1], encoding="utf-8"))
    mon = build(rt)
    json.dump(mon, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    off = [k for k, v in mon["items"].items() if not v["online"]]
    print("items", len(mon["items"]), "offline", len(off), off)
    if len(sys.argv) > 3:
        json.dump(external_assets(mon), open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)

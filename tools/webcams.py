"""珠峰地区公开摄像头：每小时（随灾种扫描）检查一次哪些在直播、取一张缩略图。只记录事实：是否在播、标题、取图时间、源地址。

来源（2026-10-14 在 GitHub 运行器上实测）：
  1. YouTube 频道 WEBCAM NEPAL LIVE（UCCCVkU6r9ZTD8E4z7AtuOIw）：Hotel Everest View（珠峰全景）、卢卡拉机场、罗布切、纳姆切等直播。
     “是否在播”取自 YouTube 页面里的 isLiveNow；缩略图由 YouTube 生成，更新时间由 YouTube 决定，不保证是这一刻的画面。
  2. EvK2Minoprio 金字塔 / 卡拉帕塔尔摄像头（evk2minoprio.org/webcam）：图像文件的服务器修改时间就是最后一张图的时间
     （实测最后更新 2024-11-24，已停更）。
输出：<out>/webcams.json，<out>/cam_<编号>.jpg（480×360 左右的小图）。
"""
import json, os, re, sys, time, urllib.request
from datetime import datetime, timezone

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
UA = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36", "accept-language": "en"}
CH = "UCCCVkU6r9ZTD8E4z7AtuOIw"
KEEP = re.compile(r"EVEREST|LUKLA|LOBUCHE|NAMCHE|KHUMBU|GORAKSHEP|PHERICHE|DINGBOCHE|TENGBOCHE|GOKYO|KHARE|MERA|AMA DABLAM", re.I)
NOW = datetime.now(timezone.utc)


def get(url, raw=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read(); h = dict(r.headers)
    return (b, h) if raw else b.decode("utf-8", "ignore")


def yt_live():
    """频道当前在播的直播：/streams 页里带“直播中”标记的条目；再逐个打开确认 isLiveNow。"""
    cams, seen = [], set()
    for url in (f"https://www.youtube.com/channel/{CH}/streams", f"https://www.youtube.com/channel/{CH}/live"):
        try: t = get(url)
        except Exception as e: print("yt", url, e); continue
        for m in re.finditer(r'"videoId":"([\w-]{11})"', t):
            vid = m.group(1)
            if vid in seen: continue
            seen.add(vid)
        if len(seen) > 40: break
    for vid in list(seen)[:40]:
        try: p = get(f"https://www.youtube.com/watch?v={vid}")
        except Exception: continue
        live = re.search(r'"isLiveNow":true', p) is not None or re.search(r'"isLive":true', p) is not None
        title = (re.search(r'"title":"([^"]{5,200})"', p) or [None, ""])[1] if re.search(r'"title":"([^"]{5,200})"', p) else ""
        owner = re.search(r'"channelId":"([\w-]+)"', p)
        if not live or (owner and owner.group(1) != CH) or not KEEP.search(title): continue
        cams.append({"id": "yt-" + vid, "kind": "youtube", "title": title.encode().decode("unicode_escape", "ignore") if "\\u" in title else title,
                     "operator": "WEBCAM NEPAL LIVE（YouTube）", "url": f"https://www.youtube.com/watch?v={vid}", "live": True,
                     "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault_live.jpg", "note": "缩略图由 YouTube 生成，更新时间由 YouTube 决定，不保证是这一刻的画面"})
    return cams


def evk2():
    b, h = get("https://ftp.mountaingenius.org/PYRCEOP/PWC.jpg", raw=True)
    lm = h.get("Last-Modified") or h.get("last-modified")
    t = datetime.strptime(lm, "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=timezone.utc) if lm else None
    fresh = t and (NOW - t).total_seconds() < 2 * 86400
    return {"id": "evk2-pyramid", "kind": "image", "title": "金字塔 / 卡拉帕塔尔（EvK2Minoprio，海拔约 5,675 m，朝向珠峰）", "operator": "EvK2Minoprio（意大利）",
            "url": "https://evk2minoprio.org/webcam/", "image": "https://ftp.mountaingenius.org/PYRCEOP/PWC.jpg", "live": bool(fresh),
            "last_image": t.strftime("%Y-%m-%dT%H:%M:%SZ") if t else None, "_bytes": b,
            "note": "图像文件的服务器修改时间就是最后一张图的时间" + ("" if fresh else "；已停更")}


def main():
    os.makedirs(OUT, exist_ok=True)
    cams = []
    try: cams += yt_live()
    except Exception as e: print("youtube", e)
    try: cams.append(evk2())
    except Exception as e: print("evk2", e)
    for c in cams:
        try:
            b = c.pop("_bytes", None) or get(c["thumb"], raw=True)[0]
            if c["kind"] == "image" and len(b) > 120000:   # 原图太大：用 Pillow 缩到 480 宽
                try:
                    from PIL import Image; import io
                    im = Image.open(io.BytesIO(b)); im.thumbnail((480, 480)); o = io.BytesIO(); im.convert("RGB").save(o, "JPEG", quality=70); b = o.getvalue()
                except Exception: pass
            open(os.path.join(OUT, f"cam_{c['id']}.jpg"), "wb").write(b)
            c["file"] = f"hazards/cam_{c['id']}.jpg"; c["fetched"] = NOW.strftime("%Y-%m-%dT%H:%M:%SZ"); c["bytes"] = len(b)
        except Exception as e:
            c["err"] = str(e)[:120]
    json.dump({"updated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "cams": cams}, open(os.path.join(OUT, "webcams.json"), "w"), ensure_ascii=False, indent=1)
    print(len(cams), "cams;", sum(1 for c in cams if c.get("live")), "live")
    for c in cams: print(" ", c["id"], c.get("live"), c["title"][:80])


if __name__ == "__main__":
    main()

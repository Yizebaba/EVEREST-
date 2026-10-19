"""为 MiroFish（群体智能推演引擎，github.com/666ghj/MiroFish）生成“种子材料”和“模拟需求”。

MiroFish 的输入（见其 README 与 backend/app/api/graph.py）：
  - files：种子材料，PDF / MD / TXT，可多个（每个 ≤50 MB）
  - simulation_requirement：用自然语言写的模拟（推演）需求，必填
  - additional_context：额外说明，可选
本脚本只用本平台的真实数据（GitHub events 分支的证据包、灾种扫描、实时采集、运行记录、外部库目录）写成 Markdown 档案，
每个数字都带来源和时间。推演结果是“模拟”，不是证据，不进入证据链。

用法：python3 tools/mirofish_seed.py <输出目录> [场景: combined|everest|global|strategy]
输出：<输出目录>/seed/*.md、requirement.txt（取自环境变量 MF_REQUIREMENT，即使用者自己写的推演要求）、context.txt、manifest.json
"""
import json, os, subprocess, sys, time
from collections import Counter

OUT = sys.argv[1] if len(sys.argv) > 1 else "mirofish_in"
SCEN = sys.argv[2] if len(sys.argv) > 2 else "combined"
REPO = "Yizebaba/EVEREST-"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
os.makedirs(os.path.join(OUT, "seed"), exist_ok=True)


def raw(path, ref):
    return subprocess.check_output(["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{REPO}/contents/{path}?ref={ref}"])


def J(path, ref):
    try: return json.loads(raw(path, ref))
    except Exception as e:
        print("缺", path, e); return None


def bj(t):
    if not t: return "—"
    try:
        import datetime as dt
        d = dt.datetime.fromisoformat(t.replace("Z", "+00:00")) + dt.timedelta(hours=8)
        return d.strftime("%Y-%m-%d %H:%M") + "（北京）"
    except Exception: return t


idx = J("index.json", "events") or {}
scan = J("hazards/scan.json", "events") or {}
recs = (J("hazards/records.json", "events") or {}).get("records", [])
cat = J("hazards/catalog.json", "events") or {}
rt = J("rt.json", "facet-live") or {}
fst = J("facet_status.json", "facet-live") or {}
pipe = J("data/displacement_summary.json", "main") or {}
cams = J("hazards/webcams.json", "events") or {}
try: runs = json.loads(subprocess.check_output(["gh", "api", f"repos/{REPO}/actions/runs?per_page=100"])).get("workflow_runs", [])
except Exception: runs = []

W = {}
def w(name, text): W[name] = text.strip() + "\n"

# ---------- 01 平台概况 ----------
by_name = Counter(r.get("name") for r in runs); ok_name = Counter(r.get("name") for r in runs if r.get("conclusion") == "success")
w("01_平台概况与运行实况.md", f"""
# EVEREST：公开地球观测数据的真实度审计与事件证据平台 —— 平台概况与运行实况

生成时间：{bj(NOW)}。本档案只陈述可核对的事实，每个数字后面注明来源。

## 1. 平台是什么
EVEREST 是一个开源项目（GitHub 仓库 {REPO}），做两件事：
1. **真实度审计**：持续检查公开的地球观测和灾害数据源是否在线、是否按时更新、数值是否可信（停报不等于正常）。
2. **事件证据链**：发现事件候选后，把多个独立公开来源在时间线上排列，生成证据包，并做不可篡改存证（OpenTimestamps 比特币时间戳、RFC 3161 时间戳（FreeTSA、DigiCert）、Sigstore 签名与 Rekor 透明日志），再用两套以上互不相干的工具做 9 项独立核对。导出 W3C PROV 与 RO-Crate。

平台原则：监测与推演分开；不做天气预报；每个数字都有来源；证据只增不改；人工证据先审后用；重计算不在 GitHub Actions 上跑。

## 2. 架构（全部实测在运行）
- Cloudflare Worker（everest-facets）：每分钟一轮，实时采集 {len(rt.get('sources', {}))} 个源（地震台 IO.EVN、BIPAD 水位站、EMSC、USGS、尼泊尔国家地震中心、NASA GIBS 卫星图、IODA 网络连通、BIPAD 警报、GDACS、DORIS 信标、ADS-B、新闻、珠峰摄像头缩略图）。最近一轮汇总：{bj(rt.get('updated'))}。
- GitHub Actions：灾种扫描（每小时，由 Worker 触发）、证据包生成（有新信号立即、否则每小时）、每日 InSAR 管线、ADS-B。
- 外部计算：哥白尼 openEO 云端干涉（InSAR）、微软 Planetary Computer（Sentinel-1 RTC 坡面雷达亮度，OCHA 0005 方法）。
- 展示：claude.ai 上的总览页（三维节点图 + 证据链 + 治理审计）、EVEREST MCP 连接器（15 个只读工具）、Claude 插件 1.2.0（10 个技能）。

## 3. 运行实况（GitHub Actions 最近 {len(runs)} 次运行）
""" + "\n".join(f"- {k}：成功 {ok_name[k]} / {v}" for k, v in by_name.most_common()) + f"""

## 4. 坡面雷达基线
376 块坡面，历史影像 {fst.get('scenes', {}).get('d')} / {fst.get('scenes', {}).get('n')} 景已算（来源：facet_status.json，{bj(fst.get('t'))}）。基线完成前不出分级。

## 5. 每日 InSAR 管线（Sentinel-1 Burst 23790，IW1，相对轨道 12）
最新影像对 {(pipe.get('insar_pair') or {}).get('master')} → {(pipe.get('insar_pair') or {}).get('slave')}；状态 {((pipe.get('results') or {}).get('insar_displacement') or {}).get('status')}；平均相干 {((pipe.get('results') or {}).get('insar_displacement') or {}).get('coherence_mean')}。
位移没有稳定参考点，不给毫米数，不用于灾害判断（来源：data/displacement_summary.json，{pipe.get('timestamp_utc')} UTC）。
""")

# ---------- 02 数据源 ----------
S = scan.get("sources", {})
st = Counter(v.get("state") for v in S.values()); lat = Counter(v.get("latency") for v in S.values())
rows = "\n".join(f"| {k} | {v.get('state')} | {v.get('latency') or '—'} | {v.get('n') if v.get('n') is not None else '—'} | {v.get('local') if v.get('local') is not None else '—'} | {v.get('need') or v.get('err') or ''} |" for k, v in S.items())
rtrows = "\n".join(f"| {k} | {'正常' if v.get('ok') else '失败'} | {bj(v.get('at'))} | {(v.get('err') or '')[:80]} |" for k, v in (rt.get("sources") or {}).items())
w("02_数据源与实测状态.md", f"""
# EVEREST 数据源与实测状态

生成时间：{bj(NOW)}。来源：events 分支 hazards/scan.json（灾种扫描 {bj(scan.get('updated'))}）、facet-live 分支 rt.json（实时采集 {bj(rt.get('updated'))}）。

## 1. 联合国减灾署 281 种灾害的逐个实测扫描
按 UNDRR–ISC《灾害信息简介》（HIPS）281 种灾害，每小时实测 {len(S)} 个公开来源：正常 {st.get('ok', 0)}，需要密钥 {st.get('key', 0)}，失败 {st.get('fail', 0)}。
时效分级（按每种灾害最快的非新闻来源）：{json.dumps(scan.get('by_latency'), ensure_ascii=False)}。
281 种灾害的覆盖：{json.dumps(scan.get('by_state'), ensure_ascii=False)}（local=尼泊尔/珠峰范围内有记录，global=外地有记录，observed=有持续观测，ok_none=来源正常但 90 天无记录）。

| 来源 | 状态 | 时效 | 记录数 | 本地记录 | 备注 |
|---|---|---|---|---|---|
{rows}

## 2. 实时采集（Cloudflare Worker）
| 源 | 状态 | 最近取数 | 错误 |
|---|---|---|---|
{rtrows}

## 3. 已知局限（事实）
- 6 个来源需要注册密钥（Cloudflare Radar、Global Forest Watch、NASA FIRMS、OpenAQ、ACLED、ReliefWeb），未注册前不取数。
- GDELT 新闻接口对云服务器 IP（Cloudflare、GitHub）普遍限流，改用尼泊尔媒体 RSS 作替代。
- EvK2Minoprio 金字塔摄像头图像文件最后修改于 2024-11-24，已停更；YouTube 珠峰直播缩略图本身滞后。
- 尼泊尔 BIPAD 水位站 15 个中只有部分在报；停报原因无法从数据判断。
""")

# ---------- 03 事件与证据包 ----------
evs = idx.get("events", {})
blocks = []
for eid, m in sorted(evs.items(), key=lambda kv: kv[1].get("t", ""), reverse=True):
    p = J(f"events/{eid}.json", "events") or {}
    tl = p.get("timeline") or []
    kinds = Counter(x.get("kind") for x in tl)
    srcs = Counter((x.get("src") or "").split(" · ")[0] for x in tl if x.get("kind") in ("SUPPORTING", "CONTRADICTORY"))
    o = (m.get("ots") or [{}])[-1]; v = o.get("verify") or {}
    lines = "\n".join(f"  - {bj(x.get('t'))} · {x.get('kind')} · {x.get('src')}：{(x.get('text') or '')[:160]}" for x in tl[:14])
    blocks.append(f"""### {p.get('title') or eid}
- 编号：{eid}；类型：{p.get('kind')}；HIPS：{', '.join(p.get('hips') or [])}；地点：{p.get('place')}（{p.get('lat')}, {p.get('lon')}）
- 首个信号：{bj(p.get('t'))}；证据包生成：{bj(p.get('built'))}
- 时间线 {len(tl)} 条：支持 {kinds.get('SUPPORTING', 0)}，矛盾 {kinds.get('CONTRADICTORY', 0)}，缺失 {kinds.get('MISSING', 0)}；独立来源：{', '.join(f'{k}×{n}' for k, n in srcs.most_common(8))}
- 存证：{len(m.get('ots') or [])} 个快照；最新快照比特币状态 {o.get('status')}（区块 {o.get('bitcoin_block') or '待确认'}）；独立核对 {v.get('passed')}/{v.get('total')}
- 时间线前若干条：
{lines}
""")
by_src = Counter(r.get("src") for r in recs)
w("03_事件证据包与全球灾种记录.md", f"""
# EVEREST 事件证据包与全球灾种记录

生成时间：{bj(NOW)}。来源：events 分支 index.json、events/<编号>.json、hazards/records.json。

## 1. 自动发现、已出证据包的事件（近 60 天，共 {len(evs)} 个）
规则：尼泊尔 / 珠峰范围内，BIPAD 灾害事件库有伤亡记录、GDACS 警报、USGS 崩塌、水位越线，或两家以上媒体报道的雪崩、冰湖溃决、泥石流、滑坡，生成事件候选并出证据包。证据包只陈述“谁在什么时候记录了什么”，不判断成因、不预测。

{chr(10).join(blocks)}

## 2. 灾种扫描的原始记录
最近一次扫描共 {len(recs)} 条记录（含全球），按来源：
""" + "\n".join(f"- {k}：{n}" for k, n in by_src.most_common()) + """

这些记录是各公开来源原样发布的内容，只说明来源记录了什么、什么时候；同一事件可能在多个来源重复。
""")

# ---------- 04 生态与相关方（只写公开、可核对的角色） ----------
w("04_相关方与生态.md", f"""
# 喜马拉雅灾害数据与证据生态：相关方（公开角色）

本节只写各机构公开、众所周知的职能，不推测其立场。

## 尼泊尔政府与本地机构
- 尼泊尔国家减灾管理局（NDRRMA）运营 BIPAD 门户：灾害事件库、警报、实时水位与空气质量站。本平台的主要本地来源。
- 尼泊尔水文气象局（DHM）：水文遥测站网，数据经 BIPAD 转发。
- 尼泊尔国家地震中心（NSC）：本地地震测定。
- 尼泊尔保险管理局（Nepal Insurance Authority）：监管保险业，发布理赔统计。
- 尼泊尔电力局（NEA）与独立发电商协会（IPPAN）：水电项目业主。
- 萨加玛塔污染控制委员会（SPCC）、喜马拉雅救援协会（HRA）、尼泊尔登山协会、探险运营者：珠峰登山季的现场组织。

## 区域与国际机构
- ICIMOD（国际山地综合发展中心）：兴都库什—喜马拉雅区域冰川、冰湖、灾害研究与数据。
- 意大利 OGS 与 EvK2CNR、尼泊尔科学技术院（NAST）：运营珠峰金字塔实验室地震台（IO.EVN）；据 2025 年 11 月报道已加装加速度计和次声传感器以研究冰川冰震（数据是否公开未说明）。
- USGS、EMSC、GEOFON、EarthScope：地震目录与波形。
- 欧盟哥白尼（Sentinel-1/2、应急制图 EMS、全球洪水监测 GFM）、NASA（GIBS、FIRMS、EONET）、JAXA/日本气象厅（向日葵 9 号）、EUMETSAT（Meteosat IODC）。
- GDACS（联合国与欧盟全球灾害预警协调系统）、OCHA（HDX、ReliefWeb）、IFRC（GO、Montandon）。
- 世界银行等推动的灾害风险融资与参数保险：赔付取决于预先约定的触发条件（例如“地震”）。

## 开源与数据基础设施
- OpenTimestamps、FreeTSA、DigiCert TSA、Sigstore/Rekor：存证与透明日志。
- W3C PROV、RO-Crate：溯源与数据打包标准。
- 高山亚洲冰湖溃决数据库 HMAGLOFDB（ICIMOD / 乌得勒支大学等，ESSD 2023）。
- Claude 生态：MCP 官方注册表（目录 {len(cat.get('mcp', []))} 个相关服务器）、官方插件市场（{len(cat.get('plugins', []))} 个插件）、官方技能库（{len(cat.get('skills', []))} 个技能）。

## 一个公开报道的案例（单一来源，未独立核实）
据 Insurance Business Asia 报道：2026 年 8 月 26 日朗塘国家公园上方冰川崩塌，USGS 认为很可能由涉及冰川的快速坡体失稳引发，造成特里苏里河谷泥石流；报道称上千人遇难、近 4000 人失踪；尼泊尔保险业初步索赔约 258.7 亿卢比；Upper Trishuli-1 水电站的参数保险以地震为触发条件，事件不是地震，赔付取决于触发条件是否满足。
本平台同日记录：GDACS 发布“Flood in Nepal（红色）”，证据包编号 gdacs-FL-2026-08-26。
""")

# ---------- 推演要求：只用使用者自己写的文字（网页表单 → 工作流输入 requirement → 环境变量 MF_REQUIREMENT），本脚本不代写 ----------
REQT = os.environ.get("MF_REQUIREMENT", "").strip()
if len(REQT) < 10: sys.exit("缺少推演要求：请在网页表单里自己填写（至少 10 个字）")
open(os.path.join(OUT, "requirement.txt"), "w").write(REQT)
open(os.path.join(OUT, "context.txt"), "w").write("种子材料来自 EVEREST 平台的真实数据（截至 " + bj(NOW) + "），每个数字附来源。推演结果单独保存、标注为推演，不进入证据链。")
for k, v in W.items(): open(os.path.join(OUT, "seed", k), "w").write(v)
json.dump({"generated": NOW, "scenario": SCEN, "files": {k: len(v.encode()) for k, v in W.items()}}, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
print("seed files:", {k: len(v.encode()) for k, v in W.items()})

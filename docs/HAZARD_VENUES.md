# 281 种灾害的专业顶刊顶会和可引用数据

**完整表格（自动更新）**：[events 分支 `hazards/HAZARD_VENUES.md`](https://github.com/Yizebaba/EVEREST-/blob/events/hazards/HAZARD_VENUES.md)，原始数据 [`hazards/venues.json`](https://github.com/Yizebaba/EVEREST-/blob/events/hazards/venues.json)。

每种灾害列出：

- **专业顶刊顶会前三**：2020 年以来该主题论文 ≥ 5 篇的期刊或会议，去掉综合性大刊后按 h 指数排序；
- **可引用的数据论文**：ESSD、Scientific Data、Geoscience Data Journal、Data in Brief 四本数据期刊里最相关的三篇，可作数据源或在证据包里引用；
- **高被引方法论文**：2020 年以来被引最多的三篇。

## 怎么生成

`tools/venue_rank.py` 在 GitHub Actions 上查 OpenAlex（公开学术数据库，免费），`tools/venues_report.py` 生成表格。每天 02:41 UTC 自动续跑。
OpenAlex 按天计额度：不配密钥每天约 30 种，配了免费密钥（GitHub Secret `OPENALEX_API_KEY`，在 <https://openalex.org/settings/api> 取）一次跑完 281 种。

## 怎么用到证据链里

- **证据包引用**（证据包 v18 起）：事件带灾害编码时，证据包附上该灾种的数据论文和专业期刊（`references` 字段），RO-Crate 里写成 `citation`。只作背景参考，不进时间线、不当作本次事件的证据。
- **找新数据源**：数据论文里有公开接口、持续更新的数据集，可以在总览页“证据链 → 证据源”登记，实测通过后接入 `tools/hazard_scan.py`。

## 局限

h 指数衡量期刊整体影响力，不是该灾种的专业排名；检索词有歧义时会混进无关期刊。会议在 OpenAlex 里收录不全。这份表是找文献和数据的起点，引用前请人工确认。

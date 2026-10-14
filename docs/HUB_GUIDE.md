# 总览页说明

[总览页](https://claude.ai/artifact/6heopu2wizEAFMJJLDs44H)上只放数据和操作，说明都在这里。页面上的“说明 ↗”会跳到对应的一节。

**总原则：只监测，不预测。** 不发预警、不给风险概率、不做天气预报、不判断成因或责任。某个站停报，不代表那里一切正常。

目录：[运行状态](#run) · [数据来源](#sources) · [证据链](#chain) · [核对存证](#verify) · [人工证据](#upload) · [证据源](#evsrc) · [事件详情](#event) · [流程阶段与质量目标](#stages) · [治理与审计](#gov) · [知识库](#kb) · [技能](#skills) · [连接器](#conn) · [插件](#plug)

---

<a name="run"></a>
## 运行状态

- **汇总时间**：见[数据怎么同步](#sync)。
- **各采集环节**：
  - 实时采集：Cloudflare Worker 每分钟跑一轮，各数据源 5–30 分钟取一次。
  - 坡面雷达监测：Cloudflare Worker 加微软 Planetary Computer，每分钟处理一批。
  - 每日 InSAR 管线：GitHub 计划任务每天检查 4 次新影像，干涉计算在哥白尼 openEO 完成。管线读云端干涉的真实结果，没有新结果就标“不可观测”。干涉图没有做参考点校正，不能用来判断灾害。
  - ADS-B：Cloudflare 连不上 OpenSky，所以由 GitHub 运行器代取，每 15 分钟一次。显示 0 架可能只是附近没有接收站，不等于没有飞机。
- **IO.EVN 地震台**：意大利 OGS 运营，位于金字塔实验室（海拔 5010 m，距峰顶约 11 km）。Cloudflare 每 5 分钟从 GEOFON 读一次数据头，只判断台站在不在线。没有数据时，采集程序会向 GEOFON 查询台站最后一条数据的时间。停发可能是停电、通信中断或 GEOFON 转发延迟，本页不判断原因。波形图是较早的示例，不是最新。图上的尖峰可能来自地震、冰震、崩塌或人为噪声，本页不判断；平直段是数据中断（卫星链路）。
- **河流水位**：阿伦河最上游两站、博特科西口岸站长期停报，跨境上游来水没有公开预警；Imja 湖下游站自 4 月起读数不变，疑似故障。
- **卫星云图**：左边是向日葵 9 号可见光（NASA GIBS，每 10 分钟），右边是 Meteosat 雪 RGB（EUMETView，雪显示为红色调，每 15 分钟）。范围 27.3–28.7°N、86.2–87.7°E。页面每 3 小时存一张。
- **冰川流速（ITS_LIVE）**：NASA JPL 的年度合成产品，直接读公开 Zarr，不经过仓库管线。不是实时数据；同一数据块覆盖不到北坡绒布冰川。
- **仓库文件**：本页只取实测量；文件里的天气、模型打分、风险等级都没有接入。
- **链路图**：取自原架构的 SYSTEM HEALTH。每一环对应哪些阶段是本页自己归的，不是框架规定。点“模拟仓库 20 分钟没有新信号”可以看到链路怎么变。

<a name="sync"></a>
## 数据怎么同步

- **页面打开时**（装了 EVEREST 连接器并允许本页使用）：页面直接订阅连接器，实时快照每分钟、事件证据包每 2 分钟检查一次，数据一变页面就变；页面切到后台时暂停，回来时立刻补拉。
- **证据包**：Worker 发现新事件或新信号时立刻触发 GitHub 生成；总览页的人工证据清单（`manual.json`）一变也会触发。
- **每小时同步任务**：只作为后备，给没装连接器的人看；人工证据清单目前也由它写进仓库。

<a name="sources"></a>
## 数据来源

| 类别 | 来源 |
|---|---|
| 水位、灾害警报 | 尼泊尔国家减灾局 BIPAD 门户（转发尼泊尔水文气象局遥测） |
| 地震台 | GEOFON / OGS 国际台网 IO（doi:10.7914/SN/IO）；EarthScope（NK.KKN） |
| 地震目录 | 美国地质调查局（USGS）、EMSC、尼泊尔国家地震中心 |
| 卫星目录与影像 | 哥白尼数据空间目录（OData 公开查询）；微软 Planetary Computer；NASA GIBS（向日葵 9 号）；EUMETSAT EUMETView（Meteosat IODC） |
| 冰川流速 | NASA JPL ITS_LIVE（公开 S3 Zarr） |
| 网络连通 | IODA（佐治亚理工） |
| 全球灾害 | GDACS |
| 卫星信标 | IGN/IDS DORIS |
| 航空 | adsb.lol、adsb.fi、airplanes.live、OpenSky（非商业） |
| 洪水与国际记录 | 哥白尼 GFM、哥白尼应急制图（EMS）、IFRC Montandon |

采集脚本和数据都在本仓库：数据分支见 [README](../README.md#仓库结构)。

<a name="chain"></a>
## 证据链

每个自动发现的事件，都把公开来源对齐到同一条时间线：谁在什么时候记录了什么、哪些来源断了。只陈述记录，不判断成因。

证据包由这些部分组成：

| 环节 | 内容 |
|---|---|
| 发现事件 | Worker 每 5 分钟看 BIPAD 洪水警报、USGS 崩塌、GDACS、水位越线 |
| 地震台 | IO.EVN（珠峰）和 KKN（加德满都北）两台核对；一台有、一台没有的标“矛盾”；缺数时段标“缺失” |
| 地震目录 | USGS、EMSC |
| 水位站 | 事件 80 km 内的 BIPAD 站：谁在报、谁停了 |
| 网络连通 | IODA，事件所在区 |
| 卫星 | Sentinel-1/2 事件前后影像；哥白尼 GFM 自动洪水范围（每次过境都会生成，不代表测到了洪水） |
| 国际记录 | 哥白尼应急制图；IFRC Montandon（需要令牌） |
| 存证 | 每一版存不可变快照，加 OpenTimestamps 公开时间戳，之后升级为比特币区块确认 |

判定标记：**支持**（这个来源记录到了），**缺失**（该有记录但没有，或来源断了），**矛盾**（和其他来源对不上），**中性**（相关记录，但不直接支持或反对）。

<a name="hazards"></a>
## 灾种 281

联合国减灾署 2025 版 281 种灾害，每小时逐个实测一次（`hazards` 工作流；由 Worker 每小时触发，GitHub 自带的定时任务常延迟几小时，只作后备）：

- **33 个公开来源**：尼泊尔政府 BIPAD 事件库（47 类，含交通、火灾、蛇咬、食物中毒、疫情、毒气和辐射泄漏等）、BIPAD 警报和空气质量站、NASA EONET、USGS、GDACS、NOAA 空间天气、NASA 近地天体与火球、CelesTrak、WHO 疫情通报与 FluNet、WOAH 动物疫情、openFDA 召回、CISA 已利用漏洞、Have I Been Pwned、IODA、尼泊尔央行汇率、Safecast、Sentinel-5P、海啸预警中心、NOAA NCEI、IOC 潮位站、IBTrACS、NSIDC 海冰、GBIF、尼泊尔英文媒体和谷歌新闻 RSS。6 个需要密钥（Cloudflare Radar、Global Forest Watch、FIRMS、OpenAQ、ACLED、ReliefWeb），没配置时标“需密钥”。
- **新闻匹配**：每种灾害一组人工写的英文匹配词（`tools/hazard_keywords.py`），谷歌新闻的结果要求标题里有尼泊尔或西藏的地名。
- **时效**：每个来源按发布方更新频率分三级——实时（分钟到 1 小时）、准实时（几小时到 1 天）、定期（每周或更慢、档案库）；每种灾害取除新闻外实测可用来源里最快的一级（scan.json 的 `rt_tier`、`by_latency`）。新闻 RSS 是实时的，但只算线索，单列。
- **状态**：本地有记录 / 外地有记录 / 有持续观测（只有卫星或站网在测，没有“发生了”的记录）/ 来源正常但 90 天无记录 / 需密钥 / 来源失败。
- **和事件的关系**：尼泊尔死亡加失踪 3 人以上，或高山区自然灾害有人死亡失踪，单独做证据包；其余记录按距离（150 km）和时间（前 1 天到后 5 天）挂到附近事件的时间线上，按伤亡、同类、距离排序取前 25 条。

逐条对照：[`docs/HAZARDS_281.md`](HAZARDS_281.md)；原始结果在 events 分支 `hazards/`。

<a name="venues"></a>
**各灾种的专业期刊和可引用数据**：[`docs/HAZARD_VENUES.md`](HAZARD_VENUES.md)。证据包详情里的“可引用的数据和期刊”就来自这里，只作背景参考。

<a name="history"></a>
**历史记录**：事件在高山亚洲范围内时，证据包现取高山亚洲冰湖溃决数据库（HMAGLOFDB，ICIMOD 和乌得勒支大学维护，GitHub 开发版滚动更新），记下取数时的提交号：
- 事件前 1 天到后 5 天、80 km 内有收录的溃决 → 进时间线，标“支持”，链接到那一版数据库文件；
- 事件 30 km 内历史上收录过的溃决 → 证据包详情“历史记录”，每条带数据库编号和原始文献。只是数据库记录，不是这次事件的证据，不用来推测。
- 作者判为可疑、已剔除的条目（`HMAGLOFDB_removed.csv`）不读。

<a name="verify"></a>
## 核对存证

1. 在“证据链”里点“存证快照 ↗”和“.ots 证明 ↗”，把两个文件下载到同一个文件夹。
2. 安装 OpenTimestamps 客户端：`pip install opentimestamps-client`
3. 运行 `ots verify 快照文件名.json.ots`。它会显示这份文件最晚在哪个比特币区块的时间已经存在。文件改动一个字节，核对就会失败。

刚生成的存证显示“等待区块确认”，通常几小时后由证据包流程自动升级为“已上链”。

**RFC 3161 时间戳**（证据包 v17 起，和比特币时间戳互为备份，几秒内就有）：同一快照旁边还有 `.FreeTSA.tsr` 和 `.DigiCert.tsr`。用 FreeTSA 的核对：

```bash
curl -sO https://freetsa.org/files/cacert.pem && curl -sO https://freetsa.org/files/tsa.crt
openssl ts -verify -in 快照.json.FreeTSA.tsr -data 快照.json -CAfile cacert.pem -untrusted tsa.crt   # 显示 Verification: OK
```

**Sigstore 签名**（证据包 v19 起）：快照旁的 `.sigstore.json` 证明这份文件是本仓库 `evidence.yml` 工作流生成的，签名同时记入公开透明日志 Rekor（总览页“Sigstore 透明日志 ↗”）。核对：

```bash
cosign verify-blob 快照.json --bundle 快照.json.sigstore.json \
  --certificate-identity https://github.com/Yizebaba/EVEREST-/.github/workflows/evidence.yml@refs/heads/events \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com    # 显示 Verified OK
```

每个证据包还导出 W3C PROV 溯源记录（`events/<编号>.prov.json`）和 RO-Crate 描述（`events/crates/<编号>/ro-crate-metadata.json`），任何标准工具都能读。思路和出处见 [`EVIDENCE_CHAIN_RESEARCH.md`](EVIDENCE_CHAIN_RESEARCH.md)。

<a name="upload"></a>
## 人工证据

- **能提交什么**：现场照片、视频、文档（最大 20 MB）、新闻或通报链接、目击记录。上传文件需要能编辑总览页；其他人可以提交链接和文字记录。
- **指纹**：提交前浏览器先算出 SHA-256 指纹。文件改动一个字节，指纹就对不上。
- **来源记录**：照片或视频如果带 C2PA 来源记录（新款手机、相机和部分软件会写入），页面会标出来并显示生成工具；页面里不验签，可以到 [contentcredentials.org/verify](https://contentcredentials.org/verify) 核对。照片里相机记录的拍摄时间也会读出来，和填写的时间相差超过 3 小时会标出。
- **存证**：每小时把所有条目的指纹写进公开仓库（events 分支 `manual.json`），并用 OpenTimestamps 存证，证明这份材料最晚在那个时间已经存在、之后没被改过。
- **核实**：所有者标“待核实 / 已采信 / 不采信”。只有“已采信”的内容会公开并进入事件时间线；链接类证据会再抓一次内容算指纹，并请求互联网档案馆存一份副本。
- **不公开的**：提交人姓名、账号、文件本身。
- **提交前请确认**：你有权分享这份材料；它不含可识别的他人隐私（人脸、门牌、电话等），或已经处理过。说明里只写看到了什么，不写推测。

<a name="evsrc"></a>
## 证据源

“证据源”子页列出每个证据包都会自动查询的公开来源，以及大家登记的新来源。想加新的来源（别的台网、水文站、卫星产品、通报渠道），在这里登记；所有者评估后写结论：待评估 / 计划接入 / 已接入 / 不接入。

只收公开或可授权的观测记录；不收天气预报和预测类产品；需要重计算的在外部平台跑，只接结果。不要在登记里填密码或密钥。

<a name="event"></a>
## 事件详情

- **地震台信号图**：两台的 1–5 Hz 信号，相对各自背景，对数刻度。上面是 IO.EVN（珠峰），下面是 KKN（加德满都北）。蓝色虚线是第一条公开信号的时间，红色点线是背景的 5 倍。没有数据的分钟留空，不画成 0。
- **地震台强信号**只说明那一刻台站记录到较强震动，来源要结合其他证据。
- **事件候选**：要有多个独立类别的证据支持、没有强反证。具体数量由策略设定，页面没有设定这个数。进入候选后自动进入人工审核，附证据包和缺失证据说明。这只是内部通知；官方预警由主管单位发布。

<a name="stages"></a>
## 流程阶段与质量目标

质量目标的数值是示例默认值，原框架写明待主管单位确认；节点延迟是示例数据。超标只做标记，不改变节点状态，状态由质量闸门判定。只有审核员能改目标。选中一档后，球里不属于这一档的节点会变暗。

<a name="gov"></a>
## 治理与审计

- **许可证登记**：框架 A13 要求登记许可证和跨境许可清单，敏感信息最小权限。页面没有预填任何许可证内容，因为没有逐个核对过。只有被所有者指派为“数据管理员”的人写的登记才算数，别人写了会被忽略。
- **审计日志**：共享库里每个人只能写自己的日志，别人改不了。每条记录带上一条的哈希，本人事后改动或删除会被校验发现。这是页面内的校验，不等于服务器端的不可变日志。本地模式（没登录）的日志只存在你的浏览器里。

<a name="kb"></a>
## 知识库

流程图里的“驳回后归档”和“事件知识库”就是这里。驳回或解除一条计算异常后，它会自动进来。标签取自框架 A11：CONFIRMED、FALSE_ALARM、MISSED、UNKNOWN。MISSED 是事后发现的漏报，由审核员手动改。

<a name="skills"></a>
## 技能

技能和 Claude 里的“技能”是同一种文件（SKILL.md）。内置技能在仓库 [`plugin/skills`](../plugin/skills)；大家新建的技能存在总览页共享库。都能在页面上运行（会调用 EVEREST 连接器），也能下载后装进自己的 Claude。

装进 Claude：

1. 点某个技能的“下载”，得到 SKILL.md。
2. Claude 设置 → 技能 → 上传（先放进一个和技能同名的文件夹）。
3. 或者在对话里把 SKILL.md 内容贴给 Claude，说“帮我存成技能”，会出现一键保存卡片。
4. 想一次装多个，到“插件”标签自选技能打包。

写技能时不要写预测、风险概率或预警发布。保存后，所有能打开总览页的人都能看到和运行。

<a name="conn"></a>
## 连接器

EVEREST 连接器和 Claude 里的“连接器”是同一个：在对话里问珠峰现状，Claude 会调用它；总览页也调用它刷新数据、运行技能。全部 15 个工具都是只读的，只能查询，不能改任何数据。

添加方法：

1. Claude 设置 → 连接器 → 添加自定义连接器。
2. 名称填 **EVEREST**（页面按这个名字找它），地址填 `https://everest-facets.yizebaba.workers.dev/mcp`。提示“无法检查登录方式”时选“仍然继续”，登录相关的框留空。
3. 回到总览页点“用连接器刷新本页数据”，第一次会问你是否允许。
4. 在任意对话里问“珠峰现在哪些站停发”，Claude 会直接调用它。

**接入申请**：想接入新的数据源或别的连接器（MCP、REST 接口、文件下载），在“接入申请”里登记。所有者评估后写结论；接入后会变成 EVEREST 连接器里的新工具。不接天气预报类数据。

<a name="plug"></a>
## 插件

插件 = 连接器 + 一组技能，打成一个包，格式和 Claude Code 的插件一样。

- **Claude Code 直接从仓库装**：
  ```
  /plugin marketplace add Yizebaba/EVEREST-
  /plugin install everest@everest
  ```
- **下载的 .zip**：解压后在 Claude Code 里运行 `/plugin marketplace add ./文件夹名`，再 `/plugin install 插件名@插件名`。
- **Claude 网页和桌面**：连接器按[连接器](#conn)一节添加；技能在压缩包 `plugin/skills` 下，按[技能](#skills)一节上传。

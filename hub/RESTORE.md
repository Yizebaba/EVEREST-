# 如何复原（2026-10-10 14:xx 这次改动）

本次改了两处，原件都在 backup/ 里，sha256 已记录。

1. 页面背景（everest-hub-v25.html）
   - 只改了两行：`const BGM_DEFAULT="none"` 和 `<main id="stage" ... data-bg="none">`。地震背景的代码、素材都没删。
   - 恢复地震背景：把这两处的 "none" 改回 "quake"；或者直接重新发布 backup/everest-hub-v24.html
     （sha256 88b8c13b8e80b50399918532dde9f5e0670cf18742eee5c78f426996bfc08d1b）。
   - 线上页面也有版本历史：发布前的上一版是 Version 26，可在页面的版本记录里回退。

2. 后端（everest-core.zip）
   - 新增：adapters_ext.py 末尾的 ClmsSnow / summarize_sce_codes、connectors.py 里 clms_snow 一条、tools/clms_snow_counts.py、对应测试。没有改动任何已有函数。
   - 恢复：用 backup/everest-core-before-snow.zip
     （sha256 b7bf74f345b0dc249546426b7220ff371d944b5725905b45857c2138acd636ed）替换即可。

---
# 第二次改动（标签收起/悬浮 + Google/微信登录）

- 页面：everest-hub-v26.html（线上 Version 28）。复原到上一版：重新发布 backup/everest-hub-v25.html
  （sha256 a5358b997a7c1556f0d97e0663eab38c8f9dce99fa78c3a6eab60e62151bb43a），或在版本记录里回退到 Version 27。
- 后端：新增 everest_core/auth.py、api.py 的 /auth/* 路由、service.auth 的会话过期判断、server.py 的 auth 配置、tests/test_auth.py。
  复原：用 backup/everest-core-before-login.zip（sha256 8d5eb5563e32ee4823033cc5dae4f11ce0481dc137563e5592b004c2c74c1141）替换。

---
# 第三次改动（Google / 微信合并为一个“登录”入口）
- 页面：everest-hub-v27.html（线上 Version 29）。复原：重新发布 backup/everest-hub-v26.html（sha256 7ccfc919f017f817d7cef7728da95c0a7642823c743c647fd170938257d98152），或在版本记录里回退到 Version 28。
- 后端没改。

---
# 第四次改动（新增“南坡”标签 + 南坡气象站适配器）
- 页面：everest-hub-v28.html（线上 Version 30）。复原：重新发布 backup/everest-hub-v27.html（sha256 084939460b979b0422340f466395805466b2946c9ee4330b55f86056fff554bf），或回退到 Version 29。
- 后端：adapters_ext.py 末尾新增 NatGeoEverestAWS，connectors.py 新增一条，新增测试。复原：用 backup/everest-core-before-south.zip（sha256 9214cc9e6d760d3c7b23d523159a41cbf0c7836a85759897d307a122d66ea2ec）。

---
# 第五次改动（南坡真实档案数据 + 适配器列名）
- 页面：everest-hub-v29.html（线上 Version 31）。复原：重新发布 backup/everest-hub-v28.html（sha256 a62e27c9d672b12998fce23826403bb8aa92b6838ad07efa755ee44f85749fb1），或回退到 Version 30。
- 后端：南坡适配器加入真实列名（SOUTH_COLMAP / SOUTH_FILES），登记表更新。复原：backup/everest-core-before-southdata.zip（sha256 a1ffd2c7ac081837152b4127c3ec5a1497c469b662aae178c7229e23a50fcc54）。
- 仓库：Yizebaba/everest-insar-pipeline 新增 data-probe 分支（主分支没动）。删除该分支即可撤销。

---
# 第六次改动（“南坡”标签换成实时监测）
- 页面：everest-hub-v30.html（线上 Version 32）。原来的南坡气象档案（2019–2025）被替换。
- 复原：重新发布 backup/everest-hub-v29.html（sha256 b18c596dbf25d18441cd0e5a7b38e26db587dbaf47b772816bea040681703873），或在版本记录里回退到 Version 31。
- 数据采集在 GitHub：main 分支的 .github/workflows/live.yml（删除即停止），脚本在 data-probe 分支，数据在 live-data 分支。

---
# 第七次改动（南坡面板接入仓库里的公开接口）
- 页面：everest-hub-v31.html（线上 Version 33）。新增三个小节：卫星过境（哥白尼目录）、Khumbu 冰川流速（ITS_LIVE）、仓库每日 InSAR 管线产物（附核对说明）。
- 复原：重新发布 backup/everest-hub-v30.html（sha256 d1bff1fb4f64939adb68e44a592e47680215372f2c756131ebff3411b20b2573），或在版本记录里回退到 Version 32。
- 仓库：data-probe 分支的 tools/live_collect.py 新增第 5–7 段（sat.json / pipeline.json / itslive.json）。撤销：git revert 这两次提交（"live: add repo public entry points…"、"live: ITS_LIVE keep only…"）。main 分支没动。

---
# 第八次改动（运行球接入实测链路）
- 页面：everest-hub-v32.html（线上 Version 34）。中间大球改为“完整流程（实测）”，点开看三条链路；节点里新增“实测流程”12 个小球；“仓库”模块按实测核对着色（写死输入的模块显示“不可观测”）。
- 复原：重新发布 backup/everest-hub-v31.html（sha256 21ea5cfdced372c3c5dfd6a16e386b7e71bdeebb76fb5ae970a49117545ecc62），或回退到 Version 33。
- 仓库 data-probe 分支：tools/live_collect.py 第 8 段（flow.json）；新增 tools/cred_probe.py + .github/workflows/cred-probe.yml（只报告授权有没有、能不能用，结果在 probe-out 分支）。撤销：删除这两个文件和 probe-out 分支，revert 第 8 段提交。main 分支没动。

---
# 第九次改动（真实云端干涉跑通并接入运行球）
- 用户在仓库 Secret 配了 OPENEO_REFRESH_TOKEN（检查通过，令牌内容未读取）。
- 仓库 data-probe 分支新增 tools/insar_cloud_run.py + .github/workflows/insar-cloud.yml：用 main 的 cloud_insar_pipeline.py 在哥白尼 openEO 提交/取回干涉，产物（预览图、统计、元数据，不含大文件）在 insar-out 分支。在 openEO 账号里新建了一个任务 Everest_InSAR_20260928_20261010（消耗该账号月度点数）。
- 页面：everest-hub-v33.html（线上 Version 35）。完整流程 12/12，附最新干涉图和三对统计。
- 复原：重新发布 backup/everest-hub-v32.html（sha256 0ca1dc3729acff80ee97f9af1b173345fcbf9373959f31d2138e9fe7263fc4c7），或回退到 Version 34。撤销仓库部分：删除上述两个文件和 insar-out 分支。main 分支没动。

---
# 第十次改动（冰坡雷达亮度：Cloudflare 外部运行，接入运行球）
- 外部：Cloudflare Worker everest-facets（https://everest-facets.yizebaba.workers.dev），代码在 data-probe 分支 cf-worker/，D1 数据库 everest-facets，密钥 GH_TOKEN（用户配置）。结果和进度写到仓库 facet-live 分支。
- 页面：everest-hub-v34.html（线上 Version 36）。完整流程里新增 “D. 冰坡雷达亮度” 节点和实时页面链接。
- 复原：重新发布 backup/everest-hub-v33.html（sha256 6d4ab514108af447db2ede6c8e3f51aff2014fe9624ff298f3bc8be41f297124），或回退到 Version 35。
- 停用外部部分：Cloudflare 后台删除 Worker（或在设置里删掉 Cron 触发器）；GitHub 删除 facet-live 分支和那个细粒度令牌。

---
# 第十一次改动（实时源全部接入：Cloudflare 外部运行）
- 外部：everest-facets Worker 新增 src/rt.js，每 5 分钟一轮采集：向日葵 9 号（NASA GIBS）、Meteosat IODC（EUMETView）、EMSC、尼泊尔国家地震中心、IODA 萨加玛塔区、ADS-B（目前被各免费源拒绝）、GDACS、DORIS EVEC（IGN 匿名 FTP，Worker TCP）。实时页面 /rt，接口 /api/rt.json；每小时推 rt.json、每 3 小时推两张云图到仓库 facet-live 分支。
- 页面：everest-hub-v35.html（线上 Version 37）。完整流程新增 “E. 实时源” 和 8 个小球，嵌入两张云图。
- 复原：重新发布 backup/everest-hub-v34.html（sha256 47fc7fa942cbe2b0833cd153c101133a8b24102edc44bb80e14b61eb3ce5356e），或回退到 Version 36。撤销 Worker 部分：git revert data-probe 上 “cf-worker: realtime sources …” 及之后三次 rt 提交，Cloudflare 会自动重新部署。

---
# 第十二次改动（左侧新增“实时”标签）
- 页面：everest-hub-v36.html（线上 Version 38）。“实时”标签：卫星云图、EMSC/尼泊尔地震、IODA 网络连通曲线、GDACS、DORIS、ADS-B 状态，加“打开实时总览”按钮。数据为 15:13 那一轮快照。
- Worker：DORIS 每次最多查 3 个文件、记录诊断信息（data-probe 提交 c0c1ca0）。
- 复原：重新发布 backup/everest-hub-v35.html（sha256 21ad28b05dc5121fe1de95251a8f9900a4e6c7bf2a57ca2bdce600ba58ec335b），或回退到 Version 37。

---
# 第十三次改动（节点核查与修复：南坡数据改由 Cloudflare 采集）
- Worker：水位（BIPAD 15 站）、BIPAD 警报、USGS、IO.EVN 在线状态（读 miniSEED 数据头）迁到 Cloudflare；每轮最多 5 个源轮流；补全各数据源署名；IODA 标签改正；冰坡页面注明 RTC 与 OCHA 原方法差别；DORIS 修复（data-probe c534650 及之前）。
- 页面：everest-hub-v37.html（线上 Version 39）。南坡标签和运行球改用 Cloudflare 数据（16:17 那一轮），完整流程 19/21。
- 复原：重新发布 backup/everest-hub-v36.html（sha256 1cfac440ac346075a0eae888cebc105576b0aa44ef0891b541a06eee2a51d9db），或回退到 Version 38。原 GitHub 采集（live.yml / live-data 分支）未删除，仍可用。

---
# 第十四次改动（“实时”标签新增“设备维护”）
- 页面：everest-hub-v38.html（线上 Version 40）。“实时”标签加“设备维护”一栏：外部监测设备停发清单（发布时快照）+ 打开设备维护台按钮；实时数据刷新到 2026-10-12 20:43（北京）那一轮。
- 新页面：设备维护台 https://claude.ai/artifact/2yqJbpvtSYn6hFc6TSy5mj（独立页面，有自己的数据库；删掉它不影响总览）。每日定时任务用 tools/monitor_sync.py（data-probe ef37d2f）更新它的在线状态。
- 复原：重新发布 backup/everest-hub-v37.html（sha256 edf14a90614c943d98ab374fc581ca23ff87c3ea34510b78d193241c2d705c8b），或回退到 Version 39。

---
# 第十五次改动（“南坡”“实时”并入“运行状态”并整理）
- 页面：everest-hub-v39.html（线上 Version 41）。去掉“南坡”“实时”两个标签，内容并入“运行状态”，按组排列：运行总览（需要注意 + 外部运行组件 9 项）→ 数据源一览（12 个）→ 设备维护 → 水文 → 地震 → 卫星与形变 → 网络与警报 → 信标与空中 → 来源与署名 → 页面内部（示例链路，原运行状态内容）。以前停在“南坡”或“实时”的会自动打开“运行状态”。数据刷新到 2026-10-12 21:18（北京）。
- 复原：重新发布 backup/everest-hub-v38.html（sha256 dfd53db206e65cc3167b0b98146e67fa49c4d0f67d7b2ff508d7b722f36f992a），或回退到 Version 40。

---
# 第十六次改动（设备维护单独成标签；角色并入登录）
- 页面：everest-hub-v40.html（线上 Version 42）。标签变为：节点、阶段、运行状态、治理与审计、知识库、设备维护（原“角色”位置）。“设备维护”含设备维护台入口、停发清单、设备维护提醒说明、权限说明；运行状态里不再重复。“角色”标签取消，内容放进登录窗口：说明“登录 · 登记 · 权限”三件事、你现在的身份与角色、各角色权限、所有者指派角色。
- 设备维护台：改名“设备维护台”（Version 3），新增“提醒”标签（上次运行、结果、规则、提前提醒天数设置）；定时任务“设备维护提醒”改为读取提醒天数并把每次结果写入“提醒”标签。
- 复原：重新发布 backup/everest-hub-v39.html（sha256 dacef1ef80d11c70a872d6d35bc499e7fd714e84d277397e1266aa0e9eda1b78），或回退到 Version 41。设备维护台可回退到 Version 1（scratchpad maint/equipment.v1.html）。

---
# 第十七次改动（设备维护台整体并入“设备维护”标签；左侧面板可拖宽）
- 页面：everest-hub-v41.html（线上 Version 43）。“设备维护”标签里直接是完整的设备维护台：概况、待处理 / 设备 / 记录 / 提醒四个子页、新增设备、设备详情与维修记录（弹窗）、导出 CSV、提前提醒天数。数据存在本页共享数据库的 mt_assets、mt_logs、mt_monitor、mt_reminder、mt_settings 集合（参与者及以上可写）。原“打开设备维护台”“查看上次提醒”两个按钮取消。左侧面板右边缘可拖动调宽（300 px 到屏宽），双击恢复 400 px，宽度记在浏览器里。弹窗层级提到面板之上。
- 数据迁移：17 台外部设备与在线状态从旧设备维护台复制到本页数据库（旧页面没有用户数据）。
- 旧设备维护台页面改为“已并入总览”的说明页（Version 4）；每日“设备维护提醒”改为读写本页数据库。
- 复原：重新发布 backup/everest-hub-v40.html（sha256 1f2e143ce1d33b837000401f7ba1490a78445af8c5785dafaa83c640781277fe），或回退到 Version 42；旧设备维护台回退到 Version 3；定时任务的旧提示词见本节上一条（第十六次）。mt_* 集合可保留，不影响旧版本。

---
# 第十八次改动（实测异常、自动核对、确认框、英文补齐）
- 页面：everest-hub-v43.html（线上 Version 44）。（v42 是中间版本，没有单独发布。）
  - 运行总览：去掉“平台定位调研”；“云端干涉”改为每日管线自动运行（读 main 的 data/cloud_insar/latest.json）；ADS-B 写明缺什么、接通后的取数节奏。
  - IO.EVN：没有数据时说明可能原因，显示最后数据时间（来自实时采集）。
  - 仓库 InSAR“需核对”改为发布时自动核对 3 项（影像对与数值、主影像日期、云端干涉）。
  - 计算异常：4 条示例换成 6 条实测事实（IO.EVN 无数据、Kodari 停报、阿伦河上游停报、Imja 下游读数异常、8·26 吉隆冰岩崩与洪水、InSAR 数值不变）。
  - 审核、升级、确认、拒绝、驳回、解除、放行、下架、连接、断开先弹“取消 / 确定”，登录窗口说明里加了一条。
  - 英文：新内容补齐约 370 条翻译；容易误伤的短词改为整句匹配。
- Worker（data-probe 70ce8a1）：IO.EVN 无数据时向 GEOFON 可用性接口查最后数据时间；ADS-B 连通时每 5 分钟、不通时每 60 分钟。复原：回退该提交。
- 复原：重新发布 backup/everest-hub-v41.html（sha256 691a3e6ae3459d37e8cc24b4e8d2007a21db1dd3ed56da36491c7d61912490fb），或回退到 Version 43。

---
# 第十九次改动（总览数据自动更新）
- 页面：everest-hub-v44.html（线上 Version 45）。登录后订阅本页数据库 live/rt、live/fs、live/img、mt_monitor/latest，有新数据就替换嵌入的快照，重算运行总览、数据源、需要注意；本地模式仍是发布时快照。新增数据库规则：live、mt_monitor、mt_reminder 只有所有者能写（其余 27 条规则不变）。
- 新定时任务“总览实时同步”（每小时）把 facet-live 分支的 rt.json、facet_status.json、两张云图和设备在线状态写进上述文档。
- Worker（data-probe 5e591de）：D1 写入控制，每 3 分钟停 1 分钟，last_tick 每 10 分钟写一次。ADS-B 改由 GitHub 运行器代取（adsb-live 分支，d9c65b9）。
- 复原：重新发布 backup/everest-hub-v43.html（sha256 3f97aa02b3188ede2f7a9d57b77f3e85b77bb3cb99d5a9b90f416e95f41e24d8）并带回原 27 条规则，或回退到 Version 44；停用定时任务“总览实时同步”。

---
# 第二十次改动（技能 / 连接器 / 插件）
- 页面：everest-hub-v45.html（线上 Version 46）。新增“技能”“连接器”“插件”三个标签：连接器标签通过 mcp 能力调用你在 Claude 里添加的 EVEREST 连接器（打开页面时若已允许会自动用它刷新数据），7 个工具可“试一下”；技能标签可查看 4 个技能全文，其中两个可在本页运行（sample 能力，运行中调用连接器）；插件标签说明包内容和安装命令。新增能力声明：mcp（EVEREST，7 个只读工具）、sample。
- Worker（data-probe 5fdbdcc、0675c00）：/mcp 连接器。仓库：plugin/（插件、技能）、.claude-plugin/marketplace.json。
- 复原：重新发布 backup/everest-hub-v44.html（sha256 294b298bdc448e231c58aec306a17a01a983d95bf7fb2a6bf45f506d296031a7）并去掉 mcp、sample 能力，或回退到 Version 45。

---
# 第二十一次改动（英文补齐；源文件改由仓库维护）
- 页面：hub/everest-hub.html（线上 Version 47）。节点名称 18 条、技能说明补英文；9 个标签中英文切换自检无残留。
- 从这次起，总览页源文件以仓库 hub/everest-hub.html 为准；之前的备份文件不再进仓库，旧版本用 Artifact 历史版本回退。
- 复原：回退到 Version 46。

---
# 第二十二次改动（技能 / 连接器 / 插件都能添加）
- 页面：hub/everest-hub.html（线上 Version 48）。
  - 技能：内置 8 个（新增日报、冰湖水位、地震简报、停发排查）；可新建、导入 SKILL.md、复制改写、下载、在本页运行，存共享库 xskill。
  - 连接器：14 个工具可改参数试调用；新增“接入申请”，存 xconn，所有者在 xconn/_review 写结论。
  - 插件：自选技能 + 连接器打包成 Claude Code 插件 zip 下载，可保存到共享库 xplug；官方插件也可下载 zip。
  - 能力声明：数据库规则 30 → 36 条（只增：xskill、xconn、xplug 各两条），mcp 工具 7 → 14。
- Worker（main 40ec1ac）：连接器新增 everest_alerts、everest_connectivity、everest_satellite_tracking、everest_air_traffic、everest_imagery、everest_station_history、everest_daily_brief。插件 1.1.0。
- 复原：回退到 Version 47（它不读新增的三个集合，数据留着不影响）；Worker 回退到 247b02f 的 cf-worker/src/mcp.js。

---
# 第二十三次改动（新定位）
- 页面：hub/everest-hub.html（线上 Version 49）。标题改为“EVEREST 真实度审计与事件证据平台”，页头副标题“公开数据真实度审计与事件证据 · 示范区：珠峰”；右上角新增“定位”按钮，弹窗说明做什么、谁承担损失、边界、市场、尚未验证项（中英文）。
- 连接器说明、插件说明、README 同步为新定位。平台定位调研文档新增第 10 节“再核实（10 月 13 日）”。
- 复原：回退到 Version 48。

---
# 第二十四次改动（去掉“示范区”字样）
- 页面：线上 Version 50。页头副标题改为“公开地球观测数据的真实度审计和事件证据平台”，定位弹窗去掉“珠峰是第一个示范区”。README、连接器说明、插件说明同步。
- 复原：回退到 Version 49。

---
# 第二十五次改动（自动发现事件 + 自动证据包）
- Worker（main fb32ccb）：每 5 分钟从 BIPAD 洪水警报（喜马拉雅高山区县）、USGS 崩塌、GDACS 橙/红级、水位越线中自动发现事件，36 小时 / 150 km 内合并；/api/events.json；连接器新增 everest_events（共 15 个工具）。
- GitHub：events 分支 + evidence 工作流 + tools/evidence_pack.py：新事件或每 6 小时生成证据包（IO.EVN 信号图、地震目录、80 km 内水位站、IODA、哥白尼应急制图、Sentinel-1/2 前后影像）。
- 页面：线上 Version 51。底部“计算异常”自动加入事件（事件候选），详情里有证据时间线、IO.EVN 图、卫星影像链接；数据随 live/fs 的 ev 字段每小时同步。
- 复原：页面回退 Version 50；Worker 回退到 7ece293 之前的 events 相关提交（删 cf-worker/src/events.js 和 index.js 里的事件段）；events 分支可直接删除。

---
# 第二十六次改动（证据链）
- 证据包 v6（events 分支 tools/evidence_pack.py）：加哥白尼 GFM 自动洪水范围、IFRC Montandon（需令牌，未配置时标缺失）、NK.KKN 第二地震台与两台一致性核对、OpenTimestamps 存证（events/archive/ 下每版快照 + .ots，之后自动升级为比特币区块确认）、两台站信号图。
- 每日管线（pipeline.py）：位移改读云端干涉真实结果，没有新结果标“不可观测”；固定矩阵文件已删除。
- 页面：线上 Version 55。左侧新增“证据链”标签；底部事件改为“时间 + 名称 / 地点 / 状态”，只放最近 14 天。
- 复原：页面回退 Version 54；证据包脚本回退到 events 分支上一版提交；管线回退 git 提交 243f2d2 之前。

---
# 第二十七次改动（证据链：添加证据源、人工上传证据）
- 页面：线上 Version 56。“证据链”标签分三个子页：事件 / 人工证据 / 证据源。
  - 人工证据：共享库 evup/<用户>；文件存本页附件库（assets 能力，只有能编辑本页的人能上传，最大 20 MB）；提交前浏览器算 SHA-256；所有者在 evup/_review 标 待核实 / 已采信 / 不采信。事件详情弹窗里也能看和上传。
  - 证据源：共享库 evsrc/<用户>，所有者在 evsrc/_review 写结论（待评估 / 计划接入 / 已接入 / 不接入）。
  - 用户写的内容切英文时不翻译（data-raw）。
  - 能力声明：数据库规则 36 → 40 条（只增：evsrc、evup 各两条）；新增 assets；mcp 工具 14 → 15（everest_events）。见 hub/capabilities.json。
- 流程：每小时同步任务读 evup → tools/manual_export.py → events 分支 manual.json（全部条目公开指纹；只有“已采信”的公开内容；不含提交人和文件本身）。manual.json 变化会触发 evidence 工作流：证据包 v8 把已采信条目列入时间线，链接取一次内容算指纹并请求互联网档案馆存档；manual.json 每一版也用 OpenTimestamps 存证。
- 复原：页面回退 Version 55（不读 evsrc/evup，数据留着无影响；能力声明回退时传 Version 55 的 capabilities，即去掉 assets 和 4 条规则）；证据包回退 VERSION 7 那次提交；同步任务提示词去掉第 5 步。

---
# 第二十八次改动（去掉右上角“定位”按钮）
- 页面：线上 Version 57。只删了按钮，定位弹窗的内容（posHTML）还在代码里。
- 复原：回退到 Version 56。

---
# 第二十九次改动（说明移到 GitHub）
- 页面：线上 Version 58。各标签和事件详情里的长说明删掉，改成“说明 ↗”链接，指向 docs/HUB_GUIDE.md 对应一节（运行状态、数据来源、证据链、核对存证、人工证据、证据源、事件详情、流程阶段、治理与审计、知识库、技能、连接器、插件）。技能列表只显示描述的第一句。右上角加“GitHub ↗”按钮，打开本仓库。页面上的数据、状态、操作都没删。
- 复原：回退到 Version 57（hub/backup 未存；Version 57 的源文件即提交 e339009 的 hub/everest-hub.html）。

---
# 第三十次改动（证据源扩充、有更新就同步、仓库改名）
- 仓库改名为 Yizebaba/EVEREST-，代码和链接里的仓库名都已更新（旧地址 GitHub 会自动跳转）。
- 证据包 v12（events 分支）：加民间地震仪 Raspberry Shake、USGS 震动图/有感报告/PAGER、GNSS（M5 以上）、GDELT 新闻、维基百科、OCHA HDX、ReliefWeb、Cloudflare Radar、NASA FIRMS、NASA 夜间灯光、地磁 Kp、Vantor 开放影像。需要账号的 4 个（RELIEFWEB_APPNAME、CF_RADAR_TOKEN、FIRMS_MAP_KEY、EARTHDATA_TOKEN）没配置时标“缺失”。
- Worker：新增 news 源（GDELT，每 30 分钟）；事件发现加“新闻线索”（雪崩、冰湖溃决、泥石流、滑坡、暴雪，同一天两家以上媒体）；连接器 everest_events 加 full 参数。
- 页面：线上 Version 59。装了连接器时页面直接订阅（快照每分钟、证据包每 2 分钟），不用等每小时同步；证据源表加新来源。
- 复原：页面回退 Version 58；证据包回退 VERSION 8 那次提交；Worker 回退到 c92995e 的 cf-worker/src。

---
# 第三十一次改动（281 种灾害编码、更多灾种、C2PA）
- 灾害分类：联合国减灾署 HIPs 2025 版 281 种 / 8 大类，逐条对照在 docs/HAZARDS_281.md、data/taxonomy/hips2025_everest.json（tools/hips_map.py 生成）。
- Worker：事件带 hips 灾害编码；BIPAD 警报从只看洪水扩到滑坡、雪崩、森林火灾、雷击、寒潮、降雪、地震（预报性的“强降雨”不建事件）；USGS M5 以上地震建事件；新闻线索扩到 18 类（含溃坝、冰雹、雷击、寒潮、森林火灾、地震、霍乱、登革热、疫情）；疫情不和自然灾害合并。
- 证据包 v13：带 hips；疫情类只查新闻、公开记录、世卫疫情通报；人工证据显示 C2PA 和相机拍摄时间。
- 页面 Version 60：事件显示灾害编码；证据源页显示 281 种覆盖统计；上传时读 C2PA 来源记录和 EXIF 拍摄时间。
- 复原：页面回退 Version 59；Worker 回退 events.js、rt.js、mcp.js 到 99a9269；证据包回退 VERSION 12 那次提交。

---
# 第三十二次改动（281 种灾害逐个实测接入）
- 新工作流 .github/workflows/hazards.yml（每小时 :17）：tools/hazard_scan.py 逐个请求 33 个公开来源（BIPAD 事件库 47 类、BIPAD 警报和空气质量、NASA EONET、USGS、GDACS、NOAA SWPC、NASA CNEOS、CelesTrak、WHO 疫情通报、WHO FluNet、WOAH WAHIS、openFDA、CISA、HIBP、IODA、尼泊尔央行汇率、Safecast、Sentinel-5P、海啸预警中心、NOAA NCEI、IOC、IBTrACS、NSIDC、GBIF、尼泊尔英文媒体与谷歌新闻 RSS；需密钥 6 个：Cloudflare Radar、GFW、FIRMS、OpenAQ、ACLED、ReliefWeb），281 种灾害逐条匹配词在 tools/hazard_keywords.py。结果写 events 分支 hazards/（scan.json、records.json 90 天、scan_events.json、run.log）。
- 事件候选：死亡+失踪 3 人以上，或高山区自然灾害有死亡失踪；有新候选时自动触发证据包。
- 证据包 v15：事件 150 km 内、前 1 天到后 5 天的灾种扫描记录挂到时间线。
- docs/HAZARDS_281.md 改为实测结果（tools/hips_report.py 生成），旧的手写状态作废。
- 页面 Version 61：证据链加“灾种 281”子页（按 8 大类、按状态筛选、数据源实测表）；数据随 live/fs 的 hz 和连接器 everest_events 更新。
- 复原：页面回退 Version 60；删除 hazards.yml 即停止扫描；证据包回退 VERSION 14。

---
# 第三十三次改动（证据链学术方法、281 灾种期刊排名、ACLED 新认证）
- 证据包 v17：每个快照加 RFC 3161 时间戳（FreeTSA、DigiCert，存 .tsr）；导出 W3C PROV-JSON（events/<编号>.prov.json）和 RO-Crate 1.1（events/crates/<编号>/ro-crate-metadata.json），均用 prov、rocrate 库校验通过。
- 证据包 v18：按灾害编码附该灾种的数据论文和专业期刊（references 字段、RO-Crate citation），只作背景参考。
- tools/venue_rank.py + tools/venues_report.py：OpenAlex 查 281 灾种的专业顶刊前三和数据论文；hazards.yml 每天 02:41 UTC 增量续跑（task=venues），结果 events 分支 hazards/venues.json、HAZARD_VENUES.md、venues.log。可选密钥 OPENALEX_API_KEY。
- hazard_scan：ACLED 改为账号认证（ACLED_EMAIL、ACLED_PASSWORD）。
- 文档：docs/EVIDENCE_CHAIN_RESEARCH.md、docs/HAZARD_VENUES.md；README、HUB_GUIDE 加 RFC 3161 核对方法。
- 复原：证据包回退 VERSION 16（v17 之前的提交）；删 hazards.yml 里 "41 2 * * *" 那行即停止期刊排名；页面未改（仍 Version 61）。

---
# 第三十四次改动（Sigstore 签名、冰湖溃决数据库实时接入、Crossref）
- 证据包 v19（events 分支 tools/evidence_pack.py 和 .github/workflows/evidence.yml）：
  - 每个新快照用 Sigstore 无密钥签名（工作流加 id-token: write 和 sigstore/cosign-installer@v3），存 .sigstore.json，记 Rekor 透明日志编号；
  - 高山亚洲冰湖溃决数据库 HMAGLOFDB（github.com/fidelsteiner/HMAGLOFDB，开发版，每次现取并记提交号）：窗口内 80 km 的收录进时间线，30 km 内的历史记录放 history 字段；
  - references：按灾害编码附数据论文和专业期刊（来自 hazards/venues.json）。
- tools/venue_rank.py：数据论文和方法论文改用 Crossref（不占 OpenAlex 额度）；OpenAlex 每种只查一次期刊分组，已有排名且检索词没变的沿用。
- tools/source_survey.py：加参考数据候选（ref_、ref2_），可用 only 参数只测某前缀。NASA COOLR 滑坡目录从 GitHub 运行器 404，暂未接入。
- tools/hub_sync.py：事件带 history、references，ots 只留最近 3 条。
- 页面 Version 62：证据包详情加“历史记录”“可引用的数据和期刊”；事件卡片加 RFC 3161 和 Sigstore 链接。
- 复原：页面回退 Version 61；events 分支证据包回退到 e609e22 之前的 tools/evidence_pack.py 和 evidence.yml（VERSION 17）；venue_rank 回退到第三十三次的提交。

---
# 第三十五次改动（扫描改为 Worker 实时触发、期刊排名规则、Sigstore 标准格式）
- GitHub 自带定时任务实测几小时不跑：Worker 每小时改 events 分支 hazards/tick.txt（第一行 scan 或 venues，每天 02:40 UTC 后第一次是 venues），events 分支新工作流 .github/workflows/hazards-tick.yml 收到后启动 main 上的 hazards 工作流。状态在 /api/events.json 的 hz_kick。hazards.yml 自带 cron 保留作后备。
- 证据包 v20：Sigstore 改用标准 bundle（application/vnd.dev.sigstore.bundle.v0.3+json），签完在运行器上立即 cosign verify-blob 自核对，结果记 self_verified。
- 期刊排名：按 h 指数 × ln(1+该主题篇数) 排序；扩充综合刊名单；雪崩、爆炸、苯、砷、镉检索词改为不歧义的说法；保存全部候选期刊（candidates）；数据论文和方法论文要求标题含检索实词。
- 复原：删 events 分支 hazards-tick.yml 即停止 Worker 触发（Worker 只会继续改 tick.txt，无副作用）；Worker 回退 cf-worker/src/events.js、index.js 到 e9ebae0 之前；证据包回退 VERSION 19。

---
# 第三十六次改动（D1 读取额度、时效分级）
- Cloudflare 邮件：D1 免费额度每天 500 万行读取已用 75%。原因：总览页开着时连接器每分钟调 everest_snapshot → status()，每次 COUNT(*) 整张 obs 表并按日期分组（约 11 万行）。
  改为：obs 行数用 MAX(rowid)（只增不删，等于行数），日期数从 scene 小表算，结果缓存 5 分钟（meta.status_cache）；scoreOne 找待打分日期改查 scene 小表（以前队列空了以后每分钟扫整张 obs）。
- hazard_scan：每个来源加时效分级 latency，每种灾害加 rt_tier，汇总 by_latency。
- 复原：Worker 回退 cf-worker/src/index.js 到这次之前的提交；hazard_scan 删 LATENCY 那段。

---
# 第三十七次改动（推断边界）
- 证据包 v22：每条时间线记录标 bound（来源类别），证据包加 bounds（这次用到的每类来源“能说明什么、不能说明什么”，共 32 类，写在 tools/evidence_pack.py 的 BOUNDS）；PROV 记录加 everest:cannotShow。
- hub_sync 带上 bounds；页面 Version 63：证据包详情加可展开的“推断边界”。
- 文档：HUB_GUIDE“推断边界”，EVIDENCE_CHAIN_RESEARCH 加 Springer Nature 检索结果。
- 复原：页面回退 Version 62；证据包回退 VERSION 21（删 BOUNDS、add_bounds 和 PROV 那一行）。

---
# 第三十八次改动（实时源扩充）
- hazard_scan 新增 9 个实时观测源（都只收“已观测到/已发生”的记录，不收预报）：机场天气实况 METAR（全球约 5000 个机场，喜马拉雅范围内逐条带坐标，其余按现象汇总）、国际 SIGMET（只收正文写 OBS 的）、美国 SPC 风暴实况报告、美国 NWS 警报（只收 certainty=Observed）、USGS 火山通告（航空颜色码橙/红）、NIFC 美国林火（48 小时新发现数）、abuse.ch ThreatFox（1 小时新增恶意软件指标）、OpenPhish（免费列表，约 12 小时更新，算准实时）、ADS-B 紧急代码 7700（只算“有观测”，不等于事故）。
- 补对应：BIPAD 警报的 11 类灾种、GDACS 火山对应火山灰。来源失败时丢弃半截记录。
- 结果：有实时来源的灾种 35 → 61（气象水文 13 → 34）。实测不通未接：airplanes.live（403）、CEMS 订阅源（404）、Coral Reef Watch（404）、中国地震台网速报（连接被断）。
- 复原：删 hazard_scan.py 里“实时观测类（2026-10-14 加）”整段和对应的 STATIC、LATENCY 行。

---
# 第三十九次改动（总览页同步缺漏）
- 原因：页面装了连接器时，每 2 分钟用 everest_events 拉事件，拿到的数据更新但缺字段（推断边界、历史记录、参考文献、灾种时效），覆盖了数据库里完整的那份，所以这些内容在页面上“没同步”。
- 修：连接器 everest_events full 带上 bounds、history、references、hazard_links，存证只带最近 3 条；灾种扫描带上每个来源的时效和每种灾害的 rt_tier。hub_sync 同样带上时效。页面 evApply 在新数据缺这些字段、且证据包版本相同时保留旧值。
- 页面 Version 64：“灾种 281”加时效分级（实时 / 准实时 / 定期 / 只有新闻）和按时效筛选，数据源表显示每个来源的时效；“证据源”里的已接入清单补上灾种扫描、历史记录、推断边界、参考文献和新的存证方式；新来源的英文名。
- 复原：页面回退 Version 63；Worker 回退 cf-worker/src/mcp.js；hub_sync 回退 hz 那段。

---
# 第四十次改动（左侧面板与底部一排的布局）
- 问题：桌面版左侧面板没有底色，文字直接压在动画上（连线、公式、几何体穿过文字），面板只有约 290 px 宽，表格挤成多行；选中标签的“再次点击收起”提示盖住面板第一行；底部一排同样没有底色；手机版“运行状态”横向溢出 16 px。
- 修（页面 Version 65，CSS 追加在样式表末尾“v65”段）：面板加深色半透明底、圆角、边框，宽度 min(560px, 44vw)，内部滚动；左侧标签列也加底；选中标签不再弹提示；底部一排条目加底；手机版表格固定布局、长词断行，不再横向溢出。
- “运行状态 → 外部运行组件”补上灾种扫描、证据包生成、期刊表、总览页同步（含英文）。
- 复原：页面回退 Version 64（或删除样式表末尾 v65 段和 LIVE.ext.rows 新增的 4 行）。

---
# 第四十一次改动（链接颜色、拖动宽度、D1 读取计量）
- 页面 Version 66：链接颜色改为浅蓝（原来没设，用浏览器默认深蓝/紫色，在深色底上看不清）；v65 把面板宽度写死后，左侧面板“拖动调整宽度”失效，改回由拖动宽度（--sideW）决定，默认 min(560px, 44vw)；“运行状态 → 需要注意”在 D1 当天读取超过 50% 时提示。
- Worker：所有 D1 查询经计量包装，累加 meta.rows_read，按 UTC 日写进 meta 表 d1r:<日期>；status() 带 d1_rows_read_today，连接器总览、每小时同步都能看到。
- 复原：页面回退 Version 65；Worker 回退 cf-worker/src/index.js 里 meterDB、meterSave 和 route 包装（export default 恢复为直接处理请求）。

---
# 第四十二次改动（取数回执、独立核对、事件显示）
- 证据包 v23（events 分支 tools/evidence_pack.py）：取数回执 receipts（时间、去掉密钥的网址、状态、SHA-256、字节数；≤64 KB 文本响应存 events/raw/<哈希>.gz）。
- 新 tools/verify_archive.py + evidence.yml 新步骤：每个新快照用 9 项独立核对（sha256 两套、openssl×2、cosign、sigstore-python、ots、prov、rocrate），结果写 index.json 的 ots[-1].verify；首轮 8 个事件全部 9/9 通过。
- 页面 Version 67：中文模式下 BIPAD 英文标题改为“地点 · 灾种中文名”（英文模式仍用原标题）；事件来源去重；事件详情里的来源和坐标可点击，跳到“证据链 → 证据源”并高亮对应来源（新增灾种扫描来源表）；底部一排按最新记录时间排序并显示最新时间，附首个信号时间；英文模式下灾种扫描生成的中文记录按句式翻译（新闻原文标题不改）；“证据链”导航英文名修正；事件卡片显示独立核对结果和取数回执条数。
- hub_sync、连接器：事件带 last_t（完整时间线上最新一条“支持/矛盾”记录的时间）和 receipts_n。
- 复原：页面回退 Version 66；证据包回退 VERSION 22（删 RECEIPTS、receipt()、redact() 和 main 里两行）；evidence.yml 删“跨实现核对”一步。

---
# 第四十三次改动（只留真实节点、去掉模拟、摄像头、界面收拾）
- 问题：“未运行（14）”里的地震台-02、相机-02、GNSS-01、AWS-02、GB-SAR-01、通知渠道、冰川状态库、冰裂缝检测、GLOF 模块、雪崩与冰崩动力学、DEM 物理门禁、L4 异常引擎等，是早期设计稿的占位节点或输入写死的旧模块，从来没有接真实数据，所以一直“未运行”；“阶段”是 L01–L15 设计框架，多数没实现；运行面板还有“示例链路 / 模拟”按钮。
- 页面 Version 68：
  - 节点只留实际在跑的；阶段换成 9 个实际环节（公开数据源、实时采集、灾种扫描、事件发现、证据包生成、存证与独立核对、同步与展示、人工证据与审核、卫星形变与坡面监测）；去掉示例社区条目、模拟按钮和处理函数。
  - 新增实测流程节点（灾种扫描、事件发现、证据包、存证、独立核对、同步、人工证据、KKN、HMAGLOFDB）和两个摄像头节点，状态由同步来的数据实时计算（dynNodes）。
  - 摄像头：tools/webcams.py 随灾种扫描每小时检查 WEBCAM NEPAL LIVE（YouTube）在播的珠峰地区直播和 EvK2Minoprio 金字塔摄像头（图像文件修改时间 2024-11-24，标为停更），取缩略图；节点详情显示图、“打开摄像头源地址 ↗”和频道链接。hub_sync 把列表和小图写进 live/img 的 cams。
  - 运行状态：顺序改为需要注意 → 自动流程（灾种扫描、证据包、同步用实时状态覆盖，新增存证与独立核对、珠峰摄像头两行）→ 证据链存在哪里（events 分支、archive、raw、PROV/RO-Crate、比特币、Rekor、本页数据库，带链接）→ 数据源一览 → 详细读数。
  - 技能（10 个，与插件 1.2.0 同步）、连接器（15 个工具）、插件面板各加一行说明，外部工具可以登记接入或组合进插件。
  - 左侧标签和列表连到中间球体：不再只画 14 条，全部节点都连；“运行状态”连采集类节点。
  - 底部事件栏改为等宽等高卡片（标题、地点一行省略，悬停看全文），可横向滚动；右侧详情面板左边缘可拖动调宽（双击恢复），关闭按钮固定在右上角圆形按钮、不再压住标签；全部滚动条统一为黄色。
- 插件 1.2.0：新技能 everest-hazards、everest-verify（已提交 main）。
- Worker：GDELT 新闻被 429 限流时等 6 秒重试一次。
- 复原：页面回退 Version 67（备份在 git 历史：本次提交之前的 hub/everest-hub.html）；插件回退 1.1.x 提交；Worker 回退 cf-worker/src/rt.js 的 news() 一段。

---
# 第四十四次改动（全部事件、真实节点补全、治理与审计、知识库、外部工具库、卫星彩色图、翻译）
- 底部事件栏：左边加范围切换——“证据包事件”（原来的，尼泊尔范围内满足规则、带证据包的）/“尼泊尔记录”/“全球灾种记录”（灾种扫描每小时从 42 个公开来源取到的原始记录，最近 30 天、显示最新约 960 条）。点一条记录在右侧看时间、来源、HIPS 灾种、坐标、伤亡、原始链接。新数据库文档 live/hzr（hub_sync 生成）。
- 节点：v68 删掉的是设计稿占位（地震台-01…、相机-01…、GNSS、AWS、GB-SAR 等，状态是随机示例）。这次把灾种扫描的 42 个公开来源作为真实节点加回来（状态来自每小时扫描，需要密钥的显示停止并写明缺哪个密钥）；实时源、南坡、卫星流程节点改为每次有新数据时重算（原来只用发布时的快照）。现在 73 个节点，全部实测。
- 卫星云图：向日葵 9 号可见光是单波段，本来就是黑白，夜里全黑。Worker 改为每 30 分钟存 5 张 JPEG（向日葵气团 RGB 彩色、红外、可见光；Meteosat 自然色、雪 RGB），范围放大到 25.5–31°N、82.5–90.5°E 并标出珠峰；夜间空白的图自动标出不显示。原来每 3 小时一张。
- 摄像头：Worker 新增 cams 源，每 10 分钟取一次 YouTube 直播缩略图，连接器每分钟带到页面；说明 YouTube 缩略图本身有滞后，以画面左下角时间为准。摄像头列表另存 live/cam。
- 证据链 → 证据源：“已在证据包里”每一行加来源链接；灾种扫描来源和“数据源实测”表的来源名都能点开来源主页。
- 治理与审计：重做。自动流程运行记录（GitHub Actions 最近 60 次，live/ops）、证据完整性审计（每个事件的存证与 9 项核对，带 Rekor 链接）、系统健康链路（按新的实际阶段）、时效分级（按实际延迟，不再用示例延迟）、数据治理登记（本平台实际用到的全部来源）、审计日志、平台规则 9 条。
- 知识库：写明用途；分事件档案、灾种定义 281（HIPS）、冰湖溃决历史、文献、归档标签。
- 技能 / 插件 / 连接器：各加“外部库”——Claude 官方技能库 anthropics/skills、Claude Code 官方插件市场和知识工作插件、MCP 官方注册表（按地球观测等关键词）；可搜索、看安装命令、一键登记接入。tools/catalog.py 随灾种扫描每小时抓目录，live/lib。
- 完整流程（中间大球）按 9 个实际阶段重写，点任意一行打开节点。
- 翻译：英文模式下节点详情、流程、推断边界、治理、知识库、外部库的中文全部有英文；HIPS 281 种灾害名并入词典。
- Worker：GDELT 429 重试；卫星图 30 分钟；cams 源。hazards.yml 增加 catalog、probe 任务。同步定时任务改为写入全部 live_*.json。
- 复原：页面回退 Version 68（备份 scratchpad/hub_v68.html，或本次提交前的 git 版本）；Worker 回退 cf-worker/src/rt.js 的 IMG 与 cams、index.js 的图像段；hub_sync 去掉 hzr/lib/ops/cam 段；定时任务提示词改回 4 个文档。

---
# 第四十五次改动（底部默认全部事件、InSAR 核对、自动运行修复）
- 底部事件栏默认“全部事件”（证据包事件 + 灾种扫描全部记录），另有“尼泊尔 / 珠峰”“已出证据包”两个切换。
- InSAR“自动核对 2 项未通过”原因：①旧版每日管线读仓库里的固定矩阵，数值每天一样（10/13 已改为只认云端干涉，页面还显示发布时的旧快照）；②管线选影像对时取“与珠峰范围相交的最新两景”，把不同轨道凑成一对（10-06 与 10-10 只隔 4 天，10-06 不在 23790 条带上）。修：models/cdse_sentinel1.py 新增 discover_burst_pair（Burst 23790 / IW1 / 相对轨道 12 / S1D，相隔 12 天，与云端干涉同一查询），pipeline.py 改用它；实测新一次运行影像对 2026-09-28 → 2026-10-10。hub_sync 每小时读最新 displacement_summary.json 重做 3 项核对，写入 live/ops.pipe，页面实时显示。
- 每日管线节点状态改用 GitHub 运行记录（live/ops），不再用发布时的快照；daily-pipeline.yml 手动触发时不再强制运行 Auto-Coder 演示。
- 哨兵卫星过境目录：新 tools/sat_catalog.py 随灾种扫描每小时取，写 hazards/sat.json → live/ops.sat（原来 live.yml 每 10 分钟的计划任务实际几乎不触发）。
- 史密森尼火山周报 403：改用史密森尼 GVP 公开地理服务（持续喷发列表）作后备，已恢复正常。
- 新闻线索：GDELT 对云服务器 IP 普遍限流（Cloudflare 和 GitHub 都 429）。tools/gdelt_news.py 随灾种扫描取一次，失败时用灾种扫描的“新闻 RSS”记录；Worker 直连失败时读 events 分支 hazards/gdelt.json。
- 复原：页面回退 Version 69；pipeline.py 改回 discover_sentinel1_slc_pair；删 tools/sat_catalog.py、tools/gdelt_news.py 及 hazards.yml 中对应两段；hazard_scan.py 删 gvp() 的 WFS 后备段；Worker 回退 news() 后备段。

---
# 第四十六次改动（底部按时间、知识图谱、MiroFish 推演）
- 底部事件栏：证据包事件和灾种扫描记录合在一起按时间倒序，最新在最左。NWS 警报原来用 onset（可能是未来的预计开始时间），改为 sent（发布时间）；页面对未来时间截到“现在”。
- 知识库 → 知识图谱：事件、来源、台站（地震台、水位站）、证据包、存证快照（哈希、比特币区块、RFC 3161、Rekor、9 项核对）、灾种、地点串成一张图，在页面里由已同步的证据包时间线和灾种扫描记录现算；常用问题按钮（某台站参与过哪些事件等）、搜索、以任意点为中心的关系图、下载整张图 JSON。
- MiroFish：tools/mirofish_seed.py 用真实数据生成 4 份种子材料（平台概况与运行实况、数据源与实测状态、事件证据包与全球记录、相关方与生态）和推演需求；tools/mirofish_run.py 按 MiroFish 后端 API 依次做本体→图谱→创建→准备→运行→报告并保存全部产物；.github/workflows/mirofish.yml 固定 MiroFish 提交号运行，结果存 events 分支 mirofish/<时间>/。需要 Secrets：LLM_API_KEY、LLM_BASE_URL、LLM_MODEL_NAME、ZEP_API_KEY。知识库 → 推演（MiroFish）显示状态、种子材料和报告，明确标为“不是证据”。
- 复原：页面回退 Version 70；删 mirofish.yml 与两个 tools 脚本；hub_sync 删 mf 段；hazard_scan.py 的 NWS 时间改回 onset。

---
# 第四十七次改动（底部滚动、281 种灾害的文献与数据源）
- 底部事件栏：左边的范围切换移出滚动区，右边单独一条横向滚动；原来卡片滚到切换下面会从边缘露出来。
- 知识库 → 文献与数据源：从只显示证据包里 5 种灾害的参考文献，改为全部 281 种：每种的 2020 年以来论文数、专业期刊（OpenAlex，h 指数）、综合期刊、数据论文、高被引论文（带 DOI）、本平台实测能取到的数据源；可搜索、按类别筛选。数据来自 events 分支 hazards/venues.json 和 scan.json，hub_sync 写 live/lit。
- 侧栏面板会把 <details> 转成固定面板，带属性的 <details> 会让结构错位（之前“运行状态”“证据链”布局乱的原因之一）；证据链的推断边界和新文献表都改为自己的展开按钮，页面里不再有带属性的 <details>。
- 复原：页面回退 Version 71；hub_sync 删 lit 段。

---
# 第四十八次改动（互联网档案馆时光机存档、MiroFish 首次运行）
- 证据包 v24（events 分支 tools/evidence_pack.py）：每条“支持 / 矛盾”记录的原始网页，用互联网档案馆公开的 Save Page Now 请时光机存一份，存档地址和时间写进时间线条目（archive、archive_t），每个网址只存一次，记账在 events/wayback.json；每次运行最多新存 15 个，被限流就停、下次继续。证据包新鲜度改为 50 分钟（每小时重算一次）。
- 页面：时间线每条后面多一个“时光机存档 ↗”；“证据链存在哪里”和证据源“存证”一行加上 Wayback Machine。
- MiroFish：仓库 Secrets 已加（DeepSeek + Zep），已启动第一次推演（combined，20 轮）。
- 复原：证据包回退 VERSION 23（删 wayback_save / wayback_attach 和 build 里的调用）；页面回退 Version 72。

## 49 · 2026-10-15 MiroFish 首跑卡住的修复
- 原因：MiroFish 模拟脚本跑完 20 轮（推特 208 + Reddit 405 = 613 次动作，10:22 完成）后进入“等待命令模式”，进程不退出，run-status 一直 running，驱动 3 小时轮询超时，没生成报告。
- 修复：tools/mirofish_run.py 在两平台都报完成后调用 /api/simulation/close-env，10 分钟未退出再 /stop；报告接口 409（图谱写入未排空）时每 30 秒重试，最多 20 分钟。
- 复原：git revert 本提交即可；不改 MiroFish 代码。
- 14:16 重跑 38749780066 在第一步失败：DeepSeek 返回 402（余额不足）。驱动现在记录上游错误正文，工作流把上游状态码写进 status.json（upstream_status / upstream_hint）。

## 50 · 2026-10-15 底部事件栏更新更快（v75）
- 原因：页面网络被封，只能等数据库被写入；写入只靠定时任务（平台限制每个任务最少间隔 1 小时）。原来灾种扫描每小时 :47、同步每小时 :38，新记录最多要等近 2 小时。
- 改动：
  - Worker（cf-worker/src/events.js hazardsKick）：灾种扫描改为每小时 :12 和 :42 各一次（漏扫 45 分钟就补一次）。
  - 定时任务“总览实时同步”从 :38 改到 :58；新增“总览半点同步（轻量）”（trig_01BnZ8UWV61AcZXoqeB4JcDa）每小时 :28，只写 live/hzr、fs、img、cam、ops。
  - 页面底部栏切换区加“扫描于 时间”。
  - tools/hazard_scan.py：新闻 RSS 没有 pubDate 时依次用 dc:date / published / updated / 网址里的日期，都没有就跳过；不再把扫描时间当发布时间（之前 Kathmandu Post 10-14 的文章显示成刚刚）。
- 复原：git revert 本提交；update_trigger 把“总览实时同步”改回 "38 * * * *"，删除 trig_01BnZ8UWV61AcZXoqeB4JcDa；页面回 Version 74。

## 51 · 2026-10-15 扫描结果直接上页面（v76），不等同步
- 连接器新工具 everest_hazard_records（cf-worker/src/mcp.js）：读 events 分支 hazards/records.json，返回与 live_hzr 相同格式。总览页 liveWatch 每 90 秒查一次，扫描一提交新记录就出现。页面能力声明的 EVEREST 工具表加了这一个（hub/capabilities.json）。
- Worker 灾种扫描改为每 20 分钟一次，不再固定 :12/:42（与同步任务脱钩）。
- “总览半点同步（轻量）”trig_01BnZ8UWV61AcZXoqeB4JcDa 停用（省额度）；:58 完整同步保留，作为没有连接器时的后备。
- 复原：git revert 本提交；页面回 Version 75（能力声明去掉 everest_hazard_records）；需要时重新启用半点同步。

## 52 · 2026-10-15 底部栏仍显示 21:48 的原因与修复（v77）
- 查实：22:47 那次扫描耗时 12 分钟，22:59:03 才提交 records.json，比 22:58 的同步晚 1 分钟，同步拿到的还是 21:48 的数据；新工具 everest_hazard_records 已部署，但 claude.ai 那边的连接器工具列表仍缓存 15 个，页面调不到。
- 修复：Worker 在页面本来就在用的 everest_events（full）里附带最新灾种记录 hzr（≤90 KB，约 600 条）；页面 hzrMerge 按“来源+链接+标题”并进已有记录（只在扫描时间更新时合并，去掉同一条的重复）；数据库那份只在更新或更全时替换。
- “总览半点同步（轻量）”重新启用，作为连接器不通时的后备。
- 复原：git revert 本提交；页面回 Version 76。

## 53 · 2026-10-16 清理旧版采集和试验工作流（用户同意删除）
- 停用工作流：live（旧版每 10 分钟采集 → live-data 分支 + GitHub Pages，与 Worker 重复，实际每 4–6 小时才跑）和 11 个试验工作流：adsb-probe、cred-probe、data-probe、doris-probe、evn-aug26、insar-cloud、liveness、ngl-probe、pc-trial、plot-evn、rt-sweep。adsb-live 在用（Worker 的 ADS-B），保留。
- 删除 main 上的 .github/workflows/live.yml。分支 data-probe、live-data 保留不动（删除分支被权限拦下；工作流已停用，它们不会再更新）。
- 复原：`gh api -X PUT repos/Yizebaba/EVEREST-/actions/workflows/<id>/enable` 重新启用；git revert 本提交恢复 live.yml。

## 54 · 2026-10-16 页面数据全部可从连接器直接取（v78，全自动改造第 1 步）
- 新文件 cf-worker/src/hub.js：Worker 直接从仓库已有文件生成卫星图（facet-live img/*.jpg）、摄像头（hazards/webcams.json + Worker 的在播缩略图）、工具库（hazards/catalog.json）、文献（hazards/venues.json + scan.json），格式与 hub_sync.py 相同。
- 运行记录和设备在线要用 GitHub Actions 接口：hazards 工作流每次扫描后运行 hub_sync.py，只把 live_ops.json、mt_monitor.json 存到 events 分支 hub/ops.json、hub/mt_monitor.json（不存图片，避免仓库膨胀）。
- 连接器：everest_events 收到 id="page:img|ops|lib|lit" 时返回这些数据（用已有工具和已有参数，避开 claude.ai 工具列表缓存；普通对话调用不受影响）。
- 页面：hubApply() 统一处理数据库和连接器两条路，谁新用谁；连接器轮询：图 5 分钟、运行记录 3 分钟、工具库和文献 30 分钟。
- 复原：git revert 本提交；页面回 Version 77。

## 55 · 2026-10-16 全自动改造第 2–5 步（v78）
- 全链路自检：cf-worker/src/hub.js hubHealth()，随 everest_snapshot 每分钟送到页面；页面顶部“链路”按钮显示正常段数或断了几段，点开看每段最后成功时间、时限、页面收到的每份数据走的是连接器还是数据库、数据库后备的最后一次真正写入（live/sync 回执）。
- 写死内容：早期 6 条异常按实时数据核对“现在怎样”（anomLive）：IO.EVN、InSAR 两条显示已恢复/已修复，Kodari、阿伦河、Imja 仍停报；IO.EVN 波形改为 tools/evn_plot.py 每小时画最近 24 小时（hazards 工作流 → events hub/evn_24h.png → 连接器 page:img）；InSAR 图在出现更新的影像对时标明“图还没生成”。
- InSAR 每日管线：Worker 每 6 小时写 hazards/tick.txt “insar” → events 分支 hazards-tick 工作流启动 daily-pipeline（run_auto_coder=false）；daily-pipeline 加并发组，GitHub 定时作兜底。
- 定时任务：“总览实时同步”改为后备，每次写回执 live/sync，只在确认已提交时算成功；“总览半点同步（轻量）”停用。
- 复原：git revert 本提交与 events 分支 fe12e52；update_trigger 恢复旧说明；页面回 Version 77。
- 补充（v79）：顶部统计栏在页面上是隐藏的（calm 模式 CSS），“链路”改为页头按钮 #linkPill；页面里灾种扫描频率的文字从“每小时”改为“每 20 分钟”（中英文）；自检里坡面时间改读 cached_at。本地无头浏览器加载测试 0 个脚本错误，并用连接器真实返回的数据跑过一遍。

## 56 · 2026-10-16 MiroFish 第三次运行被杀的修复
- 38754825731：跑到第 45 分钟（模拟中途）“Start backend and run”步骤以 exit 143（SIGTERM）结束，运行器随之退出，Save 步骤被跳过，什么都没留下。作业日志所在的存储本环境访问不到，确切的信号来源未能确认。
- 修复（.github/workflows/mirofish.yml）：后端用 setsid 放进独立会话；每分钟记录内存（mf_out/sys.log）；每 10 分钟用 tools/mirofish_checkpoint.sh 把已有产物推到 events 分支（运行器意外退出也留得下线索）；最终保存也走同一脚本，并在推送前抹掉日志里的密钥。
- 复原：git revert 本提交。

## 57 · 2026-10-16 底部事件栏和“页面不更新”的根因修复（v80）
- 底部栏内容错误：1137 条“事件”里 634 条是天气观测（METAR 337、SIGMET 104、NWS 98、SPC 95），313 条是每次扫描都重复的状态计数（CelesTrak 255、钓鱼/恶意软件计数 58）；这些高频记录把预算挤满，BIPAD 灾害事件库 580 条尼泊尔事件一条都没进来。修复：hub_sync.py、Worker（mcp.js hzrFeed）、页面（hzrClean）三处同一份 DOCK_EXCL 排除天气观测流和状态计数，同来源同标题只留最新；完整记录先放尼泊尔/珠峰范围再放全球。这些记录仍计入 281 灾种扫描，只是不进“事件”栏。
- “已出证据包 7”：底部栏只取最近 14 天的计算异常，8·26 和 9·27 两个有证据包的事件被藏了。改为所有已出证据包的事件都进栏（9 个）。
- 页面一直不用连接器的根因：启动时只有权限状态已经是 granted 才启动实时监视；从没问过（prompt）就永远不问。改为启动时问一次；拒绝时页头显示“连接器被拒绝（点此打开权限）”；每个连接器调用的结果和错误码显示在“链路”面板。
- 合并缺陷：两份记录扫描时间相同时第二份被丢弃，改为时间相同也合并新增条目。
- 同步任务 403：任务会话对本仓库没有 gh 权限（回执原文：gh api HTTP 403）。hub_sync.py 改为先用 raw.githubusercontent.com（公开仓库）读文件，运行记录取 events 分支 hub/ops.json；任务说明改为用 curl 取脚本。在禁用 gh 的环境实测能生成全部 10 个文档。
- 测试：无头浏览器 + 模拟 claude 运行时（权限从 prompt 开始，连接器返回 Worker 真实数据）：0 个脚本错误，7 个连接器调用都收到数据，底部栏 全部 927 / 尼泊尔 771 / 证据包 9；拒绝授权时页头正确提示。
- 复原：git revert 本提交；页面回 Version 79；update_trigger 恢复旧说明。

## 58 · 2026-10-16 MiroFish 第四次运行与“只生成报告”模式
- 38769313536（00:28–01:22）：setsid 与 close-env 修复生效——20 轮模拟跑完（133 个智能体，332 次动作，内存峰值约 10/16 GB，没再被杀），close-env 后 30 秒状态变为 completed；报告阶段 DeepSeek 返回 402（余额不足），没有报告。产物（本体、图谱、人设、配置、时间线、帖子、动作、sys.log）已存 events 分支 mirofish/20261015T162932Z。
- 新增：工作流结束时把 mf/backend/uploads（模拟状态）存为运行产物 mirofish-state（14 天）；输入 report_only_run + report_only_sim 时恢复它，驱动跳过图谱和模拟，只调用报告接口，省额度。
- 复原：git revert 本提交。

## 59 · 2026-10-16 定时任务被权限策略拦截的真正原因与改法（v81）
- 证据（任务回执原文）：总览同步 09:59“本会话的权限策略（auto mode classifier，原因 Code from External）拒绝用 curl 下载仓库里的外部脚本”；设备维护 08:55“下载 rt.json 和 monitor_sync.py 被本次运行环境的权限策略拦截”。昨晚的 gh 403 是同一类限制：定时任务环境不允许取仓库代码来运行。
- 改法：新建定时任务“总览数据库后备同步（连接器）”trig_0164mBFp57tBJgY61fCig3jr（每小时 :22）：只调用 EVEREST 连接器（everest_hazard_records、everest_events page:img/ops/lib/lit、everest_snapshot）取数据，再用 ArtifactData 写入，不下载不运行仓库代码；旧的“总览实时同步”trig_01FYFBVJskicnF8Zdz1QK1Qq 停用。
- 页面：“链路”面板顶部显示页面版本（v81）和打开时间，便于确认浏览器里跑的是不是最新代码。
- 复原：停用新任务、重新启用旧任务；页面回 Version 80。
- 实测（10-16 10:24、10:29）：新同步任务回执 ok=true、via=connector，写入 hzr、img、cam、ops、lit、lib、rt、mt_monitor 共 8 个文档（hzr 为 10:12 扫描、908 条事件）；新“设备维护提醒（连接器）”trig_01KV8hwbCND7u51ceM38DKQM 测试运行 ok=true，停发 7 台；旧“设备维护提醒”trig_01XjDfCRi8GT7Bax1CTwUVjf 停用。
- 另：本地 git 远程地址仍是旧仓库名 everest-insar-pipeline，代理对旧名返回 403，已改为 Yizebaba/EVEREST-。

## 60. 10-16 15:05 快照里的新闻压到 200 KB 以内（数据库 live/rt 超 256 KB 写入失败）
- 现象：14:22 的数据库后备同步回执 ok=false：“写入 live/rt 失败：263330 bytes，上限 262144”。其他 7 个文档照常写入。原因是 GDELT 新闻累计到 276 条（145 KB）。
- 改动：cf-worker/src/mcp.js 的 everest_snapshot 返回的 rt 里，新闻只留最新的若干条，使整份 rt ≤ 200 KB，并加 arts_total 记原总数；完整新闻仍用 everest_source（key=news）取。rt.json、Worker 其他接口不变。
- 复原：git revert 本次提交（Workers Builds 自动重新部署）。

## 61. 10-16 17:10 页面 v82：浏览器端自检回写数据库 live/pagediag
- 原因：页面在你的浏览器里有没有真正用上连接器，Claude 这边看不到，只能靠你贴面板文字。
- 改动：hub/everest-hub.html 只在页面主人打开时，加载 45 秒后和之后每 10 分钟，把“链路”面板要点（页面版本、连接器授权状态、每个连接器调用的最近结果和时间、底部事件栏扫描时间、各份数据来自连接器还是数据库）写进 live/pagediag。不含个人信息；其他人打开不写。
- 复原：页面回 Version 81（备份 scratchpad hub_v81_backup.html，或 git 上一版 hub/everest-hub.html），并可删除 live/pagediag。

## 62. 10-17 21:40 坡面雷达分级接入总览（页面 v83）
- 背景：Worker 坡面基线 275/275 景、199/199 个日期打分完成，10-17 20:23（北京）生成首份分级 facet_live.json：极反常 2、偏高 41、留意 40、平常 293。
- 改动：
  - cf-worker/src/hub.js 新增 hubFl（读 facet-live/facet_live.json），mcp.js 的 everest_events 增加 page:fl 分区。
  - hub/everest-hub.html：嵌入 376 块坡面几何（来自 cf-worker/src/facets.json）和发布时的分级快照；连接器 page:fl 每 30 分钟取一次，有新分级就替换；“完整流程 → 卫星形变与坡面监测”一节加分级地图、图例计数和“极反常/偏高”清单；节点“冰坡雷达亮度”显示分级计数；链路面板“页面收到的数据”加“坡面分级”。文字注明只监测、不是预警。
- 复原：页面回 Version 82（备份 scratchpad hub_v82_backup.html，或 git 上一版）；git revert 本次提交可撤回 Worker 改动。

## 63. 10-17 23:58 证据链在数据库后备里停在 10-15：补上 live/fs 同步
- 现象：用户看“证据链”的时间不对。查数据库 live/fs：ev 停在 10-15 17:32（UTC），证据包“生成于”都是 10-15。原因：10-16 改成连接器版后备同步任务时，任务只写 hzr/img/cam/ops/lib/lit/rt，漏了 live/fs（证据包事件 ev + 坡面状态 + 灾种扫描 hz）。连接器在页面前台时是新的（证据包 10-17 22:38 生成），但标签页在后台、或连接器不可用时，页面退回数据库，就看到 10-15。
- 改动：cf-worker/src/mcp.js 新增 fsDoc，everest_events 加 page:fs 分区，按原 hub_sync.py 的 live_fs 格式生成并压到 230 KB 以内；后备同步任务加一步写 live/fs。
- 复原：git revert 本次提交；任务提示词删掉 page:fs 那一步。

## 64. 10-18 00:20 事件时间以数据源为准（证据包 v25，页面 v84）
- 用户要求：事件时间用时间线里最早的报道或来源记录的时间，不用本平台发现或更新的时间；以后都这样。
- 改动：
  - tools/evidence_pack.py（events 分支实际运行的那份，main 同步一份）VERSION 25：新增 source_time。证据包 t = 发现事件时的来源记录里最早的一条；新闻线索类（news-）再算上灾种扫描里同灾种、发现日前 3 天内的新闻 RSS。来源只给日期的（BIPAD 事件库 UTC 18:15 = 尼泊尔零点，GDELT UTC 零点）标 t_prec="day"。原发现时间存 t_detected，时间来源存 t_src。index.json 的 t 同步改为来源时间。
  - cf-worker/src/mcp.js：everest_events full 带出 t_src、t_prec、t_detected。
  - hub/everest-hub.html v84：evT() 显示事件时间，只有日期的显示“MM/DD 当地日期”，不编造时刻；证据链列表显示“时间来源：…；本平台发现于 …”。
- 例：Gorkha 洪水由 10/14 08:00（GDELT 收录日）改为 10/13 13:01（北京，Al Jazeera 报道，经 Google News）；Khatyad 滑坡由 10/12 02:15 改为 10/12 当地日期。
- 复原：events 分支 git revert 9f519e46（证据包回 v24，会全部重算一次）；main git revert 本次提交；页面回 Version 83（备份 scratchpad hub_v83_backup.html）。

## 65. 10-18 23:30 GitHub Pages 停在 10-15：改为独立的 pages 工作流，页面改为跳转到实时页
- 现象：GitHub Pages 最后一次部署是 10-15 20:07（北京），之后不再更新，公开页面一直显示 10-15 的旧看板数据。
- 原因：Pages 原来由旧采集任务 .github/workflows/live.yml 顺带发布（每 10 分钟采集一次再上传 site/）。10-15 按用户同意删掉 live.yml 时没注意到它还负责 Pages。
- 改动：site/index.html 改为跳转到 Worker 实时页（https://everest-facets.yizebaba.workers.dev/rt），不再放快照；新增 .github/workflows/pages.yml，site/ 有改动或手动触发时发布。旧页面备份在 scratchpad site_index_old.html，git 历史里也有。
- 复原：git revert 本次提交（Pages 会停在跳转页；要恢复旧看板需同时恢复 live.yml 采集）。
- 10-18 23:24 用户把 Settings → Pages 的 Source 改为 GitHub Actions 后重新发布成功（run 39140332870，地址 https://yizebaba.github.io/EVEREST-/）。

## 66. 10-18 23:40 运行器固定为 ubuntu-24.04
- 原因：GitHub 通知 ubuntu-latest 从 10-19 起逐步换成 Ubuntu 26，系统库和 Python 包可能变化，导致扫描、证据包、InSAR、MiroFish 工作流突然出错。
- 改动：main 上 daily-pipeline、evidence、hazards、mirofish、pages、release-package，events 分支 hazards-tick，adsb-live 分支 adsb-live，runs-on 由 ubuntu-latest 改为 ubuntu-24.04（就是现在实际在用的版本）。
- 复原：把 ubuntu-24.04 改回 ubuntu-latest。

## 67. 10-19 00:20 一带一路样品（第一步）：项目清单、证据包支持多国、回溯测试
- 用户要求：把 World Monitor 和 MiroFish 打通、放进总览页，接入一带一路项目；先做 3 国约 10 个项目的样品，用免费数据，测"能力多少、和事实偏差多少"。
- 新增：tools/bri_registry.py + bri/projects.json（AidData 全球中国发展融资地理数据集 v3.0 的 11 个项目：尼泊尔 5、老挝 2、巴基斯坦 4，真实范围，简化到约 200 m）；bri/retro_events.json（3 起回溯测试事件，种子只给第一条公开报道）；tools/bri_retro.py + .github/workflows/bri-retro.yml（手动触发，结果放 events 分支 bri/retro/，不存证）。
- 改动：tools/evidence_pack.py 支持事件带 country（默认尼泊尔）：尼泊尔专属来源（BIPAD 水位站、IO.EVN/KKN 远于 400 km 时）不查；IODA、哥白尼应急制图、GDELT、HDX、ReliefWeb、Cloudflare Radar 按国家查。尼泊尔事件行为不变。
- 复原：git revert 本次提交；删除 events 分支 bri/。
- 10-19 00:40 第二步：tools/bri_scan.py（USGS、GDACS、NASA EONET、Google 新闻 RSS、IODA 国家告警、美英旅行建议，全部免费）接进 hazards 工作流，每 20 分钟写 events 分支 bri/live.json；Worker hub.js 新增 hubBri，连接器 everest_events 加 page:bri。复原：删 hazards.yml 里 bri 那两行、git revert。
- 10-19 01:00 回溯测试发现并修正证据包脚本 4 处问题：①维基百科没设时间上限，2025 年事件匹配到了 2026 年的条目；②BIPAD 水位站给的是“现在”的状态，事件过去 3 天以上不再列（原来对 3–14 天前的事件也列当前状态）；③哥白尼应急制图只查最近 60 次启动，改为 400 次；④尼泊尔以外的国家，IODA 地区名对不上，改查全国。复原：git revert。
- 10-19 第三步：总览页 v85 新增“一带一路”标签（在“证据链”后面）。内容：每国一张小地图（AidData 项目范围＋编号＋比例尺，周边地震/灾害警报/自然事件的位置用橙点）、美英旅行建议和 IODA 告警、每个项目一张卡（周边事件、新闻里的事件线索、其他报道折叠）、4 起事件的偏差对比表、演练（MiroFish）占位说明。数据走连接器 everest_events(id="page:bri")，每 10 分钟刷新。tools/bri_scan.py 的 USGS/GDACS/EONET 条目加了 lat/lon 供地图画点。
- 复原：用 v84 备份覆盖 hub/everest-hub.html 并重新发布到同一个 artifact；git revert 本次提交。
- 10-19 v86 一带一路标签重做：v85 在页面里排版是坏的（面板里的 </details> 被侧栏的 pn() 换成 </div>，提前关掉了外框，内容变成一列列窄条）。重做成：顶部 4 个数字（项目、周边事件、新闻线索、旅行建议最高级）＋三段切换（实时态势 / 偏差测试 / 演练）；实时态势按国家切换，地图带国界底图（Natural Earth 1:50m，tools/bri_basemap.js 生成）、首都、比例尺，默认放大到项目区，可切“看全国”；项目列表点开看详情，地图和列表联动；偏差测试按“相符 / 部分 / 缺失”统计并逐项上色。不再用 <details>。
- 复原：用 v85 或 v84 备份覆盖并重新发布；git revert 本次提交。
- 10-19 01:00 v87 接入 World Monitor（用户的免费账号，claude.ai 自定义连接器 https://worldmonitor.app/mcp ，OAuth）。免费账号每天 5 次数据调用、只能用读缓存的工具。新定时任务 trig_01FPiJV718V67Kt7XAhLs9dC 每天北京 08:17 调 3 次 get_conflict_events（巴基斯坦、尼泊尔、老挝），写页面数据库 live/wm；页面“一带一路”标签显示 UCDP 冲突事件（地图红色菱形、按离项目距离排序）和 GDELT 动荡信号（只列地名，标“未核实”）。不用它的预测类工具。首份 live/wm 由本会话手动写入（巴基斯坦 8 条、尼泊尔 0 条、老挝今天次数用完未查）。
- 复原：删除该定时任务；ArtifactData 删除 live/wm；页面用 v86 备份覆盖并重新发布；git revert。
- 10-19 01:40 一带一路分出去，成为单独的项目 Yizebaba/BRI-Empower（网页 https://yizebaba.github.io/BRI-Empower/ ，3D 地球背景，MiroFish 推演表单）。珠峰这边：总览页回到 v84 的内容（删掉 v85–v87 的“一带一路”标签、样式、底图、live/wm 订阅），右上角加“一带一路 ↗”链接，版本记 v88；Worker 去掉 page:bri；hazards.yml 去掉 bri_scan 步骤；删除 bri/、tools/bri_*.py、tools/bri_basemap.js、bri-retro.yml（都已搬到新仓库）。evidence_pack.py 的多国支持保留（不影响尼泊尔）。预测限制只在新项目里取消，珠峰照旧只监测、不预测。
- 复原：git revert 本次提交；页面用 v87 备份（scratchpad hub_v87 或 git 18b23e73）重新发布。
- 10-19 12:40 用户决定珠峰和一带一路都取消“只监测、不预测”的限制，两边都接入 MiroFish。珠峰这边：
  - 原则改为“监测与推演分开”：监测部分只写事实；推演由 MiroFish 单独运行、单独保存、标注为推演，不进证据链。改了页面政策和说明、Worker 连接器说明、README、docs/HUB_GUIDE.md、plugin 技能、site/index.html 的措辞（指标说明里“不是预警”这类描述保留）。
  - tools/mirofish_seed.py 删掉预设的推演要求，只用使用者自己写的文字（环境变量 MF_REQUIREMENT）。mirofish.yml 新增必填输入 requirement、title、request_id，记录 request.json，并在 events 分支维护 mirofish/index.json（tools/mirofish_checkpoint.sh）。已手动写入 4 次早期测试的索引。
  - 新增推演页 site/drill.html（GitHub Pages：https://yizebaba.github.io/EVEREST-/drill.html ）：写要求、连接 GitHub（令牌只存浏览器）、提交运行、看记录和报告。
  - 总览页 v89：右上角加“推演 ↗”；新增“推演”标签（记录来自连接器 page:mf，下面附最近一次运行的详情）。Worker 新增 page:mf。
- 复原：git revert 本次提交；页面用 v88 重新发布；events 分支 mirofish/index.json 可留着。
- 10-19 13:00 一带一路推演改在珠峰仓库的 mirofish 工作流里运行（新输入 project=bri、scope），共用这里的模型和 Zep 密钥，用户不用在新仓库再设密钥。种子文档由 tools/mirofish_seed_bri.py 从 Yizebaba/BRI-Empower 读取；结果放 events 分支 mirofish-bri/（有自己的 index.json 和 LATEST）。两个推演页共用浏览器里的同一个 GitHub 令牌（localStorage 键 gh_token；同一网域 yizebaba.github.io）。
- 复原：git revert 本次提交。
- 10-21 00:10 v90：新增“全球情报”标签，显示尼泊尔和中国的 World Monitor 数据（冲突、新闻要闻、断网、旅行建议）和两国地震、灾害警报；数据由 BRI-Empower 每日从 World Monitor 取全球数据、按国家整理（data/wm.json、data/country_live.json），Worker 新增 page:wm 读取。一带一路推演的国家范围改为 150 国任选（mirofish.yml 的 scope 为 ISO3）。
- 复原：git revert 本次提交；页面用 v89 备份重新发布。
- 10-21 10:30 推演改成“谁推演谁出密钥”。Worker 新增 /mf/submit、/mf/job、/mf/take、/mf/claim、/mf/done（cf-worker/src/mfq.js，D1 表 mf_jobs）：网页提交推演要求和提交者自己的模型、Zep 密钥，Worker 先试密钥再排队；新工作流 mirofish-queue.yml 每 5 分钟取排队任务并派出 mirofish.yml（每个任务一次运行，最多 3 个同时跑），mirofish.yml 用 GitHub OIDC 身份向 Worker 领取密钥（tools/mirofish_claim.py；领取后 Worker 立刻删除，6 小时没人领也删除），结束时回报。访客不再需要 GitHub 令牌。仓库主人在 Actions 里手动运行（不填 job）时仍用仓库 Secrets。
- 复原：git revert 本次提交（D1 表 mf_jobs 可留着或 DROP TABLE mf_jobs）。
- 10-21 11:00 BRI-Empower（另一个仓库）同步改动：推演标签放第一位并设为默认；表单改为填自己的模型和 Zep 密钥（提交到上面的 Worker 排队），可选 1–5 国；去掉 GitHub 令牌；右上角顺序改为 GitHub、珠峰平台、语言。种子文档每国改为 5–7 份（国家概况、参与方、全部行业贸易与物流、中国融资、近期态势、重点项目、历史事件），新增世界银行、Wikidata、UN Comtrade 分国分行业数据（tools/country_facts.py、tools/trade.py、trade.yml 每周）。
- 复原：在 BRI-Empower 仓库 git revert a52a459 及之前两次提交（种子文档、贸易数据）；改前的网页备份在 scratchpad bri_index_before_byok.html。
- 10-21 18:10 BRI-Empower：左下角大标题改为“全局●预鉴”（英文 Global ● Foresight）；英文模式补全（数据源、偏差测试有英文版 data/retro_summary_en.json，国家名、项目名、错误提示、地球提示框都翻译）；新增每周文档抓取 tools/docs_fetch.py + docs.yml（维基百科、世界银行文献库、OpenAlex 论文、ReliefWeb），每国多一份种子文档 08_documents.md。
- 复原：在 BRI-Empower 仓库 git revert 该提交；删除 docs.yml 即停止抓取。
- 10-21 23:40 推演：轮数默认“自动”（不传 max_rounds，由 MiroFish 按事件定，可填上限 5–200；工作流超时改 355 分钟）；可上传自己的 PDF/Markdown/TXT（最多 5 个、单个 10 MB、合计 20 MB，Worker 分块存 D1 表 mf_files，领取即删）；结果导出 report.md/.docx/.pdf/.html 和 process.zip（CSV），每份开头加“推演内容，不是事实”和免责声明（tools/mirofish_export.py），索引记 exports。BRI 网页：国家页咽喉要道加航空、铁路、公路（tools/chokepoints_land.py，每天两次），可折叠；“偏差测试”改名“推演测试”；推演记录可看报告和下载各格式。
- 复原：两个仓库分别 git revert 本次提交。
- 10-22 01:30 推演表单：国家可以不选（0–5 个）；种子文档改为勾选（默认全选，可全不选），只上传勾选的（mirofish_seed_bri.py 读 MF_SEEDS）；自己的资料改为“＋ 上传文件”按钮，上限提到 20 个、单个 50 MB（MiroFish 上限）、合计 100 MB，分块上传（/mf/submit 报清单 → /mf/upload → /mf/commit，D1 合计超过 300 MB 时暂停接收）。BRI 咽喉要道扩到 150 国：每国主要国际机场（OurAirports）、20 个跨境铁路口岸、公路口岸和 291 段陆地边境（data/borders.json，Natural Earth 计算），海运加各国港口；新工作流 chokepoints.yml 每天两次；国家详情页显示本国的咽喉要道。
- 复原：两个仓库分别 git revert 本次提交；删除 chokepoints.yml 即停止抓取。
- 10-22 01:15 BRI 网页左下角在“全局●预鉴”上方加三行广告词（“如果，看见未来的不同可能 / 如果，未来可以事先预演 / 那么决策的胜率会有多高呢？”），金色竖线、逐行淡入，有英文版和手机尺寸。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 01:20 BRI 推演标签的种子文档列表去掉“用这个文档推演 ↓”（已有勾选框）；种子文档标签保留下载按钮。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 01:30 BRI 广告词改到地球上方居中（用户选的方案 B），左下角恢复为只有“全局●预鉴”。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 01:45 BRI 网页：大标题改为“全量●预鉴”（英文 Full-Scope · Foresight）；“一带一路 · 150 个共建国家”移到左上角网站名下面；广告词放在大标题下面（原副标题位置），地球上方的那份去掉。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 01:55 BRI 左上角小字改为“150 个共建国家”；左下角标题 38px、广告词 16px（同一衬线字体，加载 400 字重），标题和三行广告词依次淡入，图例不动。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 02:05 BRI 左上角网站名改为“一带一路 全量●预鉴”（英文 Belt and Road Full-Scope Foresight），网页标题同步；左下角去掉大标题，只留三行广告词和图例；手机顶部按钮缩小以免挤出屏幕。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 02:10 BRI 左上角改为“一带一路 全量 预鉴”（去掉圆点），去掉英文 BRI-Empower 小字；下面一行“150 个共建国家”保留。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 02:20 BRI 推演表单“开始推演”旁加“定制推演 ✉”按钮（mailto:yizebaba@gmail.com，预填主题和询价模板，带上已选国家）。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 02:40 BRI 新增说明页 site/about.html（我们做什么、四步流程、适合的决策、行业、紧急程度四级、两种用法、免责，中英文），首页左上角最左侧加“说明”按钮；定制邮件模板加“紧急程度”一行；定制按钮改为打开浏览器 Gmail 写信页。
- 复原：在 BRI-Empower 仓库 git revert 这几次提交；删除 site/about.html。
- 10-22 03:00 所有网页去掉 MiroFish 字样：BRI 首页、说明页、数据源列表（删掉 mirofish 一项）；珠峰推演页 site/drill.html；总览页 v91（推演标签、按钮提示、说明文字）；导出文件的免责声明改为“多智能体推演”。GitHub 代码和 README 里保留（开源许可的出处）。
- 复原：两个仓库分别 git revert；总览页用 scratchpad hub_v90_before_nomf.html 重新发布。
- 10-22 03:05 BRI 首页“说明”按钮改为右上角“文档 ↗”（GitHub 左边，新标签页打开 about.html），左上角那个去掉。
- 复原：在 BRI-Empower 仓库 git revert 该提交。
- 10-22 03:20 BRI 文档页扩充（解决什么问题、数据来源和更新频率、种子文档内容、使用步骤、结果下载、密钥与隐私、写推演要求的建议、常见问题），中英文；推演表单加一句“推演要求和报告会公开在全部推演记录里”；README 重写为中英文。
- 复原：在 BRI-Empower 仓库 git revert 该提交。

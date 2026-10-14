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

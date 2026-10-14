# 281 种灾害：逐个实测

灾害分类取自联合国减灾署和国际科学理事会《灾害信息档案》2025 版（UNDRR-ISC HIPs）：281 种，8 大类。下表由每小时运行的灾种扫描（`.github/workflows/hazards.yml` → `tools/hazard_scan.py`）实测生成，最近一次：2026-10-14T03:36:12Z（UTC）。

每种灾害至少有一个实测能用的公开来源；新闻层（尼泊尔英文媒体、谷歌新闻、ReliefWeb RSS）用逐条写的匹配词（`tools/hazard_keywords.py`）覆盖全部 281 种。只记录已经发生、被公开来源记下的事，不预测。

本文件是某一次扫描的快照；每小时的最新结果在 events 分支 [`hazards/scan.json`](https://github.com/Yizebaba/EVEREST-/blob/events/hazards/scan.json)，总览页“证据链 → 灾种 281”实时显示。

## 状态

| 状态 | 数量 | 含义 |
|---|---|---|
| 本地有记录 | 35 | 近 90 天在尼泊尔、西藏或喜马拉雅一带有记录 |
| 外地有记录 | 53 | 近 90 天只在别的地区有记录（接口能用，本地没发生或没报道） |
| 有持续观测 | 11 | 有卫星或站网在持续观测，但没有“发生了”的记录（例如 Sentinel-5P 大气成分） |
| 来源正常，90 天无记录 | 182 | 至少一个来源实测能用，近 90 天没有相关记录 |

## 数据源实测

| 来源 | 结果 | 本次条数 | 其中本地 | 说明 |
|---|---|---|---|---|
| BIPAD 灾害事件库 | 正常 | 500 | 500 |  |
| BIPAD 警报 | 正常 | 100 | 100 |  |
| BIPAD 空气质量站 | 正常 | 2 | 2 |  |
| NASA EONET | 正常 | 209 | 1 |  |
| USGS 地震目录 | 正常 | 14 | 5 |  |
| GDACS | 正常 | 100 | 1 |  |
| NOAA SWPC 空间天气 | 正常 | 90 | 90 |  |
| NASA CNEOS | 正常 | 82 | 0 |  |
| CelesTrak 在轨目标 | 正常 | 223 | 0 |  |
| WHO 疫情通报 | 正常 | 100 | 0 |  |
| WHO FluNet（尼泊尔） | 正常 | 8 | 8 |  |
| WOAH WAHIS 动物疫情 | 正常 | 50 | 0 |  |
| openFDA 食品药品召回 | 正常 | 100 | 0 |  |
| CISA 已利用漏洞 | 正常 | 32 | 0 |  |
| Have I Been Pwned 数据泄露 | 正常 | 8 | 0 |  |
| Cloudflare Radar | 需密钥 |  |  | CF_RADAR_TOKEN |
| IODA 网络连通 | 正常 | 0 | 0 |  |
| 尼泊尔央行汇率 | 正常 | 0 | 0 |  |
| Safecast 辐射 | 正常 | 0 | 0 |  |
| Sentinel-5P 大气成分 | 正常 | 7 | 7 |  |
| 太平洋海啸预警中心 | 正常 | 2 | 0 |  |
| NOAA NCEI 历史灾害库 | 正常 | 42 | 0 |  |
| IOC 海平面站 | 正常 | 1 | 0 |  |
| IBTrACS 活跃气旋 | 正常 | 7 | 0 |  |
| NSIDC 海冰 | 正常 | 2 | 0 |  |
| 史密森尼火山周报 | 失败 |  |  | HTTP Error 403: Forbidden |
| GBIF 物种记录（尼泊尔） | 正常 | 2 | 2 |  |
| Global Forest Watch | 需密钥 |  |  | GFW_API_KEY |
| NASA FIRMS 火点 | 需密钥 |  |  | FIRMS_MAP_KEY |
| OpenAQ 空气质量 | 需密钥 |  |  | OPENAQ_API_KEY |
| ACLED 冲突事件 | 需密钥 |  |  | ACLED_KEY |
| ReliefWeb | 需密钥 |  |  | RELIEFWEB_APPNAME |
| 新闻 RSS | 正常 | 151 | 151 |  |

## 气象与水文（Meteorological & Hydrological）· 53 种

本地有记录 11 · 外地有记录 12 · 有持续观测 2 · 来源正常，90 天无记录 28

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| MH0101 | 下击暴流（Downburst） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0102 | 闪电（雷暴）（Lightning (electrical storm)） | 本地有记录 | 26（26） | BIPAD 灾害事件库、新闻 RSS | 2026-10-09 Thunderbolt at Bhojpur Municipality-11 |
| MH0103 | 雷暴（Thunderstorm） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| MH0201 | 沙尘暴（Dust Storm or Sandstorm） | 有持续观测 | 0（0） | NASA EONET、Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __AER_AI 覆盖喜马拉雅（有观测，未计算数值） |
| MH0202 | 雾（Fog） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0203 | 霾（Haze） | 本地有记录 | 2（2） | BIPAD 空气质量站、NASA EONET、Sentinel-5P 大气成分、新闻 RSS | 2026-10-14 Dang AQI 152.0 |
| MH0204 | 沙霾（Sand Haze） | 来源正常，90 天无记录 | 0（0） | NASA EONET、新闻 RSS |  |
| MH0205 | 烟（Smoke） | 有持续观测 | 0（0） | NASA EONET、Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __AER_AI 覆盖喜马拉雅（有观测，未计算数值） |
| MH0301 | 大风（Wind） | 本地有记录 | 22（22） | BIPAD 灾害事件库、新闻 RSS | 2026-10-09 Wind storm at Parsagadhi Municipality-1 |
| MH0302 | 德雷乔风暴（Derecho） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0303 | 烈风（Gale） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0304 | 飑（Squall） | 本地有记录 | 22（22） | BIPAD 灾害事件库、新闻 RSS | 2026-10-09 Wind storm at Parsagadhi Municipality-1 |
| MH0305 | 龙卷（Tornado） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0306 | 低压或气旋（Depression or Cyclone） | 外地有记录 | 14（0） | IBTrACS 活跃气旋、NASA EONET、新闻 RSS | 2026-10-13 Hurricane Simon |
| MH0307 | 温带气旋（Extra-tropical Cyclone） | 外地有记录 | 10（0） | IBTrACS 活跃气旋、NASA EONET、新闻 RSS | 2026-10-13 Hurricane Simon |
| MH0308 | 副热带气旋（Sub-tropical Cyclone） | 外地有记录 | 9（0） | IBTrACS 活跃气旋、NASA EONET、新闻 RSS | 2026-10-13 Hurricane Simon |
| MH0309 | 热带气旋（Tropical Cyclone） | 外地有记录 | 14（0） | GDACS、IBTrACS 活跃气旋、NASA EONET、新闻 RSS | 2026-10-13 Hurricane Simon |
| MH0401 | 干旱（Drought） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、GDACS、NASA EONET、新闻 RSS |  |
| MH0402 | 降雨（Rain） | 本地有记录 | 98（98） | BIPAD 灾害事件库、BIPAD 警报、新闻 RSS | 2026-10-10 Heavy Rainfall at Siraha-1, Siraha |
| MH0403 | 暴风雪（Blizzard） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0404 | 冰雹（Hail） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| MH0405 | 降雪（Snow） | 来源正常，90 天无记录 | 0（0） | NASA EONET、新闻 RSS |  |
| MH0406 | 雪暴（Snow Storm） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| MH0501 | 热浪（Heatwave） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、NASA EONET、新闻 RSS |  |
| MH0502 | 寒潮（Cold Wave） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、NASA EONET、新闻 RSS |  |
| MH0503 | 白灾（Dzud）（Dzud） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0504 | 冰冻（Freeze） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0505 | 白霜（Frost (Hoar Frost)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0506 | 冻雨（Freezing Rain (Supercooled Rain)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0507 | 雨凇（Glaze） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0508 | 地面霜冻（Ground Frost） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0509 | 结冰（Icing (Including Ice)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0510 | 解冻（Thaw） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0600 | 洪水（Flooding） | 本地有记录 | 192（170） | BIPAD 灾害事件库、GDACS、NASA EONET、新闻 RSS | 2026-10-14 Kathmandu Post：Flood cuts off northern Gorkha’s lifeline, disrupts Man |
| MH0601 | 沿海洪水（Coastal Flooding） | 外地有记录 | 1（0） | IOC 海平面站、新闻 RSS | 2026-10-14 全球 1766 个潮位站，最近 6 小时在报 1144 个 |
| MH0602 | 河口洪水（Estuarine (Coastal) Flooding） | 外地有记录 | 1（0） | IOC 海平面站、新闻 RSS | 2026-10-14 全球 1766 个潮位站，最近 6 小时在报 1144 个 |
| MH0603 | 山洪（Flash Flooding） | 本地有记录 | 31（31） | 新闻 RSS | 2026-10-13 Google News（尼泊尔灾害）：Flash floods in Nepal again: Warning bells for Hima |
| MH0604 | 河流洪水（Fluvial (Riverine) Flooding） | 本地有记录 | 75（75） | BIPAD 灾害事件库、BIPAD 警报、新闻 RSS | 2026-10-12 Google News（尼泊尔灾害）：What caused Nepal’s Budhi Gandaki river flood? Offi |
| MH0605 | 地下水洪水（Groundwater Flooding） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0606 | 地表积水（Surface water Flooding） | 本地有记录 | 1（1） | BIPAD 灾害事件库、新闻 RSS | 2026-10-11 Google News（尼泊尔灾害）：GMA News. . AERIAL FOOTAGE NG BAHA SA NEPAL Aerial  |
| MH0607 | 冰湖溃决洪水（Glacial Lake Outburst Flooding） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| MH0608 | 冰塞洪水（含碎屑）（Ice-Jam Flooding Including Debris） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0609 | 内涝（Ponding (Drainage) Flooding） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0610 | 融雪洪水（Snowmelt Flooding） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0701 | 畸形浪（Rogue Wave） | 外地有记录 | 1（0） | IOC 海平面站、新闻 RSS | 2026-10-14 全球 1766 个潮位站，最近 6 小时在报 1144 个 |
| MH0702 | 假潮（Seiche） | 外地有记录 | 1（0） | IOC 海平面站、新闻 RSS | 2026-10-14 全球 1766 个潮位站，最近 6 小时在报 1144 个 |
| MH0703 | 风暴潮（Storm Surge） | 外地有记录 | 1（0） | IOC 海平面站、新闻 RSS | 2026-10-14 全球 1766 个潮位站，最近 6 小时在报 1144 个 |
| MH0704 | 风暴高潮（Storm Tides） | 外地有记录 | 1（0） | IOC 海平面站、新闻 RSS | 2026-10-14 全球 1766 个潮位站，最近 6 小时在报 1144 个 |
| MH0705 | 海啸（Tsunami） | 本地有记录 | 42（2） | GDACS、NOAA NCEI 历史灾害库、太平洋海啸预警中心、新闻 RSS | 2026-10-13 Nepali Times：Stop calling the Nepal flood a ‘Himalayan Tsunami’ |
| MH0706 | 海冰（Sea ice） | 外地有记录 | 10（0） | NASA EONET、NSIDC 海冰、新闻 RSS | 2026-10-09 Iceberg D35 |
| MH0707 | 流冰（Ice flow） | 外地有记录 | 10（0） | NASA EONET、NSIDC 海冰、新闻 RSS | 2026-10-09 Iceberg D35 |
| MH0708 | 海洋热浪（Marine Heatwave） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| MH0801 | 雪崩（Avalanche） | 本地有记录 | 4（4） | BIPAD 灾害事件库、新闻 RSS | 2026-10-13 OnlineKhabar English：An avalanche and massive landslide triggered the  |

## 地外（Extraterrestrial）· 10 种

本地有记录 4 · 外地有记录 5 · 有持续观测 1

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| ET0101 | 地磁扰动（Geomagnetic Disturbance） | 本地有记录 | 62（62） | NOAA SWPC 空间天气、新闻 RSS | 2026-10-13 Space Weather Message Code: WARK04 Serial Number: 5435 Issue Time: 202 |
| ET0102 | 电离层扰动（Ionospheric Disturbance） | 本地有记录 | 15（15） | NOAA SWPC 空间天气、新闻 RSS | 2026-10-10 Space Weather Message Code: SUMXM5 Serial Number: 328 Issue Time: 2026 |
| ET0103 | 太阳耀斑（Solar Flare） | 本地有记录 | 15（15） | NOAA SWPC 空间天气、新闻 RSS | 2026-10-10 Space Weather Message Code: SUMXM5 Serial Number: 328 Issue Time: 2026 |
| ET0104 | 太阳高能粒子（Solar Energetic Particles） | 本地有记录 | 12（12） | NOAA SWPC 空间天气、新闻 RSS | 2026-10-10 Space Weather Message Code: ALTEF3 Serial Number: 3753 Issue Time: 202 |
| ET0201 | 空中爆炸（陨石）（Airburst） | 外地有记录 | 28（0） | NASA CNEOS、新闻 RSS | 2026-10-04 火球 能量 5.4e10 J |
| ET0202 | 紫外辐射（UV Radiation） | 有持续观测 | 0（0） | Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __O3 覆盖喜马拉雅（有观测，未计算数值） |
| ET0203 | 陨石撞击（Meteorite Impact） | 外地有记录 | 28（0） | NASA CNEOS、新闻 RSS | 2026-10-04 火球 能量 5.4e10 J |
| ET0204 | 航天事故（Space Hazard / Accident） | 外地有记录 | 222（0） | CelesTrak 在轨目标、新闻 RSS | 2026-10-13 新入轨 STARLINK-38442 |
| ET0205 | 近地天体（Near-Earth Object） | 外地有记录 | 54（0） | NASA CNEOS、新闻 RSS | 2026-10-13 2026 TM35 近地掠过 3.9 倍月距 |
| ET0206 | 空间碎片（Space Debris） | 外地有记录 | 1（0） | CelesTrak 在轨目标、新闻 RSS | 2026-10-14 跟踪中的碎片（四次大型解体事件）2679 个 |

## 地质（Geological）· 25 种

本地有记录 5 · 外地有记录 2 · 有持续观测 2 · 来源正常，90 天无记录 16

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| GH0101 | 地震（Earthquake） | 本地有记录 | 40（7） | BIPAD 灾害事件库、GDACS、NASA EONET、USGS 地震目录、新闻 RSS | 2026-10-14 Google News（西藏灾害）：Light mag. 3.9 earthquake - 86 km east of Maizhokung |
| GH0201 | 熔岩流（Lava Flows (Lava Domes)） | 外地有记录 | 4（0） | BIPAD 灾害事件库、GDACS、NASA EONET、NOAA NCEI 历史灾害库、新闻 RSS | 2026-05-07 Indonesia Dukono |
| GH0202 | 火山灰与碎屑（Ash/Tephra Fall (including Volcanic Ballistic projectiles)） | 外地有记录 | 4（0） | NASA EONET、NOAA NCEI 历史灾害库、新闻 RSS | 2026-05-07 Indonesia Dukono |
| GH0203 | 火山碎屑流（Pyroclastic Density Current） | 来源正常，90 天无记录 | 0（0） | NASA EONET、NOAA NCEI 历史灾害库、新闻 RSS |  |
| GH0204 | 火山泥流（Lahars） | 来源正常，90 天无记录 | 0（0） | NASA EONET、NOAA NCEI 历史灾害库、新闻 RSS |  |
| GH0205 | 火山气体与气溶胶（Volcanic Gases and Aerosols） | 有持续观测 | 0（0） | NASA EONET、NOAA NCEI 历史灾害库、Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __SO2 覆盖喜马拉雅（有观测，未计算数值） |
| GH0300 | 重力块体运动（滑坡）（Gravitational Mass Movement (Landslide)） | 本地有记录 | 150（150） | BIPAD 灾害事件库、NASA EONET、USGS 地震目录、新闻 RSS | 2026-10-14 Kathmandu Post：Nepal, India discuss border security, transnational cri |
| GH0301 | 崩落（落石、冰崩）（Falls） | 本地有记录 | 1（1） | USGS 地震目录、新闻 RSS | 2026-10-12 Google News（尼泊尔灾害）：What caused Nepal’s Budhi Gandaki river flood? Offi |
| GH0302 | 侧向扩离（Spreads） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0303 | 流动（泥石流）（Flows） | 本地有记录 | 1（1） | 新闻 RSS | 2026-10-12 Google News（西藏灾害）：The 11 October 2026 landslide and debris flow/flood  |
| GH0304 | 滑动（Slides） | 本地有记录 | 147（147） | BIPAD 灾害事件库、新闻 RSS | 2026-10-13 OnlineKhabar English：An avalanche and massive landslide triggered the  |
| GH0305 | 倾倒（Topples） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0306 | 海底滑坡（Submarine Landslide） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0307 | 砂土液化（Liquefaction） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0308 | 落水洞（Sinkhole） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0309 | 沉降与抬升（Subsidence and Uplift） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0310 | 胀缩沉降（Shrink-Swell Subsidence） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0311 | 地表破裂与裂缝（Surface Rupture & Fissure） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0401 | 压缩性土（Compressive Soils） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0402 | 土壤退化（Soil Degradation） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0403 | 土壤侵蚀（Soil Erosion） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| GH0404 | 河岸侵蚀与淤积（River Erosion & Accretion） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0405 | 海岸侵蚀与淤积（Coastal Erosion & Accretion） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0406 | 沙地侵入（Sand Encroachment） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| GH0407 | 地下气体（甲烷、氡等）（Ground Gases (CH4, Rn, etc.)） | 有持续观测 | 0（0） | Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __CH4 覆盖喜马拉雅（有观测，未计算数值） |

## 环境（Environmental）· 24 种

本地有记录 3 · 外地有记录 1 · 有持续观测 4 · 来源正常，90 天无记录 16

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| EN0101 | 室内空气污染（Household Air Pollution） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0102 | 点源空气污染（Air Pollution (Point Source)） | 有持续观测 | 0（0） | Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __NO2 覆盖喜马拉雅（有观测，未计算数值） |
| EN0103 | 室外空气污染（Ambient (Outdoor) Air Pollution） | 本地有记录 | 5（5） | BIPAD 灾害事件库、BIPAD 空气质量站、BIPAD 警报、Sentinel-5P 大气成分、新闻 RSS | 2026-10-14 Pollution Alert at Ghorahi-2, Dang |
| EN0104 | 黑碳（Black Carbon） | 本地有记录 | 2（2） | BIPAD 空气质量站、Sentinel-5P 大气成分、新闻 RSS | 2026-10-14 Dang AQI 152.0 |
| EN0105 | 酸雨（Acid Rain） | 有持续观测 | 0（0） | Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __SO2 覆盖喜马拉雅（有观测，未计算数值） |
| EN0106 | 面源污染（Runoff / Nonpoint Source Pollution） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0201 | 毁林（Deforestation） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| EN0202 | 森林衰退（Forest Declines and Diebacks） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0203 | 森林扰动（Forest Disturbances） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0204 | 森林入侵物种（Forest Invasive Species） | 有持续观测 | 0（0） | GBIF 物种记录（尼泊尔）、新闻 RSS | 尼泊尔近一年外来物种记录 0 条 |
| EN0205 | 野火（森林火灾）（Wildfires） | 本地有记录 | 242（2） | BIPAD 灾害事件库、BIPAD 警报、GDACS、NASA EONET、新闻 RSS | 2026-10-13 Forest Fire at Bhairabi-1, Dailekh |
| EN0206 | 荒漠化（Desertification） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0207 | 红树林丧失（Loss of Mangroves） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0301 | 土地退化（Land Degradation） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0302 | 海水入侵（Seawater intrusion） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0303 | 盐渍化（Salinity & Sodicity） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0304 | 湿地退化（Wetland Loss/Degradation） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0305 | 冻土消融（Permafrost Loss） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0401 | 海洋酸化（Ocean Acidification） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0402 | 海平面上升（Sea Level Rise） | 外地有记录 | 1（0） | IOC 海平面站、新闻 RSS | 2026-10-14 全球 1766 个潮位站，最近 6 小时在报 1144 个 |
| EN0403 | 富营养化（Eutrophication） | 来源正常，90 天无记录 | 0（0） | NASA EONET、新闻 RSS |  |
| EN0404 | 珊瑚白化（Coral Bleaching） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0405 | 采砂（Sand Mining） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| EN0501 | 生物多样性丧失（Biodiversity Loss） | 有持续观测 | 0（0） | GBIF 物种记录（尼泊尔）、新闻 RSS | 尼泊尔近 30 天 275 条物种观测记录 |

## 化学（Chemical）· 27 种

外地有记录 3 · 有持续观测 1 · 来源正常，90 天无记录 23

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| CH0100 | 重金属与微量元素（Heavy Metals & Trace Elements） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0101 | 砷（Arsenic） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0102 | 镉（Cadmium） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0103 | 铅（Lead） | 外地有记录 | 1（0） | openFDA 食品药品召回、新闻 RSS | 2026-10-07 Galil Importing Corp：Product contains elevated levels of lead. |
| CH0104 | 汞（Mercury） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0105 | 氟碘过量或不足（Fluoride & Iodine/Iodide Excess or Inadequate Intake） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0201 | 黄曲霉毒素（Aflatoxins） | 来源正常，90 天无记录 | 0（0） | openFDA 食品药品召回、新闻 RSS |  |
| CH0202 | 石棉（Asbestos） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0203 | 苯与烃类（Benzene & Hydrocarbons） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0300 | 有毒气体（Toxic Gases） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| CH0301 | 氨（Ammonia） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0302 | 一氧化碳（Carbon Monoxide） | 有持续观测 | 0（0） | Sentinel-5P 大气成分、新闻 RSS | Sentinel-5P __CO 覆盖喜马拉雅（有观测，未计算数值） |
| CH0303 | 氯气（Chlorine） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0400 | 窒息性气体（Asphyxiant Gases） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0500 | 持久性有机污染物（Persistent Organic Pollutants） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0501 | 农药（Pesticides） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0502 | 二噁英（Dioxins & Dioxin-like Substance） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0503 | 全氟烷基物质（Polyfluoroalkyl Substances） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0504 | 微塑料（Microplastics） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0601 | 食品与饲料污染物（Levels of Contaminants in Food & Feed） | 外地有记录 | 49（0） | BIPAD 灾害事件库、openFDA 食品药品召回、新闻 RSS | 2026-10-07 TODD'S SEEDS LLC：Products contain alfalfa seed recalled by the supplie |
| CH0602 | 劣质与假冒药品（Substandard & Falsified Medical Products） | 外地有记录 | 50（0） | openFDA 食品药品召回、新闻 RSS | 2026-10-07 Aurobindo Pharma USA Inc：Discoloration: consumer complaints received f |
| CH0603 | 甲醇（Methanol） | 来源正常，90 天无记录 | 0（0） | openFDA 食品药品召回、新闻 RSS |  |
| CH0604 | 阿片类与成瘾物质（Opioids & Other Addictive Substances） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0605 | 海洋毒素（Marine Toxins） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0901 | 腐蚀性物质（Corrosive Substances） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| CH0902 | 硝酸铵（Ammonium Nitrate） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| CH0903 | 化学战剂（Chemical Warfare Agents） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |

## 生物（Biological）· 83 种

本地有记录 5 · 外地有记录 27 · 有持续观测 1 · 来源正常，90 天无记录 50

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| BI0101 | 空气传播疾病（Airborne Diseases (human and Animal)） | 本地有记录 | 39（8） | BIPAD 灾害事件库、WHO FluNet（尼泊尔）、WHO 疫情通报、新闻 RSS | 2026-10-10 尼泊尔流感监测第 40 周：检测 37 份，阳性 21 |
| BI0102 | 血液传播病毒（Blood Borne Viruses (Human and Animal)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0103 | 腹泻病（Diarrhoeal Diseases (Human)） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| BI0104 | 食源性疾病（Foodborne Diseases (Human impact)） | 外地有记录 | 49（0） | BIPAD 灾害事件库、openFDA 食品药品召回、新闻 RSS | 2026-10-07 TODD'S SEEDS LLC：Products contain alfalfa seed recalled by the supplie |
| BI0105 | 被忽视的热带病（Neglected Tropical Diseases (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0106 | 性传播疾病（Sexually Transmitted Diseases (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0107 | 疫苗可预防疾病（Vaccine-Preventable Diseases (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0108 | 媒介传播疾病（Vector Borne Diseases (VBD) (Human and Animal)） | 本地有记录 | 2（2） | BIPAD 灾害事件库、WHO 疫情通报、新闻 RSS | 2026-10-14 Kathmandu Post：Scrub typhus fears cast a shadow over Dashain in Salyan |
| BI0109 | 病毒性出血热（Viral Haemorrhagic Fevers (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2025-03-27 Norway · Pathogenic rabbit lagoviruses (Inf. with) (Rabbit haemorrhagi |
| BI0110 | 水源性疾病（Waterborne Diseases (Human)） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| BI0111 | 隐孢子虫病（Cryptosporidium (Human and Animal)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0112 | 囊尾蚴病（Cysticercosis (Human and Animal)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0113 | 人畜共患病（Zoonotic Diseases） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0201 | 炭疽（Anthrax） | 外地有记录 | 1（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2025-05-29 Anthrax – Thailand |
| BI0202 | 布鲁氏菌病（Brucellosis (Human and Animal)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0203 | 基孔肯雅热（Chikungunya） | 外地有记录 | 2（0） | WHO 疫情通报、新闻 RSS | 2025-10-03 Chikungunya virus disease- Global situation |
| BI0204 | 霍乱（Cholera (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、新闻 RSS | 2025-08-29 Cholera – Multi-country with a focus on countries experiencing current |
| BI0205 | 新冠（COVID-19 (SARS-CoV-2) (Human)） | 外地有记录 | 1（0） | BIPAD 灾害事件库、WHO 疫情通报、新闻 RSS | 2025-05-28 COVID-19 - Global Situation |
| BI0206 | 克里米亚-刚果出血热（Crimean-Congo Haemorrhagic Fever (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0207 | 登革热（Dengue (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、新闻 RSS | 2024-07-22 Dengue – Iran (Islamic Republic of) |
| BI0208 | 白喉（Diphtheria (Human)） | 外地有记录 | 1（0） | WHO 疫情通报、新闻 RSS | 2025-11-21 Diphtheria - African Region (AFRO) |
| BI0209 | 埃博拉（Ebola (Human)） | 外地有记录 | 16（0） | WHO 疫情通报、新闻 RSS | 2026-10-08 Ebola disease caused by Bundibugyo virus - Democratic Republic of the  |
| BI0210 | 产志贺毒素大肠杆菌（Escherichia Coli (STEC) (Human)） | 外地有记录 | 30（0） | WHO 疫情通报、openFDA 食品药品召回、新闻 RSS | 2026-10-07 TODD'S SEEDS LLC：Products contain alfalfa seed recalled by the supplie |
| BI0211 | 甲肝（Hepatitis A (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0212 | 乙肝（Hepatitis B (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0213 | 丙肝（Hepatitis C (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0214 | 艾滋病（HIV and AIDS (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0215 | 拉沙热（Lassa Fever (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0216 | 麻风（Leprosy (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0217 | 钩端螺旋体病（Leptospirosis (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0218 | 李斯特菌病（Listeriosis (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、openFDA 食品药品召回、新闻 RSS | 2026-09-30 GIAS FOOD INC.：Contamination with Listeria monocytogenes |
| BI0219 | 疟疾（Malaria (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、新闻 RSS | 2024-12-27 Acute respiratory infections complicated by malaria (previously undiag |
| BI0220 | 马尔堡病毒（Marburg Virus） | 外地有记录 | 12（0） | WHO 疫情通报、新闻 RSS | 2026-01-26 Marburg virus disease- Ethiopia |
| BI0221 | 麻疹（Measles (Human)） | 外地有记录 | 4（0） | WHO 疫情通报、新闻 RSS | 2026-04-23 Measles - Bangladesh |
| BI0222 | 脑膜炎球菌脑膜炎（Meningococcal Meningitis (Human)） | 外地有记录 | 1（0） | WHO 疫情通报、新闻 RSS | 2025-04-11 Invasive meningococcal disease - Kingdom of Saudi Arabia |
| BI0223 | 中东呼吸综合征（Middle East Respiratory Syndrome (MERS) (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0224 | 猴痘（Mpox (Human)） | 外地有记录 | 6（0） | WHO 疫情通报、新闻 RSS | 2026-02-14 Mpox: recombinant virus with genomic elements of clades Ib and IIb – G |
| BI0225 | 副伤寒（Paratyphoid Fever (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0226 | 伤寒（Typhoid Fever (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0227 | 百日咳（Pertussis (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0228 | 鼠疫（Plague (Human)） | 外地有记录 | 1（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2026-06-16 Czech Republic · Aphanomyces astaci (Inf. with)(Crayfish plague)  |
| BI0229 | 脊髓灰质炎（Polio (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、新闻 RSS | 2025-08-20 Circulating vaccine-derived poliovirus type 1- Israel |
| BI0230 | 朊病毒病（Prion Diseases） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0231 | Q 热（Q Fever） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0232 | 狂犬病（Rabies (Animal and Human)） | 外地有记录 | 3（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2026-03-10 Moldova · Rabies virus (Inf. with)  |
| BI0233 | 轮状病毒（Rotavirus (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0234 | 志贺菌病（Shigellosis (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0235 | 天花（Smallpox (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0236 | 非典（SARS）（Severe Acute Respiratory Syndrome (SARS) (Human)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0237 | 结核（Tuberculosis (Human and Animal)） | 来源正常，90 天无记录 | 0（0） | WHO 疫情通报、新闻 RSS |  |
| BI0238 | 锥虫病（Trypanosomiasis & Tripanomosis (Human and Animal)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0239 | 水痘与带状疱疹（Varicella and Herpes Zoster (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0240 | 西尼罗热（West Nile Fever (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2026-09-05 Slovenia · West Nile Fever  |
| BI0241 | 黄热病（Yellow Fever (Human)） | 外地有记录 | 2（0） | WHO 疫情通报、新闻 RSS | 2026-06-24 Yellow fever - Global |
| BI0242 | 寨卡（Zika Virus (Human)） | 外地有记录 | 1（0） | WHO 疫情通报、新闻 RSS | 2025-01-29 Zika virus disease – India |
| BI0243 | 季节性流感（Seasonal Influenza (Human)） | 本地有记录 | 8（8） | WHO FluNet（尼泊尔）、新闻 RSS | 2026-09-28 尼泊尔流感监测第 40 周：检测 37 份，阳性 21 |
| BI0244 | 大流行性流感（Pandemic Influenza (Human)） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、WHO 疫情通报、新闻 RSS |  |
| BI0245 | 禽流感（Avian Influenza (Human and Animal)） | 外地有记录 | 11（0） | BIPAD 灾害事件库、WHO FluNet（尼泊尔）、WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2026-10-05 Peru · High pathogenicity avian influenza viruses (Inf. with) (poultry |
| BI0301 | 动物疫病（非人畜共患）（Animal Diseases (Not Zoonoses)） | 外地有记录 | 31（0） | WOAH WAHIS 动物疫情、新闻 RSS | 2026-10-08 Poland · Newcastle disease virus (Inf. with)  |
| BI0302 | 非洲猪瘟（African Swine Fever (Animal)） | 外地有记录 | 11（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2026-07-24 Finland · African swine fever virus (Inf. with)  |
| BI0303 | 古典猪瘟（Classical Swine Fever (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0304 | 牛传染性胸膜肺炎（Contagious Bovine Pleuropneumonia (CBPP) (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0305 | 山羊传染性胸膜肺炎（Contagious Caprine Pleuropneumonia (CCPP) (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0306 | 口蹄疫（Foot and Mouth Disease Virus (Animal)） | 外地有记录 | 2（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2026-10-05 Namibia · Foot and mouth disease virus (Inf. with)  |
| BI0307 | 牛结节性皮肤病（Lumpy Skin Disease (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0308 | 新城疫（Newcastle Disease (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0309 | 新大陆螺旋蝇（New World Screwworm (NWS) (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0310 | 小反刍兽疫（Peste des Petits Ruminants (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0311 | 裂谷热（Rift Valley Fever (Animal)） | 外地有记录 | 1（0） | WHO 疫情通报、WOAH WAHIS 动物疫情、新闻 RSS | 2025-11-05 Rift Valley fever- Mauritania and Senegal |
| BI0312 | 牛瘟（Rinderpest (Animal)） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0313 | 牡蛎病害（Oyster Disease Aquaculture） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0314 | 对虾急性肝胰腺坏死（Shrimp Diseases (Bacterial) - Acute Hepatic Pancreatic Necrosis） | 来源正常，90 天无记录 | 0（0） | WOAH WAHIS 动物疫情、新闻 RSS |  |
| BI0401 | 虫害（Insect Pest Infestations） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0402 | 蝗灾（Locust） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0403 | 入侵杂草与物种（Invasive weed/species） | 有持续观测 | 0（0） | GBIF 物种记录（尼泊尔）、新闻 RSS | 尼泊尔近一年外来物种记录 0 条 |
| BI0501 | 植物细菌病（Bacterial Plant Disease） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| BI0502 | 植物真菌病（Fungal Plant Disease） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| BI0503 | 植物病毒与类病毒病（Viral, Phytoplasma and Viroid Plant Disease Outbreaks） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| BI0601 | 抗微生物药物耐药（Antimicrobial Resistance） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0602 | 生物战剂（Biological Agents CBRNE） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| BI0603 | 有害藻华（Harmful Algal Blooms） | 来源正常，90 天无记录 | 0（0） | NASA EONET、新闻 RSS |  |
| BI0604 | 人与野生动物冲突（Human-Wildlife Conflict） | 本地有记录 | 29（29） | BIPAD 灾害事件库、新闻 RSS | 2026-10-11 Animal Incidents at Solududhkunda Municipality-5 |
| BI0605 | 蛇咬伤（Snakebite Envenoming） | 本地有记录 | 102（102） | BIPAD 灾害事件库、新闻 RSS | 2026-10-12 Snake Bite at Gauriganga Municipality-9 |

## 技术（Technological）· 50 种

本地有记录 5 · 外地有记录 3 · 来源正常，90 天无记录 42

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| TL0101 | 恶意软件（Malware） | 外地有记录 | 32（0） | CISA 已利用漏洞、新闻 RSS | 2026-10-13 Ivanti Connect Secure：Ivanti Connect Secure Authentication Bypass by S |
| TL0102 | 数据泄露（Data Breach） | 外地有记录 | 8（0） | Have I Been Pwned 数据泄露、新闻 RSS | 2026-10-12 Sharecare 泄露 318185 个账号 |
| TL0103 | 高级持续性威胁（Advanced Persistent Threat） | 外地有记录 | 32（0） | CISA 已利用漏洞、新闻 RSS | 2026-10-13 Ivanti Connect Secure：Ivanti Connect Secure Authentication Bypass by S |
| TL0104 | 拒绝服务攻击（Denial of Service） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0105 | 供应链攻击（Supply Chain Attack） | 来源正常，90 天无记录 | 0（0） | CISA 已利用漏洞、新闻 RSS |  |
| TL0106 | 网络霸凌（Cyberbullying） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0107 | 社会工程（Social Engineering） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0201 | 建筑倒塌（Building Collapse） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0202 | 高层建筑与外墙（Building, Highrise, Cladding） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0203 | 结构失效（Structural Failure） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0204 | 桥梁垮塌（Bridge Failure） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| TL0205 | 溃坝（Dam Failure） | 本地有记录 | 3（3） | 新闻 RSS | 2026-10-12 Google News（尼泊尔灾害）：Nepal flash floods: 5 missing as surge sweeps away  |
| TL0206 | 供应链中断（Supply Chain Failure） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0207 | 关键基础设施失效（Critical Infrastructure Failure） | 本地有记录 | 23（23） | BIPAD 灾害事件库、BIPAD 警报、新闻 RSS | 2026-10-09 Road closed in Siddhalek-3, Dhading |
| TL0208 | 核电站事故（Nuclear Plant Failure） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0209 | 停电（Power Outage / Blackout） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0210 | 供水中断（Water Supply Failure） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0211 | 应急通信中断（Emergency Telecommunication Failure） | 来源正常，90 天无记录 | 0（0） | IODA 网络连通、新闻 RSS |  |
| TL0212 | 无线电与通信中断（Radio and other Telecommunication Failures） | 来源正常，90 天无记录 | 0（0） | IODA 网络连通、新闻 RSS |  |
| TL0213 | 隧道事故（Tunnel Failure） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0214 | 排水与下水道内涝（Drain and Sewer Flooding） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0215 | 水库泄洪致淹（Reservoir Flooding） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0301 | 泄漏（Leaks and Spills） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| TL0302 | 污染（Pollution） | 本地有记录 | 1（1） | BIPAD 灾害事件库、Sentinel-5P 大气成分、新闻 RSS | 2026-10-09 Nepali Times：Breathing should not be killing us |
| TL0303 | 土壤污染（Soil Pollution） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0304 | 爆炸（Explosion） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、NASA EONET、USGS 地震目录、新闻 RSS |  |
| TL0305 | 火灾（Fire） | 本地有记录 | 99（99） | BIPAD 灾害事件库、NASA EONET、新闻 RSS | 2026-10-12 Fire at Dhankuta Municipality-2 |
| TL0306 | 爆炸物（Explosive Agents） | 本地有记录 | 1（1） | 新闻 RSS | 2026-10-09 Google News（西藏灾害）：Tranche Update on Xizang Gaozheng Civil Explosives C |
| TL0307 | 采矿灾害（Mining Hazards） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、USGS 地震目录、新闻 RSS |  |
| TL0308 | 油气开采事故（Safety Hazards Associated with Oil and Gas Extraction Activities） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0309 | 自然灾害引发的技术事故（Natech）（Natech） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| TL0401 | 航空事故（Air Transportation Accident） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| TL0402 | 内河航运事故（Inland Water Way Accidents） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| TL0403 | 海上事故（Maritime Accident） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0404 | 铁路事故（Rail Accident） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0405 | 道路交通事故（Road Traffic Accident） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、新闻 RSS |  |
| TL0501 | 灾害与冲突废弃物（Disaster & Conflict Waste） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0502 | 固体废物（Solid Waste） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0503 | 废水（Wastewater） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0504 | 危险废物（Hazardous Waste） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0505 | 塑料废物（Plastic Waste） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0506 | 海洋垃圾（Marine Debris） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0507 | 电子废物（Electronic Waste (E-Waste)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0508 | 医疗废物（Health-care Waste） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0509 | 填埋（Landfilling） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0510 | 废物处理塘（Waste Treatment Lagoons） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0511 | 尾矿（Tailings） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| TL0601 | 放射性废物（Radioactive Waste） | 来源正常，90 天无记录 | 0（0） | Safecast 辐射、新闻 RSS |  |
| TL0602 | 放射性物质（Radioactive Agents & Material） | 来源正常，90 天无记录 | 0（0） | BIPAD 灾害事件库、Safecast 辐射、新闻 RSS |  |
| TL0603 | 核材料（Nuclear Agents） | 来源正常，90 天无记录 | 0（0） | Safecast 辐射、新闻 RSS |  |

## 社会（Societal）· 9 种

本地有记录 2 · 来源正常，90 天无记录 7

| 编码 | 灾害 | 状态 | 90 天记录（本地） | 实测能用的来源 | 最近一条 |
|---|---|---|---|---|---|
| SO0101 | 国际武装冲突（International Armed Conflict (IAC)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| SO0102 | 非国际武装冲突（Non-International Armed Conflict (NIAC)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| SO0103 | 内乱（Civil Unrest） | 本地有记录 | 1（1） | 新闻 RSS | 2026-10-13 OnlineKhabar English：Mothers of Gen Z protest detainees stage sit-in o |
| SO0201 | 未爆弹药（Explosive Ordnance） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| SO0202 | 冲突造成的环境破坏（Environmental Degradation from Conflict） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| SO0301 | 暴力（Violence） | 本地有记录 | 2（2） | 新闻 RSS | 2026-10-14 Kathmandu Post：Envoy nominees face abuse, extortion and conflict-of-in |
| SO0302 | 踩踏（Stampede or Crushing (Human)） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| SO0303 | 自杀聚集（Suicide Cluster） | 来源正常，90 天无记录 | 0（0） | 新闻 RSS |  |
| SO0401 | 金融冲击（Financial Shock） | 来源正常，90 天无记录 | 0（0） | 尼泊尔央行汇率、新闻 RSS |  |

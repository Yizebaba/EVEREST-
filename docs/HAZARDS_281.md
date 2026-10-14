# 281 种灾害的覆盖情况

灾害分类取自联合国减灾署和国际科学理事会《灾害信息档案》（UNDRR-ISC Hazard Information Profiles，2025 版）：281 种灾害，分 8 大类。完整列表取自 IFRC Montandon 的文档（和 Montandon 用的是同一套编码）。机器可读版：[`data/taxonomy/hips2025_everest.json`](../data/taxonomy/hips2025_everest.json)。由 `tools/hips_map.py` 生成。

EVEREST 只记录已经发生、被公开来源测到的事，不预测；所以“不在范围”多是社会、网络、慢性污染这类没有公开观测记录、或不是自然事件的灾种。

| 状态 | 数量 | 含义 |
|---|---|---|
| 自动发现 + 证据包 | 22 | 能自动发现事件，并生成多源证据包 |
| 证据包里有记录 | 18 | 不单独成为事件，但证据包里会记录（旁证或背景） |
| 有公开来源，待接 | 53 | 有公开观测来源，还没接 |
| 本地不适用 | 51 | 喜马拉雅/珠峰一带不会发生（海洋、海岸、热带等） |
| 不在范围 | 137 | 不是自然事件，或没有公开、带时间的观测记录 |

## 气象与水文（Meteorological & Hydrological）· 53 种

自动发现 + 证据包 12· 证据包里有记录 3· 有公开来源，待接 11· 本地不适用 19· 不在范围 8

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| MH0101 | 下击暴流（Downburst） | 有公开来源，待接 | 闪电定位（Blitzortung，仅非商业） |
| MH0102 | 闪电（雷暴）（Lightning (electrical storm)） | 自动发现 + 证据包 | BIPAD 雷击警报、新闻线索 |
| MH0103 | 雷暴（Thunderstorm） | 有公开来源，待接 | 闪电定位（Blitzortung） |
| MH0201 | 沙尘暴（Dust Storm or Sandstorm） | 有公开来源，待接 | Sentinel-5P 气溶胶、MODIS |
| MH0202 | 雾（Fog） | 有公开来源，待接 | Himawari 可见光 |
| MH0203 | 霾（Haze） | 有公开来源，待接 | Sentinel-5P、OpenAQ（需密钥） |
| MH0204 | 沙霾（Sand Haze） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0205 | 烟（Smoke） | 有公开来源，待接 | FIRMS 火点、Sentinel-5P |
| MH0301 | 大风（Wind） | 有公开来源，待接 | 地面气象站观测（尼泊尔水文气象局） |
| MH0302 | 德雷乔风暴（Derecho） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0303 | 烈风（Gale） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0304 | 飑（Squall） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0305 | 龙卷（Tornado） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0306 | 低压或气旋（Depression or Cyclone） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0307 | 温带气旋（Extra-tropical Cyclone） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0308 | 副热带气旋（Sub-tropical Cyclone） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0309 | 热带气旋（Tropical Cyclone） | 自动发现 + 证据包 | GDACS 热带气旋（影响喜马拉雅南麓时） |
| MH0401 | 干旱（Drought） | 自动发现 + 证据包 | GDACS 干旱（慢性，只记录通报） |
| MH0402 | 降雨（Rain） | 证据包里有记录 | 卫星和影像前后对比；BIPAD 雨量站（待接） |
| MH0403 | 暴风雪（Blizzard） | 自动发现 + 证据包 | 新闻线索（blizzard） |
| MH0404 | 冰雹（Hail） | 自动发现 + 证据包 | 新闻线索（hailstorm） |
| MH0405 | 降雪（Snow） | 有公开来源，待接 | MODIS / VIIRS 积雪 |
| MH0406 | 雪暴（Snow Storm） | 自动发现 + 证据包 | 新闻线索（snowstorm） |
| MH0501 | 热浪（Heatwave） | 有公开来源，待接 | 地面气象站实测 |
| MH0502 | 寒潮（Cold Wave） | 自动发现 + 证据包 | BIPAD 寒潮警报、新闻线索 |
| MH0503 | 白灾（Dzud）（Dzud） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0504 | 冰冻（Freeze） | 有公开来源，待接 | 地面气象站实测 |
| MH0505 | 白霜（Frost (Hoar Frost)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0506 | 冻雨（Freezing Rain (Supercooled Rain)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0507 | 雨凇（Glaze） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0508 | 地面霜冻（Ground Frost） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0509 | 结冰（Icing (Including Ice)） | 有公开来源，待接 | 地面气象站实测 |
| MH0510 | 解冻（Thaw） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0600 | 洪水（Flooding） | 自动发现 + 证据包 | BIPAD 洪水警报、GDACS 洪水、水位越线、新闻线索 |
| MH0601 | 沿海洪水（Coastal Flooding） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0602 | 河口洪水（Estuarine (Coastal) Flooding） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0603 | 山洪（Flash Flooding） | 自动发现 + 证据包 | BIPAD 洪水警报、新闻线索（flash flood） |
| MH0604 | 河流洪水（Fluvial (Riverine) Flooding） | 自动发现 + 证据包 | BIPAD 洪水警报、水位越线 |
| MH0605 | 地下水洪水（Groundwater Flooding） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0606 | 地表积水（Surface water Flooding） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| MH0607 | 冰湖溃决洪水（Glacial Lake Outburst Flooding） | 自动发现 + 证据包 | 新闻线索（glacial lake / GLOF）；冰湖出口水位站（Imja、Tsho Rolpa） |
| MH0608 | 冰塞洪水（含碎屑）（Ice-Jam Flooding Including Debris） | 证据包里有记录 | 水位站、卫星影像 |
| MH0609 | 内涝（Ponding (Drainage) Flooding） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0610 | 融雪洪水（Snowmelt Flooding） | 证据包里有记录 | 水位站 |
| MH0701 | 畸形浪（Rogue Wave） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0702 | 假潮（Seiche） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0703 | 风暴潮（Storm Surge） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0704 | 风暴高潮（Storm Tides） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0705 | 海啸（Tsunami） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0706 | 海冰（Sea ice） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0707 | 流冰（Ice flow） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0708 | 海洋热浪（Marine Heatwave） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| MH0801 | 雪崩（Avalanche） | 自动发现 + 证据包 | 新闻线索（avalanche）；BIPAD 雪崩警报 |

## 地外（Extraterrestrial）· 10 种

证据包里有记录 2· 有公开来源，待接 6· 不在范围 2

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| ET0101 | 地磁扰动（Geomagnetic Disturbance） | 证据包里有记录 | 地磁 Kp 指数（GFZ） |
| ET0102 | 电离层扰动（Ionospheric Disturbance） | 证据包里有记录 | 地磁 Kp（电离层扰动的旁证） |
| ET0103 | 太阳耀斑（Solar Flare） | 有公开来源，待接 | NOAA SWPC GOES X 射线（只保留 7 天） |
| ET0104 | 太阳高能粒子（Solar Energetic Particles） | 有公开来源，待接 | NOAA SWPC 质子通量 |
| ET0201 | 空中爆炸（陨石）（Airburst） | 有公开来源，待接 | NASA CNEOS 火球数据库 |
| ET0202 | 紫外辐射（UV Radiation） | 有公开来源，待接 | Sentinel-5P 紫外指数 |
| ET0203 | 陨石撞击（Meteorite Impact） | 有公开来源，待接 | NASA CNEOS 火球数据库 |
| ET0204 | 航天事故（Space Hazard / Accident） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| ET0205 | 近地天体（Near-Earth Object） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| ET0206 | 空间碎片（Space Debris） | 有公开来源，待接 | Space-Track（需注册） |

## 地质（Geological）· 25 种

自动发现 + 证据包 5· 证据包里有记录 2· 有公开来源，待接 5· 本地不适用 11· 不在范围 2

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| GH0101 | 地震（Earthquake） | 自动发现 + 证据包 | USGS M5 以上、GDACS 地震、新闻线索 |
| GH0201 | 熔岩流（Lava Flows (Lava Domes)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0202 | 火山灰与碎屑（Ash/Tephra Fall (including Volcanic Ballistic projectiles)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0203 | 火山碎屑流（Pyroclastic Density Current） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0204 | 火山泥流（Lahars） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0205 | 火山气体与气溶胶（Volcanic Gases and Aerosols） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0300 | 重力块体运动（滑坡）（Gravitational Mass Movement (Landslide)） | 自动发现 + 证据包 | USGS 崩塌/滑坡、BIPAD 滑坡警报、新闻线索 |
| GH0301 | 崩落（落石、冰崩）（Falls） | 自动发现 + 证据包 | USGS 崩塌、新闻线索（rockfall / ice avalanche） |
| GH0302 | 侧向扩离（Spreads） | 有公开来源，待接 | Sentinel-1/2 影像 |
| GH0303 | 流动（泥石流）（Flows） | 自动发现 + 证据包 | 新闻线索（debris flow） |
| GH0304 | 滑动（Slides） | 自动发现 + 证据包 | BIPAD 滑坡警报、新闻线索 |
| GH0305 | 倾倒（Topples） | 有公开来源，待接 | Sentinel-1/2 影像 |
| GH0306 | 海底滑坡（Submarine Landslide） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0307 | 砂土液化（Liquefaction） | 有公开来源，待接 | 地震后影像 |
| GH0308 | 落水洞（Sinkhole） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0309 | 沉降与抬升（Subsidence and Uplift） | 证据包里有记录 | Sentinel-1 干涉（外部计算）、GNSS |
| GH0310 | 胀缩沉降（Shrink-Swell Subsidence） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0311 | 地表破裂与裂缝（Surface Rupture & Fissure） | 证据包里有记录 | Sentinel-1 干涉（外部计算） |
| GH0401 | 压缩性土（Compressive Soils） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0402 | 土壤退化（Soil Degradation） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| GH0403 | 土壤侵蚀（Soil Erosion） | 有公开来源，待接 | Sentinel-2 影像（慢性） |
| GH0404 | 河岸侵蚀与淤积（River Erosion & Accretion） | 有公开来源，待接 | Sentinel-2 影像（慢性） |
| GH0405 | 海岸侵蚀与淤积（Coastal Erosion & Accretion） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0406 | 沙地侵入（Sand Encroachment） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| GH0407 | 地下气体（甲烷、氡等）（Ground Gases (CH4, Rn, etc.)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |

## 环境（Environmental）· 24 种

自动发现 + 证据包 1· 证据包里有记录 3· 有公开来源，待接 6· 本地不适用 7· 不在范围 7

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| EN0101 | 室内空气污染（Household Air Pollution） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| EN0102 | 点源空气污染（Air Pollution (Point Source)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| EN0103 | 室外空气污染（Ambient (Outdoor) Air Pollution） | 证据包里有记录 | BIPAD 空气污染警报（加德满都谷地，背景） |
| EN0104 | 黑碳（Black Carbon） | 证据包里有记录 | Sentinel-5P 气溶胶（背景） |
| EN0105 | 酸雨（Acid Rain） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| EN0106 | 面源污染（Runoff / Nonpoint Source Pollution） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| EN0201 | 毁林（Deforestation） | 有公开来源，待接 | Global Forest Watch 林地损失（周报） |
| EN0202 | 森林衰退（Forest Declines and Diebacks） | 有公开来源，待接 | Global Forest Watch |
| EN0203 | 森林扰动（Forest Disturbances） | 有公开来源，待接 | Global Forest Watch |
| EN0204 | 森林入侵物种（Forest Invasive Species） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| EN0205 | 野火（森林火灾）（Wildfires） | 自动发现 + 证据包 | BIPAD 森林火灾警报、GDACS 野火、新闻线索 |
| EN0206 | 荒漠化（Desertification） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| EN0207 | 红树林丧失（Loss of Mangroves） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| EN0301 | 土地退化（Land Degradation） | 有公开来源，待接 | Sentinel-2（慢性） |
| EN0302 | 海水入侵（Seawater intrusion） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| EN0303 | 盐渍化（Salinity & Sodicity） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| EN0304 | 湿地退化（Wetland Loss/Degradation） | 有公开来源，待接 | Sentinel-2（慢性） |
| EN0305 | 冻土消融（Permafrost Loss） | 证据包里有记录 | 坡面雷达监测（背景） |
| EN0401 | 海洋酸化（Ocean Acidification） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| EN0402 | 海平面上升（Sea Level Rise） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| EN0403 | 富营养化（Eutrophication） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| EN0404 | 珊瑚白化（Coral Bleaching） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| EN0405 | 采砂（Sand Mining） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| EN0501 | 生物多样性丧失（Biodiversity Loss） | 有公开来源，待接 | GBIF 物种记录（慢性） |

## 化学（Chemical）· 27 种

不在范围 27

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| CH0100 | 重金属与微量元素（Heavy Metals & Trace Elements） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0101 | 砷（Arsenic） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0102 | 镉（Cadmium） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0103 | 铅（Lead） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0104 | 汞（Mercury） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0105 | 氟碘过量或不足（Fluoride & Iodine/Iodide Excess or Inadequate Intake） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0201 | 黄曲霉毒素（Aflatoxins） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0202 | 石棉（Asbestos） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0203 | 苯与烃类（Benzene & Hydrocarbons） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0300 | 有毒气体（Toxic Gases） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0301 | 氨（Ammonia） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0302 | 一氧化碳（Carbon Monoxide） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0303 | 氯气（Chlorine） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0400 | 窒息性气体（Asphyxiant Gases） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0500 | 持久性有机污染物（Persistent Organic Pollutants） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0501 | 农药（Pesticides） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0502 | 二噁英（Dioxins & Dioxin-like Substance） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0503 | 全氟烷基物质（Polyfluoroalkyl Substances） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0504 | 微塑料（Microplastics） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0601 | 食品与饲料污染物（Levels of Contaminants in Food & Feed） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0602 | 劣质与假冒药品（Substandard & Falsified Medical Products） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0603 | 甲醇（Methanol） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0604 | 阿片类与成瘾物质（Opioids & Other Addictive Substances） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0605 | 海洋毒素（Marine Toxins） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0901 | 腐蚀性物质（Corrosive Substances） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0902 | 硝酸铵（Ammonium Nitrate） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| CH0903 | 化学战剂（Chemical Warfare Agents） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |

## 生物（Biological）· 83 种

自动发现 + 证据包 3· 有公开来源，待接 16· 本地不适用 11· 不在范围 53

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| BI0101 | 空气传播疾病（Airborne Diseases (human and Animal)） | 有公开来源，待接 | WHO 疫情通报（Disease Outbreak News） |
| BI0102 | 血液传播病毒（Blood Borne Viruses (Human and Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0103 | 腹泻病（Diarrhoeal Diseases (Human)） | 有公开来源，待接 | WHO 疫情通报 |
| BI0104 | 食源性疾病（Foodborne Diseases (Human impact)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0105 | 被忽视的热带病（Neglected Tropical Diseases (Human)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0106 | 性传播疾病（Sexually Transmitted Diseases (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0107 | 疫苗可预防疾病（Vaccine-Preventable Diseases (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0108 | 媒介传播疾病（Vector Borne Diseases (VBD) (Human and Animal)） | 有公开来源，待接 | WHO 疫情通报 |
| BI0109 | 病毒性出血热（Viral Haemorrhagic Fevers (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0110 | 水源性疾病（Waterborne Diseases (Human)） | 自动发现 + 证据包 | 新闻线索（outbreak） |
| BI0111 | 隐孢子虫病（Cryptosporidium (Human and Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0112 | 囊尾蚴病（Cysticercosis (Human and Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0113 | 人畜共患病（Zoonotic Diseases） | 有公开来源，待接 | WHO 疫情通报、WOAH 动物疫情（WAHIS） |
| BI0201 | 炭疽（Anthrax） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0202 | 布鲁氏菌病（Brucellosis (Human and Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0203 | 基孔肯雅热（Chikungunya） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0204 | 霍乱（Cholera (Human)） | 自动发现 + 证据包 | 新闻线索（cholera） |
| BI0205 | 新冠（COVID-19 (SARS-CoV-2) (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0206 | 克里米亚-刚果出血热（Crimean-Congo Haemorrhagic Fever (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0207 | 登革热（Dengue (Human)） | 自动发现 + 证据包 | 新闻线索（dengue） |
| BI0208 | 白喉（Diphtheria (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0209 | 埃博拉（Ebola (Human)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0210 | 产志贺毒素大肠杆菌（Escherichia Coli (STEC) (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0211 | 甲肝（Hepatitis A (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0212 | 乙肝（Hepatitis B (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0213 | 丙肝（Hepatitis C (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0214 | 艾滋病（HIV and AIDS (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0215 | 拉沙热（Lassa Fever (Human)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0216 | 麻风（Leprosy (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0217 | 钩端螺旋体病（Leptospirosis (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0218 | 李斯特菌病（Listeriosis (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0219 | 疟疾（Malaria (Human)） | 有公开来源，待接 | WHO 疫情通报 |
| BI0220 | 马尔堡病毒（Marburg Virus） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0221 | 麻疹（Measles (Human)） | 有公开来源，待接 | WHO 疫情通报 |
| BI0222 | 脑膜炎球菌脑膜炎（Meningococcal Meningitis (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0223 | 中东呼吸综合征（Middle East Respiratory Syndrome (MERS) (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0224 | 猴痘（Mpox (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0225 | 副伤寒（Paratyphoid Fever (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0226 | 伤寒（Typhoid Fever (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0227 | 百日咳（Pertussis (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0228 | 鼠疫（Plague (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0229 | 脊髓灰质炎（Polio (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0230 | 朊病毒病（Prion Diseases） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0231 | Q 热（Q Fever） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0232 | 狂犬病（Rabies (Animal and Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0233 | 轮状病毒（Rotavirus (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0234 | 志贺菌病（Shigellosis (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0235 | 天花（Smallpox (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0236 | 非典（SARS）（Severe Acute Respiratory Syndrome (SARS) (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0237 | 结核（Tuberculosis (Human and Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0238 | 锥虫病（Trypanosomiasis & Tripanomosis (Human and Animal)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0239 | 水痘与带状疱疹（Varicella and Herpes Zoster (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0240 | 西尼罗热（West Nile Fever (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0241 | 黄热病（Yellow Fever (Human)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0242 | 寨卡（Zika Virus (Human)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0243 | 季节性流感（Seasonal Influenza (Human)） | 有公开来源，待接 | WHO FluNet |
| BI0244 | 大流行性流感（Pandemic Influenza (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0245 | 禽流感（Avian Influenza (Human and Animal)） | 有公开来源，待接 | WHO 疫情通报、WOAH WAHIS |
| BI0301 | 动物疫病（非人畜共患）（Animal Diseases (Not Zoonoses)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0302 | 非洲猪瘟（African Swine Fever (Animal)） | 有公开来源，待接 | WOAH WAHIS |
| BI0303 | 古典猪瘟（Classical Swine Fever (Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0304 | 牛传染性胸膜肺炎（Contagious Bovine Pleuropneumonia (CBPP) (Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0305 | 山羊传染性胸膜肺炎（Contagious Caprine Pleuropneumonia (CCPP) (Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0306 | 口蹄疫（Foot and Mouth Disease Virus (Animal)） | 有公开来源，待接 | WOAH WAHIS |
| BI0307 | 牛结节性皮肤病（Lumpy Skin Disease (Animal)） | 有公开来源，待接 | WOAH WAHIS |
| BI0308 | 新城疫（Newcastle Disease (Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0309 | 新大陆螺旋蝇（New World Screwworm (NWS) (Animal)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0310 | 小反刍兽疫（Peste des Petits Ruminants (Animal)） | 有公开来源，待接 | WOAH WAHIS |
| BI0311 | 裂谷热（Rift Valley Fever (Animal)） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0312 | 牛瘟（Rinderpest (Animal)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0313 | 牡蛎病害（Oyster Disease Aquaculture） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0314 | 对虾急性肝胰腺坏死（Shrimp Diseases (Bacterial) - Acute Hepatic Pancreatic Necrosis） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| BI0401 | 虫害（Insect Pest Infestations） | 有公开来源，待接 | FAO 虫害通报 |
| BI0402 | 蝗灾（Locust） | 有公开来源，待接 | FAO 沙漠蝗通报 |
| BI0403 | 入侵杂草与物种（Invasive weed/species） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0501 | 植物细菌病（Bacterial Plant Disease） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0502 | 植物真菌病（Fungal Plant Disease） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0503 | 植物病毒与类病毒病（Viral, Phytoplasma and Viroid Plant Disease Outbreaks） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0601 | 抗微生物药物耐药（Antimicrobial Resistance） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0602 | 生物战剂（Biological Agents CBRNE） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0603 | 有害藻华（Harmful Algal Blooms） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| BI0604 | 人与野生动物冲突（Human-Wildlife Conflict） | 有公开来源，待接 | 新闻线索 |
| BI0605 | 蛇咬伤（Snakebite Envenoming） | 有公开来源，待接 | 新闻线索 |

## 技术（Technological）· 50 种

自动发现 + 证据包 1· 证据包里有记录 8· 有公开来源，待接 9· 本地不适用 3· 不在范围 29

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| TL0101 | 恶意软件（Malware） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0102 | 数据泄露（Data Breach） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0103 | 高级持续性威胁（Advanced Persistent Threat） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0104 | 拒绝服务攻击（Denial of Service） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0105 | 供应链攻击（Supply Chain Attack） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0106 | 网络霸凌（Cyberbullying） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0107 | 社会工程（Social Engineering） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0201 | 建筑倒塌（Building Collapse） | 有公开来源，待接 | 新闻、人工证据 |
| TL0202 | 高层建筑与外墙（Building, Highrise, Cladding） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0203 | 结构失效（Structural Failure） | 有公开来源，待接 | 新闻、人工证据 |
| TL0204 | 桥梁垮塌（Bridge Failure） | 证据包里有记录 | 新闻、维基百科、人工证据 |
| TL0205 | 溃坝（Dam Failure） | 自动发现 + 证据包 | 新闻线索（dam breach / dam collapse） |
| TL0206 | 供应链中断（Supply Chain Failure） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0207 | 关键基础设施失效（Critical Infrastructure Failure） | 证据包里有记录 | IODA、夜间灯光、水位站停报 |
| TL0208 | 核电站事故（Nuclear Plant Failure） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0209 | 停电（Power Outage / Blackout） | 证据包里有记录 | NASA 夜间灯光（需 Earthdata） |
| TL0210 | 供水中断（Water Supply Failure） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0211 | 应急通信中断（Emergency Telecommunication Failure） | 证据包里有记录 | IODA、Cloudflare Radar（需令牌） |
| TL0212 | 无线电与通信中断（Radio and other Telecommunication Failures） | 证据包里有记录 | IODA、Cloudflare Radar（需令牌） |
| TL0213 | 隧道事故（Tunnel Failure） | 有公开来源，待接 | 新闻、人工证据 |
| TL0214 | 排水与下水道内涝（Drain and Sewer Flooding） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0215 | 水库泄洪致淹（Reservoir Flooding） | 有公开来源，待接 | 水位站、新闻 |
| TL0301 | 泄漏（Leaks and Spills） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0302 | 污染（Pollution） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0303 | 土壤污染（Soil Pollution） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0304 | 爆炸（Explosion） | 有公开来源，待接 | 新闻、地震台（爆炸信号） |
| TL0305 | 火灾（Fire） | 有公开来源，待接 | FIRMS 火点、新闻 |
| TL0306 | 爆炸物（Explosive Agents） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0307 | 采矿灾害（Mining Hazards） | 有公开来源，待接 | 新闻 |
| TL0308 | 油气开采事故（Safety Hazards Associated with Oil and Gas Extraction Activities） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| TL0309 | 自然灾害引发的技术事故（Natech）（Natech） | 证据包里有记录 | 同一事件的多源记录（例如洪水冲毁水电站） |
| TL0401 | 航空事故（Air Transportation Accident） | 证据包里有记录 | ADS-B 航迹（背景） |
| TL0402 | 内河航运事故（Inland Water Way Accidents） | 有公开来源，待接 | 新闻 |
| TL0403 | 海上事故（Maritime Accident） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| TL0404 | 铁路事故（Rail Accident） | 有公开来源，待接 | 新闻 |
| TL0405 | 道路交通事故（Road Traffic Accident） | 证据包里有记录 | BIPAD 道路中断记录（背景） |
| TL0501 | 灾害与冲突废弃物（Disaster & Conflict Waste） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0502 | 固体废物（Solid Waste） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0503 | 废水（Wastewater） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0504 | 危险废物（Hazardous Waste） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0505 | 塑料废物（Plastic Waste） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0506 | 海洋垃圾（Marine Debris） | 本地不适用 | 喜马拉雅一带不发生或不适用 |
| TL0507 | 电子废物（Electronic Waste (E-Waste)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0508 | 医疗废物（Health-care Waste） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0509 | 填埋（Landfilling） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0510 | 废物处理塘（Waste Treatment Lagoons） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0511 | 尾矿（Tailings） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0601 | 放射性废物（Radioactive Waste） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0602 | 放射性物质（Radioactive Agents & Material） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| TL0603 | 核材料（Nuclear Agents） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |

## 社会（Societal）· 9 种

不在范围 9

| 编码 | 灾害 | 状态 | 来源 / 说明 |
|---|---|---|---|
| SO0101 | 国际武装冲突（International Armed Conflict (IAC)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0102 | 非国际武装冲突（Non-International Armed Conflict (NIAC)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0103 | 内乱（Civil Unrest） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0201 | 未爆弹药（Explosive Ordnance） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0202 | 冲突造成的环境破坏（Environmental Degradation from Conflict） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0301 | 暴力（Violence） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0302 | 踩踏（Stampede or Crushing (Human)） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0303 | 自杀聚集（Suicide Cluster） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |
| SO0401 | 金融冲击（Financial Shock） | 不在范围 | 不是自然事件，或没有公开、带时间的观测记录 |

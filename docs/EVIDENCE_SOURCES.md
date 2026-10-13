# 灾后能留下哪些公开记录：按灾种整理

整理时间：2026-10-14。目的：现在的证据包只用到地震台、水位站、网络连通、卫星目录几类，太少。先看世界上损失最大的自然灾害有哪些，再按灾种列出灾后会在哪些**公开来源**里留下带时间戳、事后可查的记录，标出哪些已经接入、哪些可以接。

**边界不变**：只收观测记录，不收预报和预测产品；不做天气预报。气象类灾害（台风、强对流、高温）只记录“已经发生、被测到了什么”，例如雨量站读数、闪电定位、卫星看到的火点和淹水范围。

标记：**✓ 已接入** · **○ 可直接接（无需账号）** · **◇ 需要免费注册或申请密钥** · **△ 有限制（只能部分用、或许可受限）**

---

## 一、世界上损失最大的自然灾害

### 2025 年

| 口径 | 事件数 | 死亡 | 受影响人数 | 经济损失 |
|---|---|---|---|---|
| EM-DAT（CRED） | 358 | 16,607 | 1.102 亿 | 1,697 亿美元 |
| 2005–2024 年平均（EM-DAT） | 377 | 57,429 | 1.69 亿 | 2,150 亿美元 |
| Munich Re | — | 约 17,200 | — | 总损失 2,440 亿美元，保险损失 1,080 亿美元 |

Munich Re：天气相关灾害占全部损失的 92%、保险损失的 97%；洪水、强对流风暴、山火三类合计约 1,660 亿美元。

**2025 年死亡最多的 10 起**（EM-DAT）：缅甸地震 3,820；阿富汗地震 2,200；印尼气旋 Senyar 1,109；尼日利亚 Mokwa 洪水 1,100；巴基斯坦洪水 1,037；斯里兰卡气旋 Ditwah 823；苏丹滑坡 400；菲律宾台风 Kalmaegi 372；泰国洪水（Senyar）276；尼日利亚洪水 238。

**2025 年损失最大的 10 起**（EM-DAT，美元）：美国洛杉矶山火 530 亿；泰国洪水 156 亿（初值，可能下调）；缅甸地震 110 亿；牙买加飓风 Melissa 100 亿；美国 3 月强对流风暴 94 亿；中国洪水 58 亿；美国 5 月风暴 52 亿；巴西干旱 48 亿；美国 4 月风暴 46 亿；斯里兰卡气旋 Ditwah 41 亿。

### 每年各类灾害的事件数（EM-DAT，2005–2024 年平均）

洪水 169 · 风暴 108 · 地震 25 · 极端温度 23 · 湿性块体运动（滑坡、泥石流）18 · 干旱 16 · 山火 12 · 火山 5 · 干性块体运动（崩塌、落石）1

**结论**：按次数看是洪水和风暴；按死亡看是地震、热带气旋、洪水（以及高温，但高温死亡统计极不完整）；按损失看是山火、热带气旋、强对流风暴、洪水、地震。喜马拉雅特有的冰湖溃决、冰崩、雪崩在全球统计里归入洪水或块体运动。

---

## 二、各灾种会留下哪些公开记录

### 地震

| 记录 | 来源 | 状态 |
|---|---|---|
| 地震目录（时间、位置、震级） | USGS、EMSC、尼泊尔国家地震中心 | ✓ |
| 专业台站波形 | GEOFON IO.EVN、EarthScope NK.KKN | ✓ |
| 民间地震仪波形（台站更密） | Raspberry Shake AM 台网，FDSN 接口 `data.raspberryshake.org/fdsnws/` | ○ 喜马拉雅范围内有几个台、数据开放到什么程度，待在 GitHub 运行器上实测 |
| 震动烈度图、台站实测峰值加速度 | USGS ShakeMap（事件详情里的产品） | ○ |
| 公众“有感”报告 | USGS Did You Feel It?、EMSC 有感报告 | ○ |
| 地表形变 | 哥白尼 Sentinel-1 干涉；COMET LiCSAR 自动干涉图 | △ 重计算放在外部，只取结果 |
| GNSS 站位移 | 内华达大学 Nevada Geodetic Lab 每日解算 | ○ |
| 机构的伤亡与损失估计 | USGS PAGER | ○ 只作为“机构估计”记录，标明是模型估计，不是观测 |

### 洪水（含冰湖溃决、暴雨山洪）

| 记录 | 来源 | 状态 |
|---|---|---|
| 洪水警报、水位站读数和停报 | BIPAD（尼泊尔） | ✓ |
| 自动洪水范围 | 哥白尼 GFM | ✓ |
| 应急制图 | 哥白尼 EMS、国际宪章（Charter）、UNOSAT | ✓ EMS；○ Charter / UNOSAT |
| 实测降水（卫星） | NASA IMERG 半小时降水 | ◇ 需要 Earthdata 账号；是观测，不是预报 |
| 地面雨量站 | 尼泊尔水文气象局（经 BIPAD） | ○ |
| 历史洪水范围 | Global Flood Database（GFD）、达特茅斯洪水观测站（DFO） | ○ |
| 灾前灾后高分影像 | Vantor（原 Maxar）开放数据计划：重大灾害后公开灾前灾后影像，CC BY 4.0（例如 2025 年 12 月气旋 Ditwah） | △ 只在启动的灾害提供 |

### 热带气旋（台风、飓风）

| 记录 | 来源 | 状态 |
|---|---|---|
| 实际路径和强度（事后最佳路径） | IBTrACS | ○ 只用最佳路径，不用预报路径 |
| 风暴潮、海平面 | IOC 海平面监测（SLSMF，全球潮位站实时数据） | ○ |
| 海上浮标 | NOAA NDBC | ○ |
| 闪电定位 | Blitzortung | △ 只限非商业用途 |
| 断电、断网、淹水 | 见第三节通用记录 | |

### 强对流（冰雹、龙卷、雷暴大风）

| 记录 | 来源 | 状态 |
|---|---|---|
| 灾情报告 | 美国 NOAA SPC 风暴报告、欧洲强风暴数据库 ESWD | ○ SPC；△ ESWD 需申请 |
| 雷达回波存档 | NOAA NEXRAD（AWS 公开存档） | ○ 只覆盖美国 |
| 闪电 | Blitzortung | △ |

### 山火

| 记录 | 来源 | 状态 |
|---|---|---|
| 卫星火点（几小时内） | NASA FIRMS（MODIS、VIIRS） | ◇ 需要免费 MAP_KEY |
| 烧毁面积 | 欧洲 EFFIS、全球 GWIS；Sentinel-2 火前火后对比 | ○ |
| 烟和空气质量 | OpenAQ 地面站；Sentinel-5P 气溶胶 | ○ |

### 滑坡、泥石流、冰崩、雪崩

| 记录 | 来源 | 状态 |
|---|---|---|
| 地震台测到的大型崩塌 | USGS（类型 landslide）、地震台波形 | ✓ |
| 滑坡目录 | NASA 全球滑坡目录（COOLR） | ○ 更新较慢 |
| 灾前灾后影像 | Sentinel-1/2；Vantor 开放数据 | ✓ Sentinel；△ Vantor |
| 雪崩通报 | 各国雪崩中心（尼泊尔没有公开的） | △ |

### 火山

| 记录 | 来源 | 状态 |
|---|---|---|
| 每周活动报告 | 史密森尼全球火山计划（GVP） | ○ |
| 火山灰通告 | 9 个火山灰咨询中心（VAAC） | ○ |
| 热异常 | MIROVA；FIRMS 火点 | ○；◇ |
| 二氧化硫 | Sentinel-5P TROPOMI（NASA 二氧化硫产品） | ○ |

### 海啸

| 记录 | 来源 | 状态 |
|---|---|---|
| 深海压力计 | NOAA DART 浮标 | ○ |
| 潮位站 | IOC 海平面监测 | ○ |
| 海啸通告 | 太平洋海啸预警中心（PTWC）等发布的通告 | ○ 只记录“何时发了什么通告” |

### 干旱、极端高温

慢性灾害，没有明确的“发生时刻”。可记录：GRACE-FO 地下水变化、植被指数、地面气象站实测最高温。归入“背景记录”，不做事件证据包。

---

## 三、任何灾种都会留下的“社会痕迹”

这一类对证据链价值最高：不管是什么灾，灾区都会断电、断网、停航，新闻和救援机构会在某个时刻开始报道。时间点公开、可存档，而且多数不需要专业解读。

| 记录 | 来源 | 状态 |
|---|---|---|
| 断网 | IODA | ✓ |
| 断网（第二来源，可交叉核对） | Cloudflare Radar 异常和中断记录（API） | ◇ 需要 Cloudflare API 令牌（已有 Cloudflare 账号） |
| 断电（夜间灯光） | NASA Black Marble 每日夜光（VNP46A1/A2） | ◇ 需要 Earthdata 账号 |
| 航空 | ADS-B | ✓ |
| 新闻报道开始的时间 | GDELT（全球新闻，每 15 分钟更新） | ○ |
| 人道报告 | ReliefWeb API | ◇ 2025 年 11 月起要先申请 appname |
| 人道数据集 | OCHA HDX | ○ |
| 国际灾害编号与记录 | GLIDE 编号；IFRC GO / Montandon（汇总 GDACS、EM-DAT、IBTrACS、IDMC、Charter、USGS 等） | ✓ GDACS；◇ Montandon 需要令牌 |
| 流离失所 | IDMC | ○ |
| 公开网页存档 | 互联网档案馆 Wayback Machine | ✓（人工证据里的链接） |
| 现场照片、视频、目击 | 总览页“人工证据” | ✓ |
| 公开知识库的编辑历史 | 维基百科条目创建和修改时间 | ○ |

---

## 四、建议先接的 10 个

按“对所有灾种都有用、接入成本低”的顺序：

1. **GDELT**：新闻什么时候开始报道这个地点。无需账号。
2. **USGS ShakeMap / Did You Feel It? / PAGER**：每次地震自动产生，补齐“震感和影响”的记录。无需账号。
3. **Raspberry Shake**：民间地震仪，可能比专业台站离事件更近。先实测喜马拉雅范围内的台站和数据开放程度。
4. **Cloudflare Radar**：和 IODA 互相核对断网。需要 Cloudflare API 令牌，放在机密里。
5. **NASA Black Marble**：灾后断电。需要 Earthdata 账号。
6. **NASA FIRMS**：山火和火山热异常。需要免费 MAP_KEY。
7. **IOC 海平面 + NOAA DART**：海啸和风暴潮。无需账号。
8. **ReliefWeb**：人道报告时间线。需要申请 appname。
9. **Smithsonian GVP + VAAC + TROPOMI 二氧化硫**：火山一组。无需账号。
10. **Vantor 开放数据**：重大灾害的灾前灾后高分影像，CC BY 4.0。只在启动时可用。

需要账号或密钥的（Earthdata、FIRMS MAP_KEY、Cloudflare API 令牌、ReliefWeb appname、IFRC GO 令牌）由你注册，密钥放进 GitHub 或 Cloudflare 的机密，不发在聊天里。

---

## 来源

- [Munich Re 2025 自然灾害数据（Reinsurance News 报道）](https://www.reinsurancene.ws/global-insured-nat-cat-losses-fall-yoy-but-again-exceed-100bn-in-2025-munich-re/)
- [EM-DAT 2025 年报告（PDF）](https://files.emdat.be/reports/2025_EMDAT_report.pdf)、[PreventionWeb 摘要](https://www.preventionweb.net/publication/documents-and-publications/2025-disasters-numbers-earth-wind-and-fire)
- [Vantor 开放数据：气旋 Ditwah](https://vantor.com/blog/open-data-activation-cyclone-ditwah-and-flooding-across-southeast-asia/)、[AWS 开放数据登记](https://registry.opendata.aws/vantor-open-data/)
- [Raspberry Shake 数据中心（FDSN）](https://www.fdsn.org/datacenters/detail/RASPISHAKE/)
- [NASA Black Marble 断电检测](https://disasters.nasa.gov/our-impact/news/new-black-marble-product-allows-quicker-detection-power-outages-wake-disasters)
- [Cloudflare Radar 中断记录](https://developers.cloudflare.com/radar/investigate/outages)
- [ReliefWeb API 变更](https://reliefweb.int/blogpost/upcoming-changes-reliefweb-api-what-you-need-know)
- [IFRC Montandon 数据来源](https://ifrcgo.org/monty-stac-extension/model/sources/USGS/)
- [IOC 海平面监测](https://www.vliz.be/en/sea-level-station-monitoring-facility-global-hub-real-time-sea-level-data)
- [NASA FIRMS](https://learn.microsoft.com/en-us/connectors/nasafirms)
- [USGS ShakeMap 产品](https://ghsc.code-pages.usgs.gov/esi/shakemap/manual4_0/ug_products.html)

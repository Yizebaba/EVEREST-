# 281 种灾害：各灾种的专业顶刊顶会和可引用数据

自动生成于 2026-10-14T05:40:53Z，已完成 **31/281** 种（OpenAlex 按天计额度，每天自动续跑，补齐为止）。生成脚本 `tools/venue_rank.py` + `tools/venues_report.py`，原始数据 `hazards/venues.json`（events 分支）。

## 方法

1. 每种灾害一个英文检索词（多数取自 `tools/hazard_keywords.py` 的匹配词，部分手工改成学术常用说法，见 `venue_rank.py` 的 `QUERY`）。
2. 在 OpenAlex 检索 2020 年以来的论文和综述，按发表的期刊/会议分组计数，取该主题论文 ≥ 5 篇的期刊或会议（排除 Zenodo 等存储库）。
3. 去掉综合性大刊（PLoS ONE、Scientific Reports、Nature Communications、Nature、Science、PNAS 等，单独列出），按期刊整体 h 指数排前三 → **专业顶刊**。
4. 数据论文：同一检索词在 ESSD、Scientific Data、Geoscience Data Journal、Data in Brief 四本数据期刊里检索相关度最高的三篇 → **可作数据源或引用的数据集**。
5. 方法论文：同一检索词 2020 年以来被引最多的三篇。

**局限**：h 指数衡量期刊整体影响力，不是该灾种的专业排名；检索词有歧义时会混进无关期刊（例如 lightning 混进分子科学期刊）。这份表是找文献和数据的起点，用到具体期刊或数据前请人工确认。会议（如 AGU、EGU、ISCRAM）在 OpenAlex 里收录不全，排名以期刊为主。

## 总览：各大类出现最多的专业期刊

| 大类 | 已完成 | 出现最多的专业期刊（次数） |
|---|---|---|
| 气象与水文 | 31/53 | Journal of Geophysical Research Atmospheres（16）；Geophysical Research Letters（15）；The Science of The Total Environment（7）；International Journal of Molecular Sciences（4）；Journal of Climate（4） |
| 地外 | 0/10 | — |
| 地质 | 0/25 | — |
| 环境 | 0/24 | — |
| 化学 | 0/27 | — |
| 生物 | 0/83 | — |
| 技术 | 0/50 | — |
| 社会 | 0/9 | — |

## 气象与水文（Meteorological & Hydrological）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| MH0101 | 下击暴流 | `downburst` | 1038 | Journal of Geophysical Research Atmospheres（h652 · 12）<br>Geophysical Research Letters（h418 · 11）<br>Monthly Weather Review（h318 · 14） | [Downburst-like experimental impinging jet measurements at the WindEEE Dome](https://doi.org/10.1038/s41597-022-01342-1)（Scientific Data 2022，被引 35）<br>[CLIMATHUNDERR: experimental database of buoyancy-driven downbursts](https://doi.org/10.5194/essd-18-2133-2026)（Earth system science data 2026，被引 1）<br>[The ERIES-BOLT project: Behaviour of Telecommunication Lattice Towers under Thunderstorm Winds](https://doi.org/10.1038/s41597-026-06727-0)（Scientific Data 2026，被引 1） |
| MH0102 | 闪电（雷暴） | `lightning` | 77203 | Journal of Geophysical Research Atmospheres（h652 · 538）<br>International Journal of Molecular Sciences（h424 · 366）<br>Geophysical Research Letters（h418 · 411） | [The WGLC global gridded lightning climatology and time series](https://doi.org/10.5194/essd-13-3219-2021)（Earth system science data 2021，被引 115）<br>[World Wide Lightning Location Network (WWLLN) Global Lightning Climatology (WGLC) and time series, 2022 update](https://doi.org/10.5194/essd-14-5665-2022)（Earth system science data 2022，被引 39）<br>[A global database on holdover time of lightning-ignited wildfires](https://doi.org/10.5194/essd-15-1151-2023)（Earth system science data 2023，被引 26） |
| MH0103 | 雷暴 | `thunderstorms` | 21993 | Journal of Geophysical Research Atmospheres（h652 · 490）<br>Geophysical Research Letters（h418 · 321）<br>Journal of the Atmospheric Sciences（h331 · 110） | [Thunderstorm occurrence at ten sites across Great Britain over 1884–1993](https://doi.org/10.1002/gdj3.75)（Geoscience Data Journal 2019，被引 5）<br>[CanCPLD: Convective Parameters and Lightning Data to Support Future Thunderstorm Projections in North America](https://doi.org/10.1038/s41597-025-05924-7)（Scientific Data 2025，被引 3）<br>[Observations of Electric Fields Sounding in the Mature Stage of a Thunderstorm](https://doi.org/10.1002/gdj3.70081)（Geoscience Data Journal 2026，被引 1） |
| MH0201 | 沙尘暴 | `"dust storm"` | 15466 | Journal of Geophysical Research Atmospheres（h652 · 150）<br>The Science of The Total Environment（h492 · 175）<br>Geophysical Research Letters（h418 · 166） | [The Ensemble Mars Atmosphere Reanalysis System (EMARS) Version 1.0](https://doi.org/10.1002/gdj3.77)（Geoscience Data Journal 2019，被引 53）<br>[Zoning of air quality index (PM10 and PM2.5) by Arc-GIS for Khorramabad city, Iran](https://doi.org/10.1016/j.dib.2018.05.063)（Data in Brief 2018，被引 16）<br>[Observation based climatology Martian atmospheric waves perturbation Datasets](https://doi.org/10.1038/s41597-022-01909-y)（Scientific Data 2023，被引 17） |
| MH0202 | 雾 | `"dense fog"` | 2327 | Optics Express（h343 · 14）<br>Atmospheric chemistry and physics（h330 · 13）<br>Bulletin of the American Meteorological Society（h311 · 8） | [Dataset of dual-camera close-range photogrammetry for marker-based slope surface monitoring](https://doi.org/10.1016/j.dib.2026.113176)（Data in Brief 2026，被引 0）<br>[Iranian traffic sign dataset: A step towards understanding smart cities](https://doi.org/10.1016/j.dib.2026.112772)（Data in Brief 2026，被引 0）<br>[Individual Brain Charting: fifth release of high-resolution fMRI data for cognitive mapping](https://doi.org/10.1038/s41597-026-06869-1)（Scientific Data 2026，被引 0） |
| MH0203 | 霾 | `"haze pollution"` | 6793 | Journal of Geophysical Research Atmospheres（h652 · 80）<br>Environmental Science & Technology（h591 · 37）<br>The Science of The Total Environment（h492 · 87） | [LGHAP: the Long-term Gap-free High-resolution Air Pollutant concentration dataset, derived via tensor-flow-bas](https://doi.org/10.5194/essd-14-907-2022)（Earth system science data 2022，被引 157）<br>[A homogenized daily in situ PM 2.5 concentration dataset from the national air quality monitoring network in C](https://doi.org/10.5194/essd-12-3067-2020)（Earth system science data 2020，被引 41）<br>[China’s environmental policy intensity for 1978–2019](https://doi.org/10.1038/s41597-022-01183-y)（Scientific Data 2022，被引 72） |
| MH0204 | 沙霾 | `"sand haze"` | 12 | — | — |
| MH0205 | 烟 | `"wildfire smoke"` | 7179 | Journal of Geophysical Research Atmospheres（h652 · 157）<br>Environmental Science & Technology（h591 · 78）<br>The Science of The Total Environment（h492 · 84） | [A dataset on human perception of and response to wildfire smoke](https://doi.org/10.1038/s41597-019-0251-y)（Scientific Data 2019，被引 23）<br>[Daily PM2.5 concentration estimates by county, ZIP code, and census tract in 11 western states 2008–2018](https://doi.org/10.1038/s41597-021-00891-1)（Scientific Data 2021，被引 59）<br>[Contiguous United States wildland fire emission estimates during 2003–2015](https://doi.org/10.5194/essd-10-2241-2018)（Earth system science data 2018，被引 41） |
| MH0301 | 大风 | `windstorm` | 6624 | Journal of Geophysical Research Atmospheres（h652 · 44）<br>Geophysical Research Letters（h418 · 39）<br>Global Change Biology（h400 · 29） | [CLIMK–WINDS: a new database of extreme European winter windstorms](https://doi.org/10.5194/essd-17-4431-2025)（Earth system science data 2025，被引 6）<br>[A satellite-derived database for stand-replacing windthrow events in boreal forests of European Russia in 1986](https://doi.org/10.5194/essd-12-3489-2020)（Earth system science data 2020，被引 43）<br>[A spatially explicit database of wind disturbances in European forests over the period 2000–2018](https://doi.org/10.5194/essd-12-257-2020)（Earth system science data 2020，被引 115） |
| MH0302 | 德雷乔风暴 | `derecho` | 458809 | Ciencia Latina Revista Científica Multidisciplinar（h36 · 5115）<br>Polo del Conocimiento（h19 · 2510）<br>Revista Ibero-Americana de Humanidades, Ciências e Educação（h19 · 663） | [A derecho climatology (2004–2021) in the United States based on machine learning identification of bow echoes](https://doi.org/10.5194/essd-17-3721-2025)（Earth system science data 2025，被引 5）<br>[Data on accumulative allocation of water rights in the Atacama Desert (Antofagasta Region, northern Chile), 19](https://doi.org/10.1016/j.dib.2022.108296)（Data in Brief 2022，被引 2）<br>[Weather data analysis and building performance assessment during extreme climate events: A Canadian AMY weathe](https://doi.org/10.1016/j.dib.2024.110036)（Data in Brief 2024，被引 9） |
| MH0303 | 烈风 | `"gale wind"` | 184 | Weather and Forecasting（h156 · 5）<br>Atmosphere（h107 · 13） | [Wind and structural loads data measured on parabolic trough solar collectors at an operational power plant](https://doi.org/10.1038/s41597-023-02896-4)（Scientific Data 2024，被引 15）<br>[Global tropical cyclone size and intensity reconstruction dataset for 1959–2022 based on IBTrACS and ERA5 data](https://doi.org/10.5194/essd-16-5753-2024)（Earth system science data 2024，被引 22） |
| MH0304 | 飑 | `squall` | 4133 | Journal of Geophysical Research Atmospheres（h652 · 208）<br>Geophysical Research Letters（h418 · 107）<br>Journal of Climate（h411 · 30） | [A high-resolution divergence and vorticity dataset in Beijing derived from radar wind profiler mesonet measure](https://doi.org/10.5194/essd-17-3541-2025)（Earth system science data 2025，被引 1）<br>[A Satellite-based Four-decade High-resolution Quasi-global Mesoscale Convective Systems Database](https://doi.org/10.1038/s41597-026-08378-7)（Scientific Data 2026，被引 0）<br>[Ten ensembles with hourly high spatial resolution datasets for severe precipitation events in Egypt](https://doi.org/10.1016/j.dib.2020.105987)（Data in Brief 2020，被引 0） |
| MH0305 | 龙卷 | `tornado` | 87164 | Bulletin of the American Meteorological Society（h311 · 187）<br>Atmosphere（h107 · 232）<br>Research Society and Development（h37 · 1203） | [A satellite-derived database for stand-replacing windthrow events in boreal forests of European Russia in 1986](https://doi.org/10.5194/essd-12-3489-2020)（Earth system science data 2020，被引 43）<br>[All-hazards dataset mined from the US National Incident Management System 1999–2020](https://doi.org/10.1038/s41597-023-01955-0)（Scientific Data 2023，被引 58）<br>[All-hazards dataset mined from the US National Incident Management System 1999–2014](https://doi.org/10.1038/s41597-020-0403-0)（Scientific Data 2020，被引 37） |
| MH0306 | 低压或气旋 | `"cyclone disaster"` | 800 | Natural Hazards（h187 · 14）<br>Frontiers in Marine Science（h165 · 5）<br>Natural hazards and earth system sciences（h165 · 5） | [An objective hourly dataset of typhoon remnant vortices affecting China (1980–2024)](https://doi.org/10.1038/s41597-026-08405-7)（Scientific Data 2026，被引 0）<br>[Reconstructed county-level dataset of crop areas affected by typhoons in China’s coastal regions (1980–2022)](https://doi.org/10.1038/s41597-025-05834-8)（Scientific Data 2025，被引 0） |
| MH0307 | 温带气旋 | `"extratropical cyclone"` | 4493 | Journal of Geophysical Research Atmospheres（h652 · 237）<br>Geophysical Research Letters（h418 · 202）<br>Journal of Climate（h411 · 139） | [North Atlantic Extratropical Cyclone Tracks and Lagrangian-Derived Moisture Uptake Dataset](https://doi.org/10.1038/s41597-024-04091-5)（Scientific Data 2024，被引 6）<br>[A unified data set of airborne cloud remote sensing using the HALO Microwave Package (HAMP)](https://doi.org/10.5194/essd-11-921-2019)（Earth system science data 2019，被引 46）<br>[Baroclinic Wave Simulation Ensemble: a Machine Learning ready dataset](https://doi.org/10.1038/s41597-025-06089-z)（Scientific Data 2025，被引 1） |
| MH0308 | 副热带气旋 | `"subtropical cyclone"` | 319 | Journal of Geophysical Research Atmospheres（h652 · 18）<br>Geophysical Research Letters（h418 · 8）<br>Journal of Climate（h411 · 7） | [Dataset of outer tropical cyclone size from a radial wind profile](https://doi.org/10.1016/j.dib.2022.107825)（Data in Brief 2022，被引 14）<br>[Binary dataset for machine learning applications to tropical cyclone formation prediction](https://doi.org/10.1038/s41597-024-03281-5)（Scientific Data 2024，被引 5）<br>[Global tropical cyclone size and intensity reconstruction dataset for 1959–2022 based on IBTrACS and ERA5 data](https://doi.org/10.5194/essd-16-5753-2024)（Earth system science data 2024，被引 22） |
| MH0309 | 热带气旋 | `"tropical cyclone"` | 32745 | Journal of Geophysical Research Atmospheres（h652 · 568）<br>Geophysical Research Letters（h418 · 832）<br>Journal of Climate（h411 · 439） | [Generation of a global synthetic tropical cyclone hazard dataset using STORM](https://doi.org/10.1038/s41597-020-0381-2)（Scientific Data 2020，被引 251）<br>[A global historical data set of tropical cyclone exposure (TCE-DAT)](https://doi.org/10.5194/essd-10-185-2018)（Earth system science data 2018，被引 93）<br>[Estimation of global tropical cyclone wind speed probabilities using the STORM dataset](https://doi.org/10.1038/s41597-020-00720-x)（Scientific Data 2020，被引 52） |
| MH0401 | 干旱 | `drought` | 498316 | The Science of The Total Environment（h492 · 2102）<br>International Journal of Molecular Sciences（h424 · 5483）<br>New Phytologist（h412 · 1627） | [Drought Atlas of India, 1901–2020](https://doi.org/10.1038/s41597-023-02856-y)（Scientific Data 2024，被引 72）<br>[Global integrated drought monitoring and prediction system](https://doi.org/10.1038/sdata.2014.1)（Scientific Data 2014，被引 796）<br>[A pan-African high-resolution drought index dataset](https://doi.org/10.5194/essd-12-753-2020)（Earth system science data 2020，被引 144） |
| MH0402 | 降雨 | `"heavy rainfall"` | 64929 | Journal of Geophysical Research Atmospheres（h652 · 468）<br>The Science of The Total Environment（h492 · 419）<br>Geophysical Research Letters（h418 · 449） | [Inventory of Landslides Triggered by Heavy Rainfall in Fuling District, Chongqing, China, June 2019](https://doi.org/10.1002/gdj3.70062)（Geoscience Data Journal 2026，被引 0）<br>[Correction to Inventory of Landslides Triggered by Heavy Rainfall in Fuling District, Chongqing, China, June 2](https://doi.org/10.1002/gdj3.70085)（Geoscience Data Journal 2026，被引 0）<br>[TPHiPr: a long-term (1979–2020) high-accuracy precipitation dataset (1∕30°, daily) for the Third Pole region b](https://doi.org/10.5194/essd-15-621-2023)（Earth system science data 2023，被引 241） |
| MH0403 | 暴风雪 | `blizzard` | 12016 | International Journal of Molecular Sciences（h424 · 101）<br>Frontiers in Immunology（h350 · 32）<br>Nutrients（h330 · 144） | [SC2EGSet: StarCraft II Esport Replay and Game-state Dataset](https://doi.org/10.1038/s41597-023-02510-7)（Scientific Data 2023，被引 13）<br>[Enhanced automated meteorological observations at the Canadian Arctic Weather Science (CAWS) supersites](https://doi.org/10.5194/essd-14-4995-2022)（Earth system science data 2022，被引 12）<br>[Precipitation at Dumont d'Urville, Adélie Land, East Antarctica: the APRES3 field campaigns dataset](https://doi.org/10.5194/essd-10-1605-2018)（Earth system science data 2018，被引 26） |
| MH0404 | 冰雹 | `"hail storm"` | 1426 | Journal of Geophysical Research Atmospheres（h652 · 14）<br>Geophysical Research Letters（h418 · 8）<br>Atmospheric chemistry and physics（h330 · 9） | [GOES ABI-derived hailstorm polygons and tracking dataset for Brazil](https://doi.org/10.1016/j.dib.2024.110736)（Data in Brief 2024，被引 2）<br>[A new dataset of rain cells based on observations of Tropical Rainfall Measuring Mission (TRMM) precipitation ](https://doi.org/10.5194/essd-17-5137-2025)（Earth system science data 2025，被引 1）<br>[Brazilian disaster datasets and real-world instances for optimization and machine learning](https://doi.org/10.1016/j.dib.2022.108012)（Data in Brief 2022，被引 8） |
| MH0405 | 降雪 | `"heavy snowfall"` | 3717 | Journal of Geophysical Research Atmospheres（h652 · 34）<br>Geophysical Research Letters（h418 · 20）<br>Bulletin of the American Meteorological Society（h311 · 16） | [SnowRef-Drive: A Global Instruction-Driven Traffic Video Segmentation Dataset for Adverse Weather Driving Scen](https://doi.org/10.1038/s41597-026-07884-y)（Scientific Data 2026，被引 0）<br>[A position and wave spectra dataset of Marginal Ice Zone dynamics collected around Svalbard in 2022 and 2023](https://doi.org/10.1038/s41597-024-04281-1)（Scientific Data 2024，被引 8）<br>[A Monthly Snow and Sleet Series for the Greater Dublin Area 1867–2024](https://doi.org/10.1002/gdj3.70022)（Geoscience Data Journal 2025，被引 0） |
| MH0406 | 雪暴 | `"snow storm"` | 1568 | Journal of Geophysical Research Atmospheres（h652 · 13）<br>Geophysical Research Letters（h418 · 8）<br>Atmospheric chemistry and physics（h330 · 7） | [OpenMesh: wireless signal dataset for opportunistic urban weather sensing in New York City](https://doi.org/10.5194/essd-18-5817-2026)（Earth system science data 2026，被引 4）<br>[Weather data analysis and building performance assessment during extreme climate events: A Canadian AMY weathe](https://doi.org/10.1016/j.dib.2024.110036)（Data in Brief 2024，被引 9）<br>[A 6-hourly 0.1° resolution freezing rain dataset of China during 2000–2019 based on deep kernel learning](https://doi.org/10.1038/s41597-025-04582-z)（Scientific Data 2025，被引 6） |
| MH0501 | 热浪 | `"heat wave"` | 57614 | The Science of The Total Environment（h492 · 444）<br>Geophysical Research Letters（h418 · 362）<br>Global Change Biology（h400 · 265） | [Global near real‐time daily apparent temperature and heat wave dataset](https://doi.org/10.1002/gdj3.155)（Geoscience Data Journal 2022，被引 19）<br>[Global dataset on heat wave exposure due to the urban heat island effect](https://doi.org/10.1038/s41597-026-06877-1)（Scientific Data 2026，被引 3）<br>[Global dataset of heat wave types based on multi-level atmospheric temperature anomalies](https://doi.org/10.1038/s41597-026-08261-5)（Scientific Data 2026，被引 0） |
| MH0502 | 寒潮 | `"cold wave"` | 5591 | Journal of Geophysical Research Atmospheres（h652 · 31）<br>The Science of The Total Environment（h492 · 40）<br>Geophysical Research Letters（h418 · 47） | [A large-scale, multitask, multisensory dataset for climate-aware crop monitoring in the US from 2018–2022](https://doi.org/10.1038/s41597-026-06611-x)（Scientific Data 2026，被引 5）<br>[What’s the TEE: Metrics of Temperature Extremes in Europe NUTS Regions (1980-2024)](https://doi.org/10.1038/s41597-025-05352-7)（Scientific Data 2025，被引 2）<br>[A Historical Extreme Cold Events Dataset for Building Energy and Resilience Modeling Across the United States](https://doi.org/10.1038/s41597-026-07717-y)（Scientific Data 2026，被引 0） |
| MH0503 | 白灾（Dzud） | `dzud` | 341 | International Journal of Disaster Risk Reduction（h137 · 5）<br>Human Ecology（h127 · 6）<br>Land（h102 · 10） | — |
| MH0504 | 冰冻 | `"hard freeze"` | 200 | Agronomy Journal（h237 · 5）<br>EDIS（h47 · 6） | — |
| MH0505 | 白霜 | `hoarfrost` | 689 | International Journal of Molecular Sciences（h424 · 5）<br>Macromolecules（h417 · 11）<br>Frontiers in Microbiology（h343 · 27） | [A long-term hydrometeorological dataset (1993–2014) of a northern mountain basin: Wolf Creek Research Basin, Y](https://doi.org/10.5194/essd-11-89-2019)（Earth system science data 2019，被引 24）<br>[A marine and salt marsh sediment organic carbon database for European regional seas (EURO-CARBON)](https://doi.org/10.1016/j.dib.2025.111595)（Data in Brief 2025，被引 10） |
| MH0506 | 冻雨 | "freezing rain" | 待查 | | |
| MH0507 | 雨凇 | `"glaze ice"` | 543 | Renewable Energy（h319 · 6）<br>IEEE Transactions on Power Delivery（h250 · 5）<br>Physics of Fluids（h248 · 8） | — |
| MH0508 | 地面霜冻 | `"ground frost"` | 482 | Journal of Hydrology（h360 · 7）<br>Hydrological Processes（h229 · 6）<br>Plants（h175 · 5） | [An hourly ground temperature dataset for 16 high-elevation sites (3493–4377 m a.s.l.) in the Bale Mountains, E](https://doi.org/10.5194/essd-14-1043-2022)（Earth system science data 2022，被引 15）<br>[Future global annual frozen ground distribution datasets based on Frost Number Model with Kappa coefficient](https://doi.org/10.1038/s41597-026-06918-9)（Scientific Data 2026，被引 1） |
| MH0509 | 结冰 | `"atmospheric icing"` | 627 | Applied Thermal Engineering（h252 · 5）<br>Materials（h248 · 8）<br>Polymers（h237 · 7） | [An airborne in-situ dataset of cloud microphysical properties in supercooled large droplet icing conditions](https://doi.org/10.5194/essd-18-5837-2026)（Earth system science data 2026，被引 0）<br>[In situ surface cloud measurement dataset from four cloud spectrometers during the Pallas Cloud Experiment (Pa](https://doi.org/10.5194/essd-17-6497-2025)（Earth system science data 2025，被引 1） |
| MH0510 | 解冻 | "spring thaw flood" | 待查 | | |
| MH0600 | 洪水 | "flood disaster" | 待查 | | |
| MH0601 | 沿海洪水 | "coastal flood" | 待查 | | |
| MH0602 | 河口洪水 | "estuarine flooding" | 待查 | | |
| MH0603 | 山洪 | "flash floods" | 待查 | | |
| MH0604 | 河流洪水 | "river flood" | 待查 | | |
| MH0605 | 地下水洪水 | "groundwater flood" | 待查 | | |
| MH0606 | 地表积水 | inundation | 待查 | | |
| MH0607 | 冰湖溃决洪水 | "glacial lake outburst" | 待查 | | |
| MH0608 | 冰塞洪水（含碎屑） | "ice jam" | 待查 | | |
| MH0609 | 内涝 | waterlogging | 待查 | | |
| MH0610 | 融雪洪水 | "snowmelt flood" | 待查 | | |
| MH0701 | 畸形浪 | "rogue wave" | 待查 | | |
| MH0702 | 假潮 | seiche | 待查 | | |
| MH0703 | 风暴潮 | "storm surge" | 待查 | | |
| MH0704 | 风暴高潮 | "storm tide" | 待查 | | |
| MH0705 | 海啸 | tsunami | 待查 | | |
| MH0706 | 海冰 | "sea ice" | 待查 | | |
| MH0707 | 流冰 | "ice floe" | 待查 | | |
| MH0708 | 海洋热浪 | "marine heat wave" | 待查 | | |
| MH0801 | 雪崩 | avalanche | 待查 | | |

<details><summary>高被引方法论文</summary>

- **MH0101 下击暴流**：[Climate change induces multiple risks to boreal forests and forestry in Finland: A literature review](https://doi.org/10.1111/gcb.15183)（Global Change Biology 2020）；[Wind farm flow control: prospects and challenges](https://doi.org/10.5194/wes-7-2271-2022)（Wind energy science 2022）；[Investigation of near-global daytime boundary layer height using high-resolution radiosondes: first results an](https://doi.org/10.5194/acp-21-17079-2021)（Atmospheric chemistry and physics 2021）
- **MH0102 闪电（雷暴）**：[Highly accurate protein structure prediction with AlphaFold](https://doi.org/10.1038/s41586-021-03819-2)（Nature 2021）；[Dictionary learning for integrative, multimodal and scalable single-cell analysis](https://doi.org/10.1038/s41587-023-01767-y)（Nature Biotechnology 2023）；[Improved protein structure prediction using potentials from deep learning](https://doi.org/10.1038/s41586-019-1923-7)（Nature 2020）
- **MH0103 雷暴**：[GW190814: Gravitational Waves from the Coalescence of a 23 Solar Mass Black Hole with a 2.6 Solar Mass Compact](https://doi.org/10.3847/2041-8213/ab960f)（The Astrophysical Journal Letters 2020）；[Pervasive shifts in forest dynamics in a changing world](https://doi.org/10.1126/science.aaz9463)（Science 2020）；[Various Natural and Anthropogenic Factors Responsible for Water Quality Degradation: A Review](https://doi.org/10.3390/w13192660)（Water 2021）
- **MH0201 沙尘暴**：[Environmental and Health Impacts of Air Pollution: A Review](https://doi.org/10.3389/fpubh.2020.00014)（Frontiers in Public Health 2020）；[Getting the message right on nature‐based solutions to climate change](https://doi.org/10.1111/gcb.15513)（Global Change Biology 2021）；[The 2024 report of the Lancet Countdown on health and climate change: facing record-breaking threats from dela](https://doi.org/10.1016/s0140-6736(24)01822-1)（The Lancet 2024）
- **MH0202 雾**：[Terahertz Communications and Sensing for 6G and Beyond: A Comprehensive Review](https://doi.org/10.1109/comst.2024.3385908)（IEEE Communications Surveys & Tutorials 2024）；[Fast sulfate formation from oxidation of SO2 by NO2 and HONO observed in Beijing haze](https://doi.org/10.1038/s41467-020-16683-x)（Nature Communications 2020）；[Terahertz Wireless Channels: A Holistic Survey on Measurement, Modeling, and Analysis](https://doi.org/10.1109/comst.2022.3182539)（IEEE Communications Surveys & Tutorials 2022）
- **MH0203 霾**：[Enhanced secondary pollution offset reduction of primary emissions during COVID-19 lockdown in China](https://doi.org/10.1093/nsr/nwaa137)（National Science Review 2020）；[Unexpected air pollution with marked emission reductions during the COVID-19 outbreak in China](https://doi.org/10.1126/science.abb7431)（Science 2020）；[Determination of Objective Weights Using a New Method Based on the Removal Effects of Criteria (MEREC)](https://doi.org/10.3390/sym13040525)（Symmetry 2021）
- **MH0204 沙霾**：[Forecasting PM10 Concentrations in the Caribbean Area Using Machine Learning Models](https://doi.org/10.3390/atmos14010134)（Atmosphere 2023）；[Evaluating the representation of disaster hazards in SNOMED CT: gaps and opportunities](https://doi.org/10.1093/jamia/ocad153)（Journal of the American Medical Informatics Association 2023）；[Study of the Dynamical Relationships between PM2.5 and PM10 in the Caribbean Area Using a Multiscale Framework](https://doi.org/10.3390/atmos14030468)（Atmosphere 2023）
- **MH0205 烟**：[The 2020 report of The Lancet Countdown on health and climate change: responding to converging crises](https://doi.org/10.1016/s0140-6736(20)32290-x)（The Lancet 2020）；[The 2022 report of the Lancet Countdown on health and climate change: health at the mercy of fossil fuels](https://doi.org/10.1016/s0140-6736(22)01540-9)（The Lancet 2022）；[2023 AHA/ACC/ACCP/ASPC/NLA/PCNA Guideline for the Management of Patients With Chronic Coronary Disease: A Repo](https://doi.org/10.1161/cir.0000000000001168)（Circulation 2023）
- **MH0301 大风**：[The Arctic has warmed nearly four times faster than the globe since 1979](https://doi.org/10.1038/s43247-022-00498-3)（Communications Earth & Environment 2022）；[A review of the global climate change impacts, adaptation, and sustainable mitigation measures](https://doi.org/10.1007/s11356-022-19718-6)（Environmental Science and Pollution Research 2022）；[The Impact of Climate Change on Mental Health: A Systematic Descriptive Review](https://doi.org/10.3389/fpsyt.2020.00074)（Frontiers in Psychiatry 2020）
- **MH0302 德雷乔风暴**：[Isolation, quarantine, social distancing and community containment: pivotal role for old-style public health m](https://doi.org/10.1093/jtm/taaa020)（Journal of Travel Medicine 2020）；[The Impact of Climate Change on Mental Health: A Systematic Descriptive Review](https://doi.org/10.3389/fpsyt.2020.00074)（Frontiers in Psychiatry 2020）；[Policy Brief: Education during COVID-19 and beyond](https://doi.org/10.24215/18509959.26.e12)（Revista Iberoamericana de Tecnología en Educación y Educación en Tecnología 2020）
- **MH0303 烈风**：[Estimating tropical cyclone surface winds: Current status, emerging technologies, historical evolution, and a ](https://doi.org/10.1016/j.tcrr.2021.09.002)（Tropical Cyclone Research and Review 2021）；[Extensive High-Resolution Synthetic Aperture Radar (SAR) Data Analysis of Tropical Cyclones: Comparisons with ](https://doi.org/10.1175/mwr-d-20-0005.1)（Monthly Weather Review 2020）；[The Role of the Human Factor in Marine Accidents](https://doi.org/10.3390/jmse9030261)（Journal of Marine Science and Engineering 2021）
- **MH0304 飑**：[Loneliness around the world: Age, gender, and cultural differences in loneliness](https://doi.org/10.1016/j.paid.2020.110066)（Personality and Individual Differences 2020）；[Confronting the Challenge of Modeling Cloud and Precipitation Microphysics](https://doi.org/10.1029/2019ms001689)（Journal of Advances in Modeling Earth Systems 2020）；[Skilful nowcasting of extreme precipitation with NowcastNet](https://doi.org/10.1038/s41586-023-06184-4)（Nature 2023）
- **MH0305 龙卷**：[Emergency remote teaching in a time of global crisis due to CoronaVirus pandemic](https://doi.org/10.5281/zenodo.3778082)（Zenodo (CERN European Organization for Nuclear Research) 2020）；[The 2022 report of the Lancet Countdown on health and climate change: health at the mercy of fossil fuels](https://doi.org/10.1016/s0140-6736(22)01540-9)（The Lancet 2022）；[Accurate medium-range global weather forecasting with 3D neural networks](https://doi.org/10.1038/s41586-023-06185-3)（Nature 2023）
- **MH0306 低压或气旋**：[Why We Can No Longer Ignore Consecutive Disasters](https://doi.org/10.1029/2019ef001425)（Earth s Future 2020）；[Climate change and Indian agriculture: A systematic review of farmers’ perception, adaptation, and transformat](https://doi.org/10.1016/j.envc.2022.100543)（Environmental Challenges 2022）；[A Systematic Review of Coastal Vulnerability Mapping](https://doi.org/10.3390/su12072822)（Sustainability 2020）
- **MH0307 温带气旋**：[Advances in understanding large‐scale responses of the water cycle to climate change](https://doi.org/10.1111/nyas.14337)（Annals of the New York Academy of Sciences 2020）；[A Systematic, Regional Assessment of High Mountain Asia Glacier Mass Balance](https://doi.org/10.3389/feart.2019.00363)（Frontiers in Earth Science 2020）；[Why Is the Mediterranean a Climate Change Hot Spot?](https://doi.org/10.1175/jcli-d-19-0910.1)（Journal of Climate 2020）
- **MH0308 副热带气旋**：[Human health concerns regarding microplastics in the aquatic environment - From marine to food systems](https://doi.org/10.1016/j.scitotenv.2022.153730)（The Science of The Total Environment 2022）；[Impact of Model Resolution on Tropical Cyclone Simulation Using the HighResMIP–PRIMAVERA Multimodel Ensemble](https://doi.org/10.1175/jcli-d-19-0639.1)（Journal of Climate 2020）；[Recent Progress in Tropical Cyclone Intensity Forecasting at the National Hurricane Center](https://doi.org/10.1175/waf-d-20-0059.1)（Weather and Forecasting 2020）
- **MH0309 热带气旋**：[Scientists' warning on invasive alien species](https://doi.org/10.1111/brv.12627)（Biological reviews/Biological reviews of the Cambridge Philosophical Society 2020）；[Accurate medium-range global weather forecasting with 3D neural networks](https://doi.org/10.1038/s41586-023-06185-3)（Nature 2023）；[Learning skillful medium-range global weather forecasting](https://doi.org/10.1126/science.adi2336)（Science 2023）
- **MH0401 干旱**：[ERA5-Land: a state-of-the-art global reanalysis dataset for land applications](https://doi.org/10.5194/essd-13-4349-2021)（Earth system science data 2021）；[Earth beyond six of nine planetary boundaries](https://doi.org/10.1126/sciadv.adh2458)（Science Advances 2023）；[Reactive Oxygen Species and Antioxidant Defense in Plants under Abiotic Stress: Revisiting the Crucial Role of](https://doi.org/10.3390/antiox9080681)（Antioxidants 2020）
- **MH0402 降雨**：[The 2022 report of the Lancet Countdown on health and climate change: health at the mercy of fossil fuels](https://doi.org/10.1016/s0140-6736(22)01540-9)（The Lancet 2022）；[Climate change impact on flood and extreme precipitation increases with water availability](https://doi.org/10.1038/s41598-020-70816-2)（Scientific Reports 2020）；[Impact of Climate Change on Agriculture and Its Mitigation Strategies: A Review](https://doi.org/10.3390/su13031318)（Sustainability 2021）
- **MH0403 暴风雪**：[Sex and gender: modifiers of health, disease, and medicine](https://doi.org/10.1016/s0140-6736(20)31561-0)（The Lancet 2020）；[Global Initiative for Chronic Obstructive Lung Disease 2023 Report: GOLD Executive Summary](https://doi.org/10.1183/13993003.00239-2023)（European Respiratory Journal 2023）；[2023 Guideline for the Management of Patients With Aneurysmal Subarachnoid Hemorrhage: A Guideline From the Am](https://doi.org/10.1161/str.0000000000000436)（Stroke 2023）
- **MH0404 冰雹**：[Extreme weather events risk to crop-production and the adaptation of innovative management strategies to mitig](https://doi.org/10.1016/j.technovation.2021.102255)（Technovation 2021）；[The environmental factors affecting solar photovoltaic output](https://doi.org/10.1016/j.rser.2024.115073)（Renewable and Sustainable Energy Reviews 2024）；[The effects of climate change on hailstorms](https://doi.org/10.1038/s43017-020-00133-9)（Nature Reviews Earth & Environment 2021）
- **MH0405 降雪**：[A Review of the Measures to Enhance Power Systems Resilience](https://doi.org/10.1109/jsyst.2020.2965993)（IEEE Systems Journal 2020）；[Extreme weather and climate events in northern areas: A review](https://doi.org/10.1016/j.earscirev.2020.103324)（Earth-Science Reviews 2020）；[Tundra vegetation change and impacts on permafrost](https://doi.org/10.1038/s43017-021-00233-0)（Nature Reviews Earth & Environment 2022）
- **MH0406 雪暴**：[A Survey of Multi-Access Edge Computing in 5G and Beyond: Fundamentals, Technology Integration, and State-of-t](https://doi.org/10.1109/access.2020.3001277)（IEEE Access 2020）；[Cascading risks: Understanding the 2021 winter blackout in Texas](https://doi.org/10.1016/j.erss.2021.102106)（Energy Research & Social Science 2021）；[Urban Climates and Climate Change](https://doi.org/10.1146/annurev-environ-012320-083623)（Annual Review of Environment and Resources 2020）
- **MH0501 热浪**：[Global burden of 288 causes of death and life expectancy decomposition in 204 countries and territories and 81](https://doi.org/10.1016/s0140-6736(24)00367-2)（The Lancet 2024）；[Plant responses to rising vapor pressure deficit](https://doi.org/10.1111/nph.16485)（New Phytologist 2020）；[The Global Burden of Cardiovascular Diseases and Risk](https://doi.org/10.1016/j.jacc.2022.11.005)（Journal of the American College of Cardiology 2022）
- **MH0502 寒潮**：[The Impact of Climate Change on Mental Health: A Systematic Descriptive Review](https://doi.org/10.3389/fpsyt.2020.00074)（Frontiers in Psychiatry 2020）；[Machine Learning Applications for Precision Agriculture: A Comprehensive Review](https://doi.org/10.1109/access.2020.3048415)（IEEE Access 2020）；[Impacts of climate change on the livestock food supply chain; a review of the evidence](https://doi.org/10.1016/j.gfs.2020.100488)（Global Food Security 2021）
- **MH0503 白灾（Dzud）**：[Land Cover Classification using Google Earth Engine and Random Forest Classifier—The Role of Image Composition](https://doi.org/10.3390/rs12152411)（Remote Sensing 2020）；[Global snow drought hot spots and characteristics](https://doi.org/10.1073/pnas.1915921117)（Proceedings of the National Academy of Sciences 2020）；[How many large camelids in the world? A synthetic analysis of the world camel demographic changes](https://doi.org/10.1186/s13570-020-00176-z)（Pastoralism Research Policy and Practice 2020）
- **MH0504 冰冻**：[Tropicalization of temperate ecosystems in North America: The northward range expansion of tropical organisms ](https://doi.org/10.1111/gcb.15563)（Global Change Biology 2021）；[Coping with the cold: unveiling cryoprotectants, molecular signaling pathways, and strategies for cold stress ](https://doi.org/10.3389/fpls.2023.1246093)（Frontiers in Plant Science 2023）；[Global Mangrove Deforestation and Its Interacting Social-Ecological Drivers: A Systematic Review and Synthesis](https://doi.org/10.3390/su14084433)（Sustainability 2022）
- **MH0505 白霜**：[Deep learning to estimate lithium-ion battery state of health without additional degradation experiments](https://doi.org/10.1038/s41467-023-38458-w)（Nature Communications 2023）；[Empowering biomedical discovery with AI agents](https://doi.org/10.1016/j.cell.2024.09.022)（Cell 2024）；[Machine Learning-Guided Protein Engineering](https://doi.org/10.1021/acscatal.3c02743)（ACS Catalysis 2023）
- **MH0507 雨凇**：[A superhydrophobic/electrothermal synergistically anti-icing strategy based on graphene composite](https://doi.org/10.1016/j.compscitech.2020.108307)（Composites Science and Technology 2020）；[Advanced Anti‐Icing Strategies and Technologies by Macrostructured Photothermal Storage Superhydrophobic Surfa](https://doi.org/10.1002/adma.202402897)（Advanced Materials 2024）；[Design Rules for Laser‐Treated Icephobic Metallic Surfaces for Aeronautic Applications](https://doi.org/10.1002/adfm.201910268)（Advanced Functional Materials 2020）
- **MH0508 地面霜冻**：[Crop Yield Prediction Using Deep Reinforcement Learning Model for Sustainable Agrarian Applications](https://doi.org/10.1109/access.2020.2992480)（IEEE Access 2020）；[Arctic tundra shrubification: a review of mechanisms and impacts on ecosystem carbon balance](https://doi.org/10.1088/1748-9326/abf28b)（Environmental Research Letters 2021）；[Predictor complexity and feature selection affect Maxent model transferability: Evidence from global freshwate](https://doi.org/10.1111/ddi.13211)（Diversity and Distributions 2020）
- **MH0509 结冰**：[Design Rules for Laser‐Treated Icephobic Metallic Surfaces for Aeronautic Applications](https://doi.org/10.1002/adfm.201910268)（Advanced Functional Materials 2020）；[Polysiloxane as icephobic materials – The past, present and the future](https://doi.org/10.1016/j.cej.2020.127088)（Chemical Engineering Journal 2020）；[Bioinspired micro/nanostructured surfaces prepared by femtosecond laser direct writing for multi-functional ap](https://doi.org/10.1088/2631-7990/ab95f6)（International Journal of Extreme Manufacturing 2020）

</details>

## 地外（Extraterrestrial）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| ET0101 | 地磁扰动 | "geomagnetic storm" | 待查 | | |
| ET0102 | 电离层扰动 | "ionospheric disturbance" | 待查 | | |
| ET0103 | 太阳耀斑 | "solar flare" | 待查 | | |
| ET0104 | 太阳高能粒子 | "solar energetic particle" | 待查 | | |
| ET0201 | 空中爆炸（陨石） | airburst | 待查 | | |
| ET0202 | 紫外辐射 | "ultraviolet radiation exposure" | 待查 | | |
| ET0203 | 陨石撞击 | meteorite | 待查 | | |
| ET0204 | 航天事故 | "rocket debris re-entry" | 待查 | | |
| ET0205 | 近地天体 | asteroid | 待查 | | |
| ET0206 | 空间碎片 | "space debris" | 待查 | | |

<details><summary>高被引方法论文</summary>


</details>

## 地质（Geological）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| GH0101 | 地震 | earthquake | 待查 | | |
| GH0201 | 熔岩流 | "lava flow" | 待查 | | |
| GH0202 | 火山灰与碎屑 | "volcanic ash" | 待查 | | |
| GH0203 | 火山碎屑流 | pyroclastic | 待查 | | |
| GH0204 | 火山泥流 | lahar | 待查 | | |
| GH0205 | 火山气体与气溶胶 | "volcanic gas" | 待查 | | |
| GH0300 | 重力块体运动（滑坡） | landslide | 待查 | | |
| GH0301 | 崩落（落石、冰崩） | "rock fall" | 待查 | | |
| GH0302 | 侧向扩离 | "lateral spread" | 待查 | | |
| GH0303 | 流动（泥石流） | "debris flow" | 待查 | | |
| GH0304 | 滑动 | landslide | 待查 | | |
| GH0305 | 倾倒 | "rock topple" | 待查 | | |
| GH0306 | 海底滑坡 | "submarine landslide" | 待查 | | |
| GH0307 | 砂土液化 | liquefaction | 待查 | | |
| GH0308 | 落水洞 | sinkhole | 待查 | | |
| GH0309 | 沉降与抬升 | "land subsidence" | 待查 | | |
| GH0310 | 胀缩沉降 | "expansive soil" | 待查 | | |
| GH0311 | 地表破裂与裂缝 | "ground fissure" | 待查 | | |
| GH0401 | 压缩性土 | "soft soil settlement" | 待查 | | |
| GH0402 | 土壤退化 | "soil degradation" | 待查 | | |
| GH0403 | 土壤侵蚀 | "soil erosion" | 待查 | | |
| GH0404 | 河岸侵蚀与淤积 | "river bank erosion" | 待查 | | |
| GH0405 | 海岸侵蚀与淤积 | "coastal erosion" | 待查 | | |
| GH0406 | 沙地侵入 | "sand encroachment" | 待查 | | |
| GH0407 | 地下气体（甲烷、氡等） | radon | 待查 | | |

<details><summary>高被引方法论文</summary>


</details>

## 环境（Environmental）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| EN0101 | 室内空气污染 | "indoor air pollution" | 待查 | | |
| EN0102 | 点源空气污染 | "industrial emissions" | 待查 | | |
| EN0103 | 室外空气污染 | "air pollution" | 待查 | | |
| EN0104 | 黑碳 | "black carbon" | 待查 | | |
| EN0105 | 酸雨 | "acid rain" | 待查 | | |
| EN0106 | 面源污染 | "nonpoint source pollution" | 待查 | | |
| EN0201 | 毁林 | deforestation | 待查 | | |
| EN0202 | 森林衰退 | "forest dieback" | 待查 | | |
| EN0203 | 森林扰动 | "forest damage" | 待查 | | |
| EN0204 | 森林入侵物种 | "invasive species" | 待查 | | |
| EN0205 | 野火（森林火灾） | "forest fire" | 待查 | | |
| EN0206 | 荒漠化 | desertification | 待查 | | |
| EN0207 | 红树林丧失 | "mangrove loss" | 待查 | | |
| EN0301 | 土地退化 | "land degradation" | 待查 | | |
| EN0302 | 海水入侵 | "seawater intrusion" | 待查 | | |
| EN0303 | 盐渍化 | "soil salinization" | 待查 | | |
| EN0304 | 湿地退化 | "wetland loss" | 待查 | | |
| EN0305 | 冻土消融 | permafrost | 待查 | | |
| EN0401 | 海洋酸化 | "ocean acidification" | 待查 | | |
| EN0402 | 海平面上升 | "sea level rise" | 待查 | | |
| EN0403 | 富营养化 | eutrophication | 待查 | | |
| EN0404 | 珊瑚白化 | "coral bleaching" | 待查 | | |
| EN0405 | 采砂 | "sand mining" | 待查 | | |
| EN0501 | 生物多样性丧失 | "biodiversity loss" | 待查 | | |

<details><summary>高被引方法论文</summary>


</details>

## 化学（Chemical）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| CH0100 | 重金属与微量元素 | "heavy metal" | 待查 | | |
| CH0101 | 砷 | arsenic | 待查 | | |
| CH0102 | 镉 | cadmium | 待查 | | |
| CH0103 | 铅 | "lead poisoning" | 待查 | | |
| CH0104 | 汞 | "mercury poisoning" | 待查 | | |
| CH0105 | 氟碘过量或不足 | fluorosis | 待查 | | |
| CH0201 | 黄曲霉毒素 | aflatoxin | 待查 | | |
| CH0202 | 石棉 | asbestos | 待查 | | |
| CH0203 | 苯与烃类 | benzene | 待查 | | |
| CH0300 | 有毒气体 | "toxic gas" | 待查 | | |
| CH0301 | 氨 | "ammonia leak" | 待查 | | |
| CH0302 | 一氧化碳 | "carbon monoxide" | 待查 | | |
| CH0303 | 氯气 | "chlorine leak" | 待查 | | |
| CH0400 | 窒息性气体 | asphyxiation | 待查 | | |
| CH0500 | 持久性有机污染物 | "persistent organic pollutant" | 待查 | | |
| CH0501 | 农药 | pesticide | 待查 | | |
| CH0502 | 二噁英 | dioxin | 待查 | | |
| CH0503 | 全氟烷基物质 | PFAS | 待查 | | |
| CH0504 | 微塑料 | microplastic | 待查 | | |
| CH0601 | 食品与饲料污染物 | "contaminated food" | 待查 | | |
| CH0602 | 劣质与假冒药品 | "falsified medicines" | 待查 | | |
| CH0603 | 甲醇 | "methanol poisoning" | 待查 | | |
| CH0604 | 阿片类与成瘾物质 | "opioid overdose" | 待查 | | |
| CH0605 | 海洋毒素 | "shellfish poisoning" | 待查 | | |
| CH0901 | 腐蚀性物质 | "acid attack" | 待查 | | |
| CH0902 | 硝酸铵 | "ammonium nitrate" | 待查 | | |
| CH0903 | 化学战剂 | "chemical weapon" | 待查 | | |

<details><summary>高被引方法论文</summary>


</details>

## 生物（Biological）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| BI0101 | 空气传播疾病 | influenza | 待查 | | |
| BI0102 | 血液传播病毒 | "bloodborne pathogens" | 待查 | | |
| BI0103 | 腹泻病 | diarrhoea | 待查 | | |
| BI0104 | 食源性疾病 | "food poisoning" | 待查 | | |
| BI0105 | 被忽视的热带病 | "kala azar" | 待查 | | |
| BI0106 | 性传播疾病 | "sexually transmitted" | 待查 | | |
| BI0107 | 疫苗可预防疾病 | "vaccine preventable" | 待查 | | |
| BI0108 | 媒介传播疾病 | "vector-borne disease" | 待查 | | |
| BI0109 | 病毒性出血热 | "haemorrhagic fever" | 待查 | | |
| BI0110 | 水源性疾病 | "waterborne disease" | 待查 | | |
| BI0111 | 隐孢子虫病 | cryptosporidiosis | 待查 | | |
| BI0112 | 囊尾蚴病 | cysticercosis | 待查 | | |
| BI0113 | 人畜共患病 | "zoonotic disease" | 待查 | | |
| BI0201 | 炭疽 | anthrax | 待查 | | |
| BI0202 | 布鲁氏菌病 | brucellosis | 待查 | | |
| BI0203 | 基孔肯雅热 | chikungunya | 待查 | | |
| BI0204 | 霍乱 | cholera | 待查 | | |
| BI0205 | 新冠 | COVID-19 | 待查 | | |
| BI0206 | 克里米亚-刚果出血热 | "crimean congo" | 待查 | | |
| BI0207 | 登革热 | dengue | 待查 | | |
| BI0208 | 白喉 | diphtheria | 待查 | | |
| BI0209 | 埃博拉 | ebola | 待查 | | |
| BI0210 | 产志贺毒素大肠杆菌 | "Escherichia coli outbreak" | 待查 | | |
| BI0211 | 甲肝 | "hepatitis a" | 待查 | | |
| BI0212 | 乙肝 | "hepatitis b" | 待查 | | |
| BI0213 | 丙肝 | "hepatitis c" | 待查 | | |
| BI0214 | 艾滋病 | HIV | 待查 | | |
| BI0215 | 拉沙热 | lassa | 待查 | | |
| BI0216 | 麻风 | leprosy | 待查 | | |
| BI0217 | 钩端螺旋体病 | leptospirosis | 待查 | | |
| BI0218 | 李斯特菌病 | listeriosis | 待查 | | |
| BI0219 | 疟疾 | malaria | 待查 | | |
| BI0220 | 马尔堡病毒 | marburg | 待查 | | |
| BI0221 | 麻疹 | measles | 待查 | | |
| BI0222 | 脑膜炎球菌脑膜炎 | meningitis | 待查 | | |
| BI0223 | 中东呼吸综合征 | MERS | 待查 | | |
| BI0224 | 猴痘 | mpox | 待查 | | |
| BI0225 | 副伤寒 | paratyphoid | 待查 | | |
| BI0226 | 伤寒 | typhoid | 待查 | | |
| BI0227 | 百日咳 | pertussis | 待查 | | |
| BI0228 | 鼠疫 | plague | 待查 | | |
| BI0229 | 脊髓灰质炎 | polio | 待查 | | |
| BI0230 | 朊病毒病 | prion | 待查 | | |
| BI0231 | Q 热 | "q fever" | 待查 | | |
| BI0232 | 狂犬病 | rabies | 待查 | | |
| BI0233 | 轮状病毒 | rotavirus | 待查 | | |
| BI0234 | 志贺菌病 | shigellosis | 待查 | | |
| BI0235 | 天花 | smallpox | 待查 | | |
| BI0236 | 非典（SARS） | "SARS coronavirus" | 待查 | | |
| BI0237 | 结核 | tuberculosis | 待查 | | |
| BI0238 | 锥虫病 | trypanosomiasis | 待查 | | |
| BI0239 | 水痘与带状疱疹 | chickenpox | 待查 | | |
| BI0240 | 西尼罗热 | "west nile" | 待查 | | |
| BI0241 | 黄热病 | "yellow fever" | 待查 | | |
| BI0242 | 寨卡 | zika | 待查 | | |
| BI0243 | 季节性流感 | "seasonal flu" | 待查 | | |
| BI0244 | 大流行性流感 | pandemic | 待查 | | |
| BI0245 | 禽流感 | "bird flu" | 待查 | | |
| BI0301 | 动物疫病（非人畜共患） | "livestock disease" | 待查 | | |
| BI0302 | 非洲猪瘟 | "african swine fever" | 待查 | | |
| BI0303 | 古典猪瘟 | "classical swine fever" | 待查 | | |
| BI0304 | 牛传染性胸膜肺炎 | "bovine pleuropneumonia" | 待查 | | |
| BI0305 | 山羊传染性胸膜肺炎 | "caprine pleuropneumonia" | 待查 | | |
| BI0306 | 口蹄疫 | "foot-and-mouth disease" | 待查 | | |
| BI0307 | 牛结节性皮肤病 | "lumpy skin" | 待查 | | |
| BI0308 | 新城疫 | "newcastle disease" | 待查 | | |
| BI0309 | 新大陆螺旋蝇 | screwworm | 待查 | | |
| BI0310 | 小反刍兽疫 | "peste des petits ruminants" | 待查 | | |
| BI0311 | 裂谷热 | "rift valley fever" | 待查 | | |
| BI0312 | 牛瘟 | rinderpest | 待查 | | |
| BI0313 | 牡蛎病害 | "oyster disease" | 待查 | | |
| BI0314 | 对虾急性肝胰腺坏死 | "shrimp disease" | 待查 | | |
| BI0401 | 虫害 | "pest outbreak" | 待查 | | |
| BI0402 | 蝗灾 | locust | 待查 | | |
| BI0403 | 入侵杂草与物种 | "invasive weed" | 待查 | | |
| BI0501 | 植物细菌病 | "bacterial wilt" | 待查 | | |
| BI0502 | 植物真菌病 | "rice blast" | 待查 | | |
| BI0503 | 植物病毒与类病毒病 | "plant virus" | 待查 | | |
| BI0601 | 抗微生物药物耐药 | "antimicrobial resistance" | 待查 | | |
| BI0602 | 生物战剂 | bioterror | 待查 | | |
| BI0603 | 有害藻华 | "harmful algal bloom" | 待查 | | |
| BI0604 | 人与野生动物冲突 | "human-leopard conflict" | 待查 | | |
| BI0605 | 蛇咬伤 | "snake bite" | 待查 | | |

<details><summary>高被引方法论文</summary>


</details>

## 技术（Technological）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| TL0101 | 恶意软件 | malware | 待查 | | |
| TL0102 | 数据泄露 | "data breach" | 待查 | | |
| TL0103 | 高级持续性威胁 | "advanced persistent threat" | 待查 | | |
| TL0104 | 拒绝服务攻击 | DDoS | 待查 | | |
| TL0105 | 供应链攻击 | "supply chain attack" | 待查 | | |
| TL0106 | 网络霸凌 | cyberbullying | 待查 | | |
| TL0107 | 社会工程 | phishing | 待查 | | |
| TL0201 | 建筑倒塌 | "building collapse" | 待查 | | |
| TL0202 | 高层建筑与外墙 | "high rise fire" | 待查 | | |
| TL0203 | 结构失效 | "structural failure" | 待查 | | |
| TL0204 | 桥梁垮塌 | "bridge collapse" | 待查 | | |
| TL0205 | 溃坝 | "dam collapse" | 待查 | | |
| TL0206 | 供应链中断 | "supply chain disruption" | 待查 | | |
| TL0207 | 关键基础设施失效 | "infrastructure damage" | 待查 | | |
| TL0208 | 核电站事故 | "nuclear plant accident" | 待查 | | |
| TL0209 | 停电 | "power outage" | 待查 | | |
| TL0210 | 供水中断 | "water supply interruption" | 待查 | | |
| TL0211 | 应急通信中断 | "emergency communication" | 待查 | | |
| TL0212 | 无线电与通信中断 | "telecom outage" | 待查 | | |
| TL0213 | 隧道事故 | "tunnel collapse" | 待查 | | |
| TL0214 | 排水与下水道内涝 | "sewer overflow" | 待查 | | |
| TL0215 | 水库泄洪致淹 | "reservoir release" | 待查 | | |
| TL0301 | 泄漏 | "oil spill" | 待查 | | |
| TL0302 | 污染 | "environmental pollution" | 待查 | | |
| TL0303 | 土壤污染 | "soil pollution" | 待查 | | |
| TL0304 | 爆炸 | explosion | 待查 | | |
| TL0305 | 火灾 | "fire disaster" | 待查 | | |
| TL0306 | 爆炸物 | explosives | 待查 | | |
| TL0307 | 采矿灾害 | "mine accident" | 待查 | | |
| TL0308 | 油气开采事故 | "oil rig fire" | 待查 | | |
| TL0309 | 自然灾害引发的技术事故（Natech） | "industrial accident" | 待查 | | |
| TL0401 | 航空事故 | "plane crash" | 待查 | | |
| TL0402 | 内河航运事故 | "boat capsize" | 待查 | | |
| TL0403 | 海上事故 | "maritime accident" | 待查 | | |
| TL0404 | 铁路事故 | "train accident" | 待查 | | |
| TL0405 | 道路交通事故 | "road accident" | 待查 | | |
| TL0501 | 灾害与冲突废弃物 | "disaster debris" | 待查 | | |
| TL0502 | 固体废物 | "solid waste" | 待查 | | |
| TL0503 | 废水 | wastewater | 待查 | | |
| TL0504 | 危险废物 | "hazardous waste" | 待查 | | |
| TL0505 | 塑料废物 | "plastic waste" | 待查 | | |
| TL0506 | 海洋垃圾 | "marine debris" | 待查 | | |
| TL0507 | 电子废物 | e-waste | 待查 | | |
| TL0508 | 医疗废物 | "medical waste" | 待查 | | |
| TL0509 | 填埋 | landfill | 待查 | | |
| TL0510 | 废物处理塘 | "waste lagoon" | 待查 | | |
| TL0511 | 尾矿 | tailings | 待查 | | |
| TL0601 | 放射性废物 | "radioactive waste" | 待查 | | |
| TL0602 | 放射性物质 | "radioactive contamination" | 待查 | | |
| TL0603 | 核材料 | "uranium mining" | 待查 | | |

<details><summary>高被引方法论文</summary>


</details>

## 社会（Societal）

| 编码 | 灾种 | 检索词 | 2020 年以来论文 | 专业顶刊前三（h 指数 · 该主题篇数） | 可引用数据论文 |
|---|---|---|---|---|---|
| SO0101 | 国际武装冲突 | "armed conflict" | 待查 | | |
| SO0102 | 非国际武装冲突 | insurgency | 待查 | | |
| SO0103 | 内乱 | protest | 待查 | | |
| SO0201 | 未爆弹药 | "unexploded ordnance" | 待查 | | |
| SO0202 | 冲突造成的环境破坏 | "conflict pollution" | 待查 | | |
| SO0301 | 暴力 | violence | 待查 | | |
| SO0302 | 踩踏 | "crowd crush" | 待查 | | |
| SO0303 | 自杀聚集 | suicide | 待查 | | |
| SO0401 | 金融冲击 | "financial crisis" | 待查 | | |

<details><summary>高被引方法论文</summary>


</details>

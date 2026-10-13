---
name: everest-status
description: 查询珠峰（Everest）多源监测的当前状态：数据源是否正常、哪些台站停发、冰湖与河流水位、近期地震与崩塌、坡面雷达监测进度。用户问“珠峰现在怎么样”“哪些站停发”“Imja 水位多少”时使用。只监测，不预测。
---

# 珠峰监测现状查询

## 取数顺序

1. **有 EVEREST 连接器时**（工具名以 `everest_` 开头）直接调用：
   - `everest_overview`：先看总览（数据源、停发设备、坡面进度、ADS-B）。
   - `everest_offline`：停发设备清单（附最后数据时间）。
   - `everest_water_levels`：水位站，可传 `station` 关键词（如 `Imja`、`Arun`、`Kodari`）。
   - `everest_quakes`：USGS / EMSC / 尼泊尔国家地震中心，`limit` 默认 8。
   - `everest_facets`：坡面监测基线进度或分级。
   - `everest_source`：某个源的原始 JSON（evn、bipad、emsc、gibs、ioda、usgs、alerts、nsc、gdacs、doris、adsb）。
   - `everest_station_history`：单站水位序列；`everest_alerts`：灾害警报；`everest_connectivity`：当地网络连通；
     `everest_satellite_tracking`：DORIS 信标跟踪；`everest_air_traffic`：ADS-B；`everest_imagery`：最新云图链接；`everest_daily_brief`：日报。
2. **没有连接器时**：读公开快照
   `https://raw.githubusercontent.com/Yizebaba/everest-insar-pipeline/facet-live/rt.json`（每小时更新）和同分支的 `facet_status.json`。
   停发判定：水位站超过 6 小时无数据；IO.EVN 最近 20 分钟完整度为 0；DORIS 12 小时内没被跟踪。

## 回答规则

- 时间一律换成北京时间（UTC+8），并写明数据汇总时间。
- **只监测、不预测**：不说“会不会溃决/崩塌”，不给风险等级或概率。
- 停报不等于正常；外部设备（尼泊尔水文局水位站、IO.EVN、DORIS）不归本平台维修，只报告状态。
- “USGS landslide”是地震台网测到的大型崩塌，不是构造地震。
- ADS-B 显示 0 架时说明：可能是附近没有接收站，不等于没有飞机。
- 每条数字附来源（BIPAD、GEOFON、USGS、EMSC、IODA、GDACS、IGN/IDS）。

## 相关页面

- 总览：https://claude.ai/artifact/6heopu2wizEAFMJJLDs44H（“运行状态”“设备维护”标签）
- 实时采集页：https://everest-facets.yizebaba.workers.dev/rt

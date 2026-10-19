---
name: everest-lake-watch
description: 冰湖与河流水位查看：Imja、Tsho Rolpa 冰湖出口和 Dudh Koshi、Arun、Bhote Koshi 等河流水位站的最新水位、警戒/危险线、近几小时变化和是否停报。用户问“Imja 水位多少”“冰湖水位有没有变化”“哪个站停报了”时使用。
---

# 冰湖与河流水位

## 取数

1. `everest_water_levels`：全部站或按 `station` 关键词过滤，先看最新值、警戒/危险线、是否在报。
2. `everest_station_history`：用户关心的站拉序列（`hours` 默认 24，最多 72），给出最高、最低、变化量。
3. 有站停报时，调 `everest_connectivity` 看当地是否断网，作为可能原因之一写出来（只写“可能”，不下结论）。

## 写法

- 表格：站名、最新水位（m）、警戒线、危险线、24 小时变化、状态（在报/停报）、最后数据时间（北京时间）。
- 门户状态（ABOVE WARNING / DANGER LEVEL）照原样转述，并注明“来自尼泊尔水文气象局门户”；对已停报的站要说明这个状态可能是旧的或设备故障造成的。
- 监测回答不判断会不会涨水或溃决；需要推演时用 MiroFish，并标注为推演。

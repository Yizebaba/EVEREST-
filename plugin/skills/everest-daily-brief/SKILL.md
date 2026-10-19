---
name: everest-daily-brief
description: 生成珠峰监测日报：数据源状态、停发设备、近 24 小时地震与崩塌、灾害警报、水位越线、通信连通、DORIS 跟踪、坡面进度。用户说“出个日报”“今天珠峰情况汇总”“给我一份监测简报”时使用。监测与推演分开。
---

# 珠峰监测日报

## 取数

1. 调用 `everest_daily_brief`（`hours` 默认 24；用户说“最近三天”就传 72）。
2. 日报里有停发设备或越线水位站时，再调 `everest_station_history` 看那几个站的序列，写清最后数据时间。
3. 有地震或崩塌时，调 `everest_quakes` 补全震级、位置和来源。
4. 没有连接器时，读 `https://raw.githubusercontent.com/Yizebaba/EVEREST-/facet-live/rt.json` 自己汇总。

## 格式

- 标题写“EVEREST 监测日报 · 日期（北京时间）”，第一行写数据截至时间。
- 分八段：数据源、停发设备、地震与崩塌、灾害警报、水位、通信、DORIS 信标、坡面雷达。没有内容的段写“无”，不要删段。
- 每个数字附来源（BIPAD、GEOFON、USGS、EMSC、NSC、IODA、IDS/DORIS、GDACS）。
- 结尾固定一句：监测与推演分开；停报不等于正常；外部设备不归本平台维修。

## 不能做

- 不写“可能溃决”“风险升高”之类的判断，不给概率。
- 不加天气预报。

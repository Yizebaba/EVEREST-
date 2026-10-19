---
name: everest-maintenance
description: 查看和登记 EVEREST 设备维护：设备台账、维修与保养记录、保养到期、停发设备。用户说“记一条维修”“哪些设备快到保养期”“新增一台设备”“设备维护提醒”时使用。
---

# 设备维护

数据在 EVEREST 总览页的共享数据库里（总览“设备维护”标签显示同一份数据）：
`https://claude.ai/artifact/6heopu2wizEAFMJJLDs44H`，用 ArtifactData 工具读写。

## 数据结构

| 集合 | 内容 | 谁能写 |
|---|---|---|
| `mt_assets/<id>` | 设备：name, site, type, owner（自有/外部）, status（正常/故障/维修中/停用）, intervalDays, lastServiced（YYYY-MM-DD）, monitorKey, model, serial, location, notes | 参与者及以上 |
| `mt_logs/<id>` | 记录：assetId, date, kind（巡检/保养/维修/故障/校准/更换部件/其他）, summary, parts, hours, cost, statusAfter | 参与者及以上 |
| `mt_monitor/latest` | 外部台站在线状态（每小时自动写） | 仅所有者 |
| `mt_reminder/last` | 每日 08:53 提醒的结果 | 仅所有者 |
| `mt_settings/main` | leadDays：提前提醒天数（默认 14） | 参与者及以上 |

## 常用操作

- **到期判断**：下次到期 = lastServiced + intervalDays；已过期为“逾期”，leadDays 天内为“即将到期”；状态“停用”的不提醒。
- **记一条维修**：`mt_logs` 新建文档（随机 id）；如果是保养/维修且日期晚于 lastServiced，同时更新该设备的 `lastServiced`；有“处理后状态”时更新 `status`。
- **新增设备**：`mt_assets` 新建文档，至少有 name、site；外部设备 owner 填“外部”。
- 写之前先 `get` 拿 version，写时带 `if_version`；不要覆盖别人刚改的内容。

## 规则

- 外部设备（尼泊尔水文局水位站、IO.EVN、DORIS）只报告停发，不归本平台维修。
- 删除设备前先跟用户确认；已有记录保留。
- 监测与推演分开。

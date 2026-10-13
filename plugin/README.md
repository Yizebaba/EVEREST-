# EVEREST 插件

一个包里装了两样：

- **连接器** `everest`（MCP，HTTP）：`https://everest-facets.yizebaba.workers.dev/mcp`，14 个只读工具：
  `everest_overview`、`everest_offline`、`everest_water_levels`、`everest_station_history`、`everest_quakes`、`everest_alerts`、
  `everest_connectivity`、`everest_satellite_tracking`、`everest_air_traffic`、`everest_imagery`、`everest_facets`、`everest_source`、
  `everest_snapshot`、`everest_daily_brief`。
- **技能**：`everest-status`（现状查询）、`everest-daily-brief`（日报）、`everest-quake-brief`（地震简报）、`everest-lake-watch`（冰湖水位）、
  `everest-comms-check`（停发排查）、`everest-evidence-pack`（事件证据包）、`everest-maintenance`（设备维护）、`everest-hub-change`（改总览流程）。

## 安装

- **Claude 网页 / 桌面**：设置 → 连接器 → 添加自定义连接器，名称 `EVEREST`，地址填上面的 URL；技能在设置 → 技能里上传各 `SKILL.md` 所在文件夹。
- **Claude Code**：
  ```
  /plugin marketplace add Yizebaba/everest-insar-pipeline
  /plugin install everest@everest
  ```

总览页的“技能”“连接器”“插件”三个标签里有同样的内容：能直接调用连接器、运行技能，也能新建自己的技能、自选技能打包成插件下载。

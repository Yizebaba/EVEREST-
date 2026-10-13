# EVEREST 插件

一个包里装了两样：

- **连接器** `everest`（MCP，HTTP）：`https://everest-facets.yizebaba.workers.dev/mcp`，只读工具
  `everest_overview`、`everest_offline`、`everest_water_levels`、`everest_quakes`、`everest_facets`、`everest_source`。
- **技能**：`everest-status`（现状查询）、`everest-evidence-pack`（事件证据包）、`everest-maintenance`（设备维护）、`everest-hub-change`（改总览流程）。

## 安装

- **Claude 网页 / 桌面**：设置 → 连接器 → 添加自定义连接器，名称 `EVEREST`，地址填上面的 URL；技能在设置 → 技能里上传各 `SKILL.md` 所在文件夹。
- **Claude Code**：
  ```
  /plugin marketplace add Yizebaba/everest-insar-pipeline
  /plugin install everest@everest
  ```

总览页“扩展”标签里有同样的内容，并能直接调用连接器和运行技能。

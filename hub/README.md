# 总览页（EVEREST Hub）

线上：https://claude.ai/artifact/6heopu2wizEAFMJJLDs44H

- `everest-hub.html`：当前线上版本的源文件（单文件，数据在发布时嵌入，登录后每小时从数据库自动更新）。
- `capabilities.json`：发布时的能力声明（数据库 30 条规则、mcp 连接器、sample）。改能力时整份带上，只增不减。
- `RESTORE.md`：每次改动的说明和复原方法。更早的页面版本在 Artifact 的历史版本里。
- `test/`：自检脚本 `check.py` 和模拟数据库（`mockdb.js`、`mockext.js`）。

修改流程见 `plugin/skills/everest-hub-change/SKILL.md`。

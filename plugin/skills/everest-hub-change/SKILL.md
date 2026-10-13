---
name: everest-hub-change
description: 修改并发布 EVEREST 总览页（claude.ai 上的珠峰监测总览）时的固定流程：先备份、再修改、浏览器自检、写复原记录、发布。用户要求改总览页、加标签、改文字或翻译时使用。
---

# 改总览页的流程

总览页：`https://claude.ai/artifact/6heopu2wizEAFMJJLDs44H`，源文件在仓库 `hub/everest-hub.html`。

## 必须遵守

1. **可复原**：改之前把当前线上版本存一份（`hub/backup/` 或 Artifact 的历史版本），改完在 `hub/RESTORE.md` 加一条：改了什么、线上版本号、怎么回退（回退到哪个版本号或重新发布哪个备份）。
2. **只监测、不预测**：页面上不出现预测、风险概率、预警发布字样。
3. **不碰天气**：不加天气预报类内容。
4. **秘钥不进聊天、不进页面**：凭证只放在 Cloudflare / GitHub 的机密里。
5. **重计算不放 GitHub**：大的计算放在外部（openEO、Planetary Computer、Cloudflare）；GitHub 只跑小任务。
6. **数据库规则**：发布时如果要改 `capabilities`，必须带上全部现有规则（见 `hub/capabilities.json`），只增不减。

## 步骤

1. 用 Artifact `read` 取线上最新版本，和 `hub/everest-hub.html` 对比；有差异以线上为准。
2. 修改：用脚本做精确替换（每处替换先断言只出现一次），不要整页重写。
3. 自检：语法检查所有 `<script>`；用 Playwright 打开（用假 THREE 和模拟数据库），确认标签、关键面板、弹窗正常，无报错；切英文检查没有中英混杂。
4. 翻译：新加的中文界面文字同时加英文（短词放 EXS 整句表，长句放 DSTR）。
5. 发布到同一个 URL；把新文件提交回仓库 `hub/`，写 RESTORE 记录。
6. 回复用户：一句话说改了什么、线上版本号、怎么回退。

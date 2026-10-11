# 珠峰冰坡雷达亮度监测（Cloudflare Worker）

在 Cloudflare 上运行，不用 GitHub 的定时任务。计算在外部完成：
- **微软 Planetary Computer Data API**：对每个坡面求 Sentinel-1 RTC（γ0 VV，地形校正）的平均值。匿名访问，不需要账号。
- **Cloudflare D1**：存历史数据，并用 SQL 算同季气候态、z 值和 3 景连续最反常值。

Worker 本身只负责调度、记账和对外发布结果。

方法照搬 OCHA-DAP `exploratory/0005-nepal-glof-sar-precursor`（MIT 许可），坡面边界取自它的 `himalaya-facet-watch`（珠峰周围 376 个）。
只做监测：分级表示“和自己历年同季相比有多反常”，不预测，也不是预警。

## 运行方式
- 每分钟触发一次（cron `* * * * *`，UTC）。每次最多向微软发 40 个请求（免费版每次上限 50 个子请求）。
- 新影像优先处理：降轨过境后约 2 小时，微软处理完成；之后约 10 分钟内，这一景的 376 个坡面全部算完，接着重新打分。
- 首次运行会回填 2020 年以来的降轨影像，作为历史基线。约 9.4 万次请求，按每分钟 40 次算约 1.6 天。D1 免费版每天 10 万行写入是瓶颈，实际约 3–4 天建完。超额后当天停止写入，UTC 零点自动继续。基线建成前，页面显示进度，不出分级。

## 接口
- `/` 实时页面（坡面地图 + 非平静坡面列表）
- `/api/live.json` 全部结果（分级、最近 90 天统计值、历史分位、各年同季统计值、最新一景 z 值）
- `/api/status.json` 回填和打分进度

## 配置（wrangler.toml）
- `database_id`：填 Cloudflare 后台创建的 D1 数据库 ID。
- 可选：在 Worker 的 Settings → Variables and Secrets 里加一个**密钥** `GH_TOKEN`。用 GitHub 细粒度令牌，只授权本仓库，权限 Contents: Read and write。配好后，结果会写到本仓库的 `facet-live` 分支，供平台页面接入。

## 本地测试（模拟数据，不访问外网）
```
npm install
node test/mock.mjs &
cp test/dev.vars.example test/.dev.vars   # PC_STAC/PC_DATA 指向模拟服务，FACET_LIMIT=60，ALLOW_MANUAL_TICK=1
npx wrangler dev -c test/wrangler.test.toml --port 8799 --local
curl localhost:8799/__tick    # 手动触发一次
```

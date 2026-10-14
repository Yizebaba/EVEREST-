# 证据链：顶刊顶会里的思路、方法和现成工具

这份文档回答三个问题：学术界和业界怎么做“可信的证据链”；哪些已经有成熟工具；EVEREST 借了什么、还可以借什么。
每条都给出处，能点开核对。各灾种的专业期刊和可引用数据见 [`HAZARD_VENUES.md`](HAZARD_VENUES.md)。

## 一、四条主线

| 主线 | 核心问题 | 代表性工作（顶刊顶会 / 标准） | 成熟工具 | EVEREST 现状 |
|---|---|---|---|---|
| **1. 时间戳与防篡改** | 证明“这份文件最晚在某时刻已存在、之后没改过” | Haber & Stornetta, *J. Cryptology* 1991（链式时间戳）；Crosby & Wallach, **USENIX Security 2009**（防篡改日志）；IETF **RFC 3161**（可信时间戳协议）；RFC 6962 证书透明（Certificate Transparency） | OpenTimestamps；RFC 3161 时间戳机构（FreeTSA、DigiCert）；Trillian / Tessera 透明日志（transparency.dev） | ✅ OpenTimestamps（比特币）+ ✅ RFC 3161 双机构（v17）+ ✅ Sigstore Rekor 透明日志（v19） |
| **2. 来源与派生（provenance）** | 每条记录从哪来、谁发布、经过什么处理变成结论 | **W3C PROV-O / PROV-DM**（2013 推荐标准）；**RO-Crate**（Soiland-Reyes et al., *Data Science* 2022, arXiv 2108.06503）；Workflow Run Crate（arXiv 2312.07852） | `prov`（Python）、`rocrate`（Python）、ro-crate-validator | ✅ 每个证据包导出 PROV-JSON + RO-Crate（v17 新增，已用两个库校验） |
| **3. 数字取证与监管链（chain of custody）** | 证据从采集到出庭，经手人和状态可追溯 | **DFRWS** 会议 + *Forensic Science International: Digital Investigation*；**CASE / UCO** 本体（Linux Foundation 项目，DFRWS 发表）；B-CoC（区块链监管链，arXiv 1807.10359）；**Berkeley Protocol**（OHCHR + 伯克利人权中心，2020/2022，公开来源数字调查规程） | CASE 导出工具（case-utils）；Sigstore（**ACM CCS 2022**）和 in-toto（**USENIX Security 2019**）做软件供应链签名，可借来签“证据包是哪段代码生成的” | ✅ Sigstore 无密钥签名（v19 新增，签名记入 Rekor 透明日志）；人工证据有指纹、提交时间、采信状态；未导出 CASE |
| **4. 现场媒体可信度** | 手机拍的照片/视频是不是现场、有没有被改 | **C2PA** 内容凭证（Adobe、微软、BBC 等发起）；ProofMode（Guardian Project，SHA-256 + PGP 旁路证明）；Starling Lab（斯坦福 + USC Shoah 基金会，2022 年向国际刑事法院提交的数字档案） | c2patool、ProofMode App | ✅ 总览页上传时读 C2PA 标记和 EXIF 拍摄时间，记进人工证据 |

国内司法实践：最高人民法院《关于互联网法院审理案件若干问题的规定》（2018）第十一条认可电子数据经区块链、可信时间戳等技术核验后的证明力；杭州互联网法院 2018 年起用司法区块链，腾讯至信链、蚂蚁链等都接入过司法存证。这些是“机构背书的存证”，EVEREST 用的是不依赖单一机构的公开时间戳（比特币 + 两家 RFC 3161 机构），任何人可独立核对。

## 二、灾害研究里的“证据链”方法

| 方法 | 出处 | 思路 | 和 EVEREST 的对应 |
|---|---|---|---|
| **FORIN 法证式灾害调查** | IRDR（国际科学理事会“灾害风险综合研究”计划）FORIN 报告 2016 | 四种做法：比较研究、回溯性纵向研究、前瞻性纵向研究、荟萃分析；强调把多来源记录对齐到时间线后找“哪里断了” | 证据包时间线 + “支持 / 缺失 / 矛盾”判定，就是回溯性纵向对齐 |
| **CEDIM 法证灾害分析（FDA）** | 德国卡尔斯鲁厄理工学院 CEDIM | 灾后几小时到几天内，把卫星、社交媒体、台站、新闻实时汇总成事件报告 | 事件自动发现 + 证据包每次更新都存证 |
| **多源重建一场灾害** | Shugar et al., *Science* 2021（印度 Chamoli 岩冰崩，53 位作者）；Sattar et al., *Science* 2025（锡金冰湖溃决级联，doi:10.1126/science.ads2659） | 卫星影像前后对比 + 地震台记录发生时刻 + 水文站 + 目击视频 + 数值模型互相印证 | 证据包已有：两台地震对比、Sentinel-1/2 前后景、水位站在报/停报、人工上传视频。**不做模型**（只监测） |
| **地震台测滑坡** | Ekström & Stark, *Science* 2013 | 大型滑坡会在长周期地震记录里留下特征信号，可以反推发生时间 | 证据包画两台站 1–5 Hz 信号图，标出异常时刻 |
| **危机信息学** | ISCRAM 会议、*CSCW* | 社交媒体、众包信息的可信度评估和人工核实流程 | 人工证据“待核实 → 已采信”流程；新闻要两家以上媒体 |

## 三、EVEREST 借了什么（已上线）

1. **双重时间戳**：OpenTimestamps（比特币，去中心化，数小时后确认）+ RFC 3161（FreeTSA、DigiCert，几秒返回，有法律实践）。一种失效另一种还在。
2. **PROV-JSON**：每条时间线记录是一个实体，归属到发布它的来源，证据包由它们派生。别人可以用任何 PROV 工具读。
3. **RO-Crate**：每个证据包一个 `ro-crate-metadata.json`，列出文件、来源、地点、时间、生成代码。可直接上传 Zenodo / WorkflowHub。
4. **“谁没记录到”同等重要**：FORIN 的回溯思路，缺失和矛盾都写进时间线。
5. **C2PA / EXIF**：人工上传的照片视频先查内容凭证和拍摄时间。
6. **Sigstore 签名 + Rekor 透明日志**（v19）：每个快照用 GitHub Actions 身份无密钥签名，证明是本仓库工作流生成的；签名追加进公开日志，事后删改会被发现。
7. **同行评审过的历史数据库**（v19）：高山亚洲冰湖溃决数据库（Steiner & Shrestha，ESSD 2023），每次现取开发版、记提交号；只用作者确认过的条目。

### 自己核对 RFC 3161 时间戳

```bash
# 从 events 分支 events/archive/ 下载快照和同名 .FreeTSA.tsr
curl -sO https://freetsa.org/files/cacert.pem
curl -sO https://freetsa.org/files/tsa.crt
openssl ts -verify -in <快照>.json.FreeTSA.tsr -data <快照>.json -CAfile cacert.pem -untrusted tsa.crt
# 输出 Verification: OK 即通过
```

## 四、还可以借的（未做，按价值排序）

| 做法 | 价值 | 代价 | 建议 |
|---|---|---|---|
| **Zenodo 存档拿 DOI**（RO-Crate 直接上传） | 证据包可被论文引用，有永久标识 | 需要 Zenodo 令牌；每个事件一个 DOI | 值得做：重大事件手动或自动存档 |
| **CASE / UCO 导出** | 数字取证工具链（法庭用）能直接读 | 本体复杂 | 有司法用途需求时再做 |
| **Berkeley Protocol 对照表** | 公开来源调查的国际规程：采集、保存、核实、分析各步骤 | 写文档，不改代码 | 可以做一张对照表放这里 |

## 出处

- W3C PROV-O：<https://www.w3.org/TR/prov-o/>
- RO-Crate：<https://www.researchobject.org/ro-crate/>；arXiv 2108.06503；Workflow Run Crate arXiv 2312.07852
- Crosby & Wallach 2009：<https://www.usenix.org/legacy/event/sec09/tech/full_papers/crosby.pdf>
- RFC 3161：<https://www.rfc-editor.org/rfc/rfc3161>；RFC 6962：<https://www.rfc-editor.org/rfc/rfc6962>
- OpenTimestamps：<https://opentimestamps.org/>；FreeTSA：<https://freetsa.org/>
- transparency.dev（Trillian / Tessera）：<https://transparency.dev/>
- Sigstore（CCS 2022）：<https://dl.acm.org/doi/10.1145/3548606.3560596>；in-toto：<https://in-toto.io/>
- CASE：<https://caseontology.org/>
- Berkeley Protocol：<https://www.ohchr.org/en/publications/policy-and-methodological-publications/berkeley-protocol-digital-open-source>
- C2PA：<https://c2pa.org/>；ProofMode：<https://proofmode.org/>；Starling Lab：<https://www.starlinglab.org/>
- IRDR FORIN：<https://irdrinternational.org/knowledge_pool/publications/50>
- CEDIM FDA：<https://www.iip.kit.edu/english/1698.php>
- Shugar et al. 2021（A massive rock and ice avalanche caused the 2021 disaster at Chamoli）：<https://pubs.usgs.gov/publication/70221399>
- Sattar et al. 2025：doi:10.1126/science.ads2659
- Ekström & Stark 2013，*Science* 339:1416（Simple scaling of catastrophic landslide dynamics）
- ISCRAM：<https://iscram.org/>

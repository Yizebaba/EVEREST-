---
name: everest-verify
description: 核对 EVEREST 某个事件证据包的存证：快照哈希、OpenTimestamps（比特币）、RFC 3161 可信时间戳、Sigstore 签名、取数回执和平台自己的 9 项独立核对结果。用户问“这份证据包可信吗”“怎么证明没被改过”“帮我核对存证”时使用。
---

# 核对证据包存证

## 取数

1. 事件目录 `https://raw.githubusercontent.com/Yizebaba/EVEREST-/events/index.json`：`events.<编号>.ots` 列表最后一项是最新快照，含
   `file`（快照）、`sha256`、`ots`（.ots 证明）、`status`（pending / confirmed，confirmed 时有 `bitcoin_block`）、
   `tsa`（RFC 3161：FreeTSA、DigiCert 的 .tsr 文件）、`sigstore`（bundle 文件、Rekor 日志编号）、`verify`（9 项独立核对结果）。
2. 证据包本身 `events/<编号>.json`：`receipts` 是取数回执（时间、网址、返回内容 SHA-256；小文本原文在 `events/raw/<哈希>.gz`），`bounds` 是推断边界。

## 让用户自己核对（给出命令，不替用户声称“已核对”，除非真的跑过）

```bash
sha256sum 快照.json                                   # 和 index.json 里的 sha256 比
pip install opentimestamps-client && ots verify 快照.json.ots
curl -sO https://freetsa.org/files/cacert.pem && curl -sO https://freetsa.org/files/tsa.crt
openssl ts -verify -in 快照.json.FreeTSA.tsr -data 快照.json -CAfile cacert.pem -untrusted tsa.crt
cosign verify-blob 快照.json --bundle 快照.json.sigstore.json \
  --certificate-identity https://github.com/Yizebaba/EVEREST-/.github/workflows/evidence.yml@refs/heads/events \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

## 规则

- 存证只证明“这份文件最晚在那个时间已经存在、之后没改过”，不证明内容正确；内容的边界看证据包里的 `bounds`。
- `status: pending` 说明比特币确认还没完成（通常几小时），不是失败。
- 平台的 `verify` 结果是平台自己跑的；用户要独立结论就让他自己跑上面的命令。

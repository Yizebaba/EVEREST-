"""跨实现核对：每个新存证快照，用几套互不相干的工具各核对一遍，结果写回 index.json（ots[-1]["verify"]）。
在 evidence 工作流里、证据包生成之后运行（events 分支根目录）。只核对本次新加的快照（还没有 verify 字段的）。

  sha256        Python hashlib 和系统 sha256sum 各算一遍，和登记的哈希比
  rfc3161       openssl ts -verify（FreeTSA 用它自己的根证书，DigiCert 用系统证书库）
  sigstore      cosign verify-blob 和 sigstore-python 两套实现，都要求签名身份是本仓库 evidence.yml
  ots           OpenTimestamps 客户端 ots info 能解析，且证明里的哈希就是快照的哈希
  prov          W3C PROV-JSON 用 prov 库读一遍
  rocrate       RO-Crate 用 rocrate 库读一遍
"""
import hashlib, json, os, re, subprocess, sys, urllib.request

IDX = "index.json"
ID = "https://github.com/Yizebaba/EVEREST-/.github/workflows/evidence.yml@refs/heads/events"
ISS = "https://token.actions.githubusercontent.com"


def sh(*a, timeout=120):
    r = subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + "\n" + r.stderr


def fetch(url, path):
    if not os.path.exists(path):
        with urllib.request.urlopen(url, timeout=30) as r: open(path, "wb").write(r.read())
    return path


def check(eid, st):
    f = st["file"]; out = {}
    if not os.path.exists(f): return {"file": "missing"}
    b = open(f, "rb").read()
    out["sha256_python"] = hashlib.sha256(b).hexdigest() == st["sha256"]
    c, o = sh("sha256sum", f); out["sha256_coreutils"] = c == 0 and o.split()[0] == st["sha256"]
    for t in st.get("tsa") or []:
        if not t.get("file") or not os.path.exists(t["file"]): continue
        if t["tsa"] == "FreeTSA":
            try:
                ca = fetch("https://freetsa.org/files/cacert.pem", "/tmp/freetsa_ca.pem"); crt = fetch("https://freetsa.org/files/tsa.crt", "/tmp/freetsa_tsa.crt")
                c, o = sh("openssl", "ts", "-verify", "-in", t["file"], "-data", f, "-CAfile", ca, "-untrusted", crt)
            except Exception as e: c, o = 1, str(e)
        else:
            c, o = sh("openssl", "ts", "-verify", "-in", t["file"], "-data", f, "-CAfile", "/etc/ssl/certs/ca-certificates.crt")
        out["rfc3161_" + t["tsa"]] = c == 0 and "Verification: OK" in o
        if not out["rfc3161_" + t["tsa"]]: out.setdefault("_why", {})["rfc3161_" + t["tsa"]] = o.strip()[-200:]
    sg = (st.get("sigstore") or {}).get("file")
    if sg and os.path.exists(sg):
        c, o = sh("cosign", "verify-blob", f, "--bundle", sg, "--certificate-identity", ID, "--certificate-oidc-issuer", ISS)
        out["sigstore_cosign"] = c == 0
        if c: out.setdefault("_why", {})["sigstore_cosign"] = o.strip()[-200:]
        c, o = sh(sys.executable, "-m", "sigstore", "verify", "identity", "--bundle", sg, "--cert-identity", ID, "--cert-oidc-issuer", ISS, f)
        out["sigstore_python"] = c == 0
        if c: out.setdefault("_why", {})["sigstore_python"] = o.strip()[-200:]
    if st.get("ots") and os.path.exists(st["ots"]):
        c, o = sh("ots", "info", st["ots"])
        m = re.search(r"File sha256 hash: ([0-9a-f]{64})", o)
        out["ots_parse"] = c == 0 and bool(m) and m.group(1) == st["sha256"]
        if not out["ots_parse"]: out.setdefault("_why", {})["ots_parse"] = o.strip()[:200]
    pj = os.path.join("events", eid + ".prov.json")
    if os.path.exists(pj):
        try:
            import prov.model as pm
            pm.ProvDocument.deserialize(pj, format="json"); out["prov"] = True
        except Exception: out["prov"] = False
    cd = os.path.join("events", "crates", eid)
    if os.path.exists(os.path.join(cd, "ro-crate-metadata.json")):
        try:
            from rocrate.rocrate import ROCrate
            ROCrate(cd); out["rocrate"] = True
        except Exception: out["rocrate"] = False
    return out


def main():
    idx = json.load(open(IDX)); n = 0
    items = list(idx.get("events", {}).items()) + ([("manual", idx["manual"])] if idx.get("manual") else [])
    for eid, e in items:
        for st in (e.get("ots") or [])[-1:]:
            if "verify" in st and not st["verify"].get("failed"): continue   # 已全部通过的不再核；有失败的每次重核
            v = check(eid, st); why = v.pop("_why", {})
            ok = [k for k, x in v.items() if x is True]; bad = [k for k, x in v.items() if x is not True]
            st["verify"] = {"checks": v, "passed": len(ok), "total": len(v), "failed": bad, "why": why, "at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime())}
            n += 1; print(eid, f"{len(ok)}/{len(v)}", "失败：" + "、".join(bad) if bad else "全部通过", flush=True)
    json.dump(idx, open(IDX, "w"), ensure_ascii=False, indent=1)
    print("核对了", n, "个新快照")


if __name__ == "__main__":
    main()

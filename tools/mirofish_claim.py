"""推演工作流的输入和密钥。
- 网页提交的任务（IN_JOB）：用 GitHub OIDC 身份向 Worker 领取推演要求和提交者自己的密钥（领取后 Worker 立刻删除密钥），日志里打码。
- 仓库主人手动运行：用 Actions 表单和仓库 Secrets。
结果写进 $GITHUB_ENV：MF_REQUIREMENT、MF_TITLE_IN、MF_RID、MF_PROJECT、MF_SCOPE、MF_ROUNDS、MF_JOB、LLM_API_KEY、LLM_BASE_URL、LLM_MODEL_NAME、ZEP_API_KEY。
用法：python3 tools/mirofish_claim.py            （领取 / 读表单）
      python3 tools/mirofish_claim.py done <目录>  （任务结束，回报 Worker）
"""
import json, os, secrets, sys, urllib.request

W = "https://everest-facets.yizebaba.workers.dev"
E = os.environ.get


def oidc():
    r = urllib.request.Request(E("ACTIONS_ID_TOKEN_REQUEST_URL") + "&audience=everest-mf", headers={"authorization": "Bearer " + E("ACTIONS_ID_TOKEN_REQUEST_TOKEN")})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())["value"]


def post(path, body):
    r = urllib.request.Request(W + path, data=json.dumps(body).encode(), headers={"content-type": "application/json", "authorization": "Bearer " + oidc(), "user-agent": "EVEREST-mirofish"})
    return json.loads(urllib.request.urlopen(r, timeout=60).read())


if len(sys.argv) > 2 and sys.argv[1] == "done":
    st = {}
    try: st = json.load(open("mf_out/status.json"))
    except Exception: pass
    err = st.get("error") or st.get("upstream_hint") or ("" if st.get("ok") else "没有完成")
    print(post("/mf/done", {"id": E("MF_JOB"), "dir": sys.argv[2], "ok": bool(st.get("ok")), "error": err}))
    sys.exit(0)

job = (E("IN_JOB") or "").strip()
if job:
    j = post("/mf/claim", {"id": job})
    for k in ("llm_key", "zep_key"):
        if j.get(k): print("::add-mask::" + j[k])
    v = {"MF_JOB": job, "MF_RID": job, "MF_REQUIREMENT": j["requirement"], "MF_TITLE_IN": j.get("title") or "", "MF_PROJECT": j.get("project") or "bri",
         "MF_SCOPE": j.get("scope") or "", "MF_ROUNDS": str(j.get("rounds") or 0),
         "LLM_API_KEY": j["llm_key"], "LLM_BASE_URL": j["llm_base"], "LLM_MODEL_NAME": j["llm_model"], "ZEP_API_KEY": j["zep_key"]}
    print("任务", job, "已领取：", v["MF_PROJECT"], v["MF_SCOPE"], v["LLM_BASE_URL"], v["LLM_MODEL_NAME"])
    import base64
    os.makedirs("mf_upload", exist_ok=True)
    for nm in j.get("files") or []:   # 使用者上传的文件
        f = post("/mf/file", {"id": job, "name": nm})
        safe = "upload_" + os.path.basename(nm).replace(" ", "_")
        open(os.path.join("mf_upload", safe), "wb").write(base64.b64decode(f["data"]))
        print("上传文件：", safe, os.path.getsize(os.path.join("mf_upload", safe)), "字节")
else:
    v = {"MF_JOB": "", "MF_RID": E("IN_RID") or "", "MF_REQUIREMENT": E("IN_REQ") or "", "MF_TITLE_IN": E("IN_TITLE") or "", "MF_PROJECT": E("IN_PROJECT") or "everest",
         "MF_SCOPE": E("IN_SCOPE") or "", "MF_ROUNDS": E("IN_ROUNDS") or "0",
         "LLM_API_KEY": E("S_LLM_API_KEY") or "", "LLM_BASE_URL": E("S_LLM_BASE_URL") or "", "LLM_MODEL_NAME": E("S_LLM_MODEL_NAME") or "", "ZEP_API_KEY": E("S_ZEP_API_KEY") or ""}
miss = [k for k in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL_NAME", "ZEP_API_KEY") if not v[k]]
for k in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL_NAME", "ZEP_API_KEY"): print(k + ":", "set" if v[k] else "missing")
os.makedirs("mf_out", exist_ok=True)
json.dump({"missing": " ".join(miss), "job": job}, open("mf_out/secrets_check.json", "w"))
if miss: v["MISSING"] = "1"
with open(E("GITHUB_ENV"), "a") as f:
    for k, x in v.items():
        d = "EOF_" + secrets.token_hex(8)
        f.write(f"{k}<<{d}\n{x}\n{d}\n")

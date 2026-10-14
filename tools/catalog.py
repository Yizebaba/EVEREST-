"""外部工具库目录：把 Claude 官方的技能库、插件市场和 MCP 官方注册表里的条目抓下来，供总览页“技能 / 插件 / 连接器”的“外部库”显示和安装。
随灾种扫描每小时运行一次（GitHub Actions），只读公开接口，不安装任何东西。

来源（都是公开的）：
  技能  anthropics/skills（GitHub）          skills/<名称>/SKILL.md 的 name、description
  插件  anthropics/claude-plugins-official   .claude-plugin/marketplace.json（Claude Code 官方插件市场）
        anthropics/knowledge-work-plugins     .claude-plugin/marketplace.json（Claude 知识工作插件）
  连接器 MCP 官方注册表 registry.modelcontextprotocol.io（按与本平台相关的关键词检索）
输出：<out>/catalog.json
"""
import json, os, re, sys, time, urllib.parse, urllib.request

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
TOK = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
LOG = []


def get(url, gh=False):
    h = {"user-agent": "EVEREST-catalog/1.0", "accept": "application/json"}
    if gh and TOK: h["authorization"] = "Bearer " + TOK
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
        return r.read().decode("utf-8", "ignore")


def front(md):
    m = re.match(r"^---\s*\n(.*?)\n---", md, re.S); d = {}
    if not m: return d
    cur = None
    for ln in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z_-]+):\s*(.*)$", ln)
        if k: cur = k.group(1); d[cur] = k.group(2).strip().strip('"').strip("'")
        elif cur and ln.startswith((" ", "\t")): d[cur] = (d[cur] + " " + ln.strip()).strip()
    return d


def skills():
    out = []
    tree = json.loads(get("https://api.github.com/repos/anthropics/skills/git/trees/main?recursive=1", gh=True))
    paths = sorted(t["path"] for t in tree.get("tree", []) if t["path"].endswith("/SKILL.md"))
    for p in paths[:80]:
        try:
            fm = front(get("https://raw.githubusercontent.com/anthropics/skills/main/" + urllib.parse.quote(p)))
            d = os.path.dirname(p)
            out.append({"name": fm.get("name") or os.path.basename(d), "desc": (fm.get("description") or "")[:400],
                        "license": fm.get("license") or "", "src": "anthropics/skills",
                        "url": "https://github.com/anthropics/skills/tree/main/" + d, "raw": "https://raw.githubusercontent.com/anthropics/skills/main/" + p})
        except Exception as e: LOG.append(f"skill {p}: {e}")
    return out


def plugins():
    out = []
    for repo, label, mk in (("anthropics/claude-plugins-official", "Claude Code 官方插件市场", "claude-plugins-official"),
                            ("anthropics/knowledge-work-plugins", "Claude 知识工作插件", "knowledge-work-plugins")):
        try:
            m = json.loads(get(f"https://raw.githubusercontent.com/{repo}/main/.claude-plugin/marketplace.json"))
            name = m.get("name") or mk
            for p in m.get("plugins", [])[:200]:
                src = p.get("source"); url = f"https://github.com/{repo}"
                if isinstance(src, str) and src.startswith("./"): url += "/tree/main/" + src[2:]
                elif isinstance(src, dict) and src.get("url"): url = src["url"]
                elif isinstance(src, dict) and src.get("repo"): url = "https://github.com/" + src["repo"]
                out.append({"name": p.get("name"), "desc": (p.get("description") or "")[:400], "cat": p.get("category") or "",
                            "src": label, "repo": repo, "url": url,
                            "install": f"/plugin marketplace add {repo}\n/plugin install {p.get('name')}@{name}"})
        except Exception as e: LOG.append(f"plugins {repo}: {e}")
    return out


TERMS = ["earth observation", "satellite", "geospatial", "gis", "earthquake", "seismic", "disaster", "flood", "glacier",
         "climate", "nasa", "usgs", "copernicus", "sentinel", "map", "wildfire", "remote sensing", "hydrology", "air quality", "github"]


def mcp():
    seen = {}
    for t in TERMS:
        try:
            d = json.loads(get("https://registry.modelcontextprotocol.io/v0/servers?" + urllib.parse.urlencode({"search": t, "limit": 50})))
        except Exception as e:
            LOG.append(f"mcp {t}: {e}"); continue
        for it in d.get("servers", []):
            s = it.get("server", it); meta = (it.get("_meta") or {}).get("io.modelcontextprotocol.registry/official") or {}
            if meta and meta.get("isLatest") is False: continue
            n = s.get("name")
            if not n or n in seen: continue
            rem = [r.get("url") for r in (s.get("remotes") or []) if r.get("url")]
            pk = [(p.get("registryType") or p.get("registry_type") or "") + ":" + (p.get("identifier") or p.get("name") or "") for p in (s.get("packages") or [])]
            seen[n] = {"name": n, "title": s.get("title") or "", "desc": (s.get("description") or "")[:300], "version": s.get("version") or "",
                       "repo": (s.get("repository") or {}).get("url") or "", "remote": rem[0] if rem else "", "pkg": pk[:2],
                       "site": s.get("websiteUrl") or "", "term": t, "updated": meta.get("updatedAt") or ""}
        time.sleep(0.3)
    return sorted(seen.values(), key=lambda x: (not x["remote"], x["name"]))


def main():
    os.makedirs(OUT, exist_ok=True)
    c = {"updated": NOW, "skills": [], "plugins": [], "mcp": []}
    for k, f in (("skills", skills), ("plugins", plugins), ("mcp", mcp)):
        try: c[k] = f()
        except Exception as e: LOG.append(f"{k}: {e}")
    c["log"] = LOG[-30:]
    json.dump(c, open(os.path.join(OUT, "catalog.json"), "w"), ensure_ascii=False, indent=1)
    print("skills", len(c["skills"]), "plugins", len(c["plugins"]), "mcp", len(c["mcp"]))
    for l in LOG[:20]: print(" ", l)


if __name__ == "__main__":
    main()

"""把一次推演的产物导出成通用格式，并在每份文件开头加“推演”标注和免责声明：
- 报告：report.md（Markdown）、report.docx（Word）、report.pdf（PDF）、report.html（网页）
- 过程：process.zip（agents.csv 智能体、posts.csv 帖子、comments.csv 评论、actions.csv 每个动作、timeline.csv 每轮统计，另附原始 JSON）
- exports.json：导出了哪些文件
用法：python3 tools/mirofish_export.py <推演输出目录>
"""
import csv, html, json, os, shutil, subprocess, sys, zipfile

D = sys.argv[1]
J = lambda n: json.load(open(os.path.join(D, n))) if os.path.exists(os.path.join(D, n)) else None
rq = J("request.json") or {}; st = J("status.json") or {}

DIS_ZH = ("【推演内容，非事实】本文件是多智能体推演的结果：推演要求由使用者自己填写，用使用者自己的模型运行。"
          "其中的数据、过程和结论都是模拟生成的，不是事实陈述，也不是预测、投资、法律或安全建议。"
          "种子数据来自公开来源，以原始来源为准。本站（一带一路 全量 预鉴 / EVEREST）和开发团队不对推演内容的准确性、完整性及任何使用后果承担责任。")
DIS_EN = ("[SIMULATION, NOT FACT] This file is the output of a multi-agent simulation. The prompt was written by the user and run on the user's own model. "
          "All data, process and conclusions are simulated: they are not statements of fact, nor forecasts or investment, legal or security advice. "
          "Seed data comes from public sources; the original sources prevail. The site (Belt and Road Full-Scope Foresight / EVEREST) and its developers accept no liability for the accuracy, completeness or any use of this content.")
meta = [("推演要求 / Prompt", rq.get("requirement", "")), ("国家 / Countries", rq.get("scope", "")), ("项目 / Project", rq.get("project", "")),
        ("开始 / Started (UTC)", rq.get("started", "")), ("结束 / Finished (UTC)", st.get("finished", "")), ("模拟轮数上限 / Max rounds", str(st.get("max_rounds") or "自动 / auto")),
        ("运行记录 / Run log", rq.get("run_url", ""))]
out = []

rep = os.path.join(D, "REPORT.md")
if os.path.exists(rep):
    body = open(rep, encoding="utf-8").read()
    head = "> " + DIS_ZH + "\n>\n> " + DIS_EN + "\n\n" + "\n".join(f"- **{k}**：{v}" for k, v in meta if v) + "\n\n---\n\n"
    md = head + body + "\n\n---\n\n" + DIS_ZH + "\n\n" + DIS_EN + "\n"
    open(os.path.join(D, "report.md"), "w", encoding="utf-8").write(md); out.append("report.md")
    if shutil.which("pandoc"):
        css = ("body{font-family:'Noto Sans CJK SC','Noto Sans SC','Microsoft YaHei',sans-serif;max-width:820px;margin:32px auto;padding:0 20px;line-height:1.7;color:#1d1d1f}"
               "blockquote{border-left:4px solid #c9a227;background:#fbf6e6;margin:0 0 16px;padding:10px 14px;color:#5a4a12}h1,h2,h3{line-height:1.3}table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:4px 8px}")
        open(os.path.join(D, "_s.css"), "w").write(css)
        subprocess.run(["pandoc", os.path.join(D, "report.md"), "-o", os.path.join(D, "report.docx")], check=False)
        subprocess.run(["pandoc", os.path.join(D, "report.md"), "-s", "--metadata", "title=推演报告 / Simulation report", "--embed-resources", "-c", os.path.join(D, "_s.css"), "-o", os.path.join(D, "report.html")], check=False)
        os.remove(os.path.join(D, "_s.css"))
    else:
        open(os.path.join(D, "report.html"), "w", encoding="utf-8").write("<meta charset=utf-8><pre>" + html.escape(md) + "</pre>")
    for n in ("report.docx", "report.html"):
        if os.path.exists(os.path.join(D, n)): out.append(n)
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if chrome and os.path.exists(os.path.join(D, "report.html")):
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + os.path.abspath(os.path.join(D, "report.pdf")),
                        "file://" + os.path.abspath(os.path.join(D, "report.html"))], check=False, timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(os.path.join(D, "report.pdf")): out.append("report.pdf")


def wcsv(z, name, rows, cols):
    import io
    s = io.StringIO(); s.write("﻿")   # 带 BOM，Excel 直接打开不乱码
    w = csv.writer(s); w.writerow(cols)
    for r in rows: w.writerow([json.dumps(r.get(c), ensure_ascii=False) if isinstance(r.get(c), (dict, list)) else r.get(c) for c in cols])
    z.writestr(name, s.getvalue())


pf = (J("03_profiles.json") or {}).get("profiles") or []
posts = (J("08_posts.json") or {}).get("posts") or []
com = (J("09_comments.json") or {}).get("comments") or []
act = (J("10_actions.json") or {}).get("actions") or []
tl = (J("06_timeline.json") or {}).get("timeline") or []
if pf or posts or act:
    with zipfile.ZipFile(os.path.join(D, "process.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", DIS_ZH + "\n\n" + DIS_EN + "\n\nagents.csv 智能体（人设）/ agents; posts.csv 帖子 / posts; comments.csv 评论 / comments; actions.csv 每个动作 / every action; timeline.csv 每轮统计 / per round.\n"
                   + "\n".join(f"{k}: {v}" for k, v in meta if v) + "\n")
        if pf: wcsv(z, "agents.csv", pf, ["user_id", "name", "profession", "country", "age", "gender", "mbti", "interested_topics", "bio", "persona"])
        if posts: wcsv(z, "posts.csv", posts, ["post_id", "user_id", "created_at", "content", "num_likes", "num_dislikes", "num_shares", "original_post_id", "quote_content"])
        if com: wcsv(z, "comments.csv", com, ["comment_id", "post_id", "user_id", "created_at", "content", "num_likes", "num_dislikes"])
        if act: wcsv(z, "actions.csv", act, ["round_num", "timestamp", "platform", "agent_id", "agent_name", "action_type", "success", "action_args"])
        if tl: wcsv(z, "timeline.csv", tl, ["round_num", "total_actions", "twitter_actions", "reddit_actions", "active_agents_count", "first_action_time", "last_action_time", "action_types"])
        for n in ("01_ontology.json", "02_graph.json", "03_profiles.json", "04_config.json", "06_timeline.json", "07_agent_stats.json", "08_posts.json", "09_comments.json", "10_actions.json"):
            if os.path.exists(os.path.join(D, n)): z.write(os.path.join(D, n), "raw/" + n)
    out.append("process.zip")
json.dump({"files": out, "disclaimer_zh": DIS_ZH, "disclaimer_en": DIS_EN}, open(os.path.join(D, "exports.json"), "w"), ensure_ascii=False, indent=1)
print("exports:", out)

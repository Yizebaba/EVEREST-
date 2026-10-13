"""总览页自检：语法、打开、标签、报错、英文残留。用法：python3 hub/test/check.py hub/everest-hub.html [mockdata.js]
mockdata.js 里定义 window.__SEED（数据库初始内容），可选。"""
import re, sys, subprocess, json
from playwright.sync_api import sync_playwright
f = sys.argv[1]; seed = sys.argv[2] if len(sys.argv) > 2 else None
subprocess.run(["node", "-e", "const s=require('fs').readFileSync(process.argv[1],'utf8');const re=/<script>([\\s\\S]*?)<\\/script>/g;let m;while((m=re.exec(s)))new Function(m[1]);console.log('scripts ok')", f], check=True)
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(viewport={"width": 1400, "height": 1000}); errs = []
    p.on("pageerror", lambda e: errs.append(str(e)))
    p.add_init_script("""(()=>{const mk=()=>{const f=function(){};return new Proxy(f,{get:(t,k)=>k===Symbol.toPrimitive?()=>0:(k==="then"?undefined:mk()),apply:()=>mk(),construct:()=>mk(),set:()=>true})};window.THREE=mk()})()""")
    if seed:
        p.add_init_script(path=seed); p.add_init_script(path="hub/test/mockdb.js"); p.add_init_script(path="hub/test/mockext.js")
    p.goto("file://" + __import__("os").path.abspath(f)); p.wait_for_timeout(2000)
    tabs = p.evaluate("()=>[...document.querySelectorAll('[data-wb]')].map(b=>b.dataset.wb)")
    print("tabs", tabs)
    for lang in ("zh", "en"):
        for t in tabs:
            p.evaluate(f"()=>{{LANG='{lang}';WBT='{t}';render()}}"); p.wait_for_timeout(150)
            if lang == "en":
                txt = p.evaluate("()=>(document.querySelector('#side .wbody')||{}).innerText||''")
                left = [l for l in txt.split("\n") if re.search(r"[一-鿿]", l)]
                if left: print("EN 残留中文", t, len(left), left[:3])
    print("errors", errs[:5]); b.close()
    sys.exit(1 if errs else 0)

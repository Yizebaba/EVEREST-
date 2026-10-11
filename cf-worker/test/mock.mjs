// 本地模拟 Planetary Computer：STAC 搜索 + 逐坡面统计。最新一景让前 5 个坡面明显变暗，其余正常波动。
import http from "node:http";
const scenes = [];
for (let t = Date.parse("2020-01-04T00:10:50Z"); t <= Date.parse("2026-10-06T00:10:50Z"); t += 12 * 864e5) {
  const d = new Date(t).toISOString(), ymd = d.slice(0, 10).replace(/-/g, "");
  scenes.push({ id: `S1A_IW_GRDH_1SDV_${ymd}T001038_${ymd}T001103_000000_000000_rtc`, t: d });
}
scenes.reverse();
let fails = 0;
const hash = s => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
http.createServer((req, res) => {
  let b = ""; req.on("data", c => b += c); req.on("end", () => {
    const u = new URL(req.url, "http://x");
    if (u.pathname === "/search") {
      const body = JSON.parse(b), [s, e] = body.datetime.split("/");
      const f = scenes.filter(x => x.t >= s && x.t <= e).map(x => ({ id: x.id, properties: { datetime: x.t, "sat:relative_orbit": 121, platform: "sentinel-1a", "s1:processing_datetime": new Date(Date.parse(x.t) + 2 * 3600e3).toISOString() } }));
      res.end(JSON.stringify({ features: f, links: [] })); return;
    }
    if (u.pathname === "/stats") {
      if (++fails % 37 === 0) { res.statusCode = 500; res.end("Internal Server Error"); return; }
      const id = JSON.parse(b).properties.id, item = u.searchParams.get("item");
      const ymd = item.split("_")[4].slice(0, 8), doy = Math.floor((Date.parse(ymd.slice(0, 4) + "-" + ymd.slice(4, 6) + "-" + ymd.slice(6, 8)) - Date.parse(ymd.slice(0, 4) + "-01-01")) / 864e5);
      const base = -8 + (hash(id) % 600) / 100, season = 1.5 * Math.cos(2 * Math.PI * doy / 365), noise = ((hash(id + item) % 1000) / 1000 - .5) * .8;
      const k = Number(id.slice(1)) % 5 === 0 && item === scenes[0].id ? -4 : 0;   // 部分坡面在最新景明显变暗
      const db = base + season + noise + k;
      res.end(JSON.stringify({ type: "Feature", properties: { statistics: { vv_b1: { mean: 10 ** (db / 10), count: 5000 + hash(id) % 3000 } } } })); return;
    }
    res.statusCode = 404; res.end();
  });
}).listen(9911, () => console.log("mock on 9911"));

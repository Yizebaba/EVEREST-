// 本地模拟 IGN FTP：NLST 返回两份 NRT 文件名，RETR 返回带 EVEC 的 RINEX 片段
import net from "node:net";
const files = { "srlrx20261012_000026_20261012_002709": rx("2026 10 12 00 07 59", "2026 10 12 00 16 19"), "srlrx20261012_002746_20261012_020509": rx(null) };
function rx(a, b) {
  let h = "     3.00           O                   D                   RINEX VERSION / TYPE\nD01  KOKC KOKEE PARK                    40424S007  4   0    STATION REFERENCE\nD05  EVEC EVEREST                       21501S001  4   0    STATION REFERENCE\n                                                            END OF HEADER\n";
  if (!a) return h + "> 2026 10 12 01 00 00.0  0  1\nD01   -1.0 1\n";
  return h + `> ${a}.000000  0  1\nD05   -111132.535 1\n> 2026 10 12 00 10 00.000000  0  1\nD01   1\n> ${b}.000000  0  1\nD05   -21901.630 1\nD05   -3 1\n`;
}
let dataSrv, pending;
net.createServer(c => {
  c.write("220 mock\r\n");
  c.on("data", d => {
    for (const line of d.toString().split("\r\n").filter(Boolean)) {
      const [cmd, ...rest] = line.split(" "); const arg = rest.join(" ");
      if (cmd === "USER") c.write("331 ok\r\n"); else if (cmd === "PASS") c.write("230 ok\r\n"); else if (cmd === "TYPE") c.write("200 ok\r\n");
      else if (cmd === "PASV") { dataSrv = net.createServer(ds => { const send = () => { ds.end(pending); c.write("226 done\r\n"); }; if (pending != null) send(); else setTimeout(send, 50); }); dataSrv.listen(0, () => { const p = dataSrv.address().port; c.write(`227 Entering Passive Mode (127,0,0,1,${p >> 8},${p & 255})\r\n`); }); pending = null; }
      else if (cmd === "NLST") { pending = Object.keys(files).map(f => arg + "/" + f).join("\r\n") + "\r\n"; c.write("150 list\r\n"); }
      else if (cmd === "RETR") { pending = files[arg.split("/").pop()] || ""; c.write("150 file\r\n"); }
      else c.write("502 no\r\n");
    }
  });
}).listen(2121, () => console.log("ftp mock 2121"));

// 一带一路标签的国界底图：Natural Earth 1:50m（公有领域，npm world-atlas@2.0.2 + topojson-client@3.1.0），投影后裁剪，结果嵌在 hub/everest-hub.html 的 BRIBASE。用法：node tools/bri_basemap.js（在装了这两个包的目录里）
const tc=require('topojson-client');
const t50=require('./node_modules/world-atlas/countries-50m.json');
const F=tc.feature(t50,t50.objects.countries).features;
const byId=id=>F.find(f=>+f.id===id);
const CFG={NPL:{id:524,nb:[156,356,64,50],cap:["加德满都",27.7172,85.324],lbl:[["中国",29.6,84.2],["印度",26.7,81.6]]},
 LAO:{id:418,nb:[156,764,704,104,116],cap:["万象",17.9757,102.6331],lbl:[["中国",22.9,101.2],["泰国",16.0,101.4],["越南",19.6,105.4]]},
 PAK:{id:586,nb:[156,356,4,364],cap:["伊斯兰堡",33.6844,73.0479],lbl:[["阿富汗",33.6,65.6],["印度",30.2,75.6],["伊朗",27.6,61.0],["中国",36.9,77.4]]}};
const out={};
for(const [c,g] of Object.entries(CFG)){const f=byId(g.id);let x0=1e9,x1=-1e9,y0=1e9,y1=-1e9;
 const each=(geom,fn)=>{const P=geom.type==="Polygon"?[geom.coordinates]:geom.coordinates;P.forEach(p=>p.forEach(r=>r.forEach(fn)))};
 each(f.geometry,([x,y])=>{x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)});
 const px=(x1-x0)*.07,py=(y1-y0)*.07;x0-=px;x1+=px;y0-=py;y1+=py;const k=Math.cos((y0+y1)/2*Math.PI/180),W=520,S=W/((x1-x0)*k),H=Math.round((y1-y0)*S);
 const X=x=>((x-x0)*k*S),Y=y=>((y1-y)*S);
 const path=geom=>{const P=geom.type==="Polygon"?[geom.coordinates]:geom.coordinates;let d="";P.forEach(p=>p.forEach(r=>{let last="";const pts=[];r.forEach(([x,y])=>{const s=X(x).toFixed(1)+" "+Y(y).toFixed(1);if(s!==last)pts.push(s);last=s});
   // skip rings fully outside view
   const xs=r.map(q=>X(q[0])),ys=r.map(q=>Y(q[1]));if(Math.max(...xs)<-50||Math.min(...xs)>W+50||Math.max(...ys)<-50||Math.min(...ys)>H+50)return;d+="M"+pts.join("L")+"Z"}));return d};
 const clip=(pts,a,b,c,d)=>{const edges=[[p=>p[0]>=a,(p,q)=>[a,p[1]+(q[1]-p[1])*(a-p[0])/(q[0]-p[0])]],[p=>p[0]<=c,(p,q)=>[c,p[1]+(q[1]-p[1])*(c-p[0])/(q[0]-p[0])]],[p=>p[1]>=b,(p,q)=>[p[0]+(q[0]-p[0])*(b-p[1])/(q[1]-p[1]),b]],[p=>p[1]<=d,(p,q)=>[p[0]+(q[0]-p[0])*(d-p[1])/(q[1]-p[1]),d]]];
  for(const [ins,isect] of edges){const o=[];for(let i=0;i<pts.length;i++){const p=pts[i],q=pts[(i+1)%pts.length];if(ins(q)){if(!ins(p))o.push(isect(p,q));o.push(q)}else if(ins(p))o.push(isect(p,q))}pts=o;if(!pts.length)break}return pts};
 const npath=geom=>{const P=geom.type==="Polygon"?[geom.coordinates]:geom.coordinates;let d="";P.forEach(p=>p.forEach(r=>{const c=clip(r.map(([x,y])=>[X(x),Y(y)]),-4,-4,W+4,H+4);if(c.length<3)return;let last="";const pts=[];c.forEach(([x,y])=>{const s=Math.round(x)+" "+Math.round(y);if(s!==last)pts.push(s);last=s});if(pts.length>2)d+="M"+pts.join("L")+"Z"}));return d};
 const nb=g.nb.map(id=>npath(byId(id).geometry)).join("");
 out[c]={w:W,h:H,p:[+x0.toFixed(4),+y1.toFixed(4),+k.toFixed(5),+S.toFixed(3)],nb:nb,c:path(f.geometry),cap:g.cap,lbl:g.lbl};}
const s=JSON.stringify(out);require('fs').writeFileSync('bri_base.json',s);console.log(s.length,Object.fromEntries(Object.entries(out).map(([k,v])=>[k,[v.w,v.h,v.nb.length,v.c.length]])));

(()=>{const S=window.__SEED||{};const store={};for(const c in S){store[c]=Object.assign({},S[c])}
const subs=[];let n=0;const snapDoc=(c,id)=>{const v=(store[c]||{})[id];return{id,exists:!!v,data:()=>v,metadata:{}}};
const fire=()=>subs.forEach(f=>f());
function coll(c,q={}){const api={where:()=>api,orderBy:(f,d)=>coll(c,Object.assign({},q,{ob:f,dir:d})),limit:k=>coll(c,Object.assign({},q,{lim:k})),
 get:async()=>mk(),onSnapshot:(nx)=>{const f=()=>nx(mk());subs.push(f);setTimeout(f,10);return()=>{}},
 doc:(id)=>docr(c,id||("x"+(++n))),add:async d=>{const id="x"+(++n);(store[c]=store[c]||{})[id]=d;setTimeout(fire,5);return docr(c,id)}};
 function mk(){let ds=Object.keys(store[c]||{}).map(id=>snapDoc(c,id));if(q.ob)ds.sort((a,b)=>String(a.data()[q.ob]||"").localeCompare(String(b.data()[q.ob]||""))*(q.dir==="desc"?-1:1));return{docs:ds,size:ds.length,empty:!ds.length,docChanges:()=>[],metadata:{}}}
 return api}
function docr(c,id){return{id,get:async()=>snapDoc(c,id),set:async d=>{(store[c]=store[c]||{})[id]=d;setTimeout(fire,5)},update:async d=>{store[c][id]=Object.assign({},store[c][id],d);setTimeout(fire,5)},delete:async()=>{delete store[c][id];setTimeout(fire,5)},onSnapshot:nx=>{const f=()=>nx(snapDoc(c,id));subs.push(f);setTimeout(f,10);return()=>{}},collection:p=>coll(c+"/"+id+"/"+p)}}
const db={collection:p=>{const s=p.split("/");return coll(p)},doc:p=>{const s=p.split("/");return docr(s.slice(0,-1).join("/"),s[s.length-1])}};
const user={id:async()=>"u_test",can:async()=>true,canEdit:async()=>true,isOwner:async()=>true,me:async()=>({id:"u_test",name:"测试"}),profiles:async ids=>Object.fromEntries([].concat(ids).map(i=>[i,{id:i,name:""}]))};
window.claude={use:async k=>k==="db"?db:k==="user"?user:null};window.__store=store})();

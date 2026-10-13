(()=>{const base=window.claude.use;const rt=window.__SEED.live.rt;const newer=JSON.parse(JSON.stringify(rt));newer.updated="2026-10-13T04:45:00.000Z";
const mcp={callTool:async(s,t,a)=>{if(s!=="EVEREST")throw{code:"server_not_found"};if(t==="everest_snapshot")return{content:[{type:"text",text:"snap"}],payload:{result:{rt:newer,status:{scenes:{n:275,d:120}}}}};return{content:[{type:"text",text:"工具 "+t+" 结果 "+JSON.stringify(a)}]}}};
const sample=async(input,o)=>{const r=await o.tools[0].execute({tool:"everest_overview",args:{}});const txt="按技能回答：\n"+r;o.onText&&o.onText({text:txt});return{text:txt,truncated:false}};
const perms={state:async()=>"granted"};
window.claude={use:async k=>k==="mcp"?mcp:k==="sample"?sample:k==="permissions"?perms:base(k)}})();

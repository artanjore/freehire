"use strict";
const API="https://freehire.me/api/v1/jobs/search";
const ROLES=["Product Manager","AI Product Manager","Program Manager","Business Analyst","Product Analyst"];
const CACHE_KEY="my-job-board-api-v1",TRACK_KEY="my-job-board-tracking-v1",TTL=3*60*60*1000;
const $=id=>document.getElementById(id);
let jobs=[],tracking={},visible=24,loadedAt=null,loadError="";
try{tracking=JSON.parse(localStorage.getItem(TRACK_KEY)||"{}")||{}}catch{tracking={}}
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const key=j=>j.public_slug||j.url;
const cleanUrl=s=>{try{const u=new URL(s);return ["http:","https:"].includes(u.protocol)?u.href:null}catch{return null}};
const date=s=>{if(!s)return "Date unavailable";const d=new Date(s);return Number.isNaN(d.getTime())?"Date unavailable":d.toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})};
function store(){try{localStorage.setItem(TRACK_KEY,JSON.stringify(tracking))}catch{}}
function refreshStats(){const records=Object.values(tracking);$("savedCount").textContent=records.filter(x=>x.saved).length;$("appliedCount").textContent=records.filter(x=>x.status==="applied").length;$("interviewCount").textContent=records.filter(x=>x.status==="interviewing").length;$("total").textContent=jobs.length.toLocaleString()}
function render(){
  const role=$("role").value,q=$("query").value.trim().toLowerCase(),mode=$("mode").value,view=$("view").value;
  const filtered=jobs.filter(j=>{
    const t=tracking[key(j)]||{};
    if(role&&!(j._matched_roles||[]).includes(role))return false;
    if(q&&!([j.title,j.company,j.location,j.description].join(" ").toLowerCase().includes(q)))return false;
    if(mode&&j.work_mode!==mode)return false;
    if(view==="saved"&&!t.saved)return false;
    if(view==="applied"&&t.status!=="applied")return false;
    if(view==="interviewing"&&t.status!=="interviewing")return false;
    return true;
  });
  $("shown").textContent=filtered.length+" shown by filters";
  const subset=filtered.slice(0,visible);
  $("jobs").innerHTML=subset.map(j=>{
    const id=key(j),t=tracking[id]||{},url=cleanUrl(j.url);
    const status=t.status||"new";
    return '<article class="job"><div class="job-top"><div><h2>'+esc(j.title||"Untitled role")+'</h2><div class="company">'+esc(j.company||"Company unavailable")+'</div></div><span class="pill">'+esc(j.work_mode||"Unspecified")+'</span></div><div class="meta"><span>⌖ '+esc(j.location||"Location unspecified")+'</span><span>Posted '+esc(date(j.posted_at))+'</span></div><div class="actions">'+(url?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Apply ↗</a>':'')+'<button data-id="'+esc(id)+'" data-action="save" aria-pressed="'+Boolean(t.saved)+'">'+(t.saved?"★ Saved":"☆ Save")+'</button><select data-id="'+esc(id)+'" data-action="status" aria-label="Application status for '+esc(j.title)+'"><option value="new" '+(status==="new"?"selected":"")+'>Not applied</option><option value="applied" '+(status==="applied"?"selected":"")+'>Applied</option><option value="interviewing" '+(status==="interviewing"?"selected":"")+'>Interviewing</option><option value="rejected" '+(status==="rejected"?"selected":"")+'>Rejected</option><option value="offer" '+(status==="offer"?"selected":"")+'>Offer</option></select></div></article>';
  }).join("")||'<div class="empty">'+(loadError?esc(loadError):"No matching jobs. Try adjusting your filters.")+'</div>';
  $("moreWrap").hidden=filtered.length<=visible;
  refreshStats();
}
async function requestRole(role){
  const p=new URLSearchParams({q:role,countries:"US",open_within_days:"14",sort:"posted_at",order:"desc",limit:"50"});
  const response=await fetch(API+"?"+p,{headers:{Accept:"application/json"}});
  if(!response.ok)throw new Error("FreeHire API returned "+response.status);
  const body=await response.json();
  if(!Array.isArray(body.data))throw new Error("Unexpected API response");
  if(body.meta?.ignored_params?.length)console.warn("Ignored API filters",body.meta.ignored_params);
  return body.data;
}
async function load(force=false){
  $("refresh").disabled=true;$("status").textContent="Checking latest listings…";loadError="";
  try{
    if(!force){const cached=JSON.parse(localStorage.getItem(CACHE_KEY)||"null");if(cached&&Date.now()-cached.time<TTL&&Array.isArray(cached.jobs)){jobs=cached.jobs;loadedAt=cached.time;$("status").textContent="Showing cached jobs · refreshes every 3 hours";render();return}}
    const results=await Promise.allSettled(ROLES.map(requestRole));
    const map=new Map(),errors=[];
    results.forEach((result,i)=>{if(result.status==="rejected"){errors.push(ROLES[i]);return}for(const job of result.value){const id=key(job);if(!id)continue;const previous=map.get(id);if(previous){previous._matched_roles=[...new Set([...previous._matched_roles,ROLES[i]])]}else{map.set(id,{...job,_matched_roles:[ROLES[i]]})}}});
    if(!map.size)throw new Error("No job results returned. Try refreshing later.");
    jobs=[...map.values()].sort((a,b)=>String(b.posted_at||"").localeCompare(String(a.posted_at||"")));
    loadedAt=Date.now();try{localStorage.setItem(CACHE_KEY,JSON.stringify({time:loadedAt,jobs}))}catch{}
    $("status").textContent=errors.length?"Updated, but some searches failed: "+errors.join(", "):"Jobs updated from FreeHire";
  }catch(e){loadError=e.message||"Unable to load jobs";$("status").textContent=loadError;try{const cached=JSON.parse(localStorage.getItem(CACHE_KEY)||"null");if(cached?.jobs?.length){jobs=cached.jobs;loadedAt=cached.time;loadError="";$("status").textContent="API unavailable · showing previously cached jobs"}}catch{}}
  finally{$("refresh").disabled=false;$("updated").textContent=loadedAt?"Last loaded "+new Date(loadedAt).toLocaleString():"Not loaded";render()}
}
$("jobs").addEventListener("click",e=>{const b=e.target.closest('button[data-action="save"]');if(!b)return;const id=b.dataset.id;tracking[id]={...(tracking[id]||{}),saved:!tracking[id]?.saved};store();render()});
$("jobs").addEventListener("change",e=>{const s=e.target.closest('select[data-action="status"]');if(!s)return;tracking[s.dataset.id]={...(tracking[s.dataset.id]||{}),status:s.value};store();render()});
for(const id of ["role","mode","view"])$(id).addEventListener("change",()=>{visible=24;render()});
$("query").addEventListener("input",()=>{visible=24;render()});
$("refresh").addEventListener("click",()=>load(true));
$("more").addEventListener("click",()=>{visible+=24;render()});
load();

'use strict';
const $ = id => document.getElementById(id);
const form = $('brief-form');
const token = document.querySelector('meta[name="atlas-csrf"]').content;
let busy = false;
let original = '';
const labels = {brand:'品牌策略',social:'社群內容',copy:'文案撰寫',seo:'搜尋優化',ads:'廣告策略',email:'電子報',analytics:'成效與量測',research:'資料研究',events:'活動規劃'};
const errors = {MODEL_TIMEOUT:'模型等待超過 150 秒。沒有產出可驗證的完整回應；可稍後重試。',MODEL_UNAVAILABLE:'這個模型目前不適用於已登入的 Codex 帳號。請由擁有者確認 ATLAS_CODEX_MODEL。',CODEX_UNAVAILABLE:'找不到可執行的 Codex CLI。請由擁有者確認絕對路徑 ATLAS_CODEX_BIN。',MODEL_FAILED:'Codex 執行失敗。請由擁有者確認登入狀態與模型；未使用範例取代結果。',MODEL_INCOMPLETE:'模型未回報完整成功的 turn.completed 終態，結果未交付。',EMPTY_MODEL_OUTPUT:'模型沒有回傳文字；本次不算完成。',BUSY:'另一個請求仍在執行。本機只允許一份工作，請稍後再試。',REQUEST_TOO_LARGE:'任務與背景合計超過 16 KB，請縮短文字再試。',CSRF_REJECTED:'頁面憑證已失效。請重新整理後再送出。'};
function status(message, state='') { $('status').textContent = message; $('status').className = 'status ' + state; }
function visibility(id, show) { $(id).hidden = !show; }
function paragraph(text, parent, cls='') { const p=document.createElement('p'); p.textContent=text; p.className=cls; parent.append(p); return p; }
function render(data) {
  original=data.output;
  $('result').value=data.output;
  $('edited').textContent='模型原始回應';
  $('workstreams').replaceChildren();
  const domains=data.plan.domains || [];
  for (const domain of domains) { const chip=document.createElement('span'); chip.className='chip'; chip.textContent=labels[domain] || domain; $('workstreams').append(chip); }
  if (!domains.length) paragraph('需求尚無明確對應分工；請檢查模型列出的假設。', $('workstreams'), 'small subtle');
  $('methods').textContent='內建方法：' + ((data.plan.methods || []).join(' · ') || '無對應方法；以明示假設起草');
  const discovery=data.discovery || {};
  $('discovery-status').textContent=discovery.attempted ? '已實際嘗試唯讀搜尋 · ' + discovery.status + '。外部資料未核准；本次只採內建方法，不代表完成市場研究。' : '依任務重用內建方法，未搜尋外部儲存庫。';
  $('sources').replaceChildren();
  for (const source of data.sources || []) {
    const item=document.createElement('div'); item.className='source';
    const url=String(source.html_url || '');
    if (/^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(url)) { const a=document.createElement('a'); a.href=url; a.target='_blank'; a.rel='noopener noreferrer'; a.textContent=source.full_name; item.append(a); }
    else paragraph(source.full_name || '來源未確認', item);
    paragraph('實際觀察：' + (source.state || 'UNKNOWN') + ' · 待審核 / 未啟用', item, 'subtle');
    paragraph('授權、固定版本與主機相容性尚未通過完整人工檢查。', item, 'subtle');
    $('sources').append(item);
  }
  if (!(data.sources || []).length) paragraph(discovery.attempted ? '沒有可列出的外部來源。沒有補上虛構儲存庫。' : '本次無外部搜尋來源；方法出自隨附 ATLAS 方法包。', $('sources'), 'small subtle');
  $('reviews').replaceChildren();
  for (const review of data.pending_reviews || []) { const li=document.createElement('li'); li.textContent=review; $('reviews').append(li); }
  visibility('delivery',true);
}
$('sample').addEventListener('click', () => {
  $('task').value='請將這段 IG 社群貼文改寫成三個完整版本，每篇 80–120 字，分別用提問、生活情境、品牌觀點開場，最後只留一個留言 CTA。原文：下午忙累了，來一杯咖啡，讓自己慢下來。請不要編造店址、優惠、得獎、顧客故事或成效數據。';
  $('context').value='虛構示範品牌「慢半拍咖啡」。這不是實際客戶資料。受眾假設：工作節奏快、想在午後稍作休息的人。語氣：自然、溫暖、不說教。產品、價格與門市資訊皆未提供，不可自行補寫。';
  $('task').focus();
});
$('clear').addEventListener('click', () => {
  if (busy) return;
  form.reset(); $('result').value=''; original='';
  ['delivery','loading','error'].forEach(id=>visibility(id,false)); visibility('empty',true);
  $('action-status').textContent=''; status('尚未開始 · 等你的一句需求');
});
form.addEventListener('submit', async event => {
  event.preventDefault(); if (busy || !form.reportValidity()) return;
  const payload=JSON.stringify({task:$('task').value,context:$('context').value});
  if (new TextEncoder().encode(payload).length > 16384) { visibility('error',true); $('error').textContent=errors.REQUEST_TOO_LARGE; return; }
  busy=true; ['generate','sample','clear'].forEach(id=>$(id).disabled=true);
  ['empty','error','delivery'].forEach(id=>visibility(id,false)); visibility('loading',true);
  $('action-status').textContent=''; status('請求已送出 · 等待後端完成來源檢查與模型回應');
  const start=Date.now(); $('elapsed').textContent='已等待 0 秒';
  const timer=setInterval(()=>$('elapsed').textContent='已等待 ' + Math.floor((Date.now()-start)/1000) + ' 秒',1000);
  try {
    const response=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json','X-Atlas-CSRF':token},body:payload});
    const data=await response.json();
    if (!response.ok) throw new Error(data.error || 'GENERATION_FAILED');
    if (typeof data.output !== 'string' || !data.output.trim()) throw new Error('EMPTY_MODEL_OUTPUT');
    render(data); status('已收到完整模型回應 · 仍待人工審核', 'success');
  } catch (error) {
    const code=error.message;
    $('error').textContent=(errors[code] || '本次請求未成功。請確認本機服務仍在執行；沒有以預製內容取代模型結果。') + '\n可修改需求後重試；輸入內容仍保留在本頁。';
    visibility('error',true); status('本次未完成 · 沒有交付替代成果', 'failure');
  } finally { clearInterval(timer); visibility('loading',false); busy=false; ['generate','sample','clear'].forEach(id=>$(id).disabled=false); }
});
$('result').addEventListener('input', () => { $('edited').textContent=$('result').value===original ? '模型原始回應' : '已在本頁修改 · 未另存'; });
$('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('result').value); $('action-status').textContent='已複製目前文字'; }
  catch (_) { $('result').select(); $('action-status').textContent='請按 ⌘C / Ctrl+C 複製選取文字'; }
});
$('download').addEventListener('click', () => {
  const blob=new Blob([$('result').value],{type:'text/markdown;charset=utf-8'});
  const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='ATLAS-DRAFT.md'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
  $('action-status').textContent='已建立目前文字的 Markdown 下載';
});

import {SHAPES,PlaySession,makeWindow,validateWindow,quality,spectrum,infer,toCSV} from './core.js';
import MODEL from '../models/tinycnn.json' with {type:'json'};
import BENCH from '../reports/synthetic-benchmark.json' with {type:'json'};
import REAL_BENCH from '../reports/physionet-pilot/benchmark.json' with {type:'json'};
import REAL_EXAMPLE from '../reports/physionet-pilot/example-real-window.json' with {type:'json'};

const $=id=>document.getElementById(id);
const targets=[...document.querySelectorAll('[data-target]')];
let session=null, signal=makeWindow(), signalTrusted=true, signalSeed=144, signalAnalysis=null, observations=[];
let signalMode='synthetic';
const clock=()=>performance.now();
const active=()=>session&&!['idle','complete','stopped'].includes(session.phase);
const label=i=>`${i+1} · ${SHAPES[i]}`;
const seconds=x=>x==null?'—':`${(x/1000).toFixed(1)} s`;
function download(name,text,type='application/json'){
  const url=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');
  a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function gameInfo(){
  const mode=session?.mode||$('mode').value;
  $('game-title').textContent=mode==='memory'?'Sequence Buffer':'Rule Router';
  $('game-instruction').textContent=mode==='memory'?'Memorise the symbol buffer, then reproduce its order on the response pads.':'MATCH: choose the cue. OPPOSITE: Node ↔ Phase, Pulse ↔ Gate. The rule changes every two rounds.';
  $('level').disabled=active()||$('mode').value==='switch';
}
function renderGame(){
  gameInfo();
  const phase=session?.phase||'idle',summary=session?.summary()||{completed:0,correct:0,median_duration_ms:null};
  $('completed').textContent=summary.completed;
  $('correct').textContent=summary.completed?`${summary.correct} / ${summary.completed}`:'—';
  $('median').textContent=seconds(summary.median_duration_ms);
  $('progress-fill').style.width=`${summary.completed/8*100}%`;
  $('round-label').textContent=session?`${String(session.counter).padStart(2,'0')} / 08 · ${phase.toUpperCase()}`:'AWAITING RUN';
  targets.forEach(b=>b.disabled=phase!=='active');
  for(const id of ['mode','target-size'])$(id).disabled=!!active();
  $('pause').disabled=!['preview','active','paused'].includes(phase);
  $('pause').textContent=phase==='paused'?'Resume':'Pause';
  $('stop').disabled=!active();
  $('advance').disabled=['active','paused'].includes(phase);
  $('advance').textContent=phase==='preview'?'I’m ready →':phase==='feedback'?'Load next trial →':['complete','stopped'].includes(phase)?'Configure new run':'Load first trial →';
  if(phase==='preview'){
    $('cue').textContent=session.mode==='memory'?session.expected.map(label).join(' → '):`${session.rule.toUpperCase()} · Cue: ${label(session.cue)}`;
    $('game-status').textContent='Preview the buffer. Select “I’m ready” to open the response phase.';
  }else if(phase==='active'){
    $('cue').textContent=session.mode==='memory'?`Response buffer · ${session.responses.length} of ${session.expected.length} symbols entered`:`${session.rule.toUpperCase()} · Cue: ${label(session.cue)}`;
    $('game-status').textContent='Enter the symbol sequence using the response pads or keys 1–4. No deadline.';
  }else if(phase==='paused'){
    $('cue').textContent='Run paused · Response timer suspended';$('game-status').textContent='Resume to continue the current trial. Paused time is excluded from the response duration.';
  }else if(['feedback','complete'].includes(phase)){
    const last=session.records.at(-1);
    $('cue').textContent=last.correct?'Sequence verified / response recorded.':`Reference sequence / ${last.expected.map(label).join(' → ')}`;
    $('game-status').textContent=phase==='complete'?'Run complete. Inspect the ledger, export the data or configure another task.':'Trial recorded. Load the next trial when ready.';
  }else if(phase==='stopped'){
    $('cue').textContent='Run closed / completed trials are ready to export';$('game-status').textContent='The unfinished round was not scored.';
  }
  const suggestion=session?.suggestion();
  $('suggestion').hidden=suggestion==null;
  if(suggestion!=null)$('suggestion-text').textContent=`From the last four trials, use a buffer of ${suggestion} symbols? Apply the change below if you want to test this setting.`;
  $('export-session').disabled=!session;
  $('export-csv').disabled=!summary.completed;
  const tbody=$('round-table');tbody.replaceChildren();
  if(!summary.completed){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='No completed trials in the ledger.';tr.append(td);tbody.append(tr);}
  for(const r of session?.records||[]){
    const tr=document.createElement('tr');
    for(const value of [r.round,r.expected.length,r.correct?'Match':'Mismatch',seconds(r.duration_ms),[...new Set(r.responses.map(x=>x.input))].join(' + ')]){const td=document.createElement('td');td.textContent=value;tr.append(td);}
    tbody.append(tr);
  }
  renderTimer();
}
function renderTimer(){
  if(session?.phase==='active')$('timer').textContent=seconds(clock()-session.started-session.pausedMs);
  else if(['feedback','complete'].includes(session?.phase))$('timer').textContent=seconds(session.records.at(-1)?.duration_ms);
  else if(session?.phase!=='paused')$('timer').textContent='0.0 s';
}
function newSession(){
  session=new PlaySession({mode:$('mode').value,level:Number($('level').value),seed:144+Math.floor(clock())%100000});
  observations=[];recordObservation();session.begin(clock());renderGame();
}
$('advance').addEventListener('click',()=>{
  if(!session||['complete','stopped'].includes(session.phase))newSession();
  else if(session.phase==='preview'){session.ready(clock());renderGame();targets[0].focus();}
  else if(session.phase==='feedback'){session.begin(clock());renderGame();}
});
function answer(value,input){
  if(!session||!session.respond(value,clock(),input))return;
  if(['feedback','complete'].includes(session.phase)){
    session.records.at(-1).layout={unit:'CSS_px',viewport_width:innerWidth,viewport_height:innerHeight,
      targets:targets.map(b=>{const r=b.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};})};
  }
  renderGame();
  if(['feedback','complete'].includes(session.phase))$('advance').focus();
}
targets.forEach(b=>b.addEventListener('click',()=>answer(Number(b.dataset.target),'pointer')));
document.addEventListener('keydown',e=>{
  if(e.repeat||e.ctrlKey||e.metaKey||e.altKey||(e.target instanceof Element&&e.target.matches('input,select,textarea')))return;
  if(/^[1-4]$/.test(e.key)&&session?.phase==='active'){e.preventDefault();answer(Number(e.key)-1,'keyboard');}
});
$('pause').addEventListener('click',()=>{if(session?.phase==='paused')session.resume(clock());else session?.pause(clock());renderGame();});
$('stop').addEventListener('click',()=>{session?.stop(clock());renderGame();});
$('accept-suggestion').addEventListener('click',()=>{session?.acceptSuggestion();renderGame();});
function pauseFor(event){if(session?.pause(clock())){session.events.push({event,round:session.counter});renderGame();}}
document.addEventListener('visibilitychange',()=>{if(document.hidden)pauseFor('hidden_tab');});
window.addEventListener('resize',()=>pauseFor('viewport_resize'));
document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',()=>pauseFor('section_navigation')));
$('mode').addEventListener('change',()=>{if(!active()){session=null;renderGame();$('cue').textContent='Configure the run, then load the first trial.';}});
$('target-size').addEventListener('change',()=>document.documentElement.style.setProperty('--target',`${Number($('target-size').value)}px`));
$('reduce-motion').addEventListener('change',()=>document.documentElement.classList.toggle('reduce-motion',$('reduce-motion').checked));
document.documentElement.classList.add('reduce-motion');
setInterval(renderTimer,200);
$('export-session').addEventListener('click',()=>{
  const output=session.export();output.settings={target_size_px:Number($('target-size').value),reduced_motion:$('reduce-motion').checked};
  output.signal_observations=observations;output.signal_note='Independent window observations, not synchronised EEG acquisition. Classifications never control game difficulty.';
  download('neuroweave-session.json',JSON.stringify(output,null,2));
});
$('export-csv').addEventListener('click',()=>download('neuroweave-rounds.csv',toCSV(session.records),'text/csv'));

function recordObservation(){
  if(!signalAnalysis||observations.length>=200)return;
  observations.push({observed_at_iso:new Date().toISOString(),source:signalMode==='recorded'?'physionet-eegmmidb':signalTrusted?'synthetic':'user-supplied',
    epoch_id:signalMode==='recorded'?REAL_EXAMPLE.provenance.epoch_id:null,
    usable:signalAnalysis.quality.usable,prediction:signalAnalysis.label==null?null:MODEL.classes[signalAnalysis.label],
    probabilities:signalAnalysis.probabilities});
}
function plotSignal(){
  const samples=signal.samples,colors=['#6b9cff','#ff9858','#91d7f2','#dce5f8'];
  const scale=Math.max(60,...samples.flat().map(Math.abs));
  let svg='<title>EEG waveform, 8 channels, 2 seconds</title>';
  for(let tick=0;tick<=4;tick++)svg+=`<path d="M${42+tick*150} 6V260" stroke="#293951" stroke-width="1"/><text x="${42+tick*150}" y="280" fill="#a6b2c8" font-size="10" text-anchor="middle">${tick*.5}</text>`;
  samples.forEach((channel,c)=>{
    const y=20+c*32;
    const points=channel.map((v,i)=>`${(42+i/255*600).toFixed(2)},${(y-v/scale*13).toFixed(2)}`).join(' ');
    const escaped=signal.channels[c].replace(/[&<>"']/g,v=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[v]));
    svg+=`<text x="5" y="${y+4}" fill="#a6b2c8" font-size="10">${escaped}</text><polyline points="${points}" fill="none" stroke="${colors[c%4]}" stroke-width="1.4"/>`;
  });
  $('waveform').innerHTML=svg;
  $('wave-caption').textContent=`${signalMode==='recorded'?'Recorded':signalTrusted?'Artificial':'Imported'} samples · vertical scale ±${Math.ceil(scale)} µV / channel`;
  const sp=signalAnalysis.spectrum,max=Math.max(...sp.power.slice(0,81),.01),width=290,height=175;
  const points=sp.power.slice(0,81).map((p,i)=>`${40+i/80*width},${195-p/max*height}`).join(' ');
  let chart='<title>Average channel power spectral density from 0 to 40 Hz</title>';
  chart+='<rect x="98" y="20" width="36.25" height="175" fill="#6b9cff17"/><rect x="134.25" y="20" width="123.25" height="175" fill="#ff985815"/>';
  for(let i=0;i<=4;i++)chart+=`<path d="M40 ${195-i*height/4}H330" stroke="#293951"/><text x="34" y="${199-i*height/4}" text-anchor="end" fill="#a6b2c8" font-size="9">${(i*max/4).toFixed(1)}</text>`;
  for(let i=0;i<=4;i++)chart+=`<text x="${40+i*width/4}" y="214" fill="#a6b2c8" text-anchor="middle" font-size="10">${i*10}</text>`;
  chart+=`<polyline points="${points}" fill="none" stroke="#6b9cff" stroke-width="2.5"/><text x="186" y="237" fill="#a6b2c8" font-size="10" text-anchor="middle">Frequency (Hz)</text>`;
  $('spectrum').innerHTML=chart;
}
function renderSignal(){
  const q=quality(signal.samples),sp=spectrum(signal.samples);
  const decoded=signalTrusted?infer(signal.samples,MODEL):{quality:q,label:null,probabilities:null};
  signalAnalysis={...decoded,spectrum:sp};
  $('source-label').textContent=signalMode==='recorded'?'RECORDED EEG · PHYSIONET':signalTrusted?'SYNTHETIC EEG':'IMPORTED · LOCAL ONLY';
  $('seed-label').textContent=signalMode==='recorded'?`${REAL_EXAMPLE.provenance.epoch_id} · 128 Hz`:signalTrusted?`SEED ${signalSeed} · 128 Hz · 2 s`:'128 Hz · 2 s · IMPORT';
  $('recorded-note').hidden=signalMode!=='recorded';
  $('condition').disabled=signalMode!=='synthetic';$('artifact').disabled=signalMode!=='synthetic';$('new-window').disabled=signalMode!=='synthetic';
  $('recorded-window').setAttribute('aria-pressed',String(signalMode==='recorded'));
  $('synthetic-replay').setAttribute('aria-pressed',String(signalMode==='synthetic'));
  $('quality-label').dataset.state=q.usable?'usable':'blocked';
  $('quality-label').textContent=q.usable?'Usable demo window':'Abstain';
  $('quality-detail').textContent=q.usable?'No flat channel or amplitude flag detected.':q.reasons.join(' · ');
  $('prediction').textContent=decoded.label==null?'No prediction':MODEL.classes[decoded.label];
  $('prediction-detail').textContent=signalMode==='recorded'?'Recorded EEG analysis. Real-model evaluation appears in the evidence table below.':!signalTrusted?'The synthetic-only model is disabled for imported data.':!q.usable?'Quality gate blocked inference.':`Softmax score: ${(Math.max(...decoded.probabilities)*100).toFixed(1)}%. Uncalibrated; not a clinical confidence score.`;
  const distances=MODEL.baseline_centres.map(v=>Math.abs(sp.feature-v)),base=distances[1]<distances[0]?1:0;
  $('baseline').textContent=q.usable&&signalTrusted?MODEL.classes[base]:'No prediction';
  $('baseline-detail').textContent=q.usable?`8–13 Hz power: ${sp.alpha.toFixed(1)} µV² · 13–30 Hz power: ${sp.beta.toFixed(1)} µV²`:'Inspect the raw waveform before interpreting its spectrum.';
  plotSignal();recordObservation();
}
function regenerate(){
  signalSeed+=17;signal=makeWindow(signalSeed,Number($('condition').value),$('artifact').value);signalTrusted=true;signalMode='synthetic';$('import-status').textContent='';renderSignal();
}
function loadRecorded(){
  signal={schema:'neuroweave.eeg.v1',source:'physionet-eegmmidb',sample_rate_hz:128,unit:'uV',
    channels:[...REAL_EXAMPLE.channels],samples:REAL_EXAMPLE.samples.map(c=>[...c]),
    provenance:structuredClone(REAL_EXAMPLE.provenance),dataset_doi:REAL_EXAMPLE.dataset_doi,
    license:REAL_EXAMPLE.license,preprocessing:structuredClone(REAL_EXAMPLE.preprocessing)};
  signalTrusted=false;signalMode='recorded';$('import-status').textContent='Public recorded trial · common-average reference · 1–40 Hz offline filter · classification available through the Python benchmark.';renderSignal();
}
$('recorded-window').addEventListener('click',loadRecorded);
$('synthetic-replay').addEventListener('click',regenerate);
$('new-window').addEventListener('click',regenerate);
$('condition').addEventListener('change',regenerate);
$('artifact').addEventListener('change',regenerate);
$('export-window').addEventListener('click',()=>download('neuroweave-eeg-window.json',JSON.stringify(signal,null,2)));
$('import-window').addEventListener('change',async e=>{
  const file=e.target.files?.[0];if(!file)return;
  try{
    if(file.size>500000)throw new Error('Please use a JSON file smaller than 500 KB.');
    const parsed=JSON.parse(await file.text());signal=validateWindow(parsed);signalTrusted=false;signalMode='imported';renderSignal();
    $('import-status').textContent='Imported locally. Quality and spectral analysis are available; classification is disabled.';
  }catch(error){$('import-status').textContent=`Import rejected: ${error.message}`;}
  e.target.value='';
});
$('benchmark-score').textContent=`${(BENCH.cnn.balanced_accuracy*100).toFixed(0)}% / ${(BENCH.spectral_baseline.balanced_accuracy*100).toFixed(0)}%`;
const realNames={bandpower_logistic:'Band power + logistic',csp_lda:'CSP + shrinkage LDA',cnn_ensemble:'Compact CNN · 3 seeds'};
const realRows=$('real-results');realRows.replaceChildren();
for(const [name,metric] of Object.entries(REAL_BENCH.models)){
  const row=document.createElement('tr');
  const interval=metric.subject_bootstrap_95_ci.map(v=>(v*100).toFixed(1)+'%').join('–');
  for(const value of [realNames[name],(metric.subject_macro_balanced_accuracy*100).toFixed(1)+'%',interval]){
    const cell=document.createElement('td');cell.textContent=value;row.append(cell);
  }
  realRows.append(row);
}
const q=REAL_BENCH.quality,testSplit=REAL_BENCH.splits.test;
$('real-cohort').textContent=`${q.accepted_epochs} accepted trials / ${q.rejected_epochs} rejected / ${testSplit.epochs} test trials from ${testSplit.subjects.length} unseen people`;
$('real-subjects').textContent=testSplit.subjects.map(s=>'S'+String(s).padStart(3,'0')).join(' · ');
loadRecorded();renderGame();

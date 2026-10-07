import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM,VirtualConsole} from 'jsdom';
const html=readFileSync(new URL('../dist/index.html',import.meta.url),'utf8');
function setup(t){
  const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e));
  const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://example.invalid/',pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){w.structuredClone=structuredClone;w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};}});
  t.after(()=>{dom.window.close();assert.deepEqual(errors,[]);});
  return {w:dom.window,$:id=>dom.window.document.getElementById(id)};
}
const click=(w,id)=>w.document.getElementById(id).click();
function correctRound(w,$){
  if(!$('round-label').textContent.includes('PREVIEW'))click(w,'advance');
  const expected=Array.from($('cue').textContent.matchAll(/([1-4]) ·/g),m=>m[1]);
  click(w,'advance');
  assert.ok(!$('cue').textContent.includes('Node')&&!$('cue').textContent.includes('Pulse'));
  for(const key of expected)w.document.dispatchEvent(new w.KeyboardEvent('keydown',{key,bubbles:true}));
}
test('standalone page initialises recorded EEG analysis and idle game',t=>{
  const {w,$}=setup(t);assert.ok($('waveform').querySelectorAll('polyline').length===8);assert.equal($('prediction').textContent,'No prediction');assert.match($('source-label').textContent,/RECORDED EEG/);assert.equal($('completed').textContent,'0');assert.ok([...w.document.querySelectorAll('[data-target]')].every(b=>b.disabled));
});
test('four keyboard rounds produce review rows and an optional difficulty suggestion',t=>{
  const {w,$}=setup(t);for(let i=0;i<4;i++)correctRound(w,$);assert.equal($('completed').textContent,'4');assert.equal($('round-table').children.length,4);assert.equal($('suggestion').hidden,false);click(w,'accept-suggestion');click(w,'advance');assert.equal([...$('cue').textContent.matchAll(/([1-4]) ·/g)].length,3);
});
test('pause hides the cue and blocks all targets until resume',t=>{
  const {w,$}=setup(t);click(w,'advance');click(w,'advance');click(w,'pause');assert.match($('cue').textContent,/paused/);w.document.querySelector('[data-target]').click();assert.equal($('completed').textContent,'0');click(w,'pause');assert.equal(w.document.querySelector('[data-target]').disabled,false);
});
test('artefact selector makes model abstain and clean replay restores prediction',t=>{
  const {w,$}=setup(t);click(w,'synthetic-replay');$('artifact').value='spike';$('artifact').dispatchEvent(new w.Event('change'));assert.equal($('prediction').textContent,'No prediction');assert.equal($('quality-label').textContent,'Abstain');$('artifact').value='clean';$('artifact').dispatchEvent(new w.Event('change'));assert.match($('prediction').textContent,/Condition/);
});
test('rule activity retains its cue, records a response and finish-early stops safely',t=>{
  const {w,$}=setup(t);$('mode').value='switch';$('mode').dispatchEvent(new w.Event('change'));click(w,'advance');const key=$('cue').textContent.match(/([1-4]) ·/)[1];click(w,'advance');assert.match($('cue').textContent,/MATCH/);w.document.dispatchEvent(new w.KeyboardEvent('keydown',{key,bubbles:true}));assert.equal($('correct').textContent,'1 / 1');click(w,'advance');click(w,'stop');assert.match($('round-label').textContent,/STOPPED/);assert.equal($('export-session').disabled,false);
});
test('imported synthetic-labelled file cannot enable the synthetic-only model',async t=>{
  const {w,$}=setup(t);const fixture=readFileSync(new URL('../data/example-window.json',import.meta.url),'utf8');
  Object.defineProperty($('import-window'),'files',{value:[{size:fixture.length,text:async()=>fixture}],configurable:true});
  $('import-window').dispatchEvent(new w.Event('change'));await new Promise(r=>setImmediate(r));
  assert.equal($('prediction').textContent,'No prediction');assert.match($('source-label').textContent,/IMPORTED/);assert.equal($('quality-label').textContent,'Usable demo window');
});
test('recorded replay never uses synthetic predictions and retains motor-channel labels',t=>{
  const {w,$}=setup(t);assert.equal($('condition').disabled,true);assert.match($('waveform').textContent,/FC3/);
  click(w,'synthetic-replay');assert.match($('prediction').textContent,/Condition/);assert.equal($('condition').disabled,false);
  click(w,'recorded-window');assert.equal($('prediction').textContent,'No prediction');assert.equal($('baseline').textContent,'No prediction');
  assert.equal($('condition').disabled,true);assert.equal($('recorded-note').hidden,false);
});
test('real evidence table reports held-out participant scores separately from synthetic accuracy',t=>{
  const {w,$}=setup(t);const report=JSON.parse(readFileSync(new URL('../reports/physionet-pilot/benchmark.json',import.meta.url),'utf8'));
  assert.equal($('real-results').children.length,3);
  assert.match($('real-results').textContent,new RegExp((report.models.cnn_ensemble.subject_macro_balanced_accuracy*100).toFixed(1).replace('.','\\.')+'%'));
  assert.match($('real-cohort').textContent,/6 unseen people/);assert.match($('benchmark-score').textContent,/100% \/ 100%/);
});
test('imported channel text is displayed safely without becoming SVG markup',async t=>{
  const {w,$}=setup(t);const fixture=JSON.parse(readFileSync(new URL('../data/example-window.json',import.meta.url),'utf8'));
  fixture.channels[0]='<svg onload="alert(1)">';const text=JSON.stringify(fixture);
  Object.defineProperty($('import-window'),'files',{value:[{size:text.length,text:async()=>text}],configurable:true});
  $('import-window').dispatchEvent(new w.Event('change'));await new Promise(r=>setImmediate(r));
  assert.match($('source-label').textContent,/IMPORTED/);assert.equal($('waveform').querySelectorAll('svg').length,0);
  assert.ok($('waveform').textContent.includes('<svg onload="alert(1)">'));
});

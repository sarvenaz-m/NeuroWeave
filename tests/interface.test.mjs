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
test('standalone page initialises charts, model output and idle game',t=>{
  const {w,$}=setup(t);assert.ok($('waveform').querySelectorAll('polyline').length===8);assert.match($('prediction').textContent,/Condition/);assert.equal($('completed').textContent,'0');assert.ok([...w.document.querySelectorAll('[data-target]')].every(b=>b.disabled));
});
test('four keyboard rounds produce review rows and an optional difficulty suggestion',t=>{
  const {w,$}=setup(t);for(let i=0;i<4;i++)correctRound(w,$);assert.equal($('completed').textContent,'4');assert.equal($('round-table').children.length,4);assert.equal($('suggestion').hidden,false);click(w,'accept-suggestion');click(w,'advance');assert.equal([...$('cue').textContent.matchAll(/([1-4]) ·/g)].length,3);
});
test('pause hides the cue and blocks all targets until resume',t=>{
  const {w,$}=setup(t);click(w,'advance');click(w,'advance');click(w,'pause');assert.match($('cue').textContent,/paused/);w.document.querySelector('[data-target]').click();assert.equal($('completed').textContent,'0');click(w,'pause');assert.equal(w.document.querySelector('[data-target]').disabled,false);
});
test('artefact selector makes model abstain and clean replay restores prediction',t=>{
  const {w,$}=setup(t);$('artifact').value='spike';$('artifact').dispatchEvent(new w.Event('change'));assert.equal($('prediction').textContent,'No prediction');assert.equal($('quality-label').textContent,'Abstain');$('artifact').value='clean';$('artifact').dispatchEvent(new w.Event('change'));assert.match($('prediction').textContent,/Condition/);
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

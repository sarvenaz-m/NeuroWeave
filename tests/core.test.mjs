import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {makeWindow,quality,validateWindow,spectrum,infer,PlaySession,toCSV} from '../src/core.js';
const model=JSON.parse(readFileSync(new URL('../models/tinycnn.json',import.meta.url)));
const reference=JSON.parse(readFileSync(new URL('reference.json',import.meta.url)));

test('browser CNN reproduces Python forward pass on four unseen virtual-subject windows',()=>{
  for(const fixture of reference){const actual=infer(fixture.samples,model);actual.probabilities.forEach((p,i)=>assert.ok(Math.abs(p-fixture.probabilities[i])<1e-10));assert.equal(actual.label,fixture.label);}
});
test('browser periodogram matches NumPy FFT values and integrated band feature',()=>{
  for(const fixture of reference){const actual=spectrum(fixture.samples);actual.power.forEach((p,i)=>assert.ok(Math.abs(p-fixture.psd[i])<1e-8));assert.ok(Math.abs(actual.feature-fixture.band_feature)<1e-10);}
});
test('known 10 Hz sine has its PSD maximum at 10 Hz and 50 uV² integrated power',()=>{
  const x=Array.from({length:8},()=>Array.from({length:256},(_,i)=>10*Math.sin(2*Math.PI*10*i/128)));
  const s=spectrum(x);assert.equal(s.frequencies[s.power.indexOf(Math.max(...s.power))],10);
  assert.ok(Math.abs(s.power.reduce((a,b)=>a+b,0)*.5-50)<1e-8);
});
test('artefacts and flat channels prevent CNN inference',()=>{
  for(const a of ['spike','flat']){const x=makeWindow(144,0,a);assert.equal(quality(x.samples).usable,false);assert.equal(infer(x.samples,model).probabilities,null);}
});
test('non-finite and malformed inputs fail quality checks',()=>{
  assert.equal(quality([]).usable,false);const x=makeWindow().samples;x[0][1]=NaN;assert.equal(quality(x).usable,false);
});
test('window import checks schema, shape, units and unique channel labels',()=>{
  const x=makeWindow();assert.equal(validateWindow(x).source,'user-supplied');
  for(const patch of [{sample_rate_hz:256},{unit:'mV'},{schema:'other'},{channels:Array(8).fill('C')},{samples:[[1,2]]}])assert.throws(()=>validateWindow({...x,...patch}));
});
test('window generator is deterministic without sharing arrays',()=>{
  const a=makeWindow(4,1),b=makeWindow(4,1);assert.deepEqual(a,b);a.samples[0][0]=0;assert.notEqual(a.samples[0][0],b.samples[0][0]);
});
test('responses outside active phase and duplicate final clicks cannot score',()=>{
  const s=new PlaySession({rounds:1});assert.equal(s.respond(0,0),false);s.begin(1);assert.equal(s.respond(0,2),false);s.ready(3);for(const v of s.expected)s.respond(v,4);assert.equal(s.phase,'complete');assert.equal(s.respond(0,5),false);assert.equal(s.records.length,1);
});
test('pause excludes idle time and blocks input',()=>{
  const s=new PlaySession();s.begin(0);s.ready(10);s.respond(s.expected[0],20);s.pause(30);assert.equal(s.respond(1,200),false);s.resume(1030);s.respond(s.expected[1],1040);assert.equal(s.records[0].duration_ms,30);assert.equal(s.records[0].paused_ms,1000);
});
test('preview pause is not subtracted from response timing',()=>{
  const s=new PlaySession();s.begin(0);s.pause(10);s.resume(1000);s.ready(1100);for(const v of s.expected)s.respond(v,1200);assert.equal(s.records[0].duration_ms,100);
});
test('clock reversal and invalid configuration are rejected',()=>{
  assert.throws(()=>new PlaySession({level:7}));const s=new PlaySession();s.begin(20);assert.throws(()=>s.ready(19));
});
test('difficulty changes require explicit acceptance after four completed rounds',()=>{
  const s=new PlaySession();let t=0;
  for(let i=0;i<4;i++){s.begin(t++);s.ready(t++);for(const v of s.expected)s.respond(v,t++);}
  assert.equal(s.level,2);assert.equal(s.suggestion(),3);assert.equal(s.acceptSuggestion(),true);assert.equal(s.level,3);assert.equal(s.events[0].after_round,4);
});
test('rule switching changes the expected response and remains seed-reproducible',()=>{
  const s=new PlaySession({mode:'switch'});let t=0;
  for(let i=0;i<4;i++){s.begin(t++);assert.equal(s.rule,i<2?'match':'opposite');assert.equal(s.expected[0],i<2?s.cue:(s.cue+2)%4);s.ready(t++);s.respond(s.expected[0],t++);}
});
test('early finish preserves completed rounds and does not score unfinished work',()=>{
  const s=new PlaySession();s.begin(0);s.ready(1);s.respond(s.expected[0],2);s.stop(3);assert.equal(s.records.length,0);assert.equal(s.phase,'stopped');assert.equal(s.events[0].partial_round,1);
});
test('JSON export cannot mutate engine state; CSV has one row per completed round',()=>{
  const s=new PlaySession({rounds:1});s.begin(0);s.ready(1);for(const v of s.expected)s.respond(v,2);const e=s.export();e.records[0].correct=false;assert.equal(s.records[0].correct,true);assert.equal(e.behaviour_source,'local_browser_interaction');assert.equal(toCSV(s.records).trim().split('\n').length,2);
});

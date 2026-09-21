export const VERSION = '1.1.0';
export const SHAPES = ['Node', 'Pulse', 'Phase', 'Gate'];
export function rng(seed=144) {
  let s=seed>>>0 || 1;
  return ()=>{s^=s<<13;s^=s>>>17;s^=s<<5;return (s>>>0)/4294967296;};
}
export function mean(a){return a.reduce((s,v)=>s+v,0)/a.length;}
export function median(a){if(!a.length)return null;const b=[...a].sort((x,y)=>x-y),i=Math.floor(b.length/2);return b.length%2?b[i]:(b[i-1]+b[i])/2;}
export function quality(samples){
  if(!Array.isArray(samples)||samples.length!==8||samples.some(c=>!Array.isArray(c)||c.length!==256||c.some(x=>!Number.isFinite(x))))
    return {usable:false,reasons:['Invalid shape or non-finite samples']};
  const reasons=[];
  if(samples.some(c=>{const avg=mean(c);return Math.sqrt(mean(c.map(v=>(v-avg)**2)))<.5;}))reasons.push('Flat channel');
  if(samples.some(c=>c.some(v=>Math.abs(v)>150)))reasons.push('Amplitude exceeds demo threshold');
  return {usable:!reasons.length,reasons};
}
export function makeWindow(seed=144,condition=0,artifact='clean'){
  const random=rng(seed), t=Array.from({length:256},(_,i)=>i/128);
  const samples=Array.from({length:8},()=>{
    const phase=random()*Math.PI*2,gain=.65+random()*.7,drift=.15+random()*.65;
    return t.map(v=>gain*(14*Math.sin(2*Math.PI*(condition?20:10)*v+phase)+3*Math.sin(2*Math.PI*(condition?10:20)*v+phase*.7))+4*Math.sin(2*Math.PI*drift*v+phase)+(random()+random()+random()-1.5)*8);
  });
  if(artifact==='spike')for(let i=108;i<120;i++)samples[0][i]+=220;
  if(artifact==='flat')samples[3]=Array(256).fill(0);
  return {schema:'neuroweave.eeg.v1',source:'synthetic',sample_rate_hz:128,unit:'uV',channels:Array.from({length:8},(_,i)=>`C${i+1}`),samples};
}
export function validateWindow(obj){
  if(!obj||obj.schema!=='neuroweave.eeg.v1'||obj.sample_rate_hz!==128||obj.unit!=='uV')throw new Error('Use neuroweave.eeg.v1 with 128 Hz samples in uV.');
  if(!Array.isArray(obj.channels)||obj.channels.length!==8||obj.channels.some(v=>typeof v!=='string'||v.length>24)||new Set(obj.channels).size!==8)throw new Error('Eight unique channel labels are required.');
  if(!Array.isArray(obj.samples)||obj.samples.length!==8||obj.samples.some(c=>!Array.isArray(c)||c.length!==256||c.some(v=>!Number.isFinite(v)||Math.abs(v)>100000)))throw new Error('Expected eight channels of 256 finite samples each (absolute amplitude ≤ 100000 uV).');
  return {schema:obj.schema,source:'user-supplied',sample_rate_hz:128,unit:'uV',channels:[...obj.channels],samples:obj.samples.map(c=>[...c])};
}
export function spectrum(samples){
  const n=256,fs=128,window=Array.from({length:n},(_,i)=>.5-.5*Math.cos(2*Math.PI*i/n));
  const norm=fs*window.reduce((s,v)=>s+v*v,0), p=Array(129).fill(0);
  for(const channel of samples){
    const avg=mean(channel),x=channel.map((v,i)=>(v-avg)*window[i]);
    for(let k=0;k<=128;k++){
      let re=0,im=0;
      for(let i=0;i<n;i++){re+=x[i]*Math.cos(2*Math.PI*k*i/n);im-=x[i]*Math.sin(2*Math.PI*k*i/n);}
      p[k]+=(re*re+im*im)/norm*(k===0||k===128?1:2)/samples.length;
    }
  }
  const freqs=p.map((_,i)=>i*.5);
  const alpha=p.reduce((s,v,i)=>s+(freqs[i]>=8&&freqs[i]<13?v*.5:0),0);
  const beta=p.reduce((s,v,i)=>s+(freqs[i]>=13&&freqs[i]<=30?v*.5:0),0);
  return {frequencies:freqs,power:p,alpha,beta,feature:Math.log((beta+1e-8)/(alpha+1e-8))};
}
export function infer(samples,model){
  const q=quality(samples);
  if(!q.usable)return {quality:q,probabilities:null,label:null};
  const {kernel,bias,head,head_bias}=model.parameters;
  const x=samples.map(c=>{const avg=mean(c);return c.map(v=>(v-avg)/20);});
  const pooled=Array(8).fill(0);
  for(let out=0;out<8;out++){
    for(let t=0;t<60;t++){
      let sum=bias[out];
      for(let c=0;c<8;c++)for(let k=0;k<17;k++)sum+=x[c][t*4+k]*kernel[out][c][k];
      pooled[out]+=Math.max(0,sum)/60;
    }
  }
  const logits=head_bias.map((v,i)=>v+pooled.reduce((s,x,j)=>s+x*head[j][i],0));
  const max=Math.max(...logits),exp=logits.map(v=>Math.exp(v-max)),total=exp[0]+exp[1];
  const probabilities=exp.map(v=>v/total);
  return {quality:q,probabilities,label:probabilities[1]>probabilities[0]?1:0};
}
export class PlaySession {
  constructor({mode='memory',level=2,seed=144,rounds=8}={}){
    if(!['memory','switch'].includes(mode)||![2,3,4].includes(level)||!Number.isInteger(rounds)||rounds<1||rounds>24)throw new Error('Invalid session settings');
    this.mode=mode;this.level=level;this.seed=seed;this.rounds=rounds;this.random=rng(seed);
    this.records=[];this.events=[];this.phase='idle';this.counter=0;this.lastTime=-Infinity;
  }
  time(now){if(!Number.isFinite(now)||now<this.lastTime)throw new Error('Monotonic time required');this.lastTime=now;}
  begin(now){
    this.time(now);
    if(!['idle','feedback'].includes(this.phase))return false;
    if(this.records.length>=this.rounds){this.phase='complete';return false;}
    this.counter=this.records.length+1;
    this.cue=Math.floor(this.random()*4);
    this.rule=Math.floor((this.counter-1)/2)%2?'opposite':'match';
    this.expected=this.mode==='memory'?Array.from({length:this.level},()=>Math.floor(this.random()*4)):[this.rule==='match'?this.cue:(this.cue+2)%4];
    this.responses=[];this.pausedMs=0;this.phase='preview';this.levelAtStart=this.level;return true;
  }
  ready(now){this.time(now);if(this.phase!=='preview')return false;this.started=now;this.phase='active';return true;}
  respond(value,now,input='pointer'){
    this.time(now);
    if(this.phase!=='active'||!Number.isInteger(value)||value<0||value>3)return false;
    this.responses.push({value,ms:now-this.started-this.pausedMs,input:input==='keyboard'?'keyboard':'pointer'});
    if(this.responses.length===this.expected.length){
      const correct=this.responses.every((r,i)=>r.value===this.expected[i]);
      this.records.push({round:this.counter,mode:this.mode,level:this.levelAtStart,rule:this.mode==='switch'?this.rule:null,
        expected:[...this.expected],responses:this.responses.map(r=>({...r})),correct,
        duration_ms:now-this.started-this.pausedMs,paused_ms:this.pausedMs});
      this.phase=this.records.length===this.rounds?'complete':'feedback';
    }
    return true;
  }
  pause(now){this.time(now);if(!['preview','active'].includes(this.phase))return false;this.previous=this.phase;this.pausedAt=now;this.phase='paused';return true;}
  resume(now){this.time(now);if(this.phase!=='paused')return false;if(this.previous==='active')this.pausedMs+=now-this.pausedAt;this.phase=this.previous;return true;}
  stop(now){this.time(now);if(['idle','complete','stopped'].includes(this.phase))return false;this.events.push({event:'stop',partial_round:this.counter});this.phase='stopped';return true;}
  suggestion(){
    if(this.mode!=='memory'||this.records.length<4||this.phase!=='feedback')return null;
    const last=this.records.slice(-4);if(last.some(r=>r.level!==this.level))return null;
    const ratio=last.filter(r=>r.correct).length/4;
    const proposed=ratio>=.75?Math.min(4,this.level+1):ratio<=.25?Math.max(2,this.level-1):this.level;
    return proposed===this.level?null:proposed;
  }
  acceptSuggestion(){const n=this.suggestion();if(n===null)return false;this.events.push({event:'level_change',after_round:this.records.length,from:this.level,to:n});this.level=n;return true;}
  summary(){return {completed:this.records.length,correct:this.records.filter(r=>r.correct).length,median_duration_ms:median(this.records.map(r=>r.duration_ms))};}
  export(){return {schema:'neuroweave.session.v1',app_version:VERSION,behaviour_source:'local_browser_interaction',clinical_validation:false,
    symbols:[...SHAPES],mode:this.mode,seed:this.seed,planned_rounds:this.rounds,status:this.phase,records:structuredClone(this.records),events:structuredClone(this.events),summary:this.summary()};}
}
export function toCSV(records){
  return ['round,mode,level,rule,correct,duration_ms,paused_ms',...records.map(r=>[r.round,r.mode,r.level,r.rule||'',r.correct,Math.round(r.duration_ms),Math.round(r.paused_ms)].join(','))].join('\n')+'\n';
}

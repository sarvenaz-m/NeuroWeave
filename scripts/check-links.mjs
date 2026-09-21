import {readdir,readFile,access} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
const root=resolve(new URL('..',import.meta.url).pathname);
async function walk(path){const result=[];for(const e of await readdir(path,{withFileTypes:true})){if(['node_modules','.git','.venv','__pycache__'].includes(e.name))continue;const p=resolve(path,e.name);if(e.isDirectory())result.push(...await walk(p));else if(e.name.endsWith('.md'))result.push(p);}return result;}
let count=0;const missing=[];
for(const file of await walk(root)){
 const body=await readFile(file,'utf8');
 for(const match of body.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)){
  const href=match[1].split('#')[0];if(!href||/^[a-z]+:/i.test(href))continue;
  try{await access(resolve(dirname(file),decodeURIComponent(href)));count++;}catch{missing.push(`${file}: ${href}`);}
 }
}
if(missing.length)throw Error(missing.join('\n'));
console.log(`${count} local Markdown links resolve.`);

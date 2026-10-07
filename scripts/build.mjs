import {readFile,writeFile,mkdir} from 'node:fs/promises';
const read=p=>readFile(new URL('../'+p,import.meta.url),'utf8');
const html=(await read('src/index.html')).replace(/<img id="hero-artwork"[^>]+>/,await read('docs/media/signal-core.svg'));
const css=await read('src/style.css');
const core=(await read('src/core.js')).replace(/^export /gm,'');
const app=(await read('src/app.js')).replace(/^import .*;\n/gm,'');
const model=await read('models/tinycnn.json'),benchmark=await read('reports/synthetic-benchmark.json');
const realReport=JSON.parse(await read('reports/physionet-pilot/benchmark.json'));
const realSummary=JSON.stringify({dataset:realReport.dataset,splits:realReport.splits,quality:realReport.quality,
  primary_metric:realReport.primary_metric,models:realReport.models,comparisons:realReport.comparisons});
const realWindow=await read('reports/physionet-pilot/example-real-window.json');
const js=`'use strict';\nconst MODEL=${model};\nconst BENCH=${benchmark};\nconst REAL_BENCH=${realSummary};\nconst REAL_EXAMPLE=${realWindow};\n${core}\n${app}`;
if(js.includes('</script>'))throw Error('Unsafe embedded closing script tag');
const built=html.replace('<link rel="stylesheet" href="style.css">',`<style>${css}</style>`)
  .replace('<script type="module" src="app.js"></script>',`<script>${js}</script>`);
await mkdir(new URL('../dist/',import.meta.url),{recursive:true});
await writeFile(new URL('../dist/index.html',import.meta.url),built);
console.log(`Built standalone demo (${Buffer.byteLength(built)} bytes); no runtime network dependencies.`);

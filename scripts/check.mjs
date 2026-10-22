import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const edition=JSON.parse(read('docs/edition.json'));
const meta=JSON.parse(read('edition.json'));
assert.equal(edition.metadata_sha256,sha(read('edition.json')));
assert.equal(edition.edition,meta.version);
assert.equal(edition.edition,JSON.parse(read('package.json')).version);
assert(read('CITATION.cff').includes(`version: ${meta.version}`));
const book=read('BOOK_UA.md');
assert.equal(sha(book),edition.book_sha256);
assert.equal(book,read('docs/downloads/BOOK_UA.md'));
for(const f of edition.source_files){
 const source=read(f.path);
 assert.equal(sha(source),f.sha256);
 const numbers=[...source.matchAll(/^## (\d+) /gm)].map(m=>Number(m[1]));
 assert.deepEqual(numbers,numbers.map((_,i)=>i+1),`section numbering mismatch: ${f.path}`);
}
assert.equal(edition.empirical_trials,0);
const report=JSON.parse(read('research/runtime-results.json'));
assert.equal(edition.runtime_report_sha256,sha(read('research/runtime-results.json')));
assert.equal(edition.runtime_checks,report.tests_run);
assert.equal(report.success,true);
assert.equal(report.llm_trials,0);
assert.equal(report.results.length,report.tests_run);
assert(report.results.every(r=>r.status==='passed'));
const reportInputs=fs.readdirSync(path.join(root,'examples'))
 .filter(f=>/\.(?:py|json)$/.test(f)).map(f=>`examples/${f}`);
reportInputs.push('research/run_runtime_checks.py');
assert(reportInputs.includes('examples/iris-events.json'),'missing runtime fixture');
assert.deepEqual(Object.keys(report.sources).sort(),reportInputs.sort(),'runtime report input coverage mismatch');
for(const [file,hash] of Object.entries(report.sources))assert.equal(sha(read(file)),hash,`stale runtime report: ${file}`);
const html=read('docs/index.html');
assert.equal((html.match(/class="part"/g)||[]).length,meta.parts.length);
for(const p of meta.parts)assert(html.includes(`id="${p.id}"`));
for(const a of ['style.css','reader.js']){const raw=fs.readFileSync(path.join(root,'docs/assets',a));assert(html.includes(`${a}?v=${sha(raw).slice(0,12)}`));}
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
assert.equal(new Set(ids).size,ids.length,'duplicate HTML ids');
for(const m of html.matchAll(/href="#([^"]+)"/g))assert(ids.includes(m[1]),`missing anchor ${m[1]}`);
const markdown=['README.md','REVIEW_GUIDE.md','ABSTRACT.en.md','AUTHORS.md','READER_NOTE.md',
 'CHANGELOG.md','BOOK_UA.md','examples/README.md','research/comparison-notes.md',...edition.source_files.map(f=>f.path)];
for(const f of markdown){
 const s=read(f);
 assert(!/\/home\/pustota|itoken=|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}/.test(s),`private material pattern in ${f}`);
 for(const m of s.matchAll(/\]\(([^)]+)\)/g)){
  if(!/^(?:https?:|#)/.test(m[1]))assert(fs.existsSync(path.resolve(root,path.dirname(f),m[1])),`${f}: missing ${m[1]}`);
  if(m[1].startsWith('https://diadkoshmek.github.io/ai-ontology/#')){
   const target=decodeURIComponent(new URL(m[1]).hash.slice(1));
   assert(ids.includes(target),`${f}: missing reader anchor ${target}`);
  }
 }
}
assert(!/<script[^>]+src="https?:|<link[^>]+href="https?:/.test(html),'remote executable/style dependency');
const pdf=JSON.parse(read('docs/pdf-edition.json'));
assert.equal(pdf.schema,'ai-ontology-pdf/1');
assert.equal(pdf.edition,meta.version);
assert.equal(pdf.pdf,'docs/downloads/ai-ontology-book-01-uk.pdf');
const pdfInputs=['edition.json','BOOK_UA.md','build/tokens.json','scripts/build_pdf.py','requirements.txt',
 'docs/assets/serif.ttf','docs/assets/serif-italic.ttf','docs/assets/serif-bold.ttf'];
assert.deepEqual(Object.keys(pdf.inputs).sort(),pdfInputs.sort(),'PDF input coverage mismatch');
for(const [file,hash] of Object.entries(pdf.inputs))assert.equal(sha(fs.readFileSync(path.join(root,file))),hash,`stale PDF input: ${file}`);
const pdfBytes=fs.readFileSync(path.join(root,pdf.pdf));
assert.equal(pdfBytes.subarray(0,5).toString(),'%PDF-');
assert.equal(sha(pdfBytes),pdf.pdf_sha256,'PDF artifact hash mismatch');
console.log('Source hashes, local links, anchors, full-text parity and asset bindings verified. Pattern scan is not a comprehensive secret audit.');

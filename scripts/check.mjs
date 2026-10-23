import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
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
assert(read('research/README.md').includes(`accompanying book v${meta.version}**`),'research README edition mismatch');
// Research artifacts retain their originating edition when only the book is
// revised. Their full rendering inputs and bytes are still checked below.
const notLaterEdition = origin => {
 assert(/^\d+\.\d+\.\d+$/.test(origin),'invalid artifact origin edition');
 const from=origin.split('.').map(Number),to=meta.version.split('.').map(Number);
 const at=from.findIndex((v,i)=>v!==to[i]);
 assert(at<0||from[at]<to[at],'artifact edition is newer than the book');
};
const claims=JSON.parse(execFileSync('python3',['scripts/check_claim_history.py'],{cwd:root,encoding:'utf8'}));
assert.equal(claims.edition,meta.version);
assert.equal(claims.semantic_support_verified,false);
const book=read('BOOK_UA.md');
assert.equal(sha(book),edition.book_sha256);
assert.equal(book,read('docs/downloads/BOOK_UA.md'));
for(const f of edition.source_files){
 const source=read(f.path);
 assert.equal(sha(source),f.sha256);
 const numbers=[...source.matchAll(/^## (\d+) /gm)].map(m=>Number(m[1]));
 assert.deepEqual(numbers,numbers.map((_,i)=>i+1),`section numbering mismatch: ${f.path}`);
}
const studyBytes=read('research/study-summary.json');
const study=JSON.parse(studyBytes);
assert.equal(edition.study_summary_sha256,sha(studyBytes));
assert.equal(edition.scored_model_calls,study.scored_model_calls);
assert.equal(edition.scored_model_calls,study.cohorts.reduce((n,c)=>n+c.scored_calls,0));
assert.equal(edition.model_cohorts,study.cohorts.length);
assert.equal(edition.scored_model_calls_scope,'original-scoped-continuity-study-only');
for(const row of edition.additional_evaluations){
 const raw=read(row.path);assert.equal(sha(raw),row.sha256,`stale evaluation report: ${row.path}`);
 const report=JSON.parse(raw);
 assert.equal(row.captured_turns,report.scored_calls??report.observed_complete_rows??report.captured_calls);
}
assert.equal(edition.total_captured_model_turns,edition.scored_model_calls+edition.additional_evaluations.reduce((n,r)=>n+r.captured_turns,0));
for(const dir of ['participation_pilot','gpt_profile_pilot','gpt_profile_pilot_v2','transfer_calibration','transfer_calibration_v2','transfer_calibration_v3','transfer_reading','handoff_repair','closed_loop']){
 const frozen=JSON.parse(read(`research/${dir}/freeze.json`));
 for(const [file,hash] of Object.entries(frozen.input_sha256))assert.equal(sha(read(`research/${dir}/${file}`)),hash,`frozen profile source drift: ${dir}/${file}`);
}
assert.equal(edition.unique_cases,study.unique_cases);
assert.equal(edition.integration_smoke_calls,study.integration_smoke_calls);
for(const [file,hash] of Object.entries(study.inputs_sha256))assert.equal(sha(read(file)),hash,`stale study summary: ${file}`);
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
const foundation=JSON.parse(read('research/foundation-checks.json'));
assert.equal(foundation.success,true);assert.equal(foundation.llm_calls,0);
for(const [file,hash] of Object.entries(foundation.sources))assert.equal(sha(read(file)),hash,`stale foundation check: ${file}`);
const supplement=JSON.parse(read('research/closed-loop-supplement.json'));
for(const [file,hash] of Object.entries(supplement.source_sha256))assert.equal(sha(read(file)),hash,`stale closed-loop supplement: ${file}`);
const cases=JSON.parse(read('research/engineering-cases-results.json'));
assert.equal(cases.schema,'ontology-engineering-cases/1');
assert.equal(cases.llm_calls,0);
assert.equal(cases.historical_failures_reproduced,2);
const caseInputs=fs.readdirSync(path.join(root,'research/engineering_cases'))
 .filter(f=>f.endsWith('.py')||f==='provenance.json').map(f=>`research/engineering_cases/${f}`);
assert.deepEqual(Object.keys(cases.source_sha256).sort(),caseInputs.sort(),'engineering case source coverage mismatch');
for(const [file,hash] of Object.entries(cases.source_sha256))assert.equal(sha(read(file)),hash,`stale engineering case: ${file}`);
const html=read('docs/index.html');
assert.equal((html.match(/class="part"/g)||[]).length,meta.parts.length);
for(const p of meta.parts)assert(html.includes(`id="${p.id}"`));
for(const a of ['style.css','reader.js']){const raw=fs.readFileSync(path.join(root,'docs/assets',a));assert(html.includes(`${a}?v=${sha(raw).slice(0,12)}`));}
const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
assert.equal(new Set(ids).size,ids.length,'duplicate HTML ids');
for(const m of html.matchAll(/href="#([^"]+)"/g))assert(ids.includes(m[1]),`missing anchor ${m[1]}`);
const markdown=['README.md','REVIEW_GUIDE.md','ABSTRACT.en.md','AUTHORS.md','READER_NOTE.md','CLAIMS.md','practical/README.md','research/HANDOFF_REPAIR_REPORT.md','research/handoff_controls/README.md','research/handoff_repair/README.md',
 'README.uk.md','BOOK_EN.md','ontology/README.md','ontology/FOUNDATION.md','research/CLOSED_LOOP_STUDY.md',
 'CHANGELOG.md','BOOK_UA.md','examples/README.md','research/comparison-notes.md','research/README.md','research/SCOPED_CONTINUITY_STUDY.md','research/PROFILE_PARTICIPATION_STUDY.md','research/READING_TRANSFER_STUDY.md','research/TRANSFER_STUDY_DESIGN.md','research/transfer_reading/THIRD_PARTY_READING.md',...edition.source_files.map(f=>f.path)];
for(const f of markdown){
 const s=read(f);
 assert(!/\/home\/pustota|itoken=|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}/.test(s),`private material pattern in ${f}`);
 for(const m of s.matchAll(/\]\(([^)]+)\)/g)){
  if(!/^(?:https?:|#)/.test(m[1])){
   const localPath=m[1].split(/[?#]/,1)[0];
   assert(fs.existsSync(path.resolve(root,path.dirname(f),localPath)),`${f}: missing ${m[1]}`);
  }
  if(m[1].startsWith('https://diadkoshmek.github.io/ai-ontology/#')){
   const target=decodeURIComponent(new URL(m[1]).hash.slice(1));
   assert(ids.includes(target),`${f}: missing reader anchor ${target}`);
  }
 }
}
assert(!/<script[^>]+src="https?:|<link(?=[^>]+rel="stylesheet")[^>]+href="https?:/.test(html),'remote executable/style dependency');
const renderInputs=paths=>paths.map(f=>fs.readFileSync(path.join(root,f)));
const fontInputs=['docs/assets/serif.ttf','docs/assets/serif-italic.ttf','docs/assets/serif-bold.ttf'];
const bookPdfKey=sha(Buffer.concat([Buffer.from(book),...renderInputs(['edition.json','scripts/build_pdf.py','requirements.txt',...fontInputs])])).slice(0,12);
const transferPdfKey=sha(Buffer.concat(renderInputs(['research/READING_TRANSFER_STUDY.md','research/reading-transfer-results.png','scripts/build_paper.py','requirements.txt',...fontInputs]))).slice(0,12);
const repairPdfKey=sha(Buffer.concat(renderInputs(['research/HANDOFF_REPAIR_REPORT.md','scripts/build_paper.py','requirements.txt',...fontInputs]))).slice(0,12);
const paperPdfKey=sha(Buffer.concat(renderInputs(['research/SCOPED_CONTINUITY_STUDY.md','research/continuity-results.png','scripts/build_paper.py','requirements.txt',...fontInputs]))).slice(0,12);
assert(html.includes(`downloads/ai-ontology-book-01-uk.pdf?v=${bookPdfKey}`),'book PDF download cache binding');
assert(html.includes(`downloads/scoped-continuity-study-en.pdf?v=${paperPdfKey}`),'paper PDF download cache binding');
assert(html.includes(`downloads/reading-transfer-study-en.pdf?v=${transferPdfKey}`),'transfer paper PDF download cache binding');
assert(html.includes(`downloads/handoff-repair-study-en.pdf?v=${repairPdfKey}`),'repair paper PDF download cache binding');
assert(html.includes(`downloads/BOOK_UA.md?v=${sha(book).slice(0,12)}`),'full-text download cache binding');

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
const paper=JSON.parse(read('docs/paper-edition.json'));
assert.equal(paper.schema,'ai-ontology-paper/1');
notLaterEdition(paper.edition);
assert(read('research/SCOPED_CONTINUITY_STUDY.md').includes(`Organization of Self*, v${paper.edition}.`),'working paper origin edition mismatch');
const paperInputs=['research/SCOPED_CONTINUITY_STUDY.md','research/continuity-results.png',
 'scripts/build_paper.py','requirements.txt','docs/assets/serif.ttf','docs/assets/serif-bold.ttf','docs/assets/serif-italic.ttf'];
assert.deepEqual(Object.keys(paper.inputs).sort(),paperInputs.sort(),'paper input coverage mismatch');
for(const [file,hash] of Object.entries(paper.inputs))assert.equal(sha(fs.readFileSync(path.join(root,file))),hash,`stale paper input: ${file}`);
assert.equal(paper.pdf,'docs/downloads/scoped-continuity-study-en.pdf');
const paperBytes=fs.readFileSync(path.join(root,paper.pdf));
assert.equal(paperBytes.subarray(0,5).toString(),'%PDF-');
assert.equal(sha(paperBytes),paper.pdf_sha256,'paper artifact hash mismatch');
const transfer=JSON.parse(read('docs/transfer-paper-edition.json'));
assert.equal(transfer.schema,'ai-ontology-paper/1');
notLaterEdition(transfer.edition);
assert.equal(transfer.pdf,'docs/downloads/reading-transfer-study-en.pdf');
assert.deepEqual(Object.keys(transfer.inputs).sort(),['research/READING_TRANSFER_STUDY.md','research/reading-transfer-results.png','scripts/build_paper.py','requirements.txt',...fontInputs].sort());
for(const [file,hash] of Object.entries(transfer.inputs))assert.equal(sha(fs.readFileSync(path.join(root,file))),hash,`stale transfer paper input: ${file}`);
assert.equal(sha(fs.readFileSync(path.join(root,transfer.pdf))),transfer.pdf_sha256,'transfer paper artifact hash mismatch');
const repair=JSON.parse(read('docs/repair-paper-edition.json'));
assert.equal(repair.schema,'ai-ontology-paper/1');
notLaterEdition(repair.edition);
assert.equal(repair.pdf,'docs/downloads/handoff-repair-study-en.pdf');
assert.deepEqual(Object.keys(repair.inputs).sort(),['research/HANDOFF_REPAIR_REPORT.md','scripts/build_paper.py','requirements.txt',...fontInputs].sort());
for(const [file,hash] of Object.entries(repair.inputs))assert.equal(sha(fs.readFileSync(path.join(root,file))),hash,`stale repair paper input: ${file}`);
assert.equal(sha(fs.readFileSync(path.join(root,repair.pdf))),repair.pdf_sha256,'repair paper artifact hash mismatch');
const figure=JSON.parse(read('research/reading-transfer-figure.json'));
for(const [file,hash] of Object.entries(figure.inputs))assert.equal(sha(fs.readFileSync(path.join(root,file))),hash,`stale transfer figure: ${file}`);
assert.equal(sha(fs.readFileSync(path.join(root,figure.output))),figure.output_sha256,'transfer figure hash mismatch');
console.log('Source hashes, local links, anchors, full-text parity and asset bindings verified. Pattern scan is not a comprehensive secret audit.');

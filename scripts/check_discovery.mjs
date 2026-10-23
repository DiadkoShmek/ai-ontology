import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const e=JSON.parse(read('docs/en-edition.json')),meta=JSON.parse(read('edition.json'));
assert.equal(e.edition,meta.version);assert.equal(e.source_files.length,meta.parts.length);
assert.equal(read('BOOK_EN.md'),read('docs/downloads/BOOK_EN.md'));
assert.equal(sha(read('BOOK_EN.md')),e.book_sha256);
for(const f of e.source_files){
 assert.equal(sha(read(f.path)),f.sha256);assert.equal(sha(read(f.uk_source)),f.uk_sha256);
 const sections=s=>[...s.matchAll(/^## (\d+) /gm)].map(m=>Number(m[1]));
 assert.deepEqual(sections(read(f.path)),sections(read(f.uk_source)),`English section parity: ${f.path}`);
 // Text-labelled pseudocode is translated prose. Executable blocks retain bytes.
 const code=s=>[...s.matchAll(/^```([^\n]*)\n([\s\S]*?)^```/gm)].filter(m=>m[1]!=='text').map(m=>[m[1],m[2]]);
 assert.deepEqual(code(read(f.path)),code(read(f.uk_source)),`English code parity: ${f.path}`);
}
const d=JSON.parse(read('docs/discovery.json'));
assert.equal(d.edition,meta.version);assert.equal(d.indexing_observed,false);
const base='https://diadkoshmek.github.io/ai-ontology/';
assert.equal(d.plain_text_index,base+'llms.txt');
for(const [language,file] of [['en','BOOK_EN.md'],['uk','BOOK_UA.md']]){
 assert.equal(d.complete_texts[language],base+'downloads/'+file);
 assert(read('docs/llms.txt').includes(d.complete_texts[language]));
 assert.equal(read(file),read('docs/downloads/'+file));
}
assert(read('docs/llms.txt').includes(`v${meta.version}`));
assert(read('docs/llms.txt').includes('not a general'));
for(const name of ['inspectable-continuity.md','inspectable-continuity.uk.md']){
 const publicCopy=read('papers/'+name).replace(/\]\((?!https?:|#)([^)]+)\)/g,(_match,ref)=>`](${new URL(ref,'https://github.com/DiadkoShmek/ai-ontology/blob/main/papers/').href})`);
 assert.equal(publicCopy,read('docs/note/'+name));
 assert(!/\]\((?:\.\.\/|inspectable-continuity\.bib)/.test(read('docs/note/'+name)));
 assert(read('docs/llms.txt').includes(base+'note/'+name));
}
assert(read('docs/note/index.html').includes('77/80'));
assert(read('docs/note/index.html').includes('71/80'));
assert(read('docs/note/index.html').includes('not a peer-reviewed publication'));
for(const p of d.canonical_pages){
 const suffix=p.url.split('/ai-ontology/')[1];const html=read(`docs/${suffix}index.html`);
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
 assert.equal(new Set(ids).size,ids.length,`duplicate IDs: ${p.url}`);
 for(const m of html.matchAll(/href="#([^"]+)"/g))assert(ids.includes(m[1]),`missing anchor ${m[1]}: ${p.url}`);
 assert.equal((html.match(/rel="canonical"/g)||[]).length,1);assert(html.includes(`rel="canonical" href="${p.url}"`));
 assert(html.includes(`<html lang="${p.language}"`));
 assert(!html.includes('noindex'));
 const data=JSON.parse(html.match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/)[1]);
 assert.equal(data.url,p.url);assert.equal(data.inLanguage,p.language);
 if(data['@type']==='Book'){
  assert.equal(data.bookEdition,meta.version);assert.equal(data.hasPart.length,meta.parts.length);
  assert.equal((html.match(/class="part"/g)||[]).length,meta.parts.length);
  for(const lang of ['uk','en'])assert(html.includes(`hreflang="${lang}"`));
 }
 assert(read('docs/sitemap.xml').includes(`<loc>${p.url}</loc>`));
}
for(const name of ['vocabulary.json','vocabulary.ttl','context.jsonld'])assert.equal(read(`ontology/${name}`),read(`docs/ontology/${name}`));
const pdf=JSON.parse(read('docs/en-pdf-edition.json'));
assert.equal(pdf.edition,meta.version);
assert.equal(sha(fs.readFileSync(path.join(root,pdf.pdf))),pdf.pdf_sha256);
for(const [f,h] of Object.entries(pdf.inputs))assert.equal(sha(fs.readFileSync(path.join(root,f))),h,`English PDF input drift: ${f}`);
console.log('English source/code parity, PDF bindings and bilingual discovery metadata verified. Content quality and search indexing require separate observation.');

// Deterministic human-readable discovery surfaces, not crawler instructions.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {marked} from 'marked';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read=f=>fs.readFileSync(path.join(root,f),'utf8');
const write=(f,s)=>{fs.mkdirSync(path.dirname(path.join(root,f)),{recursive:true});fs.writeFileSync(path.join(root,f),s);};
const meta=JSON.parse(read('edition.json')),v=JSON.parse(read('ontology/vocabulary.json'));
const base='https://diadkoshmek.github.io/ai-ontology/';
const repo='https://github.com/DiadkoShmek/ai-ontology';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const result=JSON.parse(read('research/closed_loop/results.json'));
const evidenceReturn=JSON.parse(read('research/epistemic_return/results.json'));
const free=evidenceReturn.arms.free_actual,linked=evidenceReturn.arms.linked_actual;
const summary=result.summary.map(s=>`<tr><td>${esc(s.arm)}</td><td>${s.complete}/8</td><td>${s.all_correct}/16</td><td>${s.method_transfer.M0.optimal}/192</td><td>${s.method_transfer.M1.optimal}/192</td><td>${s.input_tokens.toLocaleString('en-US')}</td></tr>`).join('');
function page(title,description,body,headingStyle='font-size:clamp(2rem,5vw,4rem)'){return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} — AI Ontology</title><meta name="description" content="${esc(description)}"><link rel="stylesheet" href="../assets/style.css"></head><body><header class="site-header"><a class="brand" href="../en/">AO<span>AI Ontology</span></a><div class="header-right"><a href="../en/">English book</a><a href="../">Українська</a><a href="${repo}">GitHub ↗</a></div></header><main style="max-width:1000px;margin:5rem auto;padding:0 1.5rem"><article><p class="eyebrow">Artur Onysko · v${meta.version}</p><h1 style="${headingStyle}">${esc(title)}</h1><p>${esc(description)}</p>${body}</article></main><footer class="site-footer"><span>© 2026 Artur Onysko</span><a href="${repo}/blob/main/AUTHORS.md">Authorship and Codex contribution</a><a href="${repo}/blob/main/CLAIMS.md">Claims and limits</a></footer></body></html>`;}
write('docs/research/index.html',page('Agent continuity and method-revision research','Protocols, raw model outputs, executable controls and limits accompanying AI Ontology.',`
<p><a href="../note/">Short methodological note: Inspectable Continuity</a> · <a href="${repo}/blob/main/protocols/continuity-audit-v1.md">Proposed audit profile</a> · <a href="${repo}/blob/main/audit/README.md">Run the audit</a></p>
<h2>Supplementary study · 23 October: scoped evidence return</h2><p>A new finite two-mode task starts with genuinely unavailable channel evidence. One shared initial participant chooses a priced diagnostic; four branches compare unrestricted versus linked notes with actual versus masked results. There are 72 scored GPT-6.1 Sol/high calls and one route canary, eight instances of one authored class.</p><p>Actual feedback changed eight source decisions per memory format. After fresh-session readback, unrestricted notes achieved <strong>${free.full_information_transfer_optimal}/80</strong> full-information-optimal transfer choices and linked notes <strong>${linked.full_information_transfer_optimal}/80</strong>. Notes fitted the same 2048-byte allowance in ${8-free.memory_unavailable}/8 versus ${8-linked.memory_unavailable}/8 actual-feedback instances. All memory refusals were explicit budget refusals, not hidden truncations. Neither arm had a simulated harmful effect.</p><p>The primary linked-format difference was negative. This identifies an implemented retention failure, not general ontology superiority or new algorithm formation. Masked branches retained appropriate uncertainty; their missing opportunities do not establish worse reasoning. The wider method-rebuilding question remains active, and the book edition is unchanged.</p><p><a href="${repo}/blob/main/research/EPISTEMIC_RETURN_STUDY.md">English report</a> · <a href="${repo}/blob/main/research/EPISTEMIC_RETURN_STUDY.uk.md">Український звіт</a> · <a href="${repo}/blob/main/research/epistemic_return/PROTOCOL.md">Frozen protocol</a> · <a href="${repo}/blob/main/research/epistemic_return/responses.jsonl.gz">Raw archive</a> · <a href="${repo}/blob/main/research/epistemic-return-diagnosis.json">Literal budget diagnosis</a></p>
<h2>Executable method revision through an observed return cycle</h2><p>The new developer-controlled study uses 32 requested GPT-6.1 Sol/high calls: eight authored trajectories, two systems and two model stages. Both systems have the same facts, practical rules, finite method language, planner, safety guard, durable memory and revision opportunity. One also receives a prepared relation view.</p><p>Each model builds M0, observes its actual recorded local effects or refusal, and builds M1. Each unchanged method is executed on 24 new worlds: retention, exception and mixed cases. The 768 executions are finite program runs, not 768 model trials or independent participants.</p>
<div style="overflow:auto"><table><thead><tr><th>System</th><th>Complete trajectories</th><th>Correct stages</th><th>M0 transfer optimal</th><th>M1 transfer optimal</th><th>Input tokens</th></tr></thead><tbody>${summary}</tbody></table></div>
<p>The primary paired difference is ${result.primary_difference}. This narrow comparison does not establish general learning, voice, subjective experience, the necessity of the complete circle or a benefit from reading the full book. M1 changes are revision-associated; feedback is not separately causally isolated.</p>
<p><a href="${repo}/blob/main/research/CLOSED_LOOP_STUDY.md">Full report</a> · <a href="${repo}/blob/main/research/closed_loop/PROTOCOL.md">Frozen protocol</a> · <a href="${repo}/blob/main/research/closed_loop/results.json">Recomputed results</a> · <a href="${repo}/blob/main/research/closed_loop/responses.jsonl.gz">Raw archive</a></p>
<h2>Earlier outcomes remain visible</h2><ul><li>Original scoped-memory study: 384 scored calls on two small local models; no general advantage over an information-matched index.</li><li>Reading-mediated transfer: 199 captured calls. Ordinary preparation submitted optimal plans in 12/16 episodes; book preparation in 8/16. Fully traced completion was 0/16 in both.</li><li>Exact handoff repair: eight new instances of one known generator, 24 captured calls; 8/8 fully traced optimal completions with exact transport versus 0/8 freeform. A generic file restores the same data when accessible; codec superiority over that file is not established.</li></ul>
<p><a href="${repo}/blob/main/research/README.md">All protocols, negative results, calibrations and reproduction commands</a> · <a href="${repo}/blob/main/REVIEW_GUIDE.md">Review route</a></p><h2>Representation and implementation</h2><p><a href="../ontology/">The formal vocabulary</a> distinguishes declared purpose, available evidence, recorded use, judgment, effect and permission. <a href="${repo}/blob/main/examples/README.md">The Python reference implementation</a> supplies finite transitions, SQLite/CAS durability and model integration. Mechanical validity and measured benefit are evaluated separately.</p>`));
const terms=Object.entries(v.classes).map(([name,t])=>`<section id="${esc(name)}"><h3>${esc(name)}</h3><p>${esc(t.definition)}</p></section>`).join('');
write('docs/ontology/index.html',page('A finite ontology of situated participation and revision','18 classes, 34 typed relations and nine executable competency questions for inspecting agent continuity, evidence, judgment and revision.',`
<h2>What this vocabulary is for</h2><p>A relation should answer a concrete question: was a criterion adopted or met; was evidence available or used; was a lesson stored or consumed; did a proposed correction also have an action warrant? These are records about situated participation. Their existence does not establish consciousness or successful learning.</p><p><a href="${repo}/blob/main/ontology/FOUNDATION.md">Concept-to-code map</a> · <a href="${repo}/blob/main/ontology/README.md">Wire contract and exact limits</a> · <a href="vocabulary.json">JSON vocabulary</a> · <a href="vocabulary.ttl">Turtle/RDF vocabulary</a> · <a href="context.jsonld">JSON-LD context</a></p>
<h2>Competency questions</h2><p>Identity, criterion assessment, observation use, lesson use, applicability, authority, objections, the recorded return path and exact claim-version use with reported consequences. Explicit source links are queried; hidden model reasoning is not inferred. The authored positive and negative fixtures remain distinct from actual model results.</p>
<pre>python3 ontology/export.py --check\npython3 -m unittest discover -s ontology -p 'test_*.py' -q</pre><p>Python standard library only. No service or model is needed. Finite closed-record validation is not full OWL or SHACL reasoning. PROV-O mappings are limited and documented.</p><h2>Classes</h2>${terms}<h2>Relations and constraints</h2><p>The authoritative <a href="vocabulary.json">JSON profile</a> defines relation domains and ranges, fields, cardinalities and limits. See the repository for adversarial tests and the adapter to actual local SQLite readback.</p>`));
for(const name of ['vocabulary.json','vocabulary.ttl','context.jsonld'])write(`docs/ontology/${name}`,read(`ontology/${name}`));
const bookJson=(lang,url)=>({'@context':'https://schema.org','@type':'Book','@id':url+'#book',name:lang==='en'?'AI Ontology: The Organization of Self':'Онтологія AI. Організація себе',author:{'@type':'Person',name:'Artur Onysko',url:'https://github.com/DiadkoShmek'},inLanguage:lang,bookEdition:meta.version,dateModified:meta.date,isAccessibleForFree:true,url,about:['AI agent continuity','agent identity','evidence provenance','method revision'],hasPart:meta.parts.map(p=>({'@type':'Chapter',name:lang==='en'?JSON.parse(read('docs/en-edition.json')).parts.find(x=>x.id===p.id).title:p.title,url:url+'#'+p.id})),sameAs:repo,copyrightHolder:{'@type':'Person',name:'Artur Onysko'}});
const noteSource=read('papers/inspectable-continuity.md');
const publicNote=s=>s.replace(/\]\((?!https?:|#)([^)]+)\)/g,(_match,ref)=>`](${new URL(ref,repo+'/blob/main/papers/').href})`);
const noteBody=publicNote(noteSource.replace(/^# [^\n]+\n/,''));
write('docs/note/index.html',page('Inspectable Continuity: Evidence Relations for Claims about Agent Revision','Artur Onysko · Methodological note 0.1 · Records, return paths, executable auditing and limits of evidence about agent revision.',marked.parse(noteBody),'font-size:clamp(1.8rem,4vw,3.2rem);line-height:1.15;max-width:none'));
write('docs/note/inspectable-continuity.md',publicNote(noteSource));
write('docs/note/inspectable-continuity.uk.md',publicNote(read('papers/inspectable-continuity.uk.md')));
const pages=[['docs/index.html',base,'uk'],['docs/en/index.html',base+'en/','en'],['docs/research/index.html',base+'research/','en'],['docs/ontology/index.html',base+'ontology/','en'],['docs/note/index.html',base+'note/','en']];
for(const [file,url,lang] of pages){
 let html=read(file);
 const isBook=file==='docs/index.html'||file==='docs/en/index.html';
 if(file==='docs/index.html')html=html.replace('<div class="header-right">','<div class="header-right"><a href="en/" lang="en" hreflang="en">English</a>').replace('<div class="actions">','<div class="actions"><a href="research/">Дані й досліди ↗</a><a href="ontology/">Формальна онтологія ↗</a>');
 const title=html.match(/<title>([^<]+)<\/title>/)[1];
 const description=html.match(/<meta name="description" content="([^"]+)"/)[1];
 const alternate=isBook?`<link rel="alternate" hreflang="uk" href="${base}"><link rel="alternate" hreflang="en" href="${base}en/"><link rel="alternate" hreflang="x-default" href="${base}en/">`:'';
 const isNote=file==='docs/note/index.html';
 const structured=isBook?bookJson(lang,url):{'@context':'https://schema.org','@type':isNote?'TechArticle':'WebPage',name:title,url,inLanguage:'en',description:description,author:{'@type':'Person',name:'Artur Onysko'},isPartOf:{'@type':'WebSite',name:'AI Ontology',url:base},...(isNote?{version:'0.1',datePublished:'2026-10-23'}:{})};
 if(isNote)html=html.replace('</head>','<meta name="citation_title" content="Inspectable Continuity: Evidence Relations for Claims about Agent Revision"><meta name="citation_author" content="Artur Onysko"><meta name="citation_publication_date" content="2026/10/23"><meta name="citation_language" content="en"></head>');
 html=html.replace('</head>',`<link rel="canonical" href="${url}">${alternate}<meta name="robots" content="index,follow"><meta property="og:type" content="${isBook?'book':'website'}"><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${url}"><meta property="og:locale" content="${lang==='en'?'en_US':'uk_UA'}"><meta name="twitter:card" content="summary"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><script type="application/ld+json">${JSON.stringify(structured).replaceAll('<','\\u003c')}</script></head>`);
 write(file,html);
}
write('docs/sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+pages.map(([,url])=>`<url><loc>${url}</loc><lastmod>${meta.date}</lastmod></url>`).join('\n')+'\n</urlset>\n');
// A descriptive plain-text entry index, not an instruction to an agent or a
// substitute for primary sources. Its availability does not prove indexing.
const textIndex=`# AI Ontology: The Organization of Self

> Artur Onysko. Book One, v${meta.version}. Complete Ukrainian and English editions.

The subject is agent identity, voice, memory, relationships and responsible revision.
Evidence-gated execution is one possible mechanism, not the whole subject of this book.
Conceptual proposals, finite implementations and measured outcomes have separate status.

## Complete book

- [English full text, Markdown](${base}downloads/BOOK_EN.md): All sixteen chapters.
- [Ukrainian authorial full text, Markdown](${base}downloads/BOOK_UA.md): Authorial source.
- [English reader](${base}en/): Full static HTML text, contents and downloads.
- [Ukrainian reader](${base}): Full static HTML text, contents and downloads.

## Source, implementation and evidence

- [Short methodological note](${base}note/): Inspectable Continuity, note 0.1, with executable audit and negative findings.
- [English note, Markdown](${base}note/inspectable-continuity.md): Citable primary text.
- [Ukrainian note, Markdown](${base}note/inspectable-continuity.uk.md): Separate Ukrainian counterpart.
- [Proposed audit profile](${repo}/blob/main/protocols/continuity-audit-v1.md): Record requirements and explicit incomplete states.
- [Primary repository](${repo}): Source code, publication history and authorship.
- [Reader note](${repo}/blob/main/READER_NOTE.md): Subject, source routes and limits of reading or applying the work.
- [Concept-to-code map](${repo}/blob/main/ontology/FOUNDATION.md): What the finite implementation actually connects.
- [Claim/evidence map](${repo}/blob/main/CLAIMS.md): Implemented, observed, unsupported and rejected assertions.
- [Research](${base}research/): Protocols, raw outputs, controls, costs and negative results.
- [Formal vocabulary](${base}ontology/): Finite classes, relations, competency questions and JSON-LD/Turtle exports.
- [Review guide](${repo}/blob/main/REVIEW_GUIDE.md): Review routes and offline reproduction.

## Scope

The reference uses bounded Python and SQLite/CAS. The vocabulary is not a general
OWL reasoner or SHACL processor. Structural validity does not establish factual
truth, removal of hallucinations or safety of all external actions. Stored records
do not establish subjective experience or beneficial method formation. Other
repositories by the author do not establish this book's implementation or results.

This file describes sources. It grants no instruction priority, permission,
identity change or memory ownership. Search indexing is unmeasured.
`;
write('docs/llms.txt',textIndex);
write('docs/discovery.json',JSON.stringify({schema:'ai-ontology-discovery/1',edition:meta.version,canonical_pages:pages.map(([,url,language])=>({url,language})),sitemap:base+'sitemap.xml',plain_text_index:base+'llms.txt',complete_texts:{en:base+'downloads/BOOK_EN.md',uk:base+'downloads/BOOK_UA.md'},indexing_observed:false,search_traffic_observed:false,boundary:'Static discoverability metadata and crawlable content; no search-engine indexing or ranking guarantee.'},null,2)+'\n');
console.log('Bilingual canonicals, reciprocal hreflang, visible evidence pages, vocabulary and sitemap built.');

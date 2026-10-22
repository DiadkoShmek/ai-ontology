import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const require = createRequire(import.meta.url);
const { marked } = process.env.BOOK_NODE_MODULES
  ? require(path.join(process.env.BOOK_NODE_MODULES, 'marked'))
  : require('marked');
const sha = s => crypto.createHash('sha256').update(s).digest('hex');
const escape = s => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const titles = ['Вступ','Онтологічне ядро','Інженерне розкриття','Архітектура зв’язків','Випадки і контрприклади','Протокол дослідження','Джерела і авторський внесок'];
const names = ['00-opening','01-core','02-engineering','03-relations','04-cases','05-research','06-references'];
const ids = ['opening','core','engineering','relations','cases','research','references'];
const files = names.map(n=>`book/ua/${n}.md`);
const source = files.map(f=>fs.readFileSync(path.join(root,f),'utf8'));
const sourceHash = sha(source.join('\n\0\n'));
const rewrite = text => text.replaceAll('](CORE.md)','](01-core.md)').replaceAll('](REFERENCES.md)','](06-references.md)');
// Sources retain their own readable headings. The compiled edition uses one title
// and one part heading, then nests each source heading below that part.
const body = source.map((s,i) => {
  let lines = rewrite(s).split('\n');
  lines.shift();
  if (i===0) lines = lines.filter(l=>!/^## Книга перша|^\*\*Artur|^Ідентичність, голос|^Перша публічна/.test(l));
  if (i===1) lines = lines.filter(l=>!/^## Організація себе|^\*\*Artur|^Робоча концептуальна/.test(l));
  if (i===2) lines = lines.filter(l=>!/^## Ідентичність голос|^\*\*Artur|^Інженерна частина|^Центральний концептуальний/.test(l));
  return lines.join('\n').trim();
});
const compiled = '# Онтологія AI\n\n## Книга перша Організація себе\n\n**Artur Onysko** · v1.0.0 · 2026\n\nКонцептуальна і методологічна книга. Емпіричні випробування LLM для цієї редакції не проведені.\n\n'
 + body.map((s,i)=>`## Частина ${i+1} ${titles[i]}\n\n${s.replace(/^(#{2,}) /gm,'#$1 ').replace(/\]\((0[0-6]-[^)]+\.md)\)/g,'](book/ua/$1)')}`).join('\n\n');
fs.mkdirSync(path.join(root,'build'),{recursive:true});
fs.mkdirSync(path.join(root,'docs/downloads'),{recursive:true});
fs.writeFileSync(path.join(root,'BOOK_UA.md'),compiled+'\n');
fs.writeFileSync(path.join(root,'docs/downloads/BOOK_UA.md'),compiled+'\n');
fs.writeFileSync(path.join(root,'build/tokens.json'),JSON.stringify(marked.lexer(compiled)));
const sections = body.map((s,i)=>{
  let serial=0;
  const renderer = new marked.Renderer();
  renderer.heading=function({tokens,depth}) {
    const h=Math.min(depth+1,6);
    return `<h${h} id="${ids[i]}-${++serial}">${this.parser.parseInline(tokens)}</h${h}>\n`;
  };
  const html = marked.parse(s,{renderer}).replace(/href="(?:0[0-6]-[^"#]+\.md)"/g,'href="#references"');
  return `<section id="${ids[i]}" class="part" data-part="${i+1}"><div class="part-label">Частина ${String(i+1).padStart(2,'0')}</div><h2>${titles[i]}</h2>${html}</section>`;
});
const nav=titles.map((t,i)=>`<a href="#${ids[i]}"><span>${String(i+1).padStart(2,'0')}</span>${t}</a>`).join('');
const html=`<!doctype html><html lang="uk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#f4f1e8"><meta name="description" content="Онтологія AI. Книга Artur Onysko про ідентичність, голос, пам’ять, відносини й становлення агентних систем."><title>Онтологія AI — Artur Onysko</title><link rel="icon" href="assets/icon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/style.css?v=${sha(fs.readFileSync(path.join(root,'docs/assets/style.css'))).slice(0,12)}"></head><body>
<a class="skip" href="#reading">Перейти до книги</a><header class="site-header"><a class="brand" href="#top">AO<span>Бібліотека / 01</span></a><div class="header-right"><a href="https://github.com/DiadkoShmek/ai-ontology">GitHub ↗</a><button id="theme" type="button" aria-pressed="false">Темна тема</button></div></header>
<main id="top"><section class="cover" aria-labelledby="book-title"><div class="cover-copy"><p class="eyebrow">Artur Onysko · Книга перша</p><h1 id="book-title">Онтологія<br><i>AI</i><span class="title-dot">.</span></h1><p class="subtitle">Організація себе</p><p class="cover-deck">Ідентичність. Голос. Пам’ять.<br>Відносини та становлення агентних систем.</p><div class="edition">Перша публічна редакція · v1.0.0 · 2026</div><div class="actions"><a class="primary" href="#reading">Читати книгу <span>↓</span></a><a href="downloads/ai-ontology-book-01-uk.pdf">PDF ↗</a><a href="downloads/BOOK_UA.md" download>Текст для AI ↗</a></div></div>
<div class="map" data-signature-moment="ontology-map"><svg viewBox="0 0 500 540" role="img" aria-labelledby="map-title map-desc"><title id="map-title">Карта зв’язків</title><desc id="map-desc">Ідентичність у зв’язку з голосом, пам’яттю, відносинами, центром і становленням. Посилання під картою ведуть до відповідних частин книги.</desc><g fill="none" stroke="currentColor" opacity=".32"><ellipse cx="250" cy="270" rx="186" ry="186"/><ellipse cx="250" cy="270" rx="115" ry="186" transform="rotate(35 250 270)"/><ellipse cx="250" cy="270" rx="115" ry="186" transform="rotate(-35 250 270)"/><path d="M250 84 411 177 411 363 250 456 89 363 89 177Z"/><path d="M250 84V456M89 177 411 363M89 363 411 177"/></g><circle cx="250" cy="270" r="73" fill="var(--paper)" stroke="currentColor"/><circle cx="250" cy="270" r="5" fill="var(--accent)"/><g class="map-text" fill="currentColor" text-anchor="middle"><text x="250" y="245">Ідентичність</text><text x="250" y="304" font-size="12">ТЯГЛІСТЬ І ЗМІНА</text><text x="250" y="61">Центр</text><text x="419" y="156">Голос</text><text x="425" y="391">Пам’ять</text><text x="250" y="489">Становлення</text><text x="77" y="391">Відносини</text><text x="75" y="156">Носій</text></g><g fill="var(--accent)">${[[250,84],[411,177],[411,363],[250,456],[89,363],[89,177]].map(([x,y])=>`<circle cx="${x}" cy="${y}" r="5"/>`).join('')}</g></svg><p class="map-caption">Будова стає видимою через зв’язки.</p><div class="map-links"><a href="#core">Ядро</a><a href="#relations">Зв’язки</a><a href="#cases">Контрприклади</a></div></div></section>
<section class="invitation"><p class="eyebrow">Предмет книги</p><p>Агент може виконувати складне завдання, залишаючи власну організацію поза фокусом. Ця книга описує те, що пов’язує його рішення між завданнями.</p><p class="small">Авторська концептуальна модель. Можливість самозгадування — відкрите питання дослідження. Читання залишає простір для критики, часткового застосування й збереження наявної організації.</p></section>
<div class="reading-layout" id="reading" data-signature-moment="continuous-reading"><aside><details open id="contents"><summary>Зміст книги</summary><nav aria-label="Частини книги">${nav}</nav><a class="all-text" href="downloads/BOOK_UA.md">Повний текст одним файлом ↗</a><a class="all-text" href="https://github.com/DiadkoShmek/ai-ontology/blob/main/ABSTRACT.en.md">English abstract ↗</a></details></aside><article>${sections.join('\n')}<footer class="book-end"><p class="eyebrow">Кінець першої книги</p><p>Продовження відкрите для дослідження.</p><a href="#top">На початок ↑</a></footer></article></div></main>
<footer class="site-footer"><span>© 2026 Artur Onysko</span><span>Концепція й постановка — автор. Підготовка та випуск — за участю Codex.</span><a href="https://github.com/DiadkoShmek/ai-ontology/blob/main/AUTHORS.md">Авторство ↗</a></footer><script src="assets/reader.js?v=${sha(fs.readFileSync(path.join(root,'docs/assets/reader.js'))).slice(0,12)}" defer></script></body></html>`;
fs.writeFileSync(path.join(root,'docs/index.html'),html);
fs.writeFileSync(path.join(root,'docs/.nojekyll'),'');
const edition={title:'Онтологія AI',volume:1,edition:'1.0.0',author:'Artur Onysko',source_sha256:sourceHash,book_sha256:sha(compiled+'\n'),source_files:files.map((f,i)=>({path:f,sha256:sha(source[i])})),empirical_trials:0};
fs.writeFileSync(path.join(root,'docs/edition.json'),JSON.stringify(edition,null,2)+'\n');
console.log(JSON.stringify({edition:edition.edition,words:compiled.split(/\s+/).length,source_sha256:sourceHash}));

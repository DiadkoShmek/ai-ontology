const theme=document.querySelector('#theme');
theme?.addEventListener('click',()=>{const dark=document.body.classList.toggle('dark');theme.setAttribute('aria-pressed',String(dark));theme.textContent=dark?(theme.dataset.light??'Світла тема'):(theme.dataset.dark??'Темна тема');});
const links=[...document.querySelectorAll('nav a')];
if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{for(const e of entries){if(e.isIntersecting){for(const a of links)a.setAttribute('aria-current',String(a.hash===`#${e.target.id}`));}}},{rootMargin:'-10% 0px -70% 0px'});document.querySelectorAll('.part').forEach(s=>observer.observe(s));}
if(matchMedia('(max-width:650px)').matches)document.querySelector('#contents')?.removeAttribute('open');

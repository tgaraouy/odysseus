const SECTIONS = [
  {id:'dashboard',   label:'Tableau de bord'},
  {id:'signalements',label:'Signalements'},
  {id:'validation',  label:'Validation'},
  {id:'ethique',     label:'Éthique & probité'},
  {id:'metriques',   label:'Métriques'},
  {id:'journal',     label:'Journal & assurance'},
];
const GLY={critique:'▲',majeur:'◆',mineur:'•'};
let D=null, active='dashboard';

async function boot(){
  let r;
  try{ r=await fetch('/api/mohtasib/overview',{credentials:'same-origin'}); }
  catch(e){ document.getElementById('main').innerHTML='<p class="empty">Erreur réseau.</p>'; return; }
  if(r.status===401){ document.getElementById('main').innerHTML='<p class="empty">Session expirée ou non connecté. <a href="/login" style="color:var(--observed)">Se connecter</a>.</p>'; return; }
  if(!r.ok){ document.getElementById('main').innerHTML='<p class="empty">Le service de données a répondu '+r.status+'. Réessayez, ou <a href="/agent" style="color:var(--observed)">ouvrir l’application agent</a>.</p>'; return; }
  D=await r.json();
  document.getElementById('role-badge').textContent = (D.roles&&D.roles.length)? D.roles.join(' · ') : 'aucun rôle — accès nul';
  const shown = SECTIONS.filter(s=>D[s.id]!=null);
  document.getElementById('nav').innerHTML = shown.map(s=>{
    let n=''; if(s.id==='signalements'&&D.dashboard) n=D.dashboard.n_signalements;
    if(s.id==='validation'&&D.validation) n=(D.validation.file||[]).length;
    return `<a data-s="${s.id}">${s.label}${n!==''?`<span class="n">${n}</span>`:''}</a>`;
  }).join('') || '<p class="note" style="padding:8px">Aucune section — votre rôle ne donne accès à rien.</p>';
  document.querySelectorAll('nav a').forEach(a=>a.onclick=()=>go(a.dataset.s));
  if(shown.length) go(shown[0].id); else document.getElementById('main').innerHTML='<p class="empty">Aucun accès.</p>';
}
function go(id){ active=id; document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('on',a.dataset.s===id)); render(); }

function render(){
  const m=document.getElementById('main');
  const R={dashboard:dash,signalements:sig,validation:val,ethique:eth,metriques:met,journal:jour}[active];
  m.innerHTML = R? R() : '<p class="empty">—</p>';
}
function head(eb,h){ return `<div class="eyebrow">${eb}</div><h1>${h}</h1>`; }

function dash(){
  const d=D.dashboard; if(!d) return '<p class="empty">Accès restreint.</p>';
  return head('vue d’ensemble','Tableau de bord')+`
  <div class="tiles">
    <div class="tile"><div class="k">Marchés contrôlés</div><div class="v">${d.n_tenders}</div></div>
    <div class="tile"><div class="k">Signalements</div><div class="v">${d.n_signalements}</div></div>
    <div class="tile"><div class="k">Critiques</div><div class="v crit">${d.par_severite.critique}</div></div>
    <div class="tile"><div class="k">Majeurs</div><div class="v maj">${d.par_severite.majeur}</div></div>
    <div class="tile"><div class="k">En attente de validation</div><div class="v">${d.en_attente_validation}</div></div>
  </div>
  <p class="note">Couverture exhaustive du périmètre ingéré (pas d’échantillon). Un signalement reste
  <span class="mono">pending</span> jusqu’à validation d’un magistrat.</p>`;
}
function flagCard(f){
  const conf = (f.source&&(f.source.includes('LLM')||f.source.includes('sémantique')))?'INFERRED'
    : (f.source&&f.source.includes('heuristique'))?'CLAIMED':'OBSERVED';
  return `<div class="flag sev-${f.severite}"><div class="flag-h">
    <span class="glyph">${GLY[f.severite]||'•'}</span>
    <span class="mono">[${f.controle}]</span><strong>${f.titre}</strong>
    <span class="pill pending">${f.statut}</span>
    <span class="confp ${conf}">${conf}</span>
    <span class="conf">conf. ${(f.confiance||0).toFixed?f.confiance.toFixed(2):f.confiance}</span>
  </div><div class="flag-b">
    <div><span class="cle">marché</span>${f.tender||'—'}</div>
    <div><span class="cle">attendu</span>${f.attendu||'—'}</div>
    <div><span class="cle">observé</span>${f.observe||'—'}</div>
    <div><span class="cle">source</span>${f.source||'—'}</div>
    <div><span class="cle">base</span>${f.base||'—'}</div>
  </div></div>`;
}
function sig(){
  const s=D.signalements;
  if(s&&s.masque) return head('contrôles','Signalements')+`<div class="masked">Accès restreint à votre rôle : <b>${s.n}</b> signalement(s) existent, contenu masqué.</div>`;
  if(!s||!s.length) return head('contrôles','Signalements')+'<p class="empty">Aucun signalement.</p>';
  const ord={critique:0,majeur:1,mineur:2};
  return head('contrôles · triés par risque','Signalements')+[...s].sort((a,b)=>ord[a.severite]-ord[b.severite]).map(flagCard).join('');
}
function val(){
  const v=D.validation; if(!v) return '<p class="empty">Accès restreint.</p>';
  const f=v.file||[];
  return head('humain dans la boucle','Validation → constat')+
    `<p class="note">${v.peut_valider?'Vous pouvez promouvoir un signalement en constat (autorité magistrat).':'Consultation seule — la validation est réservée au magistrat rapporteur.'}</p>`+
    (f.length?f.map(flagCard).join(''):'<p class="empty">File vide.</p>');
}
function eth(){
  const e=D.ethique;
  if(e&&e.masque) return head('éthique','Éthique & probité')+`<div class="masked">Accès restreint : <b>${e.n}</b> alerte(s) de probité existent, contenu réservé au responsable éthique.</div>`;
  if(!e||!e.length) return head('éthique','Éthique & probité')+'<p class="note">Aucune alerte de probité (DOP / conflits) sur les contrôles exécutés.</p>';
  return head('éthique · DOP / conflits','Éthique & probité')+e.map(flagCard).join('');
}
function met(){
  const m=D.metriques; if(!m) return '<p class="empty">Accès restreint.</p>';
  const groups=[['performance','Performance'],['accuracy','Exactitude'],['reliability','Fiabilité'],['drift_predictability','Dérive'],['security','Sécurité'],['assurance','Assurance']];
  let html=head('mesuré · sur données réelles','Métriques');
  for(const [k,label] of groups){ const g=m[k]; if(!g) continue;
    const items=Object.entries(g).filter(([kk])=>kk!=='source'&&!kk.startsWith('_')).slice(0,6);
    html+=`<h2 style="margin-top:22px">${label} <span class="confp ${g.source||''}" style="font-size:9px">${g.source||''}</span></h2><div class="metric-grid">`+
      items.map(([kk,vv])=>`<div class="metric"><div class="mk">${kk.replace(/_/g,' ')}</div><div class="mv">${typeof vv==='object'?(vv.valeur??vv.mediane??JSON.stringify(vv).slice(0,40)):vv}</div><div class="md">${typeof vv==='object'?(vv.detail||vv.src||''):''}</div></div>`).join('')+`</div>`;
  }
  return html;
}
function jour(){
  const j=D.journal; if(!j) return '<p class="empty">Accès restreint.</p>';
  if(j.erreur) return head('assurance','Journal de preuve')+`<p class="empty">${j.erreur}</p>`;
  return head('assurance · chaîne de hachage','Journal de preuve')+`
    <div class="tiles"><div class="tile"><div class="k">Hauteur de chaîne</div><div class="v">${j.hauteur}</div></div>
    <div class="tile"><div class="k">Intégrité</div><div class="v" style="font-size:20px">${j.verifiee?'<span class="ok-badge">vérifiée ✓</span>':'ROMPUE ✗'}</div></div></div>
    <h2 style="margin-top:20px">Blocs par type</h2>
    <div class="metric-grid">${Object.entries(j.par_type).map(([t,n])=>`<div class="metric"><div class="mk">${t}</div><div class="mv">${n}</div></div>`).join('')}</div>
    <h2 style="margin-top:22px">Blocs récents</h2>
    ${j.recents.map(b=>`<div class="jrow"><span class="t">${b.type}</span><span class="h">${b.hash10}</span><span>${(b.confiance||'—')}</span><span class="h">${b.ts}</span></div>`).join('')}`;
}
boot();

const SECTIONS = [
  {id:'dashboard',   label:'Tableau de bord'},
  {id:'priorisation',label:'Priorisation'},
  {id:'dossiers',    label:'Dossiers'},
  {id:'signalements',label:'Signalements'},
  {id:'inter_marche',label:'Schémas inter-marchés'},
  {id:'validation',  label:'Validation'},
  {id:'ethique',     label:'Éthique & probité'},
  {id:'metriques',   label:'Métriques'},
  {id:'conformite',  label:'Conformité au défi'},
  {id:'journal',     label:'Journal & assurance'},
];
const GLY={critique:'▲',majeur:'◆',mineur:'•'};
let D=null, active='dashboard', TEN=null;  // TEN = the currently open dossier (per-tender)

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
    if(s.id==='dossiers'&&D.dossiers) n=D.dossiers.length;
    return `<a data-s="${s.id}">${s.label}${n!==''?`<span class="n">${n}</span>`:''}</a>`;
  }).join('') || '<p class="note" style="padding:8px">Aucune section — votre rôle ne donne accès à rien.</p>';
  document.querySelectorAll('nav a').forEach(a=>a.onclick=()=>go(a.dataset.s));
  if(shown.length) route(); else document.getElementById('main').innerHTML='<p class="empty">Aucun accès.</p>';
}
function setNavActive(id){ document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('on',a.dataset.s===id)); }
function go(id){ if(location.hash.replace(/^#/,'')===id) route(); else location.hash=id; }

// URL is the source of truth: #<section> or #dossier=<encoded ref>. Deep-links
// and browser back/forward both flow through route().
async function route(){
  if(!D) return;
  const h = location.hash.replace(/^#/,'');
  if(h.indexOf('dossier=')===0){
    const ref = decodeURIComponent(h.slice('dossier='.length));
    active='dossiers'; setNavActive('dossiers');
    if(!TEN || TEN.reference!==ref) await openTender(ref); else render();
    return;
  }
  const shown = SECTIONS.filter(s=>D[s.id]!=null);
  const sec = shown.find(s=>s.id===h);
  const target = sec ? sec.id : (shown[0] && shown[0].id);
  active=target; TEN=null; setNavActive(target); render();
}

function render(){
  const m=document.getElementById('main');
  if(active==='dossiers' && TEN){ m.innerHTML = tenderView(); return; }
  const R={dashboard:dash,priorisation:prio,dossiers:doss,signalements:sig,inter_marche:inter,validation:val,ethique:eth,metriques:met,conformite:conf,journal:jour}[active];
  m.innerHTML = R? R() : '<p class="empty">—</p>';
}
function head(eb,h){ return `<div class="eyebrow">${eb}</div><h1>${h}</h1>`; }
function esc(v){ return (v==null?'':String(v)).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
function sevChips(s){ s=s||{}; return `${s.critique?`<span class="chip crit">▲ ${s.critique} crit.</span>`:''}${s.majeur?`<span class="chip maj">◆ ${s.majeur} maj.</span>`:''}${s.mineur?`<span class="chip min">• ${s.mineur} min.</span>`:''}`; }

// ── Dossiers: list of tenders, each opening a full end-to-end drill-down ──
function doss(){
  const list=D.dossiers; if(!list) return '<p class="empty">Accès restreint.</p>';
  if(!list.length) return head('marchés','Dossiers')+'<p class="empty">Aucun dossier.</p>';
  return head('marchés · cliquer pour le cycle complet','Dossiers')+
    '<p class="note">Chaque dossier suit la chaîne : collecte → capture → extraction → réconciliation → contrôles → validation → livrables → journal. Couverture exhaustive du périmètre, pas d’échantillon.</p>'+
    '<div class="doss-grid">'+list.map(t=>`
      <div class="doss-card" data-ref="${esc(t.reference)}">
        <div class="doss-ref mono">${esc(t.reference)}</div>
        <div class="doss-sev">${sevChips(t.par_severite)}</div>
        <div class="doss-meta">
          <span>${t.n_signalements} signalement(s)</span>
          <span>${t.en_attente} en attente</span>
          <span class="${t.has_portal?'ok':'off'}">${t.has_portal?'source ✓':'source absente'}</span>
          ${t.has_capture?'<span class="ok">OCR ✓</span>':''}
        </div>
        <div class="doss-open">ouvrir le cycle →</div>
      </div>`).join('')+'</div>';
}

async function openTender(ref){
  const m=document.getElementById('main');
  m.innerHTML='<p class="empty">Chargement du dossier '+esc(ref)+'…</p>';
  const url='/api/mohtasib/tender/'+ref.split('/').map(encodeURIComponent).join('/');
  try{
    const r=await fetch(url,{credentials:'same-origin'});
    if(!r.ok){ m.innerHTML='<p class="empty">Dossier indisponible ('+r.status+'). <a onclick="go(\'dossiers\')" style="color:var(--observed);cursor:pointer">retour</a></p>'; return; }
    TEN=await r.json(); active='dossiers'; render();
  }catch(e){ m.innerHTML='<p class="empty">Erreur réseau.</p>'; }
}

function step(n,title,sub,body){
  return `<li class="tl-step"><div class="tl-n">${n}</div>
    <div class="tl-body"><div class="tl-h"><b>${title}</b><span class="tl-sub">${sub}</span></div>
    <div class="tl-c">${body}</div></div></li>`;
}
function kv(k,v){ return v==null||v===''?'':`<div class="kv"><span class="cle">${k}</span><span>${esc(v)}</span></div>`; }

function stepCollecte(c){
  if(!c) return '<p class="note">Accès restreint.</p>';
  if(!c.present) return `<p class="note">${esc(c.note||'Source non ingérée.')}</p>`;
  return `<div class="grid2">
    ${kv('objet',c.objet)}${kv('procédure',c.procedure)}
    ${kv('montant estimé',c.montant_estime_dh!=null?Number(c.montant_estime_dh).toLocaleString('fr')+' DH':'')}
    ${kv('publication',c.date_publication)}${kv('ouverture',c.date_ouverture)}
    ${kv('pièces',(c.documents_presents||[]).join(', '))}
    ${kv('versions',c.n_versions)}
    <div class="kv"><span class="cle">sha256 PDF</span><span class="mono h">${esc((c.sha256_pdf||'').slice(0,32))}…</span></div>
  </div>`;
}
function stepCapture(cap){
  if(!cap) return '<p class="note">Pas de capture OCR distincte pour ce marché dans ce périmètre.</p>';
  const cc=cap.concordance_tl_ocr;
  const badge = cc==null?'' : `<span class="confp ${cc>=0.95?'MEASURED':cc>=0.8?'OBSERVED':'INFERRED'}">concordance ${cc}</span>`;
  return `<div class="grid2">
    ${kv('PDF',cap.pdf)}${kv('pages',cap.pages)}
    ${kv('source retenue',cap.source_retenue)}${kv('langue OCR',cap.langue_ocr)}
    ${kv('car. couche texte',cap.text_layer_chars)}${kv('car. OCR',cap.ocr_chars)}
    ${kv('couche texte saine',cap.text_layer_sain===true?'oui':cap.text_layer_sain===false?'non':'')}
  </div><div style="margin-top:8px">${badge}</div>
  ${cap.erreur_ocr?`<p class="note">Erreur OCR : ${esc(cap.erreur_ocr)}</p>`:''}`;
}
function stepExtraction(x){
  if(!x) return '<p class="note">Aucune extraction structurée (source absente).</p>';
  const rows=[['objet','objet'],['ouverture','date_ouverture'],['montant estimé','montant_estime_dh']];
  return `<table class="xt"><thead><tr><th></th><th>base (origine)</th><th>courant (après amendements)</th></tr></thead><tbody>`+
    rows.map(([lbl,k])=>{
      const a=x.base?x.base[k]:null, b=x.courant?x.courant[k]:null;
      const diff=(a!=null&&b!=null&&String(a)!==String(b));
      return `<tr><td class="cle">${lbl}</td><td>${esc(a)}</td><td class="${diff?'chg':''}">${esc(b)}</td></tr>`;
    }).join('')+`</tbody></table>`;
}
function stepReconcil(rec){
  if(!rec) return '<p class="note">Version unique — aucun rectificatif publié.</p>';
  return rec.versions.map(v=>`
    <div class="rectbox">
      <div class="rect-h"><span class="mono">${esc(v.document)}</span>
        <span class="pill">${esc(v.type)}</span><span class="tl-sub">${esc(v.date)}</span>
        <span class="mono h" style="margin-left:auto">${esc((v.sha256||'').slice(0,12))}</span></div>
      ${v.champs.map(ch=>{
        const applied=/appliqu/i.test(ch.statut||''), susp=/suspend/i.test(ch.statut||'');
        const cls=applied?'ok':susp?'warn':'';
        return `<div class="champ">
          <span class="cle">${esc(ch.champ)}</span>
          <span class="av">${esc(ch.avant)}</span><span class="arrow">→</span><span class="ap">${esc(ch.apres)}</span>
          <span class="statut ${cls}">${esc(ch.statut)}</span>
          ${(ch.problemes&&ch.problemes.length)?`<span class="prob">⚠ ${esc(ch.problemes.join('; '))}</span>`:''}
        </div>`;
      }).join('')}
    </div>`).join('')+
    '<p class="note">Un rectificatif « suspendu » n’est jamais appliqué en dernier-gagne : il exige une validation humaine explicite.</p>';
}
function stepControles(c){
  if(c==null) return '<p class="note">Accès restreint à votre rôle.</p>';
  if(c.masque) return `<div class="masked">${c.n} signalement(s), contenu masqué pour votre rôle.</div>`;
  if(!c.length) return '<p class="note">Aucun signalement.</p>';
  const ord={critique:0,majeur:1,mineur:2};
  return [...c].sort((a,b)=>ord[a.severite]-ord[b.severite]).map(flagCard).join('');
}
function stepValidation(v){
  if(!v) return '<p class="note">Accès restreint.</p>';
  let h=`<p class="note">${v.peut_valider?'Vous pouvez promouvoir un signalement en constat (autorité magistrat).':'Consultation — la promotion en constat est réservée au magistrat rapporteur.'} · <b>${v.en_attente}</b> en attente.</p>`;
  if(v.verdicts&&v.verdicts.length){
    h+='<div class="jlist">'+v.verdicts.map(b=>`<div class="jrow"><span class="t">constat ${esc(b.claim_id||'')}</span><span class="ok-badge">${esc(b.verdict)}</span><span>${esc(b.actor)}</span><span class="h">${esc(b.hash10)}</span></div>`).join('')+'</div>';
  } else { h+='<p class="note">Aucun constat validé pour l’instant.</p>'; }
  return h;
}
function stepLivrables(l){
  if(l==null) return '<p class="note">Accès restreint.</p>';
  if(!l.length) return '<p class="note">Aucun livrable rattaché.</p>';
  return '<div class="jlist">'+l.map(x=>`<div class="jrow lrow" data-livrable="${esc(x.fichier)}"><span class="t mono">${esc(x.fichier)}</span><span>${esc(x.titre||'')}</span><span class="h">${x.octets} o</span><a class="dl" href="/api/mohtasib/livrable-docx/${esc(x.fichier.replace(/\.md$/,'.docx'))}" download onclick="event.stopPropagation()">.docx ↓</a><span class="open-l">ouvrir →</span></div>`).join('')+'</div>';
}
function stepJournal(j){
  if(j==null) return '<p class="note">Accès restreint.</p>';
  if(!j.length) return '<p class="note">Aucun bloc de journal ne référence ce marché.</p>';
  return '<div class="jlist">'+j.map(b=>`<div class="jrow"><span class="t">${esc(b.type)}</span><span class="h">${esc(b.hash10)}</span><span>${esc(b.actor)}</span><span class="h">${esc(b.ts||'')}</span></div>`).join('')+'</div>';
}

function tenderView(){
  const t=TEN; if(!t) return doss();
  let h=`<a class="back" onclick="go('dossiers')">← tous les dossiers</a>`+
    head('dossier · cycle complet de bout en bout',t.reference)+
    `<div class="doss-sev big">${sevChips(t.par_severite)}<span class="chip">${t.n_signalements} signalement(s)</span></div>`+
    '<ol class="timeline">'+
    step(1,'Collecte','source & métadonnées', stepCollecte(t.collecte))+
    step(2,'Capture','OCR FR + AR, fidélité mesurée', stepCapture(t.capture))+
    step(3,'Extraction','champs structurés', stepExtraction(t.extraction))+
    step(4,'Réconciliation','versions & rectificatifs', stepReconcil(t.reconciliation))+
    step(5,'Contrôles','signalements détectés', stepControles(t.controles))+
    step(6,'Validation','humain dans la boucle', stepValidation(t.validation))+
    step(7,'Livrables','pièces produites', stepLivrables(t.livrables))+
    step(8,'Journal','preuve chaînée (hash)', stepJournal(t.journal))+
    '</ol>';
  return h;
}

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
function prio(){
  const p=D.priorisation; if(!p) return '<p class="empty">Accès restreint.</p>';
  const rk=p.ranking||[];
  const maxs=Math.max(1,...rk.map(r=>r.score||0));
  let html=head('DSS · marchés à investiguer en priorité','Priorisation')+
    `<p class="note">Classement par <b>score de risque déterministe</b> (somme pondérée des signaux — explicable, ligne à ligne). Données exportées au standard <span class="mono">OCDS 1.1</span> · <a class="dl" href="/api/mohtasib/ocds" download>ocds.json ↓</a></p>
    <div class="masked" style="border-color:rgba(143,180,222,.3);background:rgba(143,180,222,.08);color:var(--fg-2)">${esc(p.note||'')}</div>`;
  html+='<div style="margin-top:16px">'+rk.map(r=>{
    const w=Math.round(100*(r.score||0)/maxs);
    const isDemo=/AO[-_]/.test(r.marche||'');
    const ref=isDemo?`<a class="tlink" href="#dossier=${encodeURIComponent(r.marche)}">${esc(r.marche)} →</a>`:`<span class="mono">${esc(r.marche)}</span>`;
    return `<div class="prow">
      <div class="pscore"><span class="pnum">${r.score}</span><span class="pbar" style="width:${w}%"></span></div>
      <div class="pbody"><div class="ph">${ref} <span class="tl-sub">${esc(r.type)}</span></div>
        <div class="pobjet">${esc(r.objet||'—')}</div>
        <div class="pdetail mono">${(r.detail||[]).map(esc).join(' · ')||'—'}</div></div>
    </div>`;
  }).join('')+'</div>';
  return html;
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
    <div><span class="cle">marché</span>${f.tender?`<a class="tlink" href="#dossier=${encodeURIComponent(f.tender)}">${esc(f.tender)} →</a>`:'—'}</div>
    <div><span class="cle">attendu</span>${f.attendu||'—'}</div>
    <div><span class="cle">observé</span>${f.observe||'—'}</div>
    <div><span class="cle">source</span>${f.source||'—'}</div>
    <div><span class="cle">base</span>${f.base||'—'}</div>
    ${f.citation?`<div><span class="cle">citation</span><span class="cite-txt">${esc(f.citation.citation||'')}</span></div>`:''}
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
function inter(){
  const im=D.inter_marche; if(!im) return '<p class="empty">Accès restreint.</p>';
  if(im.erreur) return head('détection prédictive','Schémas inter-marchés')+`<p class="empty">Détecteur indisponible : ${esc(im.erreur)}</p>`;
  const c=im.corpus||{};
  const SEV={majeur:'◆',mineur:'•',info:'✓'};
  const PUI={faible:'INFERRED',moyenne:'OBSERVED',bonne:'MEASURED'};
  let html=head('détection prédictive · à travers les marchés','Schémas inter-marchés')+
    `<div class="tiles">
      <div class="tile"><div class="k">PV lisibles</div><div class="v">${c.n_lisibles}/${c.n_pv}</div></div>
      <div class="tile"><div class="k">Entreprises</div><div class="v">${c.n_firmes}</div></div>
      <div class="tile"><div class="k">Signaux</div><div class="v">${(im.signaux||[]).length}</div></div>
    </div>
    <div class="masked" style="border-color:rgba(143,180,222,.3);background:rgba(143,180,222,.08);color:var(--fg-2)">${esc(c.adequation||'')}</div>`;
  html+=(im.signaux||[]).map(s=>`
    <div class="flag sev-${s.severite==='info'?'mineur':s.severite}">
      <div class="flag-h">
        <span class="glyph">${SEV[s.severite]||'•'}</span>
        <span class="mono">[${esc(s.type)}]</span><strong>${esc(s.titre)}</strong>
        <span class="confp ${esc(s.confiance)}">${esc(s.confiance)}</span>
        <span class="conf">puissance ${esc(s.puissance)}</span>
      </div>
      <div class="flag-b">
        <div><span class="cle">observé</span>${esc(s.observe)}</div>
        ${s.marches&&s.marches.length?`<div><span class="cle">marchés</span>${s.marches.filter(Boolean).map(esc).join(', ')}</div>`:''}
        ${s.firmes&&s.firmes.length?`<div><span class="cle">entreprises</span>${s.firmes.map(esc).join(' · ')}</div>`:''}
        <div><span class="cle">base</span>${esc(s.base)}</div>
        ${s.citation?`<div><span class="cle">citation</span>${esc(s.citation.citation||'')}</div>`:''}
        ${s.note_absence?`<div><span class="cle">lecture</span><em>${esc(s.note_absence)}</em></div>`:''}
      </div>
    </div>`).join('');
  // fractionnement (contract splitting) — cross-market, same buyer
  const fr=im.fractionnement;
  if(fr && fr.corpus){
    html+=`<h2 style="margin-top:30px">Fractionnement de la commande <span class="tl-sub">même acheteur · objets voisins · même période</span></h2>
    <div class="masked" style="border-color:rgba(217,169,78,.3);background:rgba(217,169,78,.07);color:var(--fg-2)">${esc(fr.corpus.note||'')}</div>`;
    html+=(fr.signaux||[]).map(s=>`
      <div class="flag sev-${s.severite}"><div class="flag-h">
        <span class="glyph">◆</span><span class="mono">[${esc(s.type)}]</span><strong>${esc(s.titre)}</strong>
        <span class="confp ${esc(s.confiance)}">${esc(s.confiance)}</span></div>
      <div class="flag-b">
        ${(s.marches||[]).map((m,i)=>`<div><span class="cle">${i===0?'marchés':''}</span><span class="mono">${esc(m)}</span> — ${esc((s.objets||[])[i]||'')}</div>`).join('')}
        <div><span class="cle">base</span>${esc(s.base)}</div>
        ${s.citation?`<div><span class="cle">citation</span><span class="cite-txt">${esc(s.citation.citation||'')}</span></div>`:''}
      </div></div>`).join('') || '<p class="note">Aucune grappe de fractionnement détectée.</p>';
  }
  // entity resolution transparency (ICE-ready)
  const ent=im.entites;
  if(ent && ent.n_entites){
    const groups=(ent.entites||[]).filter(e=>e.n_alias>1);
    html+=`<h2 style="margin-top:30px">Résolution d'entités <span class="tl-sub">${esc(ent.methode)} · ${ent.n_entites} entités</span></h2>
    <p class="note">${esc(ent.note||'')}</p>`;
    if(groups.length){
      html+='<div class="jlist">'+groups.map(e=>`<div class="jrow"><span class="t mono">${esc(e.label)}</span><span>replie : ${e.alias.map(esc).join(' · ')}</span><span class="h">${esc(e.ice_statut)}</span></div>`).join('')+'</div>';
    }
  }
  // same-owner / same-address related-party links (Velasco)
  const li=im.liens;
  if(li && li.corpus){
    const lc=li.corpus;
    html+=`<h2 style="margin-top:30px">Liens entre soumissionnaires <span class="tl-sub">même gérant · même siège</span></h2>
    <div class="tiles">
      <div class="tile"><div class="k">Marchés</div><div class="v">${lc.n_marches}</div></div>
      <div class="tile"><div class="k">Référentiel RC/ICE</div><div class="v" style="font-size:18px">${lc.registre_present?'présent':'absent'}</div></div>
      <div class="tile"><div class="k">Liens détectés</div><div class="v" style="color:${(li.signaux||[]).length?'var(--crit)':'var(--fg-3)'}">${(li.signaux||[]).length}</div></div>
    </div>
    <div class="masked" style="border-color:rgba(217,169,78,.3);background:rgba(217,169,78,.07);color:var(--fg-2)">${esc(lc.note||'')}</div>`;
    if((li.signaux||[]).length){
      html+=(li.signaux).map(s=>`<div class="flag sev-${s.severite}"><div class="flag-h"><span class="glyph">▲</span><span class="mono">[${esc(s.type)}]</span><strong>${esc(s.titre)}</strong><span class="confp ${esc(s.confiance)}">${esc(s.confiance)}</span></div><div class="flag-b"><div><span class="cle">firmes</span>${(s.firmes||[]).map(esc).join(' · ')}</div><div><span class="cle">base</span>${esc(s.base)}</div>${s.citation?`<div><span class="cle">citation</span><span class="cite-txt">${esc(s.citation.citation||'')}</span></div>`:''}</div></div>`).join('');
    } else {
      html+='<p class="note">Aucun lien gérant/siège détecté (référentiel d\'entreprises absent — résultat attendu). Logique prouvée par <span class="mono">liens_entreprises.py --selftest</span>.</p>';
    }
  }
  // deterministic PDF-metadata forensics (Phase 2)
  const fx=im.forensics;
  if(fx && fx.corpus){
    const fc=fx.corpus;
    html+=`<h2 style="margin-top:30px">Forensics métadonnées PDF <span class="tl-sub">déterministe · origine commune des offres</span></h2>
    <div class="tiles">
      <div class="tile"><div class="k">PDF avec métadonnées</div><div class="v">${fc.n_avec_metadata}/${fc.n_pdf}</div></div>
      <div class="tile"><div class="k">Collisions inter-firmes</div><div class="v" style="color:${(fx.signaux||[]).length?'var(--crit)':'var(--fg-3)'}">${(fx.signaux||[]).length}</div></div>
      <div class="tile"><div class="k">Outils observés</div><div class="v" style="font-size:16px">${(fx.outils_observes||[]).length}</div></div>
    </div>
    <div class="masked" style="border-color:rgba(143,180,222,.3);background:rgba(143,180,222,.08);color:var(--fg-2)">${esc(fc.note||'')}</div>`;
    if((fx.signaux||[]).length){
      html+=(fx.signaux).map(s=>`<div class="flag sev-${s.severite}"><div class="flag-h"><span class="glyph">◆</span><span class="mono">[${esc(s.type)}]</span><strong>${esc(s.titre)}</strong><span class="confp ${esc(s.confiance)}">${esc(s.confiance)}</span></div><div class="flag-b"><div><span class="cle">sources</span>${(s.sources||[]).map(esc).join(' · ')}</div><div><span class="cle">base</span>${esc(s.base)}</div></div></div>`).join('');
    } else {
      html+='<p class="note">Aucune collision de métadonnées entre soumissionnaires distincts sur ce corpus (émetteur unique — résultat attendu). Logique de détection prouvée par le self-test <span class="mono">bid_forensics.py --selftest</span>.</p>';
    }
  }
  return html;
}
function conf(){
  const c=D.conformite; if(!c) return '<p class="empty">Accès restreint.</p>';
  if(c.erreur) return head('assurance','Conformité au défi')+`<p class="empty">Validateur indisponible : ${esc(c.erreur)}</p>`;
  const r=c.resume||{};
  const badge=s=>`<span class="cf-b cf-${s}">${s}</span>`;
  let html=head('World Bank GovTech 2026 · validé contre preuves réelles','Conformité au défi')+
    `<div class="tiles">
      <div class="tile"><div class="k">Conforme</div><div class="v" style="color:var(--measured)">${r.PASS||0}</div></div>
      <div class="tile"><div class="k">Partiel</div><div class="v" style="color:var(--inferred)">${r.PARTIAL||0}</div></div>
      <div class="tile"><div class="k">Écart</div><div class="v" style="color:${(r.GAP||0)?'var(--crit)':'var(--fg-3)'}">${r.GAP||0}</div></div>
      <div class="tile"><div class="k">Exigences</div><div class="v">${c.n}</div></div>
    </div>
    <p class="note">Chaque exigence du cahier des charges est confrontée à une preuve réelle
    (contrôle exécuté sur données réelles, livrable généré, métrique mesurée, cellule RBAC).
    Le statut est <b>dérivé de la preuve</b>, ré-exécutable via <span class="mono">spec_conformance.py</span> ; les écarts sont nommés, jamais masqués.</p>`;
  html+=c.resultats.map(x=>`
    <div class="cf-row cf-${x.status}">
      <div class="cf-h"><span class="mono cf-id">${esc(x.id)}</span>${badge(x.status)}
        <span class="mono cf-sec">${esc(x.section)}</span><b>${esc(x.requirement)}</b></div>
      <div class="cf-ev"><span class="cle">preuve</span><span>${esc(x.evidence||'—')}</span></div>
      <div class="cf-note"><span class="confp ${esc((x.confidence||'').split('/')[0])}">${esc(x.confidence)}</span> ${esc(x.note)}</div>
    </div>`).join('');
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
// open a dossier when its card is clicked (event delegation survives re-renders)
// minimal, dependency-free Markdown → HTML for the deliverables (headings,
// blockquotes, bold, code, nested bullet lists). Everything is escaped first.
function md2html(md){
  // italic only when _..._ is a standalone token — never inside AO_07_2024 refs
  const inl=s=>esc(s).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/(^|[\s(])_([^_]+?)_(?=[\s.,;:)]|$)/g,'$1<em>$2</em>')
    .replace(/`([^`]+?)`/g,'<code>$1</code>');
  let html='', inList=false;
  const closeList=()=>{ if(inList){ html+='</ul>'; inList=false; } };
  for(const raw of String(md).split('\n')){
    const line=raw.replace(/\s+$/,'');
    if(!line.trim()){ closeList(); continue; }
    let m;
    if(m=line.match(/^(#{1,4})\s+(.*)/)){ closeList(); const n=m[1].length; html+=`<h${n}>${inl(m[2])}</h${n}>`; continue; }
    if(m=line.match(/^>\s?(.*)/)){ closeList(); html+=`<blockquote>${inl(m[1])}</blockquote>`; continue; }
    if(m=line.match(/^(\s*)[-*]\s+(.*)/)){ if(!inList){ html+='<ul>'; inList=true; } html+=`<li class="${m[1].length>=2?'sub':''}">${inl(m[2])}</li>`; continue; }
    if(/^(-{3,}|_{3,})$/.test(line)){ closeList(); html+='<hr>'; continue; }
    closeList(); html+=`<p>${inl(line)}</p>`;
  }
  closeList();
  return html;
}
function showDoc(title, bodyHtml, docxName){
  let ov=document.getElementById('doc-ov');
  if(!ov){
    ov=document.createElement('div'); ov.id='doc-ov'; ov.className='doc-ov';
    ov.innerHTML='<div class="doc-panel"><div class="doc-bar"><b id="doc-title"></b><span class="doc-actions"><a id="doc-dl" class="dl" download>.docx ↓</a><span class="doc-x" role="button" tabindex="0">✕ fermer</span></span></div><div class="doc-body markdown" id="doc-body"></div></div>';
    document.body.appendChild(ov);
    const close=()=>ov.classList.remove('on');
    ov.addEventListener('click', e=>{ if(e.target===ov || e.target.classList.contains('doc-x')) close(); });
    document.addEventListener('keydown', e=>{ if(e.key==='Escape') close(); });
  }
  ov.querySelector('#doc-title').textContent=title;
  const dl=ov.querySelector('#doc-dl');
  if(docxName){ dl.href='/api/mohtasib/livrable-docx/'+encodeURIComponent(docxName); dl.style.display=''; }
  else { dl.style.display='none'; }
  ov.querySelector('#doc-body').innerHTML=bodyHtml;
  ov.classList.add('on');
}
async function openLivrable(fichier){
  showDoc(fichier, '<p class="note">Chargement…</p>');
  try{
    const r=await fetch('/api/mohtasib/livrable/'+encodeURIComponent(fichier),{credentials:'same-origin'});
    if(!r.ok){ showDoc(fichier, '<p class="note">Livrable indisponible ('+r.status+').</p>'); return; }
    const d=await r.json();
    showDoc(d.titre||fichier, md2html(d.markdown||''), d.docx);
  }catch(e){ showDoc(fichier, '<p class="note">Erreur réseau.</p>'); }
}

document.getElementById('main').addEventListener('click', e=>{
  const lrow=e.target.closest('.lrow');
  if(lrow && lrow.dataset.livrable){ openLivrable(lrow.dataset.livrable); return; }
  const card=e.target.closest('.doss-card');
  if(card && card.dataset.ref){ location.hash='dossier='+encodeURIComponent(card.dataset.ref); }
});
window.addEventListener('hashchange', route);
boot();

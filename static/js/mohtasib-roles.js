const LEVELCOLORS = {verificateur:'#C65A52',chef_mission:'#C65A52',magistrat:'#7FBF97',ethique:'#D9A94E',president:'#8FB4DE',admin:'#A79E8C'};
let CATALOG = [];

function show(msg, ok){ const m=document.getElementById('msg'); m.textContent=msg; m.className='msg '+(ok?'ok':'err'); setTimeout(()=>{m.className='msg';},4000); }

async function load(){
  let r;
  try { r = await fetch('/api/mohtasib/roles', {credentials:'same-origin'}); }
  catch(e){ document.getElementById('list').innerHTML='<p class="empty">Erreur réseau.</p>'; return; }
  if(r.status===403){ document.getElementById('list').innerHTML='<p class="empty">Réservé aux administrateurs.</p>'; return; }
  if(!r.ok){ document.getElementById('list').innerHTML='<p class="empty">Non authentifié — <a class="back" href="/login">se connecter</a>.</p>'; return; }
  const data = await r.json();
  CATALOG = data.catalog;
  document.getElementById('legend').innerHTML = CATALOG.map(c=>`<span class="lg" style="border-color:${LEVELCOLORS[c.id]}55">${c.label}</span>`).join('');
  const list = document.getElementById('list');
  if(!data.users.length){ list.innerHTML='<p class="empty">Aucun utilisateur.</p>'; return; }
  list.innerHTML = data.users.map(u=>renderUser(u)).join('');
  data.users.forEach(u=>wire(u.username));
}

function renderUser(u){
  const chips = CATALOG.map(c=>{
    const on = u.roles.includes(c.id);
    return `<div class="chip ${on?'on':''}" data-user="${u.username}" data-role="${c.id}">
      <span>${c.label}</span><small>${c.desc}</small></div>`;
  }).join('');
  return `<div class="user" data-u="${u.username}">
    <div class="user-head">
      <span class="uname">${u.username}</span>
      ${u.is_admin?'<span class="badge">app-admin</span>':''}
      ${u.orphan?'<span class="badge orphan">non-app</span>':''}
    </div>
    <div class="chips">${chips}</div>
    <div class="row-foot">
      <span class="dirty" id="dirty-${u.username}">modifié — non enregistré</span>
      <button class="save" id="save-${u.username}" disabled>Enregistrer</button>
    </div>
  </div>`;
}

function wire(username){
  const root = document.querySelector(`.user[data-u="${CSS.escape(username)}"]`);
  const save = document.getElementById('save-'+username);
  const dirty = document.getElementById('dirty-'+username);
  root.querySelectorAll('.chip').forEach(ch=>{
    ch.addEventListener('click', ()=>{ ch.classList.toggle('on'); save.disabled=false; dirty.classList.add('show'); });
  });
  save.addEventListener('click', async ()=>{
    const roles = [...root.querySelectorAll('.chip.on')].map(c=>c.dataset.role);
    save.disabled=true;
    try{
      const r = await fetch('/api/mohtasib/roles', {method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json'}, body:JSON.stringify({username, roles})});
      if(!r.ok){ show('Échec ('+r.status+') — droits administrateur requis.', false); save.disabled=false; return; }
      const d = await r.json();
      dirty.classList.remove('show');
      show(`Rôles de « ${username} » enregistrés : ${d.roles.join(', ')||'aucun'}.`, true);
    }catch(e){ show('Erreur réseau.', false); save.disabled=false; }
  });
}
load();

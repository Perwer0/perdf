
(function(){
  function wireDropzone(zoneId, inputSelector){
    const zone = document.getElementById(zoneId);
    if(!zone) return;
    const input = zone.querySelector(inputSelector);
    zone.addEventListener('click', ()=> input.click());
    zone.addEventListener('dragover', (e)=>{ e.preventDefault(); zone.classList.add('ring-2','ring-slate-300');});
    zone.addEventListener('dragleave', ()=> zone.classList.remove('ring-2','ring-slate-300'));
    zone.addEventListener('drop', (e)=>{
      e.preventDefault();
      zone.classList.remove('ring-2','ring-slate-300');
      if(e.dataTransfer && e.dataTransfer.files){ input.files = e.dataTransfer.files; }
    });
  }

  function wireProgress(formId, progressId){
    const form = document.getElementById(formId);
    const progress = document.getElementById(progressId);
    if(!form || !progress) return;
    form.addEventListener('submit', ()=>{
      progress.classList.remove('hidden');
      let i = 0;
      const timer = setInterval(()=>{
        i = (i+5)%100;
        progress.innerText = 'İşleniyor… %' + (i<10? '0'+i : i);
      }, 250);
      window.addEventListener('beforeunload', ()=> clearInterval(timer));
    });
  }

  wireDropzone('dropzone-merge', '#pdfs');
  wireDropzone('dropzone-split', '#pdf');
  wireDropzone('dropzone-p2i', '#pdfp2i');
  wireDropzone('dropzone-i2p', '#images');
  wireDropzone('dropzone-chat', '#pdfchat');

  wireProgress('mergeForm', 'progress-merge');
  wireProgress('splitForm', 'progress-split');
  wireProgress('p2iForm', 'progress-p2i');
  wireProgress('i2pForm', 'progress-i2p');

  // Tiny CSS helpers
  var style = document.createElement('style');
  style.innerHTML = `
    .dropzone { display:flex; align-items:center; justify-content:center; cursor:pointer; min-height:160px; border:1px dashed rgb(203,213,225); background:white; border-radius:0.75rem; padding:1rem; }
    .primary { display:inline-flex; align-items:center; justify-content:center; border-radius:0.75rem; padding:0.625rem 1rem; font-weight:600; background:#0f172a; color:white; }
    .progress { margin-top:0.75rem; width:100%; text-align:center; border:1px solid rgb(226,232,240); border-radius:0.75rem; padding:0.5rem; background:white; }
  `;
  document.head.appendChild(style);
})();


// ---- Thumbnails + Reorder for Image->PDF ----
(function(){
  const input = document.querySelector('#images');
  const thumbs = document.querySelector('#thumbs');
  const orderInput = document.querySelector('#order');
  if(!input || !thumbs || !orderInput) return;

  let files = [];

  function render(){
    thumbs.innerHTML = '';
    files.forEach((f, idx)=>{
      const url = URL.createObjectURL(f);
      const card = document.createElement('div');
      card.className = 'rounded-xl border border-slate-200 bg-white p-2 flex flex-col gap-2';
      card.innerHTML = `
        <img src="${url}" class="w-full h-32 object-cover rounded-lg" alt="${f.name}" />
        <div class="text-xs text-slate-600 truncate" title="${f.name}">${idx+1}. ${f.name}</div>
        <div class="flex gap-2">
          <button type="button" data-act="up" data-idx="${idx}" class="flex-1 rounded-lg border px-2 py-1">Yukarı</button>
          <button type="button" data-act="down" data-idx="${idx}" class="flex-1 rounded-lg border px-2 py-1">Aşağı</button>
          <button type="button" data-act="del" data-idx="${idx}" class="flex-1 rounded-lg border px-2 py-1">Sil</button>
        </div>
      `;
      thumbs.appendChild(card);
    });
    orderInput.value = files.map((_,i)=>i).join(',');
  }

  input.addEventListener('change', (e)=>{
    files = Array.from(input.files || []);
    render();
  });

  thumbs.addEventListener('click', (e)=>{
    const btn = e.target.closest('button');
    if(!btn) return;
    const act = btn.getAttribute('data-act');
    const idx = parseInt(btn.getAttribute('data-idx'));
    if(Number.isNaN(idx)) return;
    if(act === 'up' && idx > 0){
      [files[idx-1], files[idx]] = [files[idx], files[idx-1]];
    } else if(act === 'down' && idx < files.length-1){
      [files[idx+1], files[idx]] = [files[idx], files[idx+1]];
    } else if(act === 'del'){
      files.splice(idx,1);
    }
    // rebuild FileList (not directly mutable); we send order indices via hidden input
    render();
  });

  // On submit: we need to reorder the FormData too; simpler workaround:
  // We submit as selected order via hidden 'order' and let server reorder by that mapping of original indices.
  const form = document.querySelector('#i2pForm');
  form && form.addEventListener('submit', ()=>{
    // ensure hidden order matches current files order relative to original selection
    // Since browsers don't allow reordering FileList, we rely on server to map using 'order'.
    // orderInput already set in render() based on current order of files array.
  });
})();

// ---- File list + Reorder for Merge ----
(function(){
  const input = document.querySelector('#pdfs');
  const list = document.querySelector('#filelist');
  const orderInput = document.querySelector('#merge-order');
  if(!input || !list || !orderInput) return;

  let files = [];

  function render(){
    list.innerHTML = '';
    files.forEach((f, idx)=>{
      const row = document.createElement('div');
      row.className = 'rounded-xl border border-slate-200 bg-white p-2 flex items-center justify-between gap-2';
      row.innerHTML = `
        <div class="flex-1 truncate text-sm text-slate-700"><span class="text-slate-400 mr-2">${idx+1}.</span> ${f.name}</div>
        <div class="flex items-center gap-2">
          <button type="button" data-act="up" data-idx="${idx}" class="rounded-lg border px-2 py-1 text-sm">Yukarı</button>
          <button type="button" data-act="down" data-idx="${idx}" class="rounded-lg border px-2 py-1 text-sm">Aşağı</button>
          <button type="button" data-act="del" data-idx="${idx}" class="rounded-lg border px-2 py-1 text-sm">Sil</button>
        </div>
      `;
      list.appendChild(row);
    });
    orderInput.value = files.map((_,i)=>i).join(',');
  }

  input.addEventListener('change', ()=>{
    files = Array.from(input.files || []);
    render();
  });

  list.addEventListener('click', (e)=>{
    const btn = e.target.closest('button');
    if(!btn) return;
    const act = btn.getAttribute('data-act');
    const idx = parseInt(btn.getAttribute('data-idx'));
    if(Number.isNaN(idx)) return;
    if(act === 'up' && idx > 0){
      [files[idx-1], files[idx]] = [files[idx], files[idx-1]];
    } else if(act === 'down' && idx < files.length-1){
      [files[idx+1], files[idx]] = [files[idx], files[idx+1]];
    } else if(act === 'del'){
      files.splice(idx,1);
    }
    render();
  });
})();

// ---- Theme Toggle ----
(function(){
  var btn = document.getElementById('themeToggle');
  if(!btn) return;
  function setTheme(dark){
    document.documentElement.classList.toggle('dark', !!dark);
    try{ localStorage.setItem('perdf-theme', dark ? 'dark' : 'light'); }catch(e){}
    btn.textContent = document.documentElement.classList.contains('dark') ? '☀️' : '🌙';
  }
  btn.addEventListener('click', function(){
    var dark = !document.documentElement.classList.contains('dark');
    setTheme(dark);
  });
  // init button state
  setTimeout(function(){
    btn.textContent = document.documentElement.classList.contains('dark') ? '☀️' : '🌙';
  }, 0);
})();

// ---- Entrance animation: mark main as faded-in ----
(function(){
  var main = document.querySelector('main');
  if(main) main.classList.add('fade-in-slow');
})();


// ---- Toast system ----
window.perdfToast = (function(){
  var root = document.getElementById('toast-root');
  if(!root){ return {show:function(){}}; }
  function show(msg, type){
    var el = document.createElement('div');
    var base = 'rounded-xl px-4 py-3 text-sm shadow border transition pointer-events-auto ';
    var theme = (type==='error')
      ? 'bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-900/30 dark:border-rose-800 dark:text-rose-200'
      : 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-900/30 dark:border-emerald-800 dark:text-emerald-200';
    el.className = base + theme + ' fade-in';
    el.textContent = msg;
    root.appendChild(el);
    setTimeout(function(){ el.style.opacity='0'; el.style.transform='translateY(-4px)'; }, 2600);
    setTimeout(function(){ root.removeChild(el); }, 3100);
  }
  return { show: show };
})();

// Attach to forms that download files via hidden iframe for non-navigation UX
(function(){
  var forms = document.querySelectorAll('form[action="/merge"], form[action="/split"], form[action="/pdf_to_image"], form[action="/image_to_pdf"]');
  forms.forEach(function(f){
    f.setAttribute('target', 'dl_iframe');
    f.addEventListener('submit', function(){
      window.perdfToast.show('İşlem başladı…', 'ok');
    });
  });
  var iframe = document.getElementById('dl_iframe');
  if(iframe){
    iframe.addEventListener('load', function(){
      // On any response load, assume success; if server sent an HTML error page, at least notify finish
      window.perdfToast.show('İşlem tamamlandı. İndiriliyor…', 'ok');
    });
  }
})();


// ---- 3D Hero Animation (Three.js) ----
(function(){
  var container = document.getElementById('hero3d');
  if(!container || !window.THREE || container.querySelector('model-viewer')) return;
  var w = container.clientWidth, h = container.clientHeight;

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
  camera.position.set(0, 0, 4);

  var renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
  renderer.setSize(w, h);
  container.innerHTML = '';
  container.appendChild(renderer.domElement);

  // Lights
  var ambient = new THREE.AmbientLight(0xffffff, 0.8);
  scene.add(ambient);
  var dir = new THREE.DirectionalLight(0xffffff, 0.6);
  dir.position.set(3,4,5);
  scene.add(dir);

  // PDF-like card geometry
  var geo = new THREE.BoxGeometry(2.6, 3.6, 0.05, 1, 1, 1);
  var mat = new THREE.MeshStandardMaterial({color: 0xffffff, roughness:0.3, metalness:0.1});
  var card = new THREE.Mesh(geo, mat);
  scene.add(card);

  // A thin secondary sheet
  var mat2 = new THREE.MeshStandardMaterial({color: 0xe2e8f0, roughness:0.5, metalness:0.05});
  var card2 = new THREE.Mesh(new THREE.BoxGeometry(2.5, 3.5, 0.03), mat2);
  card2.position.set(-0.15, -0.15, -0.08);
  scene.add(card2);

  // Background gradient reactive to theme
  function setBG(){
    var dark = document.documentElement.classList.contains('dark');
    renderer.setClearColor(dark ? 0x0b1220 : 0xf4f6fb, 1);
  }
  setBG();
  var mo = new MutationObserver(setBG);
  mo.observe(document.documentElement, { attributes:true, attributeFilter:['class'] });

  // Resize
  window.addEventListener('resize', function(){
    var w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h);
    camera.aspect = w/h; camera.updateProjectionMatrix();
  });

  // Mouse parallax
  var targetRotX = -0.35, targetRotY = 0.4;
  container.addEventListener('mousemove', function(e){
    var r = container.getBoundingClientRect();
    var x = (e.clientX - r.left)/r.width * 2 - 1;
    var y = (e.clientY - r.top)/r.height * 2 - 1;
    targetRotY = x * 0.6;
    targetRotX = -y * 0.6;
  });

  // Animate
  function animate(){
    requestAnimationFrame(animate);
    card.rotation.x += (targetRotX - card.rotation.x) * 0.06;
    card.rotation.y += (targetRotY - card.rotation.y) * 0.06;
    card2.rotation.x = card.rotation.x * 0.9;
    card2.rotation.y = card.rotation.y * 0.9;
    renderer.render(scene, camera);
  }
  animate();
})();


// ---- Start Modal (animated) ----
(function(){
  var btn = document.getElementById('startBtn');
  var modal = document.getElementById('startModal');
  if(!modal) return;
  var card = modal.querySelector('.start-modal-card');
  var bg = modal.querySelector('.modal-bg');
  var closeBtn = document.getElementById('startClose');
  function open(){ modal.classList.remove('hidden'); setTimeout(function(){ card.classList.add('show'); }, 0); }
  function close(){ card.classList.remove('show'); setTimeout(function(){ modal.classList.add('hidden'); }, 180); }
  btn && btn.addEventListener('click', function(e){ e.preventDefault(); open(); });
  closeBtn && closeBtn.addEventListener('click', close);
  bg && bg.addEventListener('click', close);
  window.addEventListener('keydown', function(e){ if(e.key==='Escape') close(); });
})();


// ---- 3D Hero enrichment ----
(function(){
  var container = document.getElementById('hero3d');
  if(!container || !window.THREE || container.querySelector('model-viewer')) return;

  var w = container.clientWidth, h = container.clientHeight;
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
  camera.position.set(0, 0, 5);

  var renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  container.innerHTML='';
  container.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.85));
  var key = new THREE.DirectionalLight(0xffffff, 0.7);
  key.position.set(3,4,5); scene.add(key);

  var card = new THREE.Mesh(new THREE.BoxGeometry(2.6,3.6,0.06), new THREE.MeshStandardMaterial({color:0xffffff, roughness:0.25}));
  scene.add(card);

  var minis = [];
  var miniMat = new THREE.MeshStandardMaterial({color:0x94a3b8, metalness:0.1, roughness:0.6});
  for(var i=0;i<5;i++){ var m=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.7,0.04), miniMat.clone()); scene.add(m); minis.push(m); }

  function setBG(){
    var dark = document.documentElement.classList.contains('dark');
    renderer.setClearColor(dark ? 0x0b1220 : 0xf4f7fb, 1);
  }
  setBG();
  var mo = new MutationObserver(setBG);
  mo.observe(document.documentElement, {attributes:true, attributeFilter:['class']});

  window.addEventListener('resize', function(){
    var w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h); camera.aspect = w/h; camera.updateProjectionMatrix();
  });

  var playing = false;
  container.addEventListener('mouseenter', function(){ playing = true; });
  container.addEventListener('mouseleave', function(){ playing = false; });

  var t = 0;
  function animate(){
    requestAnimationFrame(animate);
    t += 0.01;
    var speed = playing ? 1.2 : 0.6;
    card.rotation.x = Math.sin(t*speed)*0.15 - 0.1;
    card.rotation.y = Math.cos(t*speed)*0.25 + 0.3;
    minis.forEach(function(m, idx){
      var a = t*speed + idx*1.2;
      var r = 1.6 + (idx%2)*0.25;
      m.position.set(Math.cos(a)*r, Math.sin(a*1.4)*0.6, Math.sin(a)*0.8);
      m.rotation.x = a*0.7; m.rotation.y = a*0.9;
    });
    renderer.render(scene, camera);
  }
  animate();
})();


// Update toggle icon on load (default light)
(function(){
  var btn = document.getElementById('themeToggle');
  if(!btn) return;
  btn.textContent = document.documentElement.classList.contains('dark') ? '☀️' : '🌙';
})();


// ---- Robust hook for "Hemen Başla" ----
(function(){
  var btn = document.getElementById('startBtn');
  if(!btn){
    // Fallback: find a .primary link whose text includes 'Hemen Başla'
    var candidates = Array.from(document.querySelectorAll('a.primary'));
    btn = candidates.find(function(a){ return (a.textContent||'').trim().toLowerCase().indexOf('hemen başla')>-1; });
    if(btn) btn.setAttribute('id','startBtn');
  }
})();


// ---- Modal keyboard shortcuts (B,S,P,G,C) ----
(function(){
  var modal = document.getElementById('startModal');
  if(!modal) return;
  var map = {};
  modal.querySelectorAll('.glass-tile').forEach(function(tile){
    var key = (tile.getAttribute('data-key')||'').toLowerCase();
    if(key) map[key] = tile.getAttribute('href');
  });
  window.addEventListener('keydown', function(e){
    if(modal.classList.contains('hidden')) return;
    var k = (e.key||'').toLowerCase();
    if(map[k]){
      window.location.href = map[k];
    }
  });
})();

// ---- Last used tool badge ----
(function(){
  var known = ['/merge','/split','/pdf_to_image','/image_to_pdf','/pdf_chat'];
  var path = window.location.pathname;
  if(known.indexOf(path) >= 0){
    try{ localStorage.setItem('perdf-last', path); }catch(e){}
  }
  var last = null;
  try{ last = localStorage.getItem('perdf-last'); }catch(e){}
  var badge = document.getElementById('lastUsedBadge');
  if(badge && last && path !== last){
    badge.href = last;
    badge.classList.remove('hidden');
  }
})();


// ---- 3D Hero v2: Try online GLTF model, fallback to card ----
(function(){
  var container = document.getElementById('hero3d');
  if(!container || !window.THREE || container.querySelector('model-viewer')) return;

  var w = container.clientWidth, h = container.clientHeight;
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
  camera.position.set(0, 0.8, 3.5);

  var renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  container.innerHTML='';
  container.appendChild(renderer.domElement);

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 1.0));
  var dir = new THREE.DirectionalLight(0xffffff, 0.9);
  dir.position.set(3,4,5);
  scene.add(dir);

  // Controls (hover orbit)
  var controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enablePan = false; controls.enableZoom = false;
  controls.autoRotate = true; controls.autoRotateSpeed = 1.0;

  function setBG(){
    var dark = document.documentElement.classList.contains('dark');
    renderer.setClearColor(dark ? 0x0b1220 : 0xf4f7fb, 1);
  }
  setBG();
  var mo = new MutationObserver(setBG);
  mo.observe(document.documentElement, {attributes:true, attributeFilter:['class']});

  window.addEventListener('resize', function(){
    var w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h); camera.aspect=w/h; camera.updateProjectionMatrix();
  });

  var clock = new THREE.Clock();
  var mixer = null;
  var modelLoaded = false;

  function loadGLTF(url){
    try{
      var loader = new THREE.GLTFLoader();
      loader.load(url, function(gltf){
        var model = gltf.scene || gltf.scene;
        model.scale.set(1.2,1.2,1.2);
        scene.add(model);
        if(gltf.animations && gltf.animations.length){
          mixer = new THREE.AnimationMixer(model);
          var action = mixer.clipAction(gltf.animations[0]);
          action.play();
        }
        modelLoaded = true;
      }, undefined, function(err){
        console.warn('GLTF failed', err);
      });
    }catch(e){ console.warn('GLTF loader missing', e); }
  }

  // Try a known CORS-friendly model
  loadGLTF('https://modelviewer.dev/shared-assets/models/Astronaut.glb');

  // Fallback: show procedural rotating cards if model doesn't load within 2s
  var fallbackGroup = new THREE.Group();
  var addedFallback = false;
  function addFallback(){
    if(addedFallback || modelLoaded) return;
    addedFallback = true
  }
  // But in JS string need true lowercase

  setTimeout(function(){
    if(modelLoaded) return;
    var g1 = new THREE.BoxGeometry(2.6,3.6,0.06);
    var m1 = new THREE.MeshStandardMaterial({color:0xffffff, roughness:0.25});
    var card = new THREE.Mesh(g1, m1);
    fallbackGroup.add(card);
    var minis = [];
    var miniMat = new THREE.MeshStandardMaterial({color:0x94a3b8, metalness:0.1, roughness:0.6});
    for(var i=0;i<5;i++){ var m=new THREE.Mesh(new THREE.BoxGeometry(0.5,0.7,0.04), miniMat.clone()); fallbackGroup.add(m); minis.push(m); }
    scene.add(fallbackGroup);
    // animate minis in animate loop
    fallbackGroup.userData.minis = minis;
  }, 2000);

  container.addEventListener('mouseenter', function(){ controls.autoRotateSpeed = 2.2; });
  container.addEventListener('mouseleave', function(){ controls.autoRotateSpeed = 1.0; });

  function animate(){
    requestAnimationFrame(animate);
    var dt = clock.getDelta();
    controls.update();
    if(mixer) mixer.update(dt);
    if(fallbackGroup.parent){
      var minis = fallbackGroup.userData.minis || [];
      var t = performance.now()*0.001;
      fallbackGroup.rotation.y = t*0.3;
      minis.forEach(function(m, idx){
        var a = t + idx*1.2;
        var r = 1.6 + (idx%2)*0.25;
        m.position.set(Math.cos(a)*r, Math.sin(a*1.4)*0.6, Math.sin(a)*0.8);
        m.rotation.x = a*0.7; m.rotation.y = a*0.9;
      });
    }
    renderer.render(scene, camera);
  }
  animate();
})();


// ---- Progress bar: start/stop correctly on download forms ----
(function(){
  var targets = [
    {formSel:'form[action="/merge"]', bar:'#progress-merge'},
    {formSel:'form[action="/split"]', bar:'#progress-split'},
    {formSel:'form[action="/pdf_to_image"]', bar:'#progress-p2i'},
    {formSel:'form[action="/image_to_pdf"]', bar:'#progress-i2p'}
  ];
  var iframe = document.getElementById('dl_iframe');
  var active = null;
  var timer = null;
  function start(el){
    if(!el) return;
    active = el;
    el.classList.remove('hidden');
    var pct = 1;
    el.textContent = 'İşleniyor... %' + pct;
    clearInterval(timer);
    timer = setInterval(function(){
      // Ease towards 90%, never exceed; the rest waits for server
      pct = Math.min(90, pct + Math.max(1, Math.floor((100-pct)*0.04)));
      el.textContent = 'İşleniyor... %' + pct;
    }, 200);
  }
  function stop(success){
    if(!active) return;
    clearInterval(timer);
    active.textContent = success ? 'Hazır! %100' : 'Tamamlandı';
    setTimeout(function(){ active.classList.add('hidden'); active = null; }, 900);
  }
  targets.forEach(function(t){
    var f = document.querySelector(t.formSel);
    var bar = document.querySelector(t.bar);
    if(!f || !bar) return;
    // ensure download via iframe
    f.setAttribute('target', 'dl_iframe');
    f.addEventListener('submit', function(){ start(bar); });
  });
  if(iframe){
    iframe.addEventListener('load', function(){ stop(true); });
  }
})();

// ---- Robust progress handling for download forms ----
(function(){
  var forms = document.querySelectorAll('form[action="/merge"], form[action="/split"], form[action="/pdf_to_image"], form[action="/image_to_pdf"]');
  var iframe = document.getElementById('dl_iframe');
  var timer = null;
  function startProgress(form){
    var bar = form.querySelector('.progress');
    if(!bar) return;
    bar.classList.remove('hidden');
    var p = 0;
    bar.textContent = 'İşleniyor... %0';
    clearInterval(timer);
    timer = setInterval(function(){
      p = Math.min(95, p + 3); // never reach 100 until load
      bar.textContent = 'İşleniyor... %' + p;
    }, 400);
  }
  function finishAll(){
    clearInterval(timer);
    document.querySelectorAll('.progress').forEach(function(bar){
      bar.textContent = 'Tamamlandı %100';
      setTimeout(function(){ bar.classList.add('hidden'); }, 800);
    });
  }
  forms.forEach(function(f){
    f.setAttribute('target','dl_iframe');
    f.addEventListener('submit', function(){ startProgress(f); });
  });
  if(iframe){
    iframe.addEventListener('load', function(){ finishAll(); });
  }
})();


// ---- PDF Icon 3D (no external assets) ----
(function(){
  var container = document.getElementById('hero3d');
  if(!container || !window.THREE) return;

  // If a <model-viewer> was previously injected, remove it
  var mv = container.querySelector('model-viewer');
  if(mv){ container.removeChild(mv); }

  var w = container.clientWidth, h = container.clientHeight;
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(45, w/h, 0.1, 100);
  camera.position.set(0, 0.3, 5);

  var renderer = new THREE.WebGLRenderer({antialias:true, alpha:true});
  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio||1));
  container.innerHTML='';
  container.appendChild(renderer.domElement);

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 0.9));
  var dir = new THREE.DirectionalLight(0xffffff, 0.7);
  dir.position.set(3,4,5); scene.add(dir);

  // Helper function to make rounded-rect plane using Shape
  function roundedRectShape(w,h,r){
    var s = new THREE.Shape();
    var x=-w/2, y=-h/2;
    s.moveTo(x+r, y);
    s.lineTo(x+w-r, y);
    s.quadraticCurveTo(x+w, y, x+w, y+r);
    s.lineTo(x+w, y+h-r);
    s.quadraticCurveTo(x+w, y+h, x+w-r, y+h);
    s.lineTo(x+r, y+h);
    s.quadraticCurveTo(x, y+h, x, y+h-r);
    s.lineTo(x, y+r);
    s.quadraticCurveTo(x, y, x+r, y);
    return s;
  }

  // Main white sheet
  var sheetGeom = new THREE.ExtrudeGeometry(roundedRectShape(2.6,3.6,0.18), {depth:0.06, bevelEnabled:false});
  var sheet = new THREE.Mesh(sheetGeom, new THREE.MeshStandardMaterial({color:0xffffff, roughness:0.3}));
  scene.add(sheet);

  // Red header band (like PDF icon)
  var headerGeom = new THREE.BoxGeometry(2.6, 0.7, 0.061);
  var header = new THREE.Mesh(headerGeom, new THREE.MeshStandardMaterial({color:0xcc1122, roughness:0.4, metalness:0.05}));
  header.position.y = 1.25;
  scene.add(header);

  // "PDF" text made as a canvas texture on a plane
  function makeTextMesh(text){
    var c = document.createElement('canvas'); c.width = 512; c.height = 256;
    var ctx = c.getContext('2d');
    ctx.fillStyle = '#cc1122'; ctx.fillRect(0,0,512,256);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 140px Inter, Arial, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(text, 256, 128);
    var tex = new THREE.CanvasTexture(c);
    var geo = new THREE.PlaneGeometry(1.8, 0.6);
    var mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({map: tex, transparent:false}));
    mesh.position.set(0, 1.25, 0.034);
    return mesh;
  }
  var pdfLabel = makeTextMesh('PDF');
  scene.add(pdfLabel);

  // Folded corner triangle
  var corner = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 0.55), new THREE.MeshStandardMaterial({color:0xf2f2f2, side:THREE.DoubleSide}));
  corner.rotation.z = -Math.PI/4;
  corner.position.set(1.0, 1.7, 0.032);
  scene.add(corner);

  // Orbiting pages (mini sheets)
  var minis = [];
  var miniMat = new THREE.MeshStandardMaterial({color:0xe5e7eb, roughness:0.6});
  for(var i=0;i<3;i++){
    var g = new THREE.BoxGeometry(0.7,0.9,0.04);
    var m = new THREE.Mesh(g, miniMat);
    scene.add(m); minis.push(m);
  }

  // Background reacts to theme
  function setBG(){
    var dark = document.documentElement.classList.contains('dark');
    renderer.setClearColor(dark ? 0x0b1220 : 0xf4f7fb, 1);
  }
  setBG();
  var mo = new MutationObserver(setBG);
  mo.observe(document.documentElement, {attributes:true, attributeFilter:['class']});

  // Resize
  window.addEventListener('resize', function(){
    var w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h); camera.aspect = w/h; camera.updateProjectionMatrix();
  });

  // Interaction
  var playing = false;
  container.addEventListener('mouseenter', function(){ playing = true; });
  container.addEventListener('mouseleave', function(){ playing = false; });

  var t=0;
  function animate(){
    requestAnimationFrame(animate);
    t += 0.01;
    var speed = playing ? 1.2 : 0.6;
    sheet.rotation.x = Math.sin(t*speed)*0.12 - 0.05;
    sheet.rotation.y = Math.cos(t*speed)*0.22 + 0.25;
    header.rotation.copy(sheet.rotation);
    pdfLabel.rotation.copy(sheet.rotation);
    corner.rotation.z = -Math.PI/4 + Math.sin(t*speed)*0.02;
    corner.rotation.x = sheet.rotation.x; corner.rotation.y = sheet.rotation.y;

    minis.forEach(function(m, idx){
      var a = t*speed + idx*1.8;
      var r = 1.8 + idx*0.25;
      m.position.set(Math.cos(a)*r, Math.sin(a*1.2)*0.7, Math.sin(a)*0.6);
      m.rotation.x = a*0.9; m.rotation.y = a*0.7;
    });

    renderer.render(scene, camera);
  }
  animate();
})();

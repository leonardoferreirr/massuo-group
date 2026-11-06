// Massuo Group: a esfera do logo em 3D ao vivo. Vidro vermelho com verniz (clearcoat), a onda preta do M
// na frente (textura feita do massuo-onda.svg, projetada de frente sobre a esfera, como no logo), reflexo
// de um ambiente escuro com softboxes, e a esfera acompanhando o mouse com suavidade. No celular responde
// à rolagem (setScroll). Carrega só na primeira interação; até lá a página mostra o pôster na mesma caixa.
//
// API: mountEsfera(canvas, { mobile, reducedMotion, onda }) -> { ready, setScroll, setPointer, pause, resume, dispose, info }
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.min.js';

const FOV = 28;
const PREENCHE = 0.985;      // diâmetro da esfera / lado do canvas (o pôster ocupa 660 de 666 px)
const LIMITE = { yaw: 0.42, pitch: 0.3 };

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

/** Textura de cor (vermelho + onda preta) e de relevo (onda em branco suave) a partir do SVG da onda. */
async function texturas(ondaUrl) {
  let svg = await fetch(ondaUrl).then((r) => r.text());
  // Safari precisa de largura e altura explícitas para desenhar SVG no canvas
  svg = svg.replace('<svg ', '<svg width="1024" height="1024" ');
  const img = new Image();
  const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml' }));
  await new Promise((res, rej) => { img.onload = res; img.onerror = rej; img.src = url; });
  const S = 1024;
  const cor = document.createElement('canvas'); cor.width = cor.height = S;
  const g = cor.getContext('2d');
  const grd = g.createRadialGradient(S * 0.44, S * 0.38, S * 0.04, S * 0.5, S * 0.5, S * 0.64);
  grd.addColorStop(0, '#ef1a26'); grd.addColorStop(0.62, '#cc0d19'); grd.addColorStop(1, '#8a0510');
  g.fillStyle = grd; g.fillRect(0, 0, S, S);
  g.drawImage(img, 0, 0, S, S);
  // máscara da onda em branco, para o relevo
  const m = document.createElement('canvas'); m.width = m.height = S;
  const gm = m.getContext('2d');
  gm.drawImage(img, 0, 0, S, S);
  gm.globalCompositeOperation = 'source-in'; gm.fillStyle = '#fff'; gm.fillRect(0, 0, S, S);
  const rel = document.createElement('canvas'); rel.width = rel.height = S;
  const gr = rel.getContext('2d');
  gr.fillStyle = '#7a7a7a'; gr.fillRect(0, 0, S, S);
  try { gr.filter = 'blur(4px)'; } catch (_) { /* sem filtro: borda dura, ainda funciona */ }
  gr.drawImage(m, 0, 0);
  URL.revokeObjectURL(url);
  const tCor = new THREE.CanvasTexture(cor); tCor.colorSpace = THREE.SRGBColorSpace; tCor.anisotropy = 4;
  const tRel = new THREE.CanvasTexture(rel);
  return { tCor, tRel };
}

/** Ambiente: sala escura com softboxes, para o reflexo de verniz (PMREM). */
function ambiente(renderer) {
  const pm = new THREE.PMREMGenerator(renderer);
  const sc = new THREE.Scene();
  sc.add(new THREE.Mesh(new THREE.BoxGeometry(12, 12, 12), new THREE.MeshBasicMaterial({ color: 0x060607, side: THREE.BackSide })));
  const luz = (w, h, x, y, z, cor, intens) => {
    const mat = new THREE.MeshBasicMaterial({ color: cor });
    mat.color.multiplyScalar(intens);
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
    mesh.position.set(x, y, z); mesh.lookAt(0, 0, 0); sc.add(mesh);
  };
  luz(3.6, 1.3, -3.2, 3.4, 2.6, 0xffffff, 7);     // softbox principal, alto à esquerda (o brilho do logo)
  luz(0.6, 5, 4.2, 0.6, 0.6, 0xdde5ff, 5.5);      // tira fria à direita: borda prata
  luz(0.35, 4, -4.4, -0.4, -0.8, 0xc9cdd3, 2.2);  // fio de luz à esquerda, atrás
  luz(1.1, 1.1, 1.6, 3.6, -2.2, 0xffffff, 1.6);   // ponto alto atrás
  luz(5, 0.35, 0, -3.8, 2.2, 0xffffff, 0.7);      // leve reflexo de piso
  const tex = pm.fromScene(sc, 0.03).texture;
  pm.dispose();
  sc.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
  return tex;
}

export async function mountEsfera(canvas, opts = {}) {
  const mobile = !!opts.mobile, reduced = !!opts.reducedMotion;
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
  renderer.setClearColor(0x000000, 0);
  const dpr = Math.min(window.devicePixelRatio || 1, mobile ? 1.5 : 2);
  renderer.setPixelRatio(dpr);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 50);
  const theta = Math.atan(PREENCHE * Math.tan((FOV / 2) * Math.PI / 180));
  camera.position.set(0, 0, 1 / Math.sin(theta));
  camera.lookAt(0, 0, 0);

  const { tCor, tRel } = await texturas(opts.onda || '/assets/img/massuo-onda.svg');
  const env = ambiente(renderer);

  const geo = new THREE.SphereGeometry(1, mobile ? 96 : 144, mobile ? 72 : 108);
  // projeção de frente: o quadrado da textura é o quadrado que envolve a esfera (como o viewBox da onda)
  const pos = geo.attributes.position, uv = geo.attributes.uv;
  for (let i = 0; i < pos.count; i++) uv.setXY(i, 0.5 + pos.getX(i) * 0.5, 0.5 + pos.getY(i) * 0.5);
  uv.needsUpdate = true;

  const material = new THREE.MeshPhysicalMaterial({
    map: tCor, bumpMap: tRel, bumpScale: mobile ? 0.6 : 0.9,
    color: 0xffffff, roughness: 0.2, metalness: 0,
    clearcoat: 1, clearcoatRoughness: 0.05,
    envMap: env, envMapIntensity: 1.25, ior: 1.5, specularIntensity: 1,
  });
  const esfera = new THREE.Mesh(geo, material);
  const grupo = new THREE.Group(); grupo.add(esfera); scene.add(grupo);

  const chave = new THREE.DirectionalLight(0xffffff, 2.6); chave.position.set(-2.6, 3.2, 2.8); scene.add(chave);
  const borda = new THREE.DirectionalLight(0xdde5ff, 1.8); borda.position.set(3.4, 0.4, -0.9); scene.add(borda);
  scene.add(new THREE.AmbientLight(0xffffff, 0.12));

  // --- estado
  let W = 1, Hh = 1;
  let yawT = 0, pitchT = 0, yaw = 0, pitch = 0;
  let scrollP = 0;
  let raf = 0, paused = false, hidden = document.visibilityState === 'hidden', disposed = false;
  let lastNow = 0, firstDone = false, readyResolve = null, t0 = 0;
  const idle = !reduced && !mobile;
  const finePointer = !mobile && !reduced && matchMedia('(pointer: fine)').matches;

  function resize() {
    const w = canvas.clientWidth || 1, h = canvas.clientHeight || 1;
    if (w === W && h === Hh) return;
    W = w; Hh = h;
    renderer.setSize(W, Hh, false);
    camera.aspect = W / Hh; camera.updateProjectionMatrix();
    request();
  }

  function render(now) {
    const t = (now - t0) / 1000;
    let iy = 0, ip = 0, by = 0;
    if (idle) { iy = Math.sin(t * 0.42) * 0.07; ip = Math.sin(t * 0.61 + 1) * 0.035; by = Math.sin(t * 0.8) * 0.012; }
    grupo.rotation.set(pitch + ip, yaw + iy, 0);
    grupo.position.y = by;
    renderer.render(scene, camera);
  }

  function request() {
    if (!raf && (!paused || !firstDone) && !hidden && !disposed) raf = requestAnimationFrame(tick);
  }

  function tick(now) {
    raf = 0;
    if (disposed) return;
    if (!t0) t0 = now;
    const dt = lastNow ? Math.min(50, now - lastNow) : 16.7; lastNow = now;
    let moving = idle;
    const k = 1 - Math.pow(0.9, dt / 16.7);
    const dy = yawT - yaw, dp = pitchT - pitch;
    if (reduced || !firstDone) { yaw = yawT; pitch = pitchT; }
    else if (Math.abs(dy) > 2e-4 || Math.abs(dp) > 2e-4) { yaw += dy * k; pitch += dp * k; moving = true; }
    else { yaw = yawT; pitch = pitchT; }
    render(now);
    if (!firstDone) {
      firstDone = true;
      requestAnimationFrame(() => { readyResolve && readyResolve(); });
    }
    if (moving && !paused && !hidden) raf = requestAnimationFrame(tick);
    else lastNow = 0;
  }

  // --- eventos (tudo passivo: nunca segura o scroll)
  const onMove = (e) => {
    if (e.pointerType && e.pointerType !== 'mouse') return;
    const r = canvas.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    yawT = clamp(((e.clientX - cx) / window.innerWidth) * 1.1, -LIMITE.yaw, LIMITE.yaw);
    pitchT = clamp(((e.clientY - cy) / window.innerHeight) * 0.9, -LIMITE.pitch, LIMITE.pitch);
    request();
  };
  if (finePointer) window.addEventListener('pointermove', onMove, { passive: true });

  const onVis = () => { hidden = document.visibilityState === 'hidden'; if (hidden) { if (raf) cancelAnimationFrame(raf); raf = 0; } else request(); };
  document.addEventListener('visibilitychange', onVis);
  const io = new IntersectionObserver((es) => {
    paused = !es[0].isIntersecting;
    if (paused) { if (raf) cancelAnimationFrame(raf); raf = 0; } else request();
  });
  io.observe(canvas);
  const ro = new ResizeObserver(() => resize());
  ro.observe(canvas);
  resize();

  const ready = new Promise((res) => { readyResolve = res; });
  request();

  return {
    ready,
    /** p = 0..1 da rolagem do topo (celular: a esfera gira conforme a página desce) */
    setScroll(p) {
      scrollP = clamp(+p || 0, 0, 1);
      if (!finePointer) { yawT = -scrollP * 0.9; pitchT = scrollP * 0.45; request(); }
    },
    setPointer(x, y) { yawT = clamp(x, -LIMITE.yaw, LIMITE.yaw); pitchT = clamp(y, -LIMITE.pitch, LIMITE.pitch); request(); },
    pause() { paused = true; if (raf) cancelAnimationFrame(raf); raf = 0; },
    resume() { paused = false; request(); },
    info() { return { drawCalls: renderer.info.render.calls, dpr, size: [W, Hh], yaw, pitch, scroll: scrollP }; },
    dispose() {
      disposed = true;
      if (raf) cancelAnimationFrame(raf);
      if (finePointer) window.removeEventListener('pointermove', onMove);
      document.removeEventListener('visibilitychange', onVis);
      io.disconnect(); ro.disconnect();
      geo.dispose(); material.dispose(); tCor.dispose(); tRel.dispose(); env.dispose();
      renderer.dispose(); renderer.forceContextLoss();
    },
  };
}

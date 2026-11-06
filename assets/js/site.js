/* Massuo Group: núcleo do site. Sem dependência para o essencial (menu, revelações, propósito aceso,
   fileira de empresas, formulário). A esfera ao vivo (esfera.js) entra logo depois do load, sobre o pôster idêntico. */
(() => {
  document.documentElement.classList.add('js');
  const d = document, h = d.documentElement, w = window;
  const mob = w.matchMedia('(max-width:860px)');
  const rm = w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ESFERA = '/assets/js/esfera.js?v=2a2426ea45';

  /* ---------- cabeçalho e menu ---------- */
  const top = d.querySelector('.top'), burger = d.querySelector('.burger');
  if (burger) burger.addEventListener('click', () => {
    const open = !h.classList.contains('menu-open');
    h.classList.toggle('menu-open', open);
    burger.setAttribute('aria-expanded', open);
    burger.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
  });
  d.querySelectorAll('.nav a').forEach(a => a.addEventListener('click', () => {
    h.classList.remove('menu-open');
    burger && burger.setAttribute('aria-expanded', 'false');
  }));

  /* âncoras da mesma página */
  d.addEventListener('click', e => {
    const a = e.target.closest('a[href*="#"]');
    if (!a) return;
    const url = new URL(a.href, location.href);
    if (url.pathname.replace(/\/$/, '') !== location.pathname.replace(/\/$/, '') || !url.hash) return;
    const alvo = d.querySelector(url.hash);
    if (!alvo) return;
    e.preventDefault();
    alvo.scrollIntoView({ behavior: rm ? 'auto' : 'smooth' });
    history.replaceState(null, '', url.hash);
  });

  /* ---------- revelações (com reserva: nada fica invisível) ---------- */
  const rvs = [...d.querySelectorAll('.rv')];
  const mostrar = el => el.classList.add('in');
  if ('IntersectionObserver' in w) {
    const io = new IntersectionObserver(es => es.forEach(en => {
      if (en.isIntersecting) { mostrar(en.target); io.unobserve(en.target); }
    }), { rootMargin: '0px 0px -8% 0px' });
    rvs.forEach(el => io.observe(el));
  } else rvs.forEach(mostrar);
  const reserva = () => rvs.forEach(el => { if (el.getBoundingClientRect().top < innerHeight) mostrar(el); });
  setTimeout(reserva, 2500);
  setTimeout(() => rvs.forEach(mostrar), 9000);

  /* ---------- esfera do logo ao vivo: entra depois do load, pôster idêntico até lá ---------- */
  const hero = d.querySelector('.hero'), esfera = d.querySelector('.esfera');
  let bola = null, montou = false;
  const montar = () => {
    if (montou || !esfera) return;
    montou = true;
    gatilhos.forEach(ev => w.removeEventListener(ev, montar));
    import(ESFERA)
      .then(m => m.mountEsfera(esfera.querySelector('.esfera__canvas'), { mobile: mob.matches, reducedMotion: rm }))
      .then(b => { bola = b; pedir(); return b.ready; })
      .then(() => esfera.classList.add('live'))
      .catch(err => console.warn('3D indisponível, fica o pôster', err));
  };
  const gatilhos = ['pointermove', 'touchstart', 'scroll', 'wheel', 'keydown'];
  if (esfera) {
    gatilhos.forEach(ev => w.addEventListener(ev, montar, { passive: true }));
    if (d.readyState === 'complete') setTimeout(montar, 900);
    else w.addEventListener('load', () => setTimeout(montar, 900), { once: true });
  }

  /* ---------- propósito aceso palavra a palavra ---------- */
  const manif = d.querySelector('[data-manifesto]'), palavras = manif ? [...manif.querySelectorAll('span')] : [];
  let acesas = -1;
  const acender = () => {
    if (!manif) return;
    const sec = manif.closest('.quem'), r = sec.getBoundingClientRect(), H = innerHeight;
    /* a seção fica parada na tela enquanto o texto acende; termina antes de ela ir embora */
    const total = Math.max(1, sec.offsetHeight - H);
    const p = rm || total < H * .2 ? 1 : Math.min(1, Math.max(0, (H * .12 - r.top) / (total * .92)));
    const n = Math.round(p * palavras.length);
    if (n !== acesas) { palavras.forEach((s, i) => s.classList.toggle('on', i < n)); acesas = n; }
  };
  /* a foto parada atrás só pinta quando a seção está por perto */
  const secQuem = d.querySelector('.quem');
  if (secQuem && 'IntersectionObserver' in w) {
    new IntersectionObserver(([en]) => secQuem.classList.toggle('perto', en.isIntersecting), { rootMargin: '30% 0px' }).observe(secQuem);
  } else if (secQuem) secQuem.classList.add('perto');

  /* ---------- um único laço de scroll ---------- */
  const zap = d.querySelector('.zap');
  let pendente = false;
  const quadro = () => {
    pendente = false;
    const y = w.scrollY;
    top && top.classList.toggle('solid', y > 40);
    const secQ = d.querySelector('.quem'), rq = secQ ? secQ.getBoundingClientRect() : null;
    /* no celular a bolinha não cobre o texto enquanto Quem somos está parada na tela */
    const parada = mob.matches && rq && rq.top < innerHeight * .5 && rq.bottom > innerHeight * .5;
    zap && zap.classList.toggle('ver', y > innerHeight * 0.5 && !parada);
    hero && hero.classList.toggle('moved', y > 20);
    acender();
    if (bola && hero) {
      /* no celular a esfera responde à rolagem do topo */
      const p = Math.min(1, Math.max(0, y / Math.max(1, hero.offsetHeight)));
      bola.setScroll(p);
    }
  };
  const pedir = () => { if (!pendente) { pendente = true; requestAnimationFrame(quadro); } };
  w.addEventListener('scroll', pedir, { passive: true });
  w.addEventListener('resize', pedir, { passive: true });
  quadro();

  /* ---------- fileira de empresas (estilo catálogo): setas, arrasto, centralizada quando cabe ---------- */
  d.querySelectorAll('[data-fila]').forEach(fila => {
    /* no toque não existe mouse: a empresa que está em foco na fileira ganha a cor */
    if (w.matchMedia('(hover:none)').matches && 'IntersectionObserver' in w) {
      const ioCor = new IntersectionObserver(es => es.forEach(en => en.target.classList.toggle('cor', en.intersectionRatio > .8)), { root: fila.querySelector('.fila__trilho'), threshold: [.8] });
      fila.querySelectorAll('.card').forEach(c => ioCor.observe(c));
    }
    const trilho = fila.querySelector('.fila__trilho');
    const ant = fila.querySelector('[data-ant]'), prox = fila.querySelector('[data-prox]');
    const passo = () => Math.max(trilho.clientWidth * 0.8, 260);
    const cabe = () => {
      fila.classList.remove('fila--cabe');
      const sobra = trilho.scrollWidth - trilho.clientWidth;
      fila.classList.toggle('fila--cabe', !mob.matches && sobra <= 2);
    };
    const estado = () => {
      if (!ant) return;
      ant.disabled = trilho.scrollLeft < 8;
      prox.disabled = trilho.scrollLeft + trilho.clientWidth > trilho.scrollWidth - 8;
    };
    ant && ant.addEventListener('click', () => trilho.scrollBy({ left: -passo(), behavior: rm ? 'auto' : 'smooth' }));
    prox && prox.addEventListener('click', () => trilho.scrollBy({ left: passo(), behavior: rm ? 'auto' : 'smooth' }));
    trilho.addEventListener('scroll', () => requestAnimationFrame(estado), { passive: true });
    w.addEventListener('resize', () => { cabe(); estado(); }, { passive: true });
    cabe(); estado();
    let x0 = 0, s0 = 0, arrasta = false, moveu = false;
    trilho.addEventListener('pointerdown', ev => {
      if (ev.pointerType !== 'mouse' || fila.classList.contains('fila--cabe')) return;
      arrasta = true; moveu = false; x0 = ev.clientX; s0 = trilho.scrollLeft;
      trilho.style.scrollSnapType = 'none';
    });
    w.addEventListener('pointermove', ev => {
      if (!arrasta) return;
      const dx = ev.clientX - x0;
      if (Math.abs(dx) > 5) moveu = true;
      trilho.scrollLeft = s0 - dx;
    }, { passive: true });
    w.addEventListener('pointerup', () => {
      if (!arrasta) return;
      arrasta = false; trilho.style.scrollSnapType = '';
    });
    trilho.addEventListener('click', ev => { if (moveu) { ev.preventDefault(); ev.stopPropagation(); moveu = false; } }, true);
  });

  /* ---------- contato: o perfil escolhido muda a rota ---------- */
  const perfil = d.querySelector('#f-perfil');
  const rotas = [...d.querySelectorAll('.rota')];
  const roteia = () => {
    const v = perfil ? perfil.value : '';
    rotas.forEach(r => r.classList.toggle('ver', r.dataset.perfil === v));
  };
  if (perfil) { perfil.addEventListener('change', roteia); roteia(); }
  d.querySelectorAll('[data-perfil-set]').forEach(a => a.addEventListener('click', () => {
    if (perfil) { perfil.value = a.dataset.perfilSet; roteia(); }
  }));

  /* ---------- formulário: mensagem pronta para o WhatsApp, pela ponte /obrigado ---------- */
  d.querySelectorAll('form.form').forEach(form => form.addEventListener('submit', e => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const f = new FormData(form), v = k => (f.get(k) || '').toString().trim();
    const sel = form.querySelector('#f-perfil');
    const rotulo = sel ? sel.options[sel.selectedIndex].text : '';
    const linhas = ['Olá! Vim pelo site do Massuo Group.', '', `Perfil: ${rotulo}`, `Nome: ${v('nome')}`, `WhatsApp: ${v('whatsapp')}`];
    if (v('cidade')) linhas.push(`Cidade: ${v('cidade')}`);
    if (v('mensagem')) linhas.push(`Mensagem: ${v('mensagem')}`);
    try { sessionStorage.setItem('mg_msg', linhas.join('\n')); } catch (_) {}
    const a = (v('perfil') || 'contato').replace(/[^a-z-]/g, '');
    location.href = `/obrigado?c=${encodeURIComponent(form.dataset.c || 'form')}&a=${a}`;
  }));
})();

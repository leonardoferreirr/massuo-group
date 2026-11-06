// Massuo Group: a esfera do logo ao vivo, feita das camadas do próprio logo (tools/esfera_camadas.py).
// A casca de vidro e seus reflexos ficam parados, e o M anda por dentro acompanhando o mouse. Parada, é
// idêntica ao logo, então o pôster troca pelo canvas sem salto. Sem biblioteca: WebGL direto.
//
// API: mountEsfera(canvas, { mobile, reducedMotion }) -> { ready, setScroll, pause, resume, dispose, info }

const VERT = `attribute vec2 a;varying vec2 v;void main(){v=a;gl_Position=vec4(a,0.,1.);}`;

const FRAG = `precision highp float;
varying vec2 v;
uniform sampler2D uC,uM;
uniform vec2 uRot,uLuz;
const float R=.988;
void main(){
  vec2 p=v;
  vec4 c=texture2D(uC,p*.5+.5);
  vec2 q=p/R;
  float rr=dot(q,q);
  if(rr<1.){
    vec3 n=vec3(q,sqrt(1.-rr));
    float ca=cos(uRot.x),sa=sin(uRot.x),cb=cos(uRot.y),sb=sin(uRot.y);
    vec3 m=vec3(n.x*ca-n.z*sa,n.y,n.x*sa+n.z*ca);
    m=vec3(m.x,m.y*cb-m.z*sb,m.y*sb+m.z*cb);
    if(m.z>0.){
      vec4 t=texture2D(uM,m.xy*R*.5+.5);
      float borda=1.-smoothstep(.94,.995,length(m.xy));
      float a=t.a*borda*smoothstep(0.,.14,m.z);
      c.rgb=mix(c.rgb,t.rgb,a);
    }
    vec3 h=normalize(vec3(uLuz*.5+vec2(-.62,.74),1.)+vec3(0.,0.,1.));
    float d=max(dot(n,h),0.);
    c.rgb+=vec3(1.,.9,.86)*pow(d,220.)*.5;
    c.rgb+=vec3(.5,.04,.05)*pow(d,16.)*.22;
  }
  gl_FragColor=vec4(c.rgb*c.a,c.a);
}`;

const LIM = { yaw: 0.27, pitch: 0.19 };
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

function compilar(gl, tipo, fonte) {
  const s = gl.createShader(tipo);
  gl.shaderSource(s, fonte);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
  return s;
}

function carregar(src) {
  return new Promise((res, rej) => {
    const im = new Image();
    im.decoding = 'async';
    im.onload = () => res(im);
    im.onerror = () => rej(new Error('imagem: ' + src));
    im.src = src;
  });
}

function textura(gl, unidade, imagem) {
  const t = gl.createTexture();
  gl.activeTexture(gl.TEXTURE0 + unidade);
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
  gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, imagem);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return t;
}

export function mountEsfera(canvas, { mobile = false, reducedMotion = false } = {}) {
  const gl = canvas.getContext('webgl', { alpha: true, antialias: true, premultipliedAlpha: true, powerPreference: 'low-power' });
  if (!gl) throw new Error('sem WebGL');

  const prog = gl.createProgram();
  gl.attachShader(prog, compilar(gl, gl.VERTEX_SHADER, VERT));
  gl.attachShader(prog, compilar(gl, gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  gl.useProgram(prog);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const aPos = gl.getAttribLocation(prog, 'a');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);
  const uRot = gl.getUniformLocation(prog, 'uRot');
  const uLuz = gl.getUniformLocation(prog, 'uLuz');
  gl.uniform1i(gl.getUniformLocation(prog, 'uC'), 0);
  gl.uniform1i(gl.getUniformLocation(prog, 'uM'), 1);
  gl.clearColor(0, 0, 0, 0);

  const DPR = Math.min(window.devicePixelRatio || 1, mobile ? 1.5 : 2);
  const medir = () => {
    const w = Math.max(1, Math.round(canvas.clientWidth * DPR));
    const h = Math.max(1, Math.round(canvas.clientHeight * DPR));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
  };

  const alvo = { x: 0, y: 0 }, mouse = { x: 0, y: 0 }, atual = { x: 0, y: 0 };
  let rolagem = 0, raf = 0, parado = false, morto = false;
  const inicio = performance.now();

  const desenhar = (agora) => {
    const t = (agora - inicio) / 1000;
    // deriva lenta, para a esfera nunca ficar morta; o mouse manda quando está presente
    // no celular não há mouse para acompanhar: a deriva é maior e mais rápida, para ficar claro que é uma animação
    const ampX = mobile ? 0.25 : 0.09, ampY = mobile ? 0.17 : 0.06, vel = mobile ? 1.7 : 1;
    const fx = reducedMotion ? 0 : Math.sin(t * 0.42 * vel) * ampX;
    const fy = reducedMotion ? 0 : Math.sin(t * 0.31 * vel + 1.1) * ampY;
    alvo.x = clamp(mouse.x * LIM.yaw + fx + rolagem * LIM.yaw, -LIM.yaw, LIM.yaw);
    alvo.y = clamp(mouse.y * LIM.pitch + fy, -LIM.pitch, LIM.pitch);
    atual.x += (alvo.x - atual.x) * 0.055;
    atual.y += (alvo.y - atual.y) * 0.055;
    medir();
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.uniform2f(uRot, atual.x, atual.y);
    gl.uniform2f(uLuz, atual.x / LIM.yaw, atual.y / LIM.pitch);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  };
  const laco = (agora) => {
    if (parado || morto) return;
    desenhar(agora);
    raf = requestAnimationFrame(laco);
  };
  const resume = () => { if (morto || !parado || reducedMotion) return; parado = false; raf = requestAnimationFrame(laco); };
  const pause = () => { parado = true; cancelAnimationFrame(raf); };

  const onMove = (e) => {
    const r = canvas.getBoundingClientRect();
    mouse.x = clamp((e.clientX - (r.left + r.width / 2)) / (innerWidth / 2), -1, 1);
    mouse.y = clamp(-(e.clientY - (r.top + r.height / 2)) / (innerHeight / 2), -1, 1);
  };
  if (!mobile && !reducedMotion) window.addEventListener('pointermove', onMove, { passive: true });

  let io = null;
  if ('IntersectionObserver' in window) {
    io = new IntersectionObserver(([en]) => (en.isIntersecting ? resume() : pause()));
    io.observe(canvas);
  }

  const ready = Promise.all([carregar('/assets/img/esfera-casca-v1.webp'), carregar('/assets/img/esfera-m-v1.webp')]).then(([c, m]) => {
    textura(gl, 0, c);
    textura(gl, 1, m);
    parado = true;
    desenhar(performance.now());
    if (!reducedMotion) { parado = false; raf = requestAnimationFrame(laco); }
  });

  return {
    ready,
    setScroll(p) { rolagem = mobile ? clamp(p, 0, 1) * 0.4 : 0; },
    pause,
    resume,
    dispose() {
      morto = true;
      cancelAnimationFrame(raf);
      window.removeEventListener('pointermove', onMove);
      if (io) io.disconnect();
    },
    info() { return { w: canvas.width, h: canvas.height, atual: { ...atual } }; },
  };
}

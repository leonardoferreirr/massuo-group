#!/usr/bin/env python3
"""Monta o site institucional do Massuo Group a partir de _src/ e gera os arquivos da raiz.

    python3 build.py

- Junta head, cabeçalho e rodapé em cada página (index, noticias, obrigado).
- Minifica assets/css/site.css e injeta no <head>.
- Carimba site.js e esfera.js com o hash do conteúdo (o Vercel guarda /assets/ em cache por um ano).
- Gera robots.txt, sitemap.xml, llms.txt, o schema (JSON-LD) e ajusta o vercel.json (noindex enquanto INDEXAR = False).
- Confere que nenhum travessão entrou no HTML.

Os textos do cliente (05/11/2026) estão aqui em cima, palavra por palavra. O que falta está em [A PREENCHER].
Imagens: python3 tools/imagens.py (lê ~/dev/_massuo-imagens).
"""
import hashlib, json, re
from datetime import date
from html import escape as e
from pathlib import Path

RAIZ = Path(__file__).parent
SRC = RAIZ / "_src"
CSS = RAIZ / "assets/css/site.css"
JS = RAIZ / "assets/js/site.js"
ESFERA = RAIZ / "assets/js/esfera.js"
IMG = RAIZ / "assets/img"

DOMINIO = "https://massuogroup.vercel.app"   # sem domínio próprio por enquanto
INDEXAR = False                              # True só quando o site for aprovado e o domínio estiver ligado
VERCEL = "massuogroup.vercel.app"
WHATSAPP = "5524998593556"                   # só dígitos com DDI, até o Paulo passar outro
OG_BASE = DOMINIO if INDEXAR else f"https://{VERCEL}"
ROBOS_IA = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User",
            "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "CCBot", "meta-externalagent"]

# sites das empresas do grupo (vercel.app até terem domínio)
SITES = {"citysteel": "https://citysteel.vercel.app", "reformuli": "https://reformuli.vercel.app", "multihall": "https://multihall.vercel.app"}

# ---------------------------------------------------------------- textos do cliente (não reescrever)
HERO_TITULO = "Transformar oportunidades em negócios sólidos e relevantes."
O_QUE_E = "O Massuo Group é um grupo empresarial idealizado para desenvolver, integrar e expandir negócios em diversos setores."
PROPOSITO = ("O propósito do Massuo Group é transformar oportunidades em negócios sólidos e relevantes, promovendo desenvolvimento, "
             "gerando valor e construindo relações duradouras. Guiado por uma visão de longo prazo, o grupo busca contribuir para a "
             "evolução dos mercados em que atua, consolidando marcas, ampliando oportunidades e construindo um legado empresarial consistente.")
FUNDADORES = [
    {"slug": "paulo-massuo", "nome": "Paulo Massuo Jr.", "cargo": "CEO Fundador do Massuo Group",
     "bio": ["Paulo Massuo Jr. é CEO Fundador do Massuo Group, grupo empresarial orientado à criação, desenvolvimento e expansão de "
             "negócios. À frente da organização, conduz a visão estratégica e o fortalecimento institucional do grupo, com foco em "
             "inovação, excelência na gestão e crescimento sustentável."],
     "proposito": "", "alt": "Paulo Massuo Jr., CEO Fundador do Massuo Group, sentado no escritório, de terno escuro e camisa branca"},
    {"slug": "sandra-sathie", "nome": "Sandra Sathie", "cargo": "COO Fundadora do Massuo Group",
     "bio": ["Sandra Sathie é COO Fundadora do Massuo Group, formada em Economia, com atuação estratégica na gestão corporativa, "
             "planejamento financeiro e desenvolvimento empresarial. Sua visão de negócios, capacidade de gestão e foco em resultados "
             "contribuem para o crescimento sustentável do grupo, fortalecendo sua estrutura organizacional e impulsionando a expansão "
             "de suas empresas."],
     "proposito": "",
     "alt": "Sandra Sathie, COO Fundadora do Massuo Group, sentada no escritório, de blazer preto e blusa branca"},
]

# ---------------------------------------------------------------- empresas (a City Steel constrói, a Reformuli reforma, a Multihall fornece o material)
EMPRESAS_LEAD = "A City Steel constrói, a Reformuli reforma e a Multihall fornece o material."
EMPRESAS = [
    {"slug": "citysteel", "nome": "City Steel", "papel": "Construção em steel frame",
     "texto": "Construção em steel frame do projeto à entrega, com engenharia que acompanha a obra e equipe própria de execução. "
              "Também é uma franquia.",
     "c1": "#6b2a06", "c2": "#0a0a0b", "ac": "#FF6A13", "logo": ("citysteel", 577, 314)},
    {"slug": "reformuli", "nome": "Reformuli", "papel": "Reforma de apartamentos",
     "texto": "Reforma de apartamentos entregues pela construtora, em três planos: Essencial, Confort e Premium. "
              "Também é uma franquia.",
     "c1": "#4d3716", "c2": "#0b0a08", "ac": "#c9974f", "logo": ("reformuli", 5669, 1235)},
    {"slug": "multihall", "nome": "Multihall", "papel": "Materiais de construção a seco",
     "texto": "Revenda de materiais para construção a seco: steel frame, telhados, divisórias e forros em drywall, e fornecimento "
              "para empreendimentos. Também é uma franquia.",
     "c1": "#1f3366", "c2": "#0d1426", "ac": "#f58a1f", "logo": ("multihall", 6254, 1732)},
]

# ---------------------------------------------------------------- contato
PERFIS = [("franqueado", "Quero ser franqueado"), ("fornecedor", "Sou fornecedor ou parceiro"),
          ("trabalhar", "Quero trabalhar no grupo"), ("cliente", "Sou cliente")]
# quem é cliente ou quer franquia vai em 1 clique ao site da empresa certa
ROTAS = {
    "cliente": ("Cliente de qual empresa?", [(m["nome"], SITES[m["slug"]]) for m in EMPRESAS]),
    "franqueado": ("Franquia de qual empresa?", [(m["nome"], SITES[m["slug"]] + "/franquia") for m in EMPRESAS]),
}
MSGS = {
    "padrao": "Olá! Vim pelo site do Massuo Group e quero falar com o grupo.",
    "franqueado": "Olá! Vim pelo site do Massuo Group e quero ser franqueado.",
    "fornecedor": "Olá! Vim pelo site do Massuo Group. Sou fornecedor ou parceiro e quero falar com o grupo.",
    "trabalhar": "Olá! Vim pelo site do Massuo Group e quero trabalhar no grupo.",
    "cliente": "Olá! Vim pelo site do Massuo Group. Sou cliente de uma das empresas do grupo.",
}

# ---------------------------------------------------------------- notícias: lista vazia até o Paulo mandar (não inventar)
# cada item: {"data": "2026-11-05", "titulo": "...", "texto": "...", "link": "https://..."} (link opcional)
NOTICIAS = []

MENU = [("Home", "/"), ("Quem somos", "/#quem-somos"), ("Fundadores", "/#fundadores"), ("Empresas", "/#empresas"),
        ("Notícias", "/noticias"), ("Contato", "/#contato")]

ARROW = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2 8h11M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5"/></svg>'
ESQ = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M14 8H3M7 4L3 8l4 4" stroke="currentColor" stroke-width="1.5"/></svg>'
FORA = '<svg viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M3 9l6-6M4 3h5v5" stroke="currentColor" stroke-width="1.3"/></svg>'
ZAP = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.4.8 3.2.6a2.8 2.8 0 0 0 1.8-1.3 2.3 2.3 0 0 0 .2-1.3c-.1-.1-.3-.2-.6-.3z"/></svg>')


# ---------------------------------------------------------------- blocos
def palavras(txt):
    """Cada palavra num span, para acender uma a uma no scroll."""
    return " ".join(f"<span>{e(p)}</span>" for p in txt.split())


def nav(atual):
    out = []
    for rotulo, href in MENU:
        cur = ' aria-current="page"' if href == atual else ""
        out.append(f'<a href="{href}"{cur}>{e(rotulo)}</a>')
    return "\n      ".join(out)


def foot_nav():
    return "\n          ".join(f'<li><a href="{href}">{e(rotulo)}</a></li>' for rotulo, href in MENU)


def foot_empresas():
    return "\n          ".join(f'<li><a href="{SITES[m["slug"]]}" target="_blank" rel="noopener">{e(m["nome"])}</a></li>' for m in EMPRESAS)


def fundadores():
    out = []
    for i, f in enumerate(FUNDADORES):
        foto = (f'<img src="/assets/img/{f["slug"]}-900.webp" srcset="/assets/img/{f["slug"]}-400.webp 400w, /assets/img/{f["slug"]}-600.webp 600w, /assets/img/{f["slug"]}-900.webp 900w" '
                f'sizes="(max-width:860px) 92vw, 32vw" alt="{e(f["alt"])}" width="900" height="900" loading="lazy" decoding="async">')
        bio = "".join(f"<p>{e(p)}</p>" for p in f["bio"])
        prop = f'<p class="proposito">{e(f["proposito"])}</p>' if f["proposito"] else ""
        out.append(f'<article class="fundador rv" data-d="{i}" id="{f["slug"]}"><figure class="fundador__foto">{foto}</figure>'
                   f'<div class="fundador__txt"><h3>{e(f["nome"])}</h3><span class="fundador__cargo">{e(f["cargo"])}</span>{bio}{prop}</div></article>')
    return "\n      ".join(out)


def card(m):
    nome, w, h = m["logo"]
    return (f'<article class="card" style="--c1:{m["c1"]};--c2:{m["c2"]};--ac:{m["ac"]}">'
            f'<div class="card__logo"><img src="/assets/img/logos/{nome}.svg" alt="{e(m["nome"])}" width="{w}" height="{h}" loading="lazy"></div>'
            f'<div class="card__txt"><h3>{e(m["nome"])}</h3><span class="card__papel">{e(m["papel"])}</span>'
            f'<div class="card__mais"><div><p>{e(m["texto"])}</p><span class="card__ir">CONHECER {ARROW}</span></div></div></div>'
            f'<a href="{SITES[m["slug"]]}" target="_blank" rel="noopener" aria-label="Conhecer a {e(m["nome"])} (abre em outra guia)"></a></article>')


def fila(cards):
    return (f'<div class="fila rv" data-d="2" data-fila><div class="fila__topo"><span class="sr">Empresas do grupo</span>'
            f'<div class="fila__setas"><button type="button" data-ant aria-label="Anteriores">{ESQ}</button>'
            f'<button type="button" data-prox aria-label="Próximos">{ARROW}</button></div></div>'
            f'<div class="fila__trilho">{"".join(cards)}</div></div>')


def perfis():
    return "\n            ".join(['<option value="" selected disabled>Escolha uma opção</option>']
                                + [f'<option value="{v}">{e(r)}</option>' for v, r in PERFIS])


def rotas():
    out = []
    for perfil, (pergunta, links) in ROTAS.items():
        ls = "".join(f'<a href="{href}" target="_blank" rel="noopener">{e(n)} {FORA}</a>' for n, href in links)
        out.append(f'<div class="rota" data-perfil="{perfil}"><span>{e(pergunta)}</span>{ls}</div>')
    return "\n        ".join(out)


def noticias():
    if not NOTICIAS:
        return ('<div class="vazio rv" data-d="2"><h2>Ainda não há notícias publicadas.</h2>'
                '<p>Quando o grupo ou uma das empresas tiver novidade, ela entra aqui.</p>'
                f'<div class="ctas"><a class="btn btn--pri" href="/#contato">Fale com a gente {ARROW}</a>'
                f'<a class="btn btn--line" href="/#empresas">Conhecer as empresas</a></div></div>')
    out = []
    for n in sorted(NOTICIAS, key=lambda x: x["data"], reverse=True):
        d = date.fromisoformat(n["data"])
        titulo = f'<a href="{n["link"]}" target="_blank" rel="noopener">{e(n["titulo"])}</a>' if n.get("link") else e(n["titulo"])
        out.append(f'<article class="noticia rv"><time datetime="{n["data"]}">{d.strftime("%d/%m/%Y")}</time>'
                   f'<div><h2 style="font-size:var(--t-h3);font-weight:400">{titulo}</h2><p>{e(n["texto"])}</p></div></article>')
    return "\n      ".join(out) + f'\n      <div class="ctas rv" style="margin-top:2rem"><a class="btn btn--pri" href="/#contato">Fale com a gente {ARROW}</a></div>'


def fundo(nome, pos="50% 50%"):
    """Imagem gerada (mg-*) atrás da seção, se já existir. A seção funciona sem ela.
    mg-sede (recepção com o logo) fica atrás de Quem somos; mg-sala (mesa com planta, perfil de aço e amostras de pedra) atrás de Empresas."""
    if not (IMG / f"{nome}-1600.webp").exists():
        return ""
    return (f'<div class="sec__fundo" aria-hidden="true"><img src="/assets/img/{nome}-1600.webp" '
            f'srcset="/assets/img/{nome}-900.webp 900w, /assets/img/{nome}-1600.webp 1600w" sizes="100vw" alt="" '
            f'width="1600" height="900" loading="lazy" decoding="async" style="object-position:{pos}"></div>')


def fone():
    w = WHATSAPP
    return f"+{w[:2]} {w[2:4]} {w[4:-4]}-{w[-4:]}" if len(w) >= 12 else ""


# ---------------------------------------------------------------- busca e IA
def schema(nome, pg):
    S, url = DOMINIO, DOMINIO + pg["path"]
    org = {"@id": f"{S}/#organizacao"}
    pessoas = [{"@type": "Person", "@id": f"{S}/#{f['slug']}", "name": f["nome"], "jobTitle": f["cargo"].split(" do ")[0],
                "worksFor": org, "image": f"{S}/assets/img/{f['slug']}-900.webp", "description": f["bio"][0]} for f in FUNDADORES]
    empresas = [{"@type": "Organization", "name": m["nome"], "url": SITES[m["slug"]], "description": m["texto"], "parentOrganization": org}
                for m in EMPRESAS]
    grupo = {"@type": "Organization", **org, "name": "Massuo Group", "description": O_QUE_E, "url": f"{S}/",
             "logo": {"@type": "ImageObject", "url": f"{S}/assets/img/completo-600.webp"}, "image": f"{S}/assets/img/og-image.jpg",
             "founder": [{"@id": p["@id"]} for p in pessoas], "subOrganization": empresas, "slogan": HERO_TITULO}
    if WHATSAPP:
        grupo["contactPoint"] = {"@type": "ContactPoint", "telephone": fone(), "contactType": "customer service", "availableLanguage": "pt-BR"}
    pagina = {"@type": "WebPage", "@id": f"{url}#pagina", "url": url, "name": pg["title"], "description": pg["desc"],
              "isPartOf": {"@id": f"{S}/#site"}, "about": org, "inLanguage": "pt-BR",
              "primaryImageOfPage": {"@type": "ImageObject", "url": f"{S}/assets/img/og-image.jpg", "width": 1200, "height": 630}}
    grafo = [grupo, *pessoas, {"@type": "WebSite", "@id": f"{S}/#site", "url": f"{S}/", "name": "Massuo Group", "inLanguage": "pt-BR", "publisher": org}, pagina]
    if pg["path"] != "/":
        pagina["breadcrumb"] = {"@id": f"{url}#trilha"}
        grafo.append({"@type": "BreadcrumbList", "@id": f"{url}#trilha", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": f"{S}/"},
            {"@type": "ListItem", "position": 2, "name": pg["trilha"], "item": url}]})
    js = json.dumps({"@context": "https://schema.org", "@graph": grafo}, ensure_ascii=False, separators=(",", ":"))
    return '<script type="application/ld+json">' + js.replace("</", "<\\/") + "</script>"


def llms():
    S = DOMINIO
    lin = ["# Massuo Group", "", f"> {O_QUE_E} {EMPRESAS_LEAD}", "",
           "## Em poucas palavras", "",
           "- Empresa: Massuo Group, grupo empresarial.",
           f"- Frase do grupo: {HERO_TITULO}",
           "- Empresas do grupo: " + "; ".join(f"{m['nome']} ({m['papel'].lower()}, {SITES[m['slug']]})" for m in EMPRESAS) + ".",
           "- Fundadores: " + "; ".join(f"{f['nome']} | {f['cargo']}" for f in FUNDADORES) + ".",
           f"- Contato: WhatsApp {fone()} e formulário em {S}/#contato." if WHATSAPP else f"- Contato: formulário em {S}/#contato.",
           "", "## Propósito", "", PROPOSITO, "", "## Fundadores", ""]
    for f in FUNDADORES:
        lin += [f"### {f['nome']} | {f['cargo']}", ""] + f["bio"] + ([""] + [f["proposito"]] if f["proposito"] else []) + [""]
    lin += ["## Empresas", "", EMPRESAS_LEAD, ""] + [f"- **{m['nome']}** ({m['papel'].lower()}): {m['texto']} Site: {SITES[m['slug']]}" for m in EMPRESAS]
    lin += ["", "## Notícias", "", "Ainda não há notícias publicadas." if not NOTICIAS else "\n".join(f"- {n['data']}: {n['titulo']}" for n in NOTICIAS)]
    lin += ["", "## Contato", "", "Perfis atendidos pelo formulário: " + "; ".join(r for _, r in PERFIS) + ".",
            "Quem é cliente ou quer franquia é levado ao site da empresa certa."]
    if WHATSAPP:
        lin += [f"- WhatsApp: {fone()} (https://wa.me/{WHATSAPP})"]
    lin += [f"- Formulário: {S}/#contato", "", "## Páginas", "",
            f"- [Início]({S}/): quem somos, fundadores, empresas e contato.",
            f"- [Notícias]({S}/noticias): novidades do grupo e das empresas.", ""]
    return "\n".join(lin)


def robots_txt():
    if INDEXAR:
        corpo = "# Buscadores e assistentes de IA podem ler o site inteiro.\nUser-agent: *\nAllow: /\n\n"
    else:
        corpo = ("# Pré-lançamento (INDEXAR = False): o Google lê as páginas para ver o noindex delas,\n"
                 "# e os robôs de IA ficam fora até o site entrar no ar.\n"
                 "User-agent: *\nAllow: /\n\n" + "".join(f"User-agent: {b}\nDisallow: /\n\n" for b in ROBOS_IA))
    return corpo + f"Sitemap: {DOMINIO}/sitemap.xml\n"


def vercel_json():
    """Com INDEXAR = False: cabeçalho X-Robots-Tag noindex em tudo. Com INDEXAR = True e domínio próprio:
    redirect permanente do .vercel.app para o DOMINIO."""
    arq = RAIZ / "vercel.json"
    atual = arq.read_text()
    cfg = json.loads(atual)
    redir = [r for r in cfg.get("redirects", []) if not any(h.get("value") == VERCEL for h in r.get("has", []))]
    if INDEXAR and VERCEL not in DOMINIO:
        host = [{"type": "host", "value": VERCEL}]
        redir += [{"source": "/", "has": host, "destination": f"{DOMINIO}/", "permanent": True},
                  {"source": "/:path*", "has": host, "destination": f"{DOMINIO}/:path*", "permanent": True}]
    if redir:
        cfg["redirects"] = redir
    else:
        cfg.pop("redirects", None)
    cab = [h for h in cfg.get("headers", []) if not any(x["key"] == "X-Robots-Tag" for x in h["headers"])]
    if not INDEXAR:
        cab.append({"source": "/(.*)", "headers": [{"key": "X-Robots-Tag", "value": "noindex"}]})
    cfg["headers"] = cab
    if cfg != json.loads(atual):
        arq.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")


# ---------------------------------------------------------------- montagem
def minificar(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s*\n\s*", "\n", css)
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)
    css = re.sub(r";}", "}", css)
    css = re.sub(r"\n+", "", css)
    return css.replace("../fonts/", "/assets/fonts/").strip()


def hash_de(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:10] if p.exists() else "0"


def carimbar_esfera():
    js = JS.read_text()
    novo = re.sub(r"/assets/js/esfera\.js(\?v=[a-z0-9]+)?", f"/assets/js/esfera.js?v={hash_de(ESFERA)}", js)
    if novo != js:
        JS.write_text(novo)


PAGINAS = {
    "index": dict(arquivo="index.html", path="/", atual="/",
                  title="Massuo Group | Grupo empresarial: City Steel, Reformuli e Multihall",
                  desc=f"{O_QUE_E} Fundado por Paulo Massuo Jr. e Sandra Sathie, reúne a City Steel, a Reformuli e a Multihall.",
                  preload='<link rel="preload" as="image" imagesrcset="/assets/img/esfera-poster-400.webp 400w, /assets/img/esfera-poster.webp 666w" '
                          'imagesizes="(max-width:860px) 74vw, 44vw" fetchpriority="high">',
                  cta="#contato"),
    "noticias": dict(arquivo="noticias.html", path="/noticias", atual="/noticias", trilha="Notícias",
                     title="Notícias | Massuo Group", desc="Novidades do Massuo Group e das empresas do grupo: City Steel, Reformuli e Multihall.",
                     preload="", cta="/#contato"),
    "obrigado": dict(arquivo="obrigado.html", path="/obrigado", atual="", title="Massuo Group | Abrindo o WhatsApp",
                     desc="Estamos abrindo a conversa com o Massuo Group.", preload="", cta="", robots="noindex,nofollow"),
}


def main():
    carimbar_esfera()
    css = minificar(CSS.read_text())
    head_t, top_t, foot_t = (SRC / "head.html").read_text(), (SRC / "top.html").read_text(), (SRC / "foot.html").read_text()
    geradas = sorted(IMG.glob("mg-*-1600.webp"))
    blocos = {
        "ARROW": ARROW, "ZAP": ZAP, "ZAP_B": ZAP.replace("<svg ", '<svg class="zapi" '),
        "HERO_TITULO": e(HERO_TITULO), "O_QUE_E": e(O_QUE_E), "PROPOSITO": palavras(PROPOSITO),
        "FUNDADORES": fundadores(), "EMPRESAS_LEAD": e(EMPRESAS_LEAD), "EMPRESAS_FILA": fila([card(m) for m in EMPRESAS]),
        "PERFIS": perfis(), "ROTAS": rotas(), "NOTICIAS": noticias(), "QUEM_FUNDO": fundo("mg-sede", "50% 42%"), "EMPRESAS_FUNDO": fundo("mg-sala", "50% 60%"),
        "WHATSAPP": WHATSAPP, "MSGS": json.dumps(MSGS, ensure_ascii=False).replace("</", "<\\/"),
        "FOOT_NAV": foot_nav(), "FOOT_EMPRESAS": foot_empresas(), "ANO": str(date.today().year),
        "ILUSTRATIVAS": "Imagens ilustrativas." if geradas else "",
    }
    jsv = hash_de(JS)
    mudou = set()
    for nome, pg in PAGINAS.items():
        robots = pg.get("robots") or ("index,follow,max-image-preview:large" if INDEXAR else "noindex,nofollow")
        head = (head_t.replace("{{CSS}}", css).replace("{{TITLE}}", e(pg["title"])).replace("{{DESC}}", e(pg["desc"]))
                .replace("{{URL}}", DOMINIO + pg["path"]).replace("{{ROBOTS}}", robots).replace("{{OG_BASE}}", OG_BASE)
                .replace("{{PRELOAD}}", pg["preload"]).replace("{{SCHEMA}}", schema(nome, pg) if nome != "obrigado" else ""))
        top = top_t.replace("{{NAV}}", nav(pg["atual"])).replace("{{TOP_CTA_HREF}}", pg["cta"])
        foot = foot_t.replace("{{JSV}}", jsv)
        html = (SRC / f"{nome}.html").read_text()
        html = html.replace("{{HEAD}}", head).replace("{{TOP}}", top).replace("{{FOOT}}", foot)
        for k, v in blocos.items():
            html = html.replace("{{" + k + "}}", v)
        sobra = re.findall(r"\{\{[A-Z_0-9]+\}\}", html)
        if sobra:
            print(f"  ! {nome}: marcadores sem valor {sorted(set(sobra))}")
        if "—" in html or "–" in html:
            print(f"  ! {nome}: travessão no HTML")
        destino = RAIZ / pg["arquivo"]
        if not destino.exists() or destino.read_text() != html:
            mudou.add(pg["path"])
            destino.write_text(html)
        print(f"  {pg['arquivo']}: {len(html.encode())/1024:.1f} KB")

    (RAIZ / "robots.txt").write_text(robots_txt())
    mapa = RAIZ / "sitemap.xml"
    antes = dict(re.findall(r"<loc>https?://[^/<]+(/[^<]*)</loc><lastmod>([\d-]+)</lastmod>", mapa.read_text())) if mapa.exists() else {}
    hoje = date.today().isoformat()
    urls = "".join(f"  <url><loc>{DOMINIO}{p}</loc><lastmod>{hoje if p in mudou or p not in antes else antes[p]}</lastmod></url>\n"
                   for p in ["/", "/noticias"])
    mapa.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    (RAIZ / "llms.txt").write_text(llms())
    vercel_json()
    faltam = [p for p in ("esfera-poster.webp", "esfera-96.webp", "nome-240.webp", "paulo-massuo-900.webp", "sandra-sathie-900.webp", "logos/citysteel.svg")
              if not (IMG / p).exists()]
    if faltam:
        print(f"  ! imagens faltando (rode python3 tools/imagens.py): {faltam}")
    print(f"  site.js v={jsv}  esfera.js v={hash_de(ESFERA)}  indexar={INDEXAR}  geradas={len(geradas)}  noticias={len(NOTICIAS)}")


if __name__ == "__main__":
    main()

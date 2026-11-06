#!/usr/bin/env python3
"""Prepara as imagens do site a partir do material do cliente em ~/dev/_massuo-imagens.

    python3 tools/imagens.py

- Logos do grupo (PNG com fundo transparente, feitos para fundo escuro) viram WebP com alpha.
- A esfera vira o pôster do 3D (até o three.js carregar) e o favicon.
- Fotos reais dos fundadores: inteiras, sem recorte e sem trocar o fundo, em 900 e 600 px.
- Logos das empresas: SVG copiado para assets/img/logos.
- Imagens geradas (prefixo mg-) entram se existirem; a home não depende delas.
"""
import shutil
from pathlib import Path
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
MAT = Path.home() / "dev/_massuo-imagens"
IMG = RAIZ / "assets/img"
LOGOS = IMG / "logos"
IMG.mkdir(parents=True, exist_ok=True)
LOGOS.mkdir(parents=True, exist_ok=True)


def webp_alpha(src, dest, largura=None, q=88):
    with Image.open(src) as im:
        im = im.convert("RGBA")
        if largura and im.width > largura:
            im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
        im.save(dest, "WEBP", quality=q, method=6)
        print(f"  {dest.relative_to(RAIZ)} {im.size} {dest.stat().st_size // 1024} KB")


def webp_foto(src, dest, largura, q=82):
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width > largura:
            im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
        im.save(dest, "WEBP", quality=q, method=6)
        print(f"  {dest.relative_to(RAIZ)} {im.size} {dest.stat().st_size // 1024} KB")


def favicons():
    """A esfera, transparente, no favicon; só o apple-touch-icon leva fundo preto."""
    with Image.open(MAT / "logos/massuo-esfera.png") as im:
        im = im.convert("RGBA")
        im.resize((32, 32), Image.LANCZOS).save(IMG / "favicon-32.png")
        im.resize((192, 192), Image.LANCZOS).save(IMG / "favicon-192.png")
        fundo = Image.new("RGBA", (180, 180), (0, 0, 0, 255))
        esf = im.resize((150, 150), Image.LANCZOS)
        fundo.alpha_composite(esf, (15, 15))
        fundo.convert("RGB").save(IMG / "apple-touch-icon.png")
    # favicon vetorial: círculo vermelho com a onda preta (o viewBox da onda é o quadrado da esfera)
    onda = (MAT / "logos/massuo-onda.svg").read_text()
    path = onda[onda.index("<path"):onda.rindex("</svg>")]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="366 75.5 659 659">'
           '<defs><radialGradient id="g" cx="38%" cy="30%" r="75%"><stop offset="0" stop-color="#ff3b3b"/>'
           '<stop offset=".55" stop-color="#d40f1e"/><stop offset="1" stop-color="#5a0309"/></radialGradient></defs>'
           '<circle cx="695.5" cy="405" r="329.5" fill="url(#g)"/>' + path + "</svg>")
    (IMG / "favicon.svg").write_text(svg)
    print("  favicon.svg, favicon-32.png, favicon-192.png, apple-touch-icon.png")


def og_image():
    """1200x630 preto com o logo completo centralizado."""
    fundo = Image.new("RGB", (1200, 630), (0, 0, 0))
    with Image.open(MAT / "logos/massuo-completo.png") as im:
        im = im.convert("RGBA")
        h = 520
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        fundo.paste(im, ((1200 - im.width) // 2, (630 - h) // 2), im)
    fundo.save(IMG / "og-image.jpg", "JPEG", quality=86, optimize=True)
    print("  og-image.jpg")


def main():
    print("logos do grupo")
    webp_alpha(MAT / "logos/massuo-esfera.png", IMG / "esfera-poster.webp", q=90)
    webp_alpha(MAT / "logos/massuo-esfera.png", IMG / "esfera-poster-400.webp", 400)
    webp_alpha(MAT / "logos/massuo-esfera.png", IMG / "esfera-96.webp", 96)
    webp_alpha(MAT / "logos/massuo-nome.png", IMG / "nome-240.webp", 240, q=84)
    webp_alpha(MAT / "logos/massuo-completo.png", IMG / "completo-600.webp", 600)
    shutil.copy(MAT / "logos/massuo-onda.svg", IMG / "massuo-onda.svg")
    favicons()
    og_image()
    print("fundadores (foto inteira, sem recorte)")
    for nome in ("paulo-massuo", "sandra-sathie"):
        for w in (900, 600, 400):
            webp_foto(MAT / f"cliente/{nome}.jpg", IMG / f"{nome}-{w}.webp", w)
    print("logos das empresas")
    shutil.copy(Path.home() / "dev/citysteel-landing/assets/img/logo-full.svg", LOGOS / "citysteel.svg")
    shutil.copy(MAT / "logos/reformuli-dourado.svg", LOGOS / "reformuli.svg")
    shutil.copy(MAT / "logos/multihall-horizontal.svg", LOGOS / "multihall.svg")
    print("imagens geradas (opcionais)")
    for p in sorted((MAT / "geradas").glob("mg-*.png")):
        for w in (1600, 900):
            webp_foto(p, IMG / f"{p.stem}-{w}.webp", w, q=80)
    if not list((MAT / "geradas").glob("mg-*.png")):
        print("  nenhuma ainda (mg-*.png); o site segue sem elas")


if __name__ == "__main__":
    main()

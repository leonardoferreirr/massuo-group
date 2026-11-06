#!/usr/bin/env python3
"""Separa a esfera do logo em duas camadas para o 3D ao vivo (assets/js/esfera.js).

- esfera-casca.webp: a casca de vidro sem o M (o M é apagado por preenchimento e suavizado).
- esfera-m.webp: o M com o chanfro vermelho, em alfa.

Juntas e paradas, reproduzem o logo. Com a esfera girando, a casca e seus reflexos ficam parados
e o M anda por dentro, como num objeto de vidro.

    python3 tools/esfera_camadas.py
"""
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
FONTE = Path.home() / "dev/_massuo-imagens/logos/massuo-esfera.png"
ONDA = Path.home() / "dev/_massuo-imagens/logos/massuo-onda.svg"
LADO = 1024

im = Image.open(FONTE).convert("RGBA")
print("fonte", im.size)
# recorta no disco e amplia com Lanczos
im = im.resize((LADO, LADO), Image.LANCZOS)
a = np.array(im).astype(np.float32)
rgb, alfa = a[..., :3], a[..., 3]

# máscara do M, a partir da onda desenhada à mão, alargada para levar o chanfro junto
import re
svg = ONDA.read_text()
vb = [float(x) for x in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
pts = [tuple(map(float, p.split())) for p in re.findall(r"[ML]([-\d.]+ [-\d.]+)", svg)]
esc = LADO * 1.0 / vb[2] * (im.width / LADO)
# a fonte tem 4 px de margem em volta do disco (d0 = r + 4), então o disco ocupa 659/667 do lado
marg = (LADO - LADO * (2 * 329.5) / (2 * (int(329.5) + 4))) / 2
k = (LADO - 2 * marg) / vb[2]
poly = [((x - vb[0]) * k + marg, (y - vb[1]) * k + marg) for x, y in pts]
m = Image.new("L", (LADO, LADO), 0)
ImageDraw.Draw(m).polygon(poly, fill=255)
m = np.array(m)

# a onda real do logo: neutro (R~G) ou preto, perto do desenho; une os dois para não deixar resto
neutro = ((np.abs(rgb[..., 0] - rgb[..., 1]) < 30) & (alfa > 200)).astype(np.uint8) * 255
perto = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (61, 61)))
lum = rgb.max(axis=2)
colado = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
real = cv2.bitwise_and(neutro, perto)
real[(lum >= 150) & (colado == 0)] = 0   # reflexo da casca perto do M fica na casca
base = cv2.bitwise_or(m, real)
base = cv2.morphologyEx(base, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
# leva junto o fio claro do chanfro
largo = cv2.dilate(base, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35)))

# casca: apaga o M por preenchimento e suaviza só a região apagada
rgb8 = np.clip(rgb, 0, 255).astype(np.uint8)
casca = cv2.inpaint(cv2.cvtColor(rgb8, cv2.COLOR_RGB2BGR), largo, 25, cv2.INPAINT_TELEA)
casca = cv2.cvtColor(casca, cv2.COLOR_BGR2RGB).astype(np.float32)
borrada = cv2.GaussianBlur(casca, (0, 0), 22)
peso = cv2.GaussianBlur(largo.astype(np.float32) / 255, (0, 0), 12)[..., None]
peso = np.clip(peso * 1.6, 0, 1)
casca = casca * (1 - peso) + borrada * peso
Image.fromarray(np.dstack([np.clip(casca, 0, 255), alfa]).astype(np.uint8), "RGBA").save(
    RAIZ / "assets/img/esfera-casca-v1.webp", "WEBP", quality=88, method=6)

# M: os pixels do logo, com alfa suave na borda larga
am = cv2.GaussianBlur(largo.astype(np.float32), (0, 0), 3.5)
am = np.clip((am - 90) / 120, 0, 1) * 255
Image.fromarray(np.dstack([rgb, am]).astype(np.uint8), "RGBA").save(
    RAIZ / "assets/img/esfera-m-v1.webp", "WEBP", quality=90, method=6, exact=True)
for n in ("esfera-casca-v1", "esfera-m-v1"):
    print(n, (RAIZ / f"assets/img/{n}.webp").stat().st_size // 1024, "KB")

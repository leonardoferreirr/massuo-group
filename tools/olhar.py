#!/usr/bin/env python3
"""Captura rápida de um trecho da página (hero com a esfera viva) para conferir o 3D.

    python3 tools/olhar.py <saida.png> [largura] [altura] [scrollY]
"""
import os, sys, asyncio
from playwright.async_api import async_playwright

CHROME = os.path.expanduser('~/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell')


async def main():
    out = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 1440
    h = int(sys.argv[3]) if len(sys.argv) > 3 else 900
    y = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=w < 800, has_touch=w < 800)
        pg = await ctx.new_page()
        erros = []
        pg.on('console', lambda m: m.type in ('error', 'warning') and erros.append(m.text))
        pg.on('pageerror', lambda e: erros.append(str(e)))
        await pg.goto('http://127.0.0.1:4250/', wait_until='load')
        await pg.mouse.move(w * 0.62, h * 0.45)
        await pg.evaluate('window.scrollTo(0,1)')
        for _ in range(30):
            await pg.wait_for_timeout(500)
            if await pg.evaluate("!!document.querySelector('.esfera.live')"):
                break
        await pg.mouse.move(w * 0.7, h * 0.4)
        await pg.evaluate(f'window.scrollTo(0,{y})')
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=out)
        print('live', await pg.evaluate("!!document.querySelector('.esfera.live')"), 'erros', erros[:6])
        await b.close()

asyncio.run(main())

#!/usr/bin/env python3
"""Confere os fluxos em Chromium próprio: menu do celular, cards das empresas, seletor de perfil,
formulário -> /obrigado -> wa.me, e a página /noticias.

    python3 tools/fluxos.py <pasta de capturas>
"""
import os, sys, asyncio
from pathlib import Path
from playwright.async_api import async_playwright

CHROME = os.path.expanduser('~/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell')
URL = 'http://127.0.0.1:4250'


async def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        erros = []
        # --- computador: cards abrem em outra guia, seletor roteia, formulário vai à ponte
        ctx = await b.new_context(viewport={'width': 1440, 'height': 900})
        pg = await ctx.new_page()
        pg.on('console', lambda m: m.type == 'error' and erros.append('1440 ' + m.text))
        pg.on('pageerror', lambda e: erros.append('1440 ' + str(e)))
        await pg.goto(URL + '/', wait_until='load')
        await pg.evaluate("document.querySelector('#empresas').scrollIntoView()")
        await pg.wait_for_timeout(1200)
        await pg.hover('.card:nth-child(2)')
        await pg.wait_for_timeout(700)
        await pg.screenshot(path=str(out / 'fluxo-card-hover.jpg'), type='jpeg', quality=72)
        async with ctx.expect_page() as nova:
            await pg.click('.card:nth-child(2) > a')
        np_ = await nova.value
        print('card abre em outra guia:', np_.url)
        await np_.close()
        await pg.evaluate("document.querySelector('#contato').scrollIntoView()")
        await pg.select_option('#f-perfil', 'cliente')
        await pg.wait_for_timeout(400)
        print('rota cliente visível:', await pg.evaluate("getComputedStyle(document.querySelector('.rota[data-perfil=cliente]')).display"))
        links = await pg.evaluate("[...document.querySelectorAll('.rota[data-perfil=cliente] a')].map(a => a.href + ' ' + a.target)")
        print('links cliente:', links)
        await pg.screenshot(path=str(out / 'fluxo-rota-cliente.jpg'), type='jpeg', quality=72)
        await pg.select_option('#f-perfil', 'franqueado')
        await pg.wait_for_timeout(300)
        print('rota franqueado:', await pg.evaluate("[...document.querySelectorAll('.rota[data-perfil=franqueado] a')].map(a => a.href)"))
        await pg.fill('#f-nome', 'Teste Massuo')
        await pg.fill('#f-zap', '(11) 90000-0000')
        await pg.fill('#f-msg', 'Mensagem de teste')
        await pg.click('.form button[type=submit]')
        await pg.wait_for_url('**/obrigado**', timeout=5000)
        print('ponte:', pg.url)
        await pg.wait_for_timeout(300)
        print('destino wa.me:', await pg.evaluate("document.getElementById('go').href"))
        print('dataLayer:', await pg.evaluate("JSON.stringify((window.dataLayer||[]).map(e => ({event:e.event, contexto:e.contexto, perfil:e.perfil})))"))
        await pg.screenshot(path=str(out / 'fluxo-obrigado.jpg'), type='jpeg', quality=72)
        # a ponte redireciona para wa.me; não seguimos (fora do site)
        await pg.goto(URL + '/noticias', wait_until='load')
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=str(out / 'noticias-1440.jpg'), type='jpeg', quality=72, full_page=True)
        print('noticias h1:', await pg.evaluate("document.querySelector('h1').textContent"), '| vazio:', await pg.evaluate("!!document.querySelector('.vazio')"))
        print('noticias aria-current:', await pg.evaluate("document.querySelector('.nav a[aria-current]').textContent"))
        await ctx.close()
        # --- celular: menu hambúrguer e fileira deslizando
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        pg = await ctx.new_page()
        pg.on('console', lambda m: m.type == 'error' and erros.append('390 ' + m.text))
        pg.on('pageerror', lambda e: erros.append('390 ' + str(e)))
        await pg.goto(URL + '/', wait_until='load')
        await pg.wait_for_timeout(800)
        await pg.click('.burger')
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=str(out / 'fluxo-menu-390.jpg'), type='jpeg', quality=72)
        print('menu aberto:', await pg.evaluate("document.documentElement.classList.contains('menu-open')"),
              '| itens visíveis:', await pg.evaluate("[...document.querySelectorAll('.nav a')].filter(a => a.getBoundingClientRect().height > 0).length"))
        await pg.click('.nav a[href=\"/#empresas\"]')
        await pg.wait_for_timeout(1200)
        print('menu fechou:', not await pg.evaluate("document.documentElement.classList.contains('menu-open')"))
        print('trilho rola:', await pg.evaluate("(t => t.scrollWidth > t.clientWidth)(document.querySelector('.fila__trilho'))"))
        await pg.evaluate("document.querySelector('.fila__trilho').scrollBy({left: 300})")
        await pg.wait_for_timeout(600)
        await pg.screenshot(path=str(out / 'fluxo-fila-390.jpg'), type='jpeg', quality=72)
        await pg.goto(URL + '/noticias', wait_until='load')
        await pg.wait_for_timeout(1000)
        await pg.screenshot(path=str(out / 'noticias-390.jpg'), type='jpeg', quality=72, full_page=True)
        print('noticias 390 lateral:', await pg.evaluate('document.documentElement.scrollWidth > innerWidth'))
        await ctx.close()
        await b.close()
        print('erros de console:', erros)

asyncio.run(main())

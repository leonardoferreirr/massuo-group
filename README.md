# Massuo Group, site institucional

Site estático do Massuo Group (grupo das empresas City Steel, Reformuli e Multihall): home com a esfera do logo em 3D ao vivo, Quem somos (o propósito aceso palavra a palavra no scroll), Fundadores, Empresas (fileira estilo catálogo), Contato com seletor de perfil; página `/noticias` (lista em constante, vazia até o cliente mandar) e `/obrigado` (ponte para o WhatsApp, que registra a conversão no `dataLayer`).

## Como editar

- Textos do cliente, empresas, perfis do contato e notícias: constantes no topo do `build.py` (`NOTICIAS = []` recebe os itens quando houver).
- Páginas: `_src/*.html` (head, cabeçalho e rodapé são compartilhados).
- Estilo: `assets/css/site.css` (vai minificado para dentro do `<head>`).
- Comportamento: `assets/js/site.js`. A esfera em 3D é `assets/js/esfera.js` (three.js via CDN, carregado na primeira interação; até lá aparece o pôster `esfera-poster.webp` na mesma caixa). A textura da onda vem de `assets/img/massuo-onda.svg`.
- Imagens: `python3 tools/imagens.py` lê `~/dev/_massuo-imagens` (logos, fotos dos fundadores, logos das empresas e as geradas `mg-*`).
- Depois de qualquer mudança: `python3 build.py`.
- Prévia local: `python3 tools/serve.py 4250`. Conferência: `python3 tools/shots.py <pasta>` (capturas em 1440 e 390), `python3 tools/fluxos.py <pasta>` (menu, cards, perfil, formulário, /noticias).

## Busca e IA

- `DOMINIO` no `build.py` (hoje `https://massuogroup.vercel.app`) alimenta canonical, og:url, schema, `sitemap.xml`, `robots.txt` e `llms.txt`.
- Schema: Organization (o grupo, com os fundadores como Person e as três empresas como subOrganization), WebSite, WebPage e BreadcrumbList em `/noticias`.
- Enquanto `INDEXAR = False`: `noindex` na meta e no `X-Robots-Tag` do `vercel.json`, robôs de IA barrados no `robots.txt`.

## Antes de ir ao ar

- `WHATSAPP` em `build.py` (hoje o número do Paulo usado nos três sites).
- Endereço do grupo: não entra até o Paulo confirmar (`[A PREENCHER]` no `llms.txt`).
- Domínio próprio: trocar `DOMINIO`, virar `INDEXAR = True`, rodar o build e fazer o deploy.

#!/usr/bin/env python3
"""Gera as páginas de "dia de publicar" em docs/ (GitHub Pages).

Lê artigos/<AAAA-MM-DD-slug>/artigo.md (+ capa.png) e perfil/quick-wins.md e cria:
  docs/artigos/<slug>.html -> artigo formatado (copia com formatação), capa, aviso curto
  docs/perfil.html         -> kit do perfil
  docs/index.html          -> lista de artigos

Uso: python3 scripts/gerar_paginas.py
"""
import html
import re
import shutil
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
BASE_URL = "https://raphammbb.github.io/linkedin-autoridade"

CSS = """
:root{--bg:#111318;--card:#1b1e26;--tx:#F5F5F2;--mut:#9aa0ac;--ac:#3FA9F5}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font-family:Inter,system-ui,sans-serif;line-height:1.55}
main{max-width:640px;margin:0 auto;padding:20px 16px 80px}
h1{font-size:22px;line-height:1.25;margin:8px 0 4px}
.meta{color:var(--mut);font-size:14px;margin-bottom:18px}
.box{background:var(--card);border-radius:14px;padding:18px;white-space:pre-wrap;font-size:16px}
.btn{display:block;width:100%;text-align:center;padding:16px;margin-top:12px;border-radius:12px;
 font-size:17px;font-weight:600;text-decoration:none;border:0;cursor:pointer}
.p{background:var(--ac);color:#06121c}.s{background:var(--card);color:var(--tx);border:1px solid #2c303b}
img{width:100%;border-radius:12px;margin-top:14px}
h2{font-size:15px;color:var(--mut);margin:26px 0 8px;text-transform:uppercase;letter-spacing:.05em}
a.row{display:block;background:var(--card);border-radius:12px;padding:14px;margin-bottom:10px;color:var(--tx);text-decoration:none}
a.row small{display:block;color:var(--mut);margin-top:2px}
.hoje{outline:2px solid var(--ac)}
"""


def secao(texto, titulo):
    m = re.search(rf"^## {re.escape(titulo)}[^\n]*\n(.*?)(?=^## |\Z)", texto, re.S | re.M)
    return m.group(1).strip() if m else ""


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_para_html(md):
    """Subconjunto de markdown: ### subtítulo (## é reservado às seções do arquivo), listas (- e 1.), parágrafos, **negrito**, *itálico*."""
    out = []
    for bloco in re.split(r"\n\s*\n", md.strip()):
        linhas = [l for l in bloco.splitlines() if l.strip()]
        if not linhas:
            continue
        if linhas[0].startswith("### "):
            out.append(f"<h2>{inline(linhas[0][4:])}</h2>")
            linhas = linhas[1:]
            if not linhas:
                continue
        if all(re.match(r"^- ", l) for l in linhas):
            out.append("<ul>" + "".join(f"<li>{inline(l[2:])}</li>" for l in linhas) + "</ul>")
        elif all(re.match(r"^\d+\. ", l) for l in linhas):
            itens = [re.sub(r"^\d+\. ", "", l) for l in linhas]
            out.append("<ol>" + "".join(f"<li>{inline(item)}</li>" for item in itens) + "</ol>")
        else:
            out.append("<p>" + "<br>".join(inline(l) for l in linhas) + "</p>")
    return "\n".join(out)


def ler_artigo(md: Path):
    t = md.read_text(encoding="utf-8")
    cab = re.search(r"^# Artigo — (.+)$", t, re.M)
    cab = cab.group(1) if cab else md.parent.name
    dm = re.search(r"(\d{2})/(\d{2})", cab)
    data = date(int(md.parent.name[:4]), int(dm.group(2)), int(dm.group(1))) if dm else None
    campo = lambda n: (re.search(rf"^\*\*{n}:\*\*\s*(.+)$", t, re.M) or [None, ""])[1].strip()
    capa = md.parent / "capa.png"
    return {
        "md": md, "slug": md.parent.name, "cab": cab, "data": data,
        "titulo": campo("Título"), "subtitulo": campo("Subtítulo"),
        "texto": secao(t, "Texto do artigo"), "aviso": secao(t, "Aviso curto no feed"),
        "faltou": secao(t, "Faltou"), "capa": capa if capa.exists() else None,
    }


def botao_copiar(alvo, rotulo, rico=False):
    return f'<button class="btn p" data-alvo="{alvo}" data-rico="{1 if rico else 0}">{rotulo}</button>'


SCRIPT_COPIAR = """<script>
document.querySelectorAll('button[data-alvo]').forEach(function(b){b.onclick=async function(){
 var el=document.getElementById(b.dataset.alvo),rico=b.dataset.rico==='1',ok=false;
 var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);
 try{ok=document.execCommand('copy')}catch(x){}
 if(!ok&&!rico){try{await navigator.clipboard.writeText(el.innerText);ok=true}catch(x){}}
 s.removeAllRanges();var o=b.textContent;b.textContent=ok?'Copiado ✓':'Não copiou, selecione e copie';
 setTimeout(function(){b.textContent=o},2200)}});
</script>"""


def pagina_artigo(a):
    e = html.escape
    capa = ""
    if a["capa"]:
        capa = (f'<img src="{e(a["slug"])}-capa.png" alt="capa">'
                f'<a class="btn s" href="{e(a["slug"])}-capa.png" download>Baixar capa</a>')
    faltou = ""
    if a["faltou"] and not a["faltou"].lower().startswith("nada"):
        faltou = f'<h2>Faltou</h2><div class="box">{e(a["faltou"])}</div>'
    aviso = "".join(f"<p>{e(p)}</p>" for p in a["aviso"].split("\n\n"))
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(a['titulo'])}</title><style>{CSS}
.art h2{{color:var(--tx);font-size:20px;text-transform:none;letter-spacing:0;margin:22px 0 8px}}
.art p,.art li{{font-size:17px}}.art ul,.art ol{{padding-left:22px}}</style></head><body><main>
<a href="../index.html" style="color:var(--mut)">← artigos</a>
<h1>{e(a['titulo'])}</h1><div class="meta">{e(a['cab'])}</div>
<h2>1. Abra o editor de artigos</h2>
<a class="btn s" href="https://www.linkedin.com/article/new/" target="_blank" rel="noopener">Abrir editor de artigos do LinkedIn</a>
<h2>2. Título e subtítulo</h2>
<div class="box" id="tit">{e(a['titulo'])}</div>{botao_copiar('tit','Copiar título')}
<h2>3. Capa</h2>{capa}
<h2>4. Texto do artigo (cola com a formatação)</h2>
<div class="box art" id="art" style="white-space:normal">{md_para_html(a['texto'])}</div>
{botao_copiar('art','Copiar artigo com formatação',True)}
<h2>5. Depois de publicar: aviso curto no feed</h2>
<div class="box" id="avi">{aviso}</div>{botao_copiar('avi','Copiar aviso')}
<div class="meta" style="margin-top:10px">Publique o aviso e cole o link do artigo no primeiro comentário. Link no corpo do post reduz o alcance.</div>
<h2>6. Primeira hora</h2>
<div class="meta">Responda cada comentário até 1 hora depois de publicar e comente em 2 ou 3 posts de outras pessoas. Isso pesa mais no alcance que o texto.</div>
{faltou}
</main>{SCRIPT_COPIAR}</body></html>"""


def pagina_perfil():
    """perfil/quick-wins.md -> docs/perfil.html (cada bloco ``` vira caixa com botão Copiar)."""
    fonte = RAIZ / "perfil" / "quick-wins.md"
    if not fonte.exists():
        return False
    e = html.escape
    titulo = "Kit do perfil"
    partes = []
    n = 0
    for sec in re.split(r"^## ", fonte.read_text(encoding="utf-8"), flags=re.M)[1:]:
        cab, _, corpo = sec.partition("\n")
        partes.append(f"<h2>{e(cab)}</h2>")
        for i, bloco in enumerate(re.split(r"```\n(.*?)```", corpo, flags=re.S)):
            if i % 2:
                n += 1
                partes.append(
                    f'<div class="box" id="b{n}">{e(bloco.strip())}</div>'
                    f'<button class="btn p" data-b="b{n}">Copiar</button>'
                )
            elif bloco.strip():
                txt = re.sub(r"`([^`]+)`", r"<code>\1</code>", e(bloco.strip()))
                partes.append(f'<p style="white-space:pre-wrap">{txt}</p>')
    (DOCS / "perfil.html").write_text(
        f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title><style>{CSS}code{{background:var(--card);padding:1px 5px;border-radius:5px}}</style></head><body><main>
<a href="index.html" style="color:var(--mut)">← posts</a>
<h1>{titulo}</h1><div class="meta">Textos prontos para colar no LinkedIn. [CONFIRMAR] e [PREENCHER] são lacunas suas.</div>
{''.join(partes)}</main><script>
document.querySelectorAll('button[data-b]').forEach(function(b){{b.onclick=async function(){{
 var el=document.getElementById(b.dataset.b),t=el.innerText;
 try{{await navigator.clipboard.writeText(t)}}catch(x){{
  var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy')}}
 b.textContent='Copiado ✓';setTimeout(function(){{b.textContent='Copiar'}},2000)}}}});
</script></body></html>""",
        encoding="utf-8",
    )
    return True


def main():
    if DOCS.exists():
        shutil.rmtree(DOCS)
    (DOCS / "artigos").mkdir(parents=True)
    artigos = [ler_artigo(m) for m in sorted((RAIZ / "artigos").glob("*/artigo.md"))]
    for a in artigos:
        if a["capa"]:
            shutil.copy(a["capa"], DOCS / "artigos" / f"{a['slug']}-capa.png")
        (DOCS / "artigos" / f"{a['slug']}.html").write_text(pagina_artigo(a), encoding="utf-8")

    hoje = date.today()
    artigos.sort(key=lambda a: a["data"] or date.max)
    futuros = [a for a in artigos if a["data"] and a["data"] >= hoje]
    passados = [a for a in artigos if a not in futuros]

    def linha(a):
        cls = "row hoje" if a["data"] == hoje else "row"
        return (f'<a class="{cls}" href="artigos/{html.escape(a["slug"])}.html">{html.escape(a["titulo"])}'
                f'<small>{html.escape(a["cab"])}</small></a>')

    corpo = ""
    if pagina_perfil():
        corpo += '<a class="row" href="perfil.html">Kit do perfil<small>Headline, competências, Sobre, experiências e pedido de recomendação</small></a>'
    corpo += "<h2>Próximos artigos</h2>" + ("".join(map(linha, futuros[:6])) or '<div class="meta">Nenhum ainda.</div>')
    if passados:
        corpo += "<h2>Anteriores</h2>" + "".join(map(linha, reversed(passados[-6:])))
    (DOCS / "index.html").write_text(
        f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Artigos LinkedIn</title><style>{CSS}</style></head><body><main>
<h1>Artigos do LinkedIn</h1><div class="meta">Toda quarta, ao meio-dia. Toque no artigo do dia e siga os passos.</div>
{corpo}</main></body></html>""",
        encoding="utf-8",
    )
    print(f"{len(artigos)} artigos geradas em {DOCS}")
    sem_texto = [str(a["md"].relative_to(RAIZ)) for a in artigos if not a["texto"] or not a["titulo"]]
    if sem_texto:
        print("ATENÇÃO: artigos sem título ou texto:", ", ".join(sem_texto))


if __name__ == "__main__":
    main()

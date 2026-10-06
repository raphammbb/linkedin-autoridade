#!/usr/bin/env python3
"""Gera as páginas de "dia de postar" em docs/ (GitHub Pages).

Lê cada 2026-semana-NN/*.md de post e cria:
  docs/<semana>/<slug>.html  -> texto com botão Copiar + botão Baixar visual
  docs/index.html            -> lista de todos os posts, próximos primeiro

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
    # prefixo: "Texto final" também casa "Texto final (versão X)"; carrossel usa "Legenda (texto do post)"
    m = re.search(rf"^## {re.escape(titulo)}[^\n]*\n(.*?)(?=^## |\Z)", texto, re.S | re.M)
    return m.group(1).strip() if m else ""


def ler_post(md: Path):
    t = md.read_text(encoding="utf-8")
    cab = re.search(r"^# Post \d+ — (.+)$", t, re.M)
    cab = cab.group(1) if cab else md.stem
    dm = re.search(r"(\d{2})/(\d{2})", cab)
    ano = 2026
    data = date(ano, int(dm.group(2)), int(dm.group(1))) if dm else None
    pauta = re.search(r"Pauta banco nº:\*\*\s*\d+\s*—\s*\"?(.+?)\"?\s*$", t, re.M)
    visual = re.search(r"`([^`]+\.(?:png|pdf))`", secao(t, "Visual"))
    return {
        "md": md,
        "cab": cab,
        "data": data,
        "tema": pauta.group(1) if pauta else cab,
        "texto": secao(t, "Texto final") or secao(t, "Legenda"),
        "comentario": secao(t, "Primeiro comentário sugerido"),
        "visual": visual.group(1) if visual else None,
    }


def pagina_post(p, semana):
    e = html.escape
    vis = ""
    if p["visual"]:
        arq = p["visual"]
        if arq.endswith(".png"):
            vis = f'<img src="{e(arq)}" alt="visual do post">'
        rot = "Baixar PDF do carrossel" if arq.endswith(".pdf") else "Baixar imagem"
        vis += f'<a class="btn s" href="{e(arq)}" download>{rot}</a>'
    com = ""
    if p["comentario"] and p["comentario"] != "—":
        com = f'<h2>Primeiro comentário</h2><div class="box">{e(p["comentario"])}</div>'
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(p['tema'])}</title><style>{CSS}</style></head><body><main>
<a href="../index.html" style="color:var(--mut)">← todos os posts</a>
<h1>{e(p['tema'])}</h1><div class="meta">{e(p['cab'])}</div>
<h2>1. Copie o texto</h2>
<div class="box" id="t">{e(p['texto'])}</div>
<button class="btn p" id="c">Copiar texto</button>
<h2>2. Baixe o visual</h2>{vis}{com}
<h2>3. Cole no LinkedIn e publique</h2>
<a class="btn s" href="https://www.linkedin.com/feed/" target="_blank" rel="noopener">Abrir LinkedIn</a>
</main><script>
document.getElementById('c').onclick=async function(){{
 var t=document.getElementById('t').innerText;
 try{{await navigator.clipboard.writeText(t)}}catch(x){{
  var r=document.createRange();r.selectNodeContents(document.getElementById('t'));
  var s=getSelection();s.removeAllRanges();s.addRange(r);document.execCommand('copy')}}
 this.textContent='Copiado ✓';setTimeout(()=>this.textContent='Copiar texto',2000)}};
</script></body></html>"""


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
    posts = []
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()
    for pasta in sorted(RAIZ.glob("20*-semana-*")):
        for md in sorted(pasta.glob("0[1-9]-*.md")):
            p = ler_post(md)
            destino = DOCS / pasta.name
            destino.mkdir(exist_ok=True)
            if p["visual"] and (pasta / p["visual"]).exists():
                shutil.copy(pasta / p["visual"], destino / p["visual"])
            (destino / f"{md.stem}.html").write_text(pagina_post(p, pasta.name), encoding="utf-8")
            p["url"] = f"{pasta.name}/{md.stem}.html"
            posts.append(p)

    hoje = date.today()
    posts.sort(key=lambda p: p["data"] or date.max)
    futuros = [p for p in posts if p["data"] and p["data"] >= hoje]
    passados = [p for p in posts if p not in futuros]

    def linha(p):
        cls = "row hoje" if p["data"] == hoje else "row"
        return (f'<a class="{cls}" href="{html.escape(p["url"])}">{html.escape(p["tema"])}'
                f'<small>{html.escape(p["cab"])}</small></a>')

    corpo = ""
    if pagina_perfil():
        corpo += '<a class="row" href="perfil.html">Kit do perfil<small>Headline, competências, Sobre, experiências e pedido de recomendação</small></a>'
    corpo += "<h2>Próximos</h2>" + "".join(map(linha, futuros[:9]))
    if passados:
        corpo += "<h2>Anteriores</h2>" + "".join(map(linha, reversed(passados[-6:])))
    (DOCS / "index.html").write_text(
        f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Posts LinkedIn</title><style>{CSS}</style></head><body><main>
<h1>Posts do LinkedIn</h1><div class="meta">Toque no post do dia, copie, baixe a imagem e publique.</div>
{corpo}</main></body></html>""",
        encoding="utf-8",
    )
    print(f"{len(posts)} páginas geradas em {DOCS}")


if __name__ == "__main__":
    main()

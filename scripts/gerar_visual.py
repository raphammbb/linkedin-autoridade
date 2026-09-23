#!/usr/bin/env python3
"""
gerar_visual.py — Motor de renderização visual da skill linkedin-autoridade-semanal.

Gera:
  --tipo post       -> 1 PNG (1080x1350 por padrão) a partir de templates/post_texto.html.j2
  --tipo carrossel  -> 1 PDF único (slides 1080x1350) a partir de templates/slide_carrossel.html.j2

Usa Chrome headless para o HTML->PNG (mesmo padrão já validado em carrossel.py e nas
propostas/auditorias em PDF — ver memória reference_html_para_pdf_chrome_headless.md)
e Pillow para juntar os PNGs dos slides num PDF único (sem dependência externa nova).

Uso:
  python3 gerar_visual.py --tipo post --json '{"pilar_label": "...", "titulo": "...", "corpo": "..."}' --out saida.png
  python3 gerar_visual.py --tipo carrossel --json '{"slides": [...]}' --out saida.pdf
  python3 gerar_visual.py --tipo post --json-file spec.json --out saida.png
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

PROJECT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"

# Candidatos de binário, em ordem de preferência — cobre Mac local e o
# sandbox cloud do scheduled-task (Linux, sem Chrome nativo, mas com o
# Chromium do Playwright pré-instalado em /opt/pw-browsers).
BROWSER_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Mac local
    "/Applications/Chromium.app/Contents/MacOS/Chromium",             # Mac local (fallback)
    "/opt/pw-browsers/chromium",                                      # cloud sandbox (Playwright)
    "google-chrome-stable",  # Linux genérico — resolvido via PATH
    "google-chrome",
    "chromium-browser",
    "chromium",
]

DEFAULT_W = 1080
DEFAULT_H = 1350


def get_env() -> Environment:
    return Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def find_browser() -> str:
    for candidate in BROWSER_CANDIDATES:
        if candidate.startswith("/"):
            if Path(candidate).exists():
                return candidate
        elif shutil.which(candidate):
            return candidate
    raise FileNotFoundError(
        "Chrome/Chromium não encontrado (nem local, nem em /opt/pw-browsers, nem no PATH). "
        "No sandbox cloud, rode antes: npx -y playwright install chromium. "
        "Local, abra o HTML manualmente e exporte via Arquivo → Imprimir → Salvar como PDF."
    )


def html_to_png(html_path: Path, png_path: Path, w: int, h: int) -> None:
    browser = find_browser()
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--window-size={w},{h}",
        "--force-device-scale-factor=1",
        "--virtual-time-budget=4000",
        f"--screenshot={png_path}",
        f"file://{html_path.absolute()}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if not png_path.exists():
        raise RuntimeError(f"Chrome headless não gerou {png_path.name}: {result.stderr[:300]}")


def render_post_texto(spec: dict, out_png: Path) -> Path:
    w = spec.get("w", DEFAULT_W)
    h = spec.get("h", DEFAULT_H)
    env = get_env()
    template = env.get_template("post_texto.html.j2")
    html = template.render(w=w, h=h, **spec)

    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "post.html"
        html_path.write_text(html, encoding="utf-8")
        out_png.parent.mkdir(parents=True, exist_ok=True)
        html_to_png(html_path, out_png, w, h)
    return out_png


def render_carrossel(spec: dict, out_pdf: Path) -> Path:
    w = spec.get("w", DEFAULT_W)
    h = spec.get("h", DEFAULT_H)
    slides = spec["slides"]
    total = len(slides)
    if not (6 <= total <= 10):
        print(f"  ! Aviso: {total} slides — fora da faixa recomendada de 6 a 10.", file=sys.stderr)

    env = get_env()
    template = env.get_template("slide_carrossel.html.j2")

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        png_paths = []
        for i, slide in enumerate(slides, start=1):
            ctx = dict(slide)
            ctx.update(w=w, h=h, index=i, total=total)
            html = template.render(**ctx)
            html_path = tmp_dir / f"slide_{i:02d}.html"
            html_path.write_text(html, encoding="utf-8")
            png_path = tmp_dir / f"slide_{i:02d}.png"
            html_to_png(html_path, png_path, w, h)
            png_paths.append(png_path)
            print(f"  ✓ slide {i:02d}/{total:02d}")

        combine_pngs_to_pdf(png_paths, out_pdf)
    return out_pdf


def combine_pngs_to_pdf(png_paths: list, out_pdf: Path) -> None:
    try:
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "Pillow não instalado. Rode: pip install Pillow (ou python3 -m pip install Pillow)."
        ) from e

    images = [Image.open(p).convert("RGB") for p in png_paths]
    first, rest = images[0], images[1:]
    first.save(out_pdf, save_all=True, append_images=rest)


def main():
    parser = argparse.ArgumentParser(description="Gera visuais (PNG/PDF) para o LinkedIn pessoal do Rapha.")
    parser.add_argument("--tipo", choices=["post", "carrossel"], required=True)
    parser.add_argument("--json", help="Spec em JSON inline.")
    parser.add_argument("--json-file", help="Caminho de um arquivo JSON com a spec.")
    parser.add_argument("--out", required=True, help="Caminho de saída (.png para post, .pdf para carrossel).")
    args = parser.parse_args()

    if args.json:
        spec = json.loads(args.json)
    elif args.json_file:
        spec = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    else:
        parser.error("Informe --json ou --json-file.")

    out_path = Path(args.out)

    if args.tipo == "post":
        render_post_texto(spec, out_path)
    else:
        render_carrossel(spec, out_path)

    print(f"✓ Gerado: {out_path}")


if __name__ == "__main__":
    main()

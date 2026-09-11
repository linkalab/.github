#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Genera le bandierine dei link fra le due lingue del profilo.

Le emoji bandiera sono sequenze di due regional indicator che il sistema
operativo deve comporre: Windows non lo fa e mostra le lettere "US" e
"IT" al posto della bandiera. Servirle come immagini dal repository le
rende identiche ovunque.

Gli SVG sono disegnati qui e rasterizzati con Chrome, perche' GitHub
rimuove gli SVG inline dal markdown.
"""

import math
import shutil
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).parent
OUT = BUILD.parent / "profile" / "assets"

ALTEZZA = 28  # 2x di 14px, l'altezza a cui stanno accanto al testo


def stella(*, cx: float, cy: float, raggio: float) -> str:
    """Path SVG di una stella a cinque punte centrata in (cx, cy)."""
    punti = []
    for i in range(10):
        r = raggio if i % 2 == 0 else raggio * 0.382
        angolo = math.pi / 2 + i * math.pi / 5
        punti.append(f"{cx + r * math.cos(angolo):.2f},{cy - r * math.sin(angolo):.2f}")
    return f'<polygon points="{" ".join(punti)}" fill="#FFFFFF"/>'


def svg_italia() -> tuple[str, int]:
    """Tre bande verticali uguali, proporzione 3:2."""
    larghezza = round(ALTEZZA * 3 / 2)
    banda = larghezza / 3
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{larghezza}" height="{ALTEZZA}" '
        f'viewBox="0 0 {larghezza} {ALTEZZA}">'
        f'<rect width="{banda}" height="{ALTEZZA}" fill="#008C45"/>'
        f'<rect x="{banda}" width="{banda}" height="{ALTEZZA}" fill="#F4F5F0"/>'
        f'<rect x="{banda * 2}" width="{banda}" height="{ALTEZZA}" fill="#CD212A"/>'
        f"</svg>"
    )
    return svg, larghezza


def svg_stati_uniti() -> tuple[str, int]:
    """Tredici strisce e cantone con 50 stelle, proporzione 19:10."""
    larghezza = round(ALTEZZA * 1.9)
    striscia = ALTEZZA / 13
    cantone_h = striscia * 7
    cantone_w = larghezza * 0.76 / 1.9

    apertura = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{larghezza}" height="{ALTEZZA}" '
        f'viewBox="0 0 {larghezza} {ALTEZZA}">'
    )
    parti = [
        apertura,
        f'<rect width="{larghezza}" height="{ALTEZZA}" fill="#FFFFFF"/>',
    ]
    for i in range(0, 13, 2):
        parti.append(
            f'<rect y="{i * striscia:.2f}" width="{larghezza}" '
            f'height="{striscia:.2f}" fill="#B31942"/>'
        )
    parti.append(
        f'<rect width="{cantone_w:.2f}" height="{cantone_h:.2f}" fill="#0A3161"/>'
    )

    # 5 file da 6 stelle alternate a 4 file da 5, come sulla bandiera reale
    passo_x = cantone_w / 12
    passo_y = cantone_h / 10
    raggio = passo_y * 0.62
    for riga in range(9):
        colonne = 6 if riga % 2 == 0 else 5
        offset = 1 if riga % 2 == 0 else 2
        for col in range(colonne):
            parti.append(
                stella(
                    cx=(offset + col * 2) * passo_x,
                    cy=(1 + riga) * passo_y,
                    raggio=raggio,
                )
            )
    parti.append("</svg>")
    return "".join(parti), larghezza


def rasterizza(*, nome: str, svg: str, larghezza: int, chrome: str) -> Path:
    page = BUILD / f"_flag-{nome}.html"
    page.write_text(
        f"<meta charset='utf-8'><style>*{{margin:0;padding:0}}"
        f"html,body{{width:{larghezza}px;height:{ALTEZZA}px}}</style>{svg}",
        encoding="utf-8",
    )
    out = OUT / f"flag-{nome}.png"
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--default-background-color=00000000",
            f"--window-size={larghezza},{ALTEZZA}",
            f"--screenshot={out}",
            page.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    return out


def main() -> int:
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome is None:
        print("ERRORE: nessun binario Chrome trovato", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    for nome, costruttore in [("it", svg_italia), ("us", svg_stati_uniti)]:
        svg, larghezza = costruttore()
        out = rasterizza(nome=nome, svg=svg, larghezza=larghezza, chrome=chrome)
        print(
            f"{out.relative_to(BUILD.parent)}  {larghezza}x{ALTEZZA}  {out.stat().st_size} byte"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Renderizza la copertina della pagina LinkedIn dal suo template HTML.

Il banner del README non si puo' riusare qui: LinkedIn mostra la
copertina a 1128x191, quasi il doppio piu' larga in proporzione, e il
logo della pagina si sovrappone all'angolo in basso a sinistra. Il
formato ha quindi un template suo, con la colonna di testo a destra e
dentro la fascia centrale che la app mobile non taglia.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import render_banner

BUILD = Path(__file__).parent
OUT = BUILD.parent / "profile" / "assets"

# 1128x191 e' la misura che LinkedIn indica per la copertina di una
# pagina aziendale; il fattore 3 serve a tenere il testo nitido sugli
# schermi ad alta densita', visto che LinkedIn riscala l'immagine.
WIDTH, HEIGHT = 1128, 191
SCALA = 3

# La copertina non porta il logotipo (lo ripete gia' l'avatar della
# pagina), quindi le servono meno asset del banner.
ASSET_RICHIESTI = [
    "space-grotesk-700.woff2",
    "manrope-400.woff2",
    "jetbrains-mono-500.woff2",
]


def controlla_asset() -> list[str]:
    """Restituisce i nomi degli asset mancanti in build/."""
    return [nome for nome in ASSET_RICHIESTI if not (BUILD / nome).is_file()]


def render(*, lang: str, variant: str, template: str, chrome: str) -> Path:
    html = (
        template.replace("__BG__", render_banner.VARIANTS[variant])
        .replace("__EYEBROW__", render_banner.COPY[lang]["eyebrow"])
        .replace("__PAYOFF__", render_banner.COPY[lang]["payoff"])
    )
    page = BUILD / f"_cover-{lang}-{variant}.html"
    page.write_text(html, encoding="utf-8")

    out = OUT / f"linkedin-cover-{lang}-{variant}.png"
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            f"--force-device-scale-factor={SCALA}",
            f"--window-size={WIDTH},{HEIGHT}",
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

    mancanti = controlla_asset()
    if mancanti:
        print("ERRORE: mancano gli asset del design system:", file=sys.stderr)
        for nome in mancanti:
            print(f"  - build/{nome}", file=sys.stderr)
        print(render_banner.DOVE_PRENDERLI, file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    template = (BUILD / "cover.html.tpl").read_text(encoding="utf-8")

    for lang in render_banner.COPY:
        for variant in render_banner.VARIANTS:
            out = render(lang=lang, variant=variant, template=template, chrome=chrome)
            print(f"{out.relative_to(BUILD.parent)}  {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Renderizza i banner del README dal template HTML usando Chrome headless.

Il design system Linkalab usa font self-hosted (Space Grotesk, Manrope,
JetBrains Mono) che GitHub non puo' caricare nel README: il banner deve
quindi essere un'immagine rasterizzata, non SVG con testo.
"""

import shutil
import subprocess
import sys
from pathlib import Path

BUILD = Path(__file__).parent
OUT = BUILD.parent / "profile" / "assets"

# forest-900 e forest-950 dai tokens/colors.css del design system
VARIANTS = {
    "light": "#0F3D2D",
    "dark": "#07251A",
}

COPY = {
    "it": {
        "eyebrow": "Dati &amp; AI per l'impresa · Cagliari e Milano",
        "payoff": "AI su misura.<br><em>Con i tuoi dati.</em>",
    },
    "en": {
        "eyebrow": "Enterprise data &amp; AI · Cagliari and Milan",
        "payoff": "AI built to measure.<br><em>On your own data.</em>",
    },
}

WIDTH, HEIGHT = 1280, 340

# Font e logo arrivano dal design system e non stanno nel repo. Senza,
# Chrome renderizza lo stesso: font di sistema al posto di Space Grotesk
# e un'immagine rotta al posto del logo, e il banner esce sbagliato
# senza che nessuno se ne accorga. Quindi si controlla prima.
ASSET_RICHIESTI = [
    "linkalab-logo-white.png",
    "space-grotesk-700.woff2",
    "space-grotesk-500.woff2",
    "manrope-400.woff2",
    "manrope-600.woff2",
    "jetbrains-mono-500.woff2",
]

DOVE_PRENDERLI = """
Copiali dal design system Linkalab (cartella Drive "Design System",
versione piu' recente) dentro build/:

    DS="<percorso del design system estratto>"
    cp "$DS/assets/logo/linkalab-logo-white.png" build/
    cp "$DS/assets/fonts/space-grotesk-700.woff2" build/
    cp "$DS/assets/fonts/space-grotesk-500.woff2" build/
    cp "$DS/assets/fonts/manrope-400.woff2" build/
    cp "$DS/assets/fonts/manrope-600.woff2" build/
    cp "$DS/assets/fonts/jetbrains-mono-500.woff2" build/
"""


def controlla_asset() -> list[str]:
    """Restituisce i nomi degli asset mancanti in build/."""
    return [nome for nome in ASSET_RICHIESTI if not (BUILD / nome).is_file()]


def render(*, lang: str, variant: str, template: str, chrome: str) -> Path:
    html = (
        template.replace("__BG__", VARIANTS[variant])
        .replace("__EYEBROW__", COPY[lang]["eyebrow"])
        .replace("__PAYOFF__", COPY[lang]["payoff"])
    )
    page = BUILD / f"_banner-{lang}-{variant}.html"
    page.write_text(html, encoding="utf-8")

    out = OUT / f"banner-{lang}-{variant}.png"
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--force-device-scale-factor=2",
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
        print(DOVE_PRENDERLI, file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    template = (BUILD / "banner.html.tpl").read_text(encoding="utf-8")

    for lang in COPY:
        for variant in VARIANTS:
            out = render(lang=lang, variant=variant, template=template, chrome=chrome)
            print(f"{out.relative_to(BUILD.parent)}  {out.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

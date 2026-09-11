#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31"]
# ///
"""Costruisce un'anteprima autonoma dei due README.

Il markdown passa dal renderer di GitHub, poi immagini e badge vengono
incorporati come data URI: la pagina risultante non fa nessuna richiesta
di rete, che e' la condizione per pubblicarla come artifact.

Il `<picture>` dei banner viene riscritto in due `<img>` governate dal
tema della pagina: `prefers-color-scheme` da solo non reagirebbe al
selettore di tema del visualizzatore.
"""

import base64
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent
BUILD = Path(__file__).parent
OUT = BUILD / "anteprima-readme.html"
RAW = "https://raw.githubusercontent.com/linkalab/.github/main/profile/"

LINGUE = {
    "it": {"file": "profile/README.md", "etichetta": "Italiano"},
    "en": {"file": "profile/README.en.md", "etichetta": "English"},
}


def data_uri(percorso: Path) -> str:
    b64 = base64.b64encode(percorso.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def badge_inline(url: str, cache: dict[str, str]) -> str:
    """Scarica un badge shields.io e lo restituisce come data URI."""
    if url not in cache:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        b64 = base64.b64encode(r.content).decode("ascii")
        cache[url] = f"data:image/svg+xml;base64,{b64}"
    return cache[url]


def rendi(md: str) -> str:
    r = requests.post(
        "https://api.github.com/markdown",
        json={"text": md, "mode": "gfm"},
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def prepara(lingua: str, cache: dict[str, str]) -> str:
    md = (ROOT / LINGUE[lingua]["file"]).read_text(encoding="utf-8")
    html = rendi(md)

    # i due banner, incorporati e commutati dal tema della pagina
    chiaro = data_uri(ROOT / "profile" / "assets" / f"banner-{lingua}-light.png")
    scuro = data_uri(ROOT / "profile" / "assets" / f"banner-{lingua}-dark.png")
    alt = re.search(r'<img[^>]+alt="([^"]*)"', html)
    testo_alt = alt.group(1) if alt else ""
    banner = (
        f'<span class="banner">'
        f'<img class="chiaro" src="{chiaro}" alt="{testo_alt}">'
        f'<img class="scuro" src="{scuro}" alt="">'
        f"</span>"
    )
    html = re.sub(r"<picture>.*?</picture>", banner, html, flags=re.DOTALL)

    # GitHub riscrive ogni immagine remota attraverso il proxy camo, quindi
    # dopo il render l'URL di shields.io non c'e' piu'. L'attributo alt
    # invece sopravvive ed e' distinto per badge: e' la chiave con cui
    # rimettere al suo posto ognuno dei data URI.
    badge_per_alt = {
        alt: url
        for alt, url in re.findall(
            r"!\[([^\]]+)\]\((https://img\.shields\.io[^)]+)\)", md
        )
    }

    def sostituisci(m: re.Match) -> str:
        tag = m.group(0)

        # badge di shields.io, riconosciuti dall'alt che camo conserva
        alt = re.search(r'alt="([^"]*)"', tag)
        if alt and alt.group(1) in badge_per_alt:
            url = badge_per_alt[alt.group(1)]
            return re.sub(r'src="[^"]*"', f'src="{badge_inline(url, cache)}"', tag)

        # immagini del repository (bandiere): il file esiste gia' in locale
        src = re.search(r'src="([^"]*)"', tag)
        if src and RAW in src.group(1):
            relativo = src.group(1).split(RAW, 1)[1]
            locale = ROOT / "profile" / relativo
            if locale.is_file():
                return tag.replace(src.group(1), data_uri(locale))
        return tag

    html = re.sub(r"<img\b[^>]*>", sostituisci, html)

    rimasti = re.findall(r'<img[^>]+src="https?://[^"]+"', html)
    if rimasti:
        raise RuntimeError(
            f"{len(rimasti)} immagini non incorporate: la pagina farebbe "
            f"richieste di rete e l'artifact le bloccherebbe. Prima: {rimasti[0][:120]}"
        )
    # i link non devono portare fuori dall'anteprima in un pannello
    html = html.replace("<a href=", '<a target="_blank" rel="noopener" href=')
    html = html.replace(RAW, "")
    return html


def main() -> int:
    cache: dict[str, str] = {}
    try:
        pagine = {lingua: prepara(lingua, cache) for lingua in LINGUE}
    except requests.HTTPError as err:
        print(f"ERRORE: render fallito: {err}", file=sys.stderr)
        return 1

    corpi = "\n".join(
        f'<article class="pagina" data-lingua="{lingua}" '
        f"{'' if lingua == 'it' else 'hidden'}>{html}</article>"
        for lingua, html in pagine.items()
    )

    modello = (BUILD / "artifact.html.tpl").read_text(encoding="utf-8")
    OUT.write_text(modello.replace("__PAGINE__", corpi), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  {OUT.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

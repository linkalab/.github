#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["feedparser>=6.0"]
# ///
"""Riempie i marker BLOG-POST-LIST nei README leggendo il feed del sito.

Replica in locale quello che la GitHub Action fa a ogni esecuzione
schedulata (stesso template, stesso formato data), cosi' i README sono
gia' popolati al primo push invece di mostrare due commenti vuoti fino
al primo giro del cron.
"""

import re
import sys
from pathlib import Path

import feedparser

FEED = "https://www.linkalab.it/feed"
MAX_POSTS = 5
START = "<!-- BLOG-POST-LIST:START -->"
END = "<!-- BLOG-POST-LIST:END -->"

ROOT = Path(__file__).parent.parent
TARGETS = [ROOT / "profile" / "README.md", ROOT / "profile" / "README.en.md"]


def build_list() -> str:
    """Costruisce la lista con lo stesso formato del workflow.

    Attenzione: questo script e la GitHub Action non condividono il
    formatter delle date. Se cambia `date_format` o `template` in
    `.github/workflows/magazine.yml`, va cambiato anche qui, altrimenti
    l'anteprima locale mostra un risultato che la produzione non produce.
    """
    feed = feedparser.parse(FEED)
    if feed.bozo and not feed.entries:
        raise RuntimeError(f"feed non leggibile: {feed.bozo_exception}")

    righe = []
    for entry in feed.entries[:MAX_POSTS]:
        d = entry.published_parsed
        data = f"{d.tm_mday:02d}.{d.tm_mon:02d}.{d.tm_year}"
        righe.append(f"- [{entry.title}]({entry.link}) <sub>{data}</sub>")
    return "\n".join(righe)


def main() -> int:
    lista = build_list()
    blocco = f"{START}\n{lista}\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)

    for target in TARGETS:
        testo = target.read_text(encoding="utf-8")
        if not pattern.search(testo):
            print(f"ERRORE: marker assenti in {target.name}", file=sys.stderr)
            return 1
        target.write_text(pattern.sub(blocco, testo), encoding="utf-8")
        print(f"aggiornato {target.relative_to(ROOT)}")

    print()
    print(lista)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

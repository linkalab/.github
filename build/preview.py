#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.31"]
# ///
"""Anteprima locale dei README, renderizzati dall'API markdown di GitHub.

Serve a guardare la pagina com'e' davvero prima di pubblicarla: il
markdown passa dallo stesso renderer di GitHub, i banner vengono
ripuntati ai file locali (su raw.githubusercontent non esistono finche'
il repo non e' pubblicato) e Chrome fotografa il risultato a 1280 e a
375 px.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent
BUILD = Path(__file__).parent
RAW = "https://raw.githubusercontent.com/linkalab/.github/main/profile/"

CSS = """
body{margin:0;background:#fff;color:#1f2328;
  font:16px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
.box{max-width:1012px;margin:0 auto;padding:32px}
img{max-width:100%}
h2{border-bottom:1px solid #d1d9e0;padding-bottom:.3em;margin-top:24px;font-size:1.5em}
table{border-collapse:collapse;margin:16px 0}
td{border:1px solid #d1d9e0;padding:6px 13px}
tr:nth-child(2n){background:#f6f8fa}
a{color:#0969da;text-decoration:none}
sub{color:#59636e}
"""


def render(md: str) -> str:
    r = requests.post(
        "https://api.github.com/markdown",
        json={"text": md, "mode": "gfm"},
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def shoot(*, page: Path, out: Path, width: int, chrome: str) -> None:
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            f"--window-size={width},2400",
            f"--screenshot={out}",
            page.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def main() -> int:
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if chrome is None:
        print("ERRORE: nessun binario Chrome trovato", file=sys.stderr)
        return 1

    for nome, sorgente in [("it", "profile/README.md"), ("en", "profile/README.en.md")]:
        md = (ROOT / sorgente).read_text(encoding="utf-8")
        # i banner non sono ancora su GitHub: punta alle copie locali
        md = md.replace(RAW, "")
        corpo = render(md)
        page = BUILD / f"_preview-{nome}.html"
        page.write_text(
            f"<meta charset='utf-8'><style>{CSS}</style><div class='box'>{corpo}</div>",
            encoding="utf-8",
        )
        # l'HTML sta in build/, le immagini in profile/assets/: symlink.
        # exists() segue il link e torna False se e' rotto, quindi da solo
        # manderebbe symlink_to su un path occupato: va tolto prima.
        link = BUILD / "assets"
        if link.is_symlink() and not link.exists():
            link.unlink()
        if not link.exists():
            link.symlink_to(ROOT / "profile" / "assets")

        for width in (1280, 375):
            out = BUILD / f"preview-{nome}-{width}.png"
            shoot(page=page, out=out, width=width, chrome=chrome)
            print(f"{out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

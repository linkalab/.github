#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Rasterizza i caroselli PDF e aggiorna il blocco nei due README.

Lo script fa il lavoro sul disco: legge i PDF di profile/assets/docs,
ne esporta le pagine con poppler e riscrive il blocco fra i marker. La
composizione del markup sta in docs_markup, che non tocca il disco.

Il perche' dei due tagli e dei titoli estratti dalle pagine sta nel
README del repository, sezione "I caroselli si sfogliano come immagini".
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

from docs_markup import (
    COPY,
    PREFISSO_PAGE,
    PREFISSO_THUMB,
    Documento,
    blocco_documento,
    sostituisci_marker,
    titolo_pagina,
)

BUILD = Path(__file__).parent
DOCS = BUILD.parent / "profile" / "assets" / "docs"
PROFILE = BUILD.parent / "profile"

# Il taglio a 400 tiene la miniatura nitida anche a densita' 1.5x senza
# far pesare la griglia piu' del banner.
THUMB_X, THUMB_Q = 400, 88
# La pagina piena si legge a schermo intero, dove 1400px bastano a
# rendere leggibile il corpo del testo di una slide 4:5.
PAGE_X, PAGE_Q = 1400, 90

POPPLER = ("pdfinfo", "pdftotext", "pdftoppm")

DOCUMENTI = [
    Documento(
        slug="ai-whitebox-identita-agenti",
        titolo={
            "it": "Agenti AI in azienda: con quali credenziali stanno agendo?",
            "en": "AI agents at work: whose credentials are they using?",
        },
        occhiello={"it": "AI WhiteBox", "en": "AI WhiteBox"},
    ),
    Documento(
        slug="compliance-shield-prodotti-assicurativi",
        titolo={
            "it": "Compliance Shield: validazione intelligente dei prodotti assicurativi",
            "en": "Compliance Shield: intelligent validation of insurance products",
        },
        occhiello={"it": "Caso studio", "en": "Case study"},
        # Tre pagine di questo carosello non staccano il titolo dal corpo
        # con una riga vuota, e l'euristica ne raccoglie la prima frase:
        # qui il titolo si scrive a mano.
        alt_override={
            1: "Compliance Shield: validazione intelligente dei prodotti assicurativi",
            4: "Dai controlli di routine alla governance strategica",
            5: "Governance verificabile per un go-to-market senza rischi",
        },
    ),
]


def pdf_di(doc: Documento) -> Path:
    return DOCS / f"{doc.slug}.pdf"


def pagine_di(doc: Documento) -> Path:
    return DOCS / doc.slug


def conta_pagine(pdf: Path) -> int:
    """Numero di pagine del PDF, letto da pdfinfo."""
    uscita = subprocess.run(
        ["pdfinfo", str(pdf)], capture_output=True, text=True, check=True
    ).stdout
    trovato = re.search(r"^Pages:\s+(\d+)$", uscita, re.MULTILINE)
    if trovato is None:
        raise ValueError(f"pdfinfo non riporta il numero di pagine di {pdf.name}")
    return int(trovato.group(1))


def testo_pagina(*, pdf: Path, pagina: int) -> str:
    """Testo di una singola pagina, nell'ordine in cui e' impaginato."""
    return subprocess.run(
        ["pdftotext", "-layout", "-f", str(pagina), "-l", str(pagina), str(pdf), "-"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def controlla_scritte(*, destinazione: Path, prefisso: str, pagine: int, pdf: Path) -> None:
    """Verifica che esista il file di ogni pagina che il README linkera'.

    Il nome che il README scrive e quello che pdftoppm ha scritto sono
    la stessa espressione in due punti del programma: se divergono, qui
    e' un errore locale, in produzione un'immagine rotta sulla vetrina.
    """
    mancanti = [
        n for n in range(1, pagine + 1) if not (destinazione / f"{prefisso}-{n}.jpg").is_file()
    ]
    if mancanti:
        raise RuntimeError(
            f"{pdf.name}: manca {prefisso}-{mancanti[0]}.jpg fra le pagine rasterizzate"
        )


def rasterizza(
    *, pdf: Path, destinazione: Path, prefisso: str, pagine: int, larghezza: int, qualita: int
) -> None:
    """Esporta le pagine del PDF in JPEG scalati, un file per pagina.

    Una pagina per invocazione, con `-singlefile`: cosi' pdftoppm scrive
    esattamente il nome ricevuto. Lasciandogli l'intero documento la
    numerazione la sceglie lui, e dalla decima pagina in poi allinea
    tutti i nomi con uno zero davanti, non solo quelli a due cifre.
    """
    destinazione.mkdir(parents=True, exist_ok=True)
    for n in range(1, pagine + 1):
        argv = ["pdftoppm", "-jpeg", "-jpegopt", f"quality={qualita}"]
        argv += ["-scale-to-x", str(larghezza), "-scale-to-y", "-1"]
        argv += ["-singlefile", "-f", str(n), "-l", str(n)]
        argv += [str(pdf), str(destinazione / f"{prefisso}-{n}")]
        subprocess.run(argv, check=True)
    controlla_scritte(destinazione=destinazione, prefisso=prefisso, pagine=pagine, pdf=pdf)


def strumenti_mancanti() -> list[str]:
    """Binari di poppler che servono e non sono installati."""
    return [nome for nome in POPPLER if shutil.which(nome) is None]


def alt_documento(doc: Documento, pagine: int) -> list[str]:
    """Testo alternativo di ogni pagina, dal titolo stampato sulla pagina."""
    testi = []
    for n in range(1, pagine + 1):
        if n in doc.alt_override:
            testi.append(doc.alt_override[n])
            continue
        titolo = titolo_pagina(testo_pagina(pdf=pdf_di(doc), pagina=n))
        testi.append(titolo or COPY["it"]["pagina_alt"].format(n=n))
    return testi


def prepara_documento(doc: Documento) -> int:
    """Rasterizza i due tagli di ogni pagina, e dice quante ne ha trovate."""
    pagine = conta_pagine(pdf_di(doc))
    for prefisso, larghezza, qualita in (
        (PREFISSO_THUMB, THUMB_X, THUMB_Q),
        (PREFISSO_PAGE, PAGE_X, PAGE_Q),
    ):
        rasterizza(
            pdf=pdf_di(doc),
            destinazione=pagine_di(doc),
            prefisso=prefisso,
            pagine=pagine,
            larghezza=larghezza,
            qualita=qualita,
        )
    return pagine


def scrivi_readme(blocchi: dict[str, list[str]]) -> None:
    """Riscrive il blocco fra i marker nel README di ciascuna lingua."""
    for lang, nome in (("it", "README.md"), ("en", "README.en.md")):
        percorso = PROFILE / nome
        aggiornato = sostituisci_marker(
            markdown=percorso.read_text(encoding="utf-8"),
            blocco="\n\n".join(blocchi[lang]),
        )
        percorso.write_text(aggiornato, encoding="utf-8")
        print(f"aggiornato {percorso.relative_to(BUILD.parent)}")


def main() -> int:
    mancanti = strumenti_mancanti()
    if mancanti:
        print("Mancano dei binari di poppler:", ", ".join(mancanti), file=sys.stderr)
        print("Su Debian e Ubuntu: sudo apt install poppler-utils", file=sys.stderr)
        return 1

    senza_pdf = [doc.slug for doc in DOCUMENTI if not pdf_di(doc).is_file()]
    if senza_pdf:
        print("PDF sorgente assenti in profile/assets/docs:", file=sys.stderr)
        for slug in senza_pdf:
            print(f"  {slug}.pdf", file=sys.stderr)
        return 1

    blocchi: dict[str, list[str]] = {lang: [] for lang in COPY}
    for doc in DOCUMENTI:
        pagine = prepara_documento(doc)
        peso_mb = pdf_di(doc).stat().st_size / 1_000_000
        for lang in COPY:
            blocchi[lang].append(
                blocco_documento(
                    doc=doc, lang=lang, alt=alt_documento(doc, pagine), peso_mb=peso_mb
                )
            )
        print(f"{doc.slug}: {pagine} pagine")

    scrivi_readme(blocchi)
    return 0


if __name__ == "__main__":
    sys.exit(main())

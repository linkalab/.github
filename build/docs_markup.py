"""Il blocco HTML con cui un carosello si presenta nel README.

Nessuna funzione qui tocca il disco o lancia un processo: il modulo
conosce i nomi dei file delle pagine, non i file. Serve a poter provare
la composizione del markup, che e' la parte che sbaglia in silenzio,
senza avere poppler ne' un PDF sotto mano.

Il perche' dei due tagli e dei titoli estratti dalle pagine sta nel
README del repository, sezione "I caroselli si sfogliano come immagini".
"""

from dataclasses import dataclass, field

RAW = "https://raw.githubusercontent.com/linkalab/.github/main/profile/assets/docs"
BLOB = "https://github.com/linkalab/.github/blob/main/profile/assets/docs"

# Tre miniature per riga nella colonna del README, una per riga sotto i 375px.
THUMB_DISPLAY = 260

# Il prefisso di un file di pagina lo scrive chi rasterizza e lo legge chi
# compone il link: sono due moduli, quindi il nome sta qui una volta sola.
PREFISSO_THUMB = "thumb"
PREFISSO_PAGE = "page"

MARKER_START = "<!-- DOCS-LIST:START -->"
MARKER_END = "<!-- DOCS-LIST:END -->"

# Oltre questa lunghezza il titolo di copertina smette di essere una
# didascalia e diventa l'inizio del corpo della slide.
ALT_MAX = 90

COPY = {
    "it": {
        "pagine": "{n} pagine",
        "scarica": "Apri il PDF completo ({mb} MB)",
        "pagina_alt": "Pagina {n}",
    },
    "en": {
        "pagine": "{n} pages",
        "scarica": "Open the full PDF ({mb} MB, in Italian)",
        "pagina_alt": "Page {n}",
    },
}


@dataclass(frozen=True)
class Documento:
    """Un carosello: lo slug dei suoi file e come si presenta nelle due lingue."""

    slug: str
    titolo: dict[str, str]
    occhiello: dict[str, str]
    alt_override: dict[int, str] = field(default_factory=dict)


def titolo_pagina(testo: str) -> str:
    """Titolo stampato in cima a una pagina, dal testo estratto dal PDF.

    Il titolo di una slide e' spezzato su piu' righe e non e' separato
    dal corpo da una riga vuota, quindi il confine si trova per
    lunghezza: si accumulano righe finche' la successiva non sfora, e
    ci si ferma prima su una riga che chiude una frase.
    """
    accumulato: list[str] = []
    for riga in (r.strip() for r in testo.splitlines()):
        if not riga:
            continue
        if accumulato and len(" ".join([*accumulato, riga])) > ALT_MAX:
            break
        accumulato.append(riga)
        if riga.endswith((".", "?", "!")):
            break
    unito = " ".join(accumulato)
    if len(unito) <= ALT_MAX:
        return unito
    return unito[:ALT_MAX].rsplit(" ", 1)[0]


def attributo(testo: str) -> str:
    """Rende un testo sicuro dentro un attributo HTML fra virgolette."""
    scambi = (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"))
    for segno, entita in scambi:
        testo = testo.replace(segno, entita)
    return testo


def miniatura(*, doc: Documento, pagina: int, alt: str) -> str:
    """Una miniatura cliccabile: src al taglio piccolo, href alla pagina intera."""
    return (
        f'<a href="{BLOB}/{doc.slug}/{PREFISSO_PAGE}-{pagina}.jpg">'
        f'<img src="{RAW}/{doc.slug}/{PREFISSO_THUMB}-{pagina}.jpg" width="{THUMB_DISPLAY}" '
        f'alt="{attributo(alt)}"></a>'
    )


def blocco_documento(*, doc: Documento, lang: str, alt: list[str], peso_mb: float) -> str:
    """Il <details> di un documento: intestazione, griglia, link al PDF."""
    copy = COPY[lang]
    conteggio = copy["pagine"].format(n=len(alt))
    scarica = copy["scarica"].format(mb=f"{peso_mb:.1f}")
    miniature = "\n".join(
        miniatura(doc=doc, pagina=n, alt=testo) for n, testo in enumerate(alt, start=1)
    )
    return (
        "<details>\n"
        f"<summary><b>{doc.titolo[lang]}</b> &middot; "
        f"{doc.occhiello[lang]}, {conteggio}</summary>\n"
        '<p align="center">\n'
        f"{miniature}\n"
        "</p>\n"
        f'<p align="center"><a href="{BLOB}/{doc.slug}.pdf">{scarica}</a></p>\n'
        "</details>"
    )


def sostituisci_marker(*, markdown: str, blocco: str) -> str:
    """Riscrive il contenuto fra i due marker, lasciando il resto intatto."""
    inizio = markdown.find(MARKER_START)
    fine = markdown.find(MARKER_END)
    if inizio == -1 or fine == -1:
        raise ValueError(f"marker {MARKER_START} o {MARKER_END} assenti nel README")
    return f"{markdown[: inizio + len(MARKER_START)]}\n{blocco}\n{markdown[fine:]}"

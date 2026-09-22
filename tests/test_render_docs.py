"""La rasterizzazione deve scrivere i file che il README linkera'.

Poppler e' il solo boundary sostituito, e il suo sostituto imita il
comportamento che ha causato il difetto: `pdftoppm` numera i file da
se' quando gli si passa l'intero documento, e da dieci pagine in su li
allinea con uno zero davanti. Il finto fa lo stesso, cosi' togliere
`-singlefile` dal codice fa fallire i test invece di rompere il profilo
pubblicato.
"""

import subprocess
from pathlib import Path

import pytest

import render_docs

TESTO_PAGINE = {
    1: "Agenti AI in azienda:\ncon quali credenziali\nstanno agendo?\nSe un agente AI usa\n",
    2: "Least Privilege: dare\nall'agente solo cio'\nche gli serve\nUn agente che analizza\n",
    3: "",
}

README = """# Profilo

Testo che precede.

<!-- DOCS-LIST:START -->
vecchio contenuto
<!-- DOCS-LIST:END -->

## Sezione che segue
"""


@pytest.fixture
def documento():
    return render_docs.Documento(
        slug="prova-carosello",
        titolo={"it": "Titolo italiano", "en": "English title"},
        occhiello={"it": "Caso studio", "en": "Case study"},
    )


@pytest.fixture
def poppler(monkeypatch):
    """Poppler sostituito, col padding di pdftoppm riprodotto fedelmente.

    Restituisce una funzione per impostare il numero di pagine del PDF
    finto: sopra le nove il nome dei file cambia forma, ed e' la soglia
    che il codice deve continuare ad attraversare senza accorgersene.
    """
    stato = {"pagine": 3}
    invocazioni: list[list[str]] = []

    def run_finto(argv, **kwargs):
        invocazioni.append(list(argv))
        binario = Path(argv[0]).name
        if binario == "pdfinfo":
            return subprocess.CompletedProcess(argv, 0, f"Pages:          {stato['pagine']}\n", "")
        if binario == "pdftotext":
            pagina = int(argv[argv.index("-f") + 1])
            return subprocess.CompletedProcess(argv, 0, TESTO_PAGINE.get(pagina, ""), "")

        destinazione = Path(argv[-1])
        if "-singlefile" in argv:
            # il nome lo decide il chiamante, pdftoppm ci mette solo l'estensione
            destinazione.with_suffix(".jpg").write_bytes(b"\xff\xd8\xff")
        else:
            # senza -singlefile numera lui, allineando le cifre al totale
            cifre = len(str(stato["pagine"]))
            for n in range(1, stato["pagine"] + 1):
                nome = f"{destinazione.name}-{str(n).zfill(cifre)}.jpg"
                destinazione.with_name(nome).write_bytes(b"\xff\xd8\xff")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run_finto)
    monkeypatch.setattr(render_docs.shutil, "which", lambda nome: f"/usr/bin/{nome}")

    def imposta_pagine(quante: int) -> list[list[str]]:
        stato["pagine"] = quante
        return invocazioni

    imposta_pagine.invocazioni = invocazioni
    return imposta_pagine


@pytest.fixture
def progetto(tmp_path, monkeypatch, documento):
    """Un repository finto con un PDF sorgente e i due README."""
    docs = tmp_path / "profile" / "assets" / "docs"
    docs.mkdir(parents=True)
    (docs / f"{documento.slug}.pdf").write_bytes(b"%PDF-1.4" + b"0" * 2_000_000)
    (tmp_path / "profile" / "README.md").write_text(README, encoding="utf-8")
    (tmp_path / "profile" / "README.en.md").write_text(README, encoding="utf-8")
    monkeypatch.setattr(render_docs, "DOCS", docs)
    monkeypatch.setattr(render_docs, "PROFILE", tmp_path / "profile")
    monkeypatch.setattr(render_docs, "BUILD", tmp_path / "build")
    monkeypatch.setattr(render_docs, "DOCUMENTI", [documento])
    return tmp_path


def file_dichiarati(markdown: str) -> list[str]:
    """I nomi dei file che il README dichiara, da entrambi i lati del link.

    Il `src` e l'`href` nominano due tagli diversi della stessa pagina, e
    il prefisso lo scrive un modulo mentre il link lo compone l'altro:
    guardarne uno solo lascerebbe scoperta meta' della coppia.
    """
    import re

    trovati = re.findall(r'<a href="([^"]+)"><img src="([^"]+)"', markdown)
    return [Path(percorso).name for coppia in trovati for percorso in coppia]


# --- poppler ---------------------------------------------------------------


def test_conta_pagine_legge_il_numero_da_pdfinfo(poppler, tmp_path):
    poppler(7)
    assert render_docs.conta_pagine(tmp_path / "x.pdf") == 7


def test_conta_pagine_senza_riga_pages_e_un_errore(monkeypatch, tmp_path):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda argv, **kw: subprocess.CompletedProcess(argv, 0, "Title: niente\n", ""),
    )
    with pytest.raises(ValueError, match="numero di pagine"):
        render_docs.conta_pagine(tmp_path / "x.pdf")


def test_rasterizza_chiede_la_larghezza_e_la_qualita_indicate(poppler, tmp_path):
    invocazioni = poppler(2)
    render_docs.rasterizza(
        pdf=tmp_path / "x.pdf",
        destinazione=tmp_path / "out",
        prefisso="thumb",
        pagine=2,
        larghezza=400,
        qualita=88,
    )
    argv = invocazioni[0]
    assert argv[argv.index("-scale-to-x") + 1] == "400"
    assert "quality=88" in argv
    assert (tmp_path / "out" / "thumb-1.jpg").is_file()


def test_rasterizza_scrive_un_file_per_pagina(poppler, tmp_path):
    poppler(11)
    render_docs.rasterizza(
        pdf=tmp_path / "x.pdf",
        destinazione=tmp_path / "out",
        prefisso="thumb",
        pagine=11,
        larghezza=400,
        qualita=88,
    )
    scritti = sorted(f.name for f in (tmp_path / "out").iterdir())
    assert "thumb-9.jpg" in scritti
    assert "thumb-11.jpg" in scritti
    assert "thumb-09.jpg" not in scritti


def test_controlla_scritte_segnala_la_pagina_che_manca(tmp_path):
    (tmp_path / "thumb-1.jpg").write_bytes(b"\xff\xd8\xff")
    with pytest.raises(RuntimeError, match="thumb-2.jpg"):
        render_docs.controlla_scritte(
            destinazione=tmp_path, prefisso="thumb", pagine=2, pdf=tmp_path / "x.pdf"
        )


def test_strumenti_mancanti_elenca_i_binari_assenti(monkeypatch):
    monkeypatch.setattr(
        render_docs.shutil, "which", lambda nome: None if nome == "pdftoppm" else "/usr/bin/x"
    )
    assert render_docs.strumenti_mancanti() == ["pdftoppm"]


def test_strumenti_presenti_non_danno_mancanze(poppler):
    assert render_docs.strumenti_mancanti() == []


# --- testo alternativo -----------------------------------------------------


def test_alt_usa_il_titolo_stampato_sulla_pagina(poppler, progetto, documento):
    assert render_docs.alt_documento(documento, 2)[0].startswith("Agenti AI in azienda")


def test_alt_di_una_pagina_senza_testo_ripiega_sul_numero(poppler, progetto, documento):
    assert render_docs.alt_documento(documento, 3)[2] == "Pagina 3"


def test_alt_override_vince_sul_titolo_estratto(poppler, progetto):
    doc = render_docs.Documento(
        slug="x",
        titolo={"it": "t", "en": "t"},
        occhiello={"it": "o", "en": "o"},
        alt_override={1: "Scritto a mano"},
    )
    assert render_docs.alt_documento(doc, 1) == ["Scritto a mano"]


# --- main ------------------------------------------------------------------


def test_main_scrive_il_blocco_in_entrambe_le_lingue(progetto, poppler):
    assert render_docs.main() == 0
    it = (progetto / "profile" / "README.md").read_text(encoding="utf-8")
    en = (progetto / "profile" / "README.en.md").read_text(encoding="utf-8")
    assert "Titolo italiano" in it and "English title" not in it
    assert "English title" in en and "Titolo italiano" not in en


def test_main_linka_solo_file_che_esistono_davvero(progetto, poppler, documento):
    poppler(11)
    assert render_docs.main() == 0
    it = (progetto / "profile" / "README.md").read_text(encoding="utf-8")
    pagine = progetto / "profile" / "assets" / "docs" / documento.slug
    dichiarati = file_dichiarati(it)

    # undici pagine, miniatura piu' pagina piena per ciascuna
    assert len(dichiarati) == 22
    mancanti = [nome for nome in dichiarati if not (pagine / nome).is_file()]
    assert mancanti == []


def test_main_rasterizza_i_due_tagli_di_ogni_pagina(progetto, poppler, documento):
    render_docs.main()
    pagine = progetto / "profile" / "assets" / "docs" / documento.slug
    assert (pagine / f"{render_docs.PREFISSO_THUMB}-1.jpg").is_file()
    assert (pagine / f"{render_docs.PREFISSO_PAGE}-1.jpg").is_file()


def test_main_riporta_il_peso_reale_del_pdf(progetto, poppler):
    render_docs.main()
    it = (progetto / "profile" / "README.md").read_text(encoding="utf-8")
    assert "2.0 MB" in it


def test_main_si_ferma_se_poppler_non_e_installato(progetto, monkeypatch, capsys):
    monkeypatch.setattr(render_docs.shutil, "which", lambda nome: None)
    assert render_docs.main() == 1
    assert "poppler" in capsys.readouterr().err


def test_main_si_ferma_se_manca_il_pdf_sorgente(progetto, poppler, documento, capsys):
    (progetto / "profile" / "assets" / "docs" / f"{documento.slug}.pdf").unlink()
    assert render_docs.main() == 1
    assert f"{documento.slug}.pdf" in capsys.readouterr().err


def test_main_lascia_intatto_il_resto_del_readme(progetto, poppler):
    render_docs.main()
    it = (progetto / "profile" / "README.md").read_text(encoding="utf-8")
    assert "Testo che precede." in it
    assert "## Sezione che segue" in it

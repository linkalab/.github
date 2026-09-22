"""Il markup deve dire il vero sulle pagine che linka.

Il modulo non tocca il disco, quindi qui non c'e' niente da sostituire:
i test girano tutti sul codice vero. Quello che tengono fermo e' il
punto che sbaglia in silenzio, cioe' che la miniatura carichi il taglio
piccolo mentre il link porta a quello grande: invertirli raddoppierebbe
il peso del profilo senza cambiare niente a schermo.
"""

import pytest

import docs_markup

TESTO_COPERTINA = (
    "Agenti AI in azienda:\ncon quali credenziali\nstanno agendo?\n"
    "Se un agente AI usa le credenziali\n"
)
TESTO_SENZA_PUNTO = (
    "Least Privilege: dare\nall'agente solo cio'\nche gli serve\n"
    "Un agente che analizza i report di bilancio non\n"
)

README = """# Profilo

Testo che precede.

<!-- DOCS-LIST:START -->
vecchio contenuto
<!-- DOCS-LIST:END -->

## Sezione che segue
"""


@pytest.fixture
def documento():
    return docs_markup.Documento(
        slug="prova-carosello",
        titolo={"it": "Titolo italiano", "en": "English title"},
        occhiello={"it": "Caso studio", "en": "Case study"},
    )


# --- titolo della pagina ---------------------------------------------------


def test_titolo_unisce_le_righe_spezzate_della_copertina():
    assert (
        docs_markup.titolo_pagina(TESTO_COPERTINA)
        == "Agenti AI in azienda: con quali credenziali stanno agendo?"
    )


def test_titolo_si_ferma_prima_del_corpo_quando_nessuna_riga_chiude_la_frase():
    atteso = "Least Privilege: dare all'agente solo cio' che gli serve"
    assert docs_markup.titolo_pagina(TESTO_SENZA_PUNTO) == atteso


def test_titolo_di_una_pagina_senza_testo_e_vuoto():
    assert docs_markup.titolo_pagina("") == ""


def test_titolo_ignora_le_righe_vuote_e_i_rientri():
    assert docs_markup.titolo_pagina("\n   \n  Solo questa.  \n\n") == "Solo questa."


def test_titolo_piu_lungo_del_massimo_tronca_a_parola_intera():
    titolo = docs_markup.titolo_pagina("parola " * 30)
    assert len(titolo) <= docs_markup.ALT_MAX
    assert titolo.endswith("parola")


# --- attributi HTML --------------------------------------------------------


def test_attributo_neutralizza_le_virgolette_e_i_tag():
    assert docs_markup.attributo('a "b" <c> & d') == "a &quot;b&quot; &lt;c&gt; &amp; d"


def test_attributo_non_ri_neutralizza_le_entita_che_ha_appena_scritto():
    # la & va sostituita per prima, altrimenti &lt; diventa &amp;lt;
    assert docs_markup.attributo("<") == "&lt;"


# --- miniature -------------------------------------------------------------


def test_miniatura_carica_il_taglio_piccolo_e_linka_quello_grande(documento):
    html = docs_markup.miniatura(doc=documento, pagina=2, alt="Pagina due")
    assert f'src="{docs_markup.RAW}/{documento.slug}/thumb-2.jpg"' in html
    assert f'href="{docs_markup.BLOB}/{documento.slug}/page-2.jpg"' in html


def test_miniatura_non_pagina_il_numero_come_fa_pdftoppm(documento):
    # i file li scrive `-singlefile` col nome esatto: se qui comparisse
    # thumb-09.jpg il README linkerebbe un file che nessuno ha scritto
    html = docs_markup.miniatura(doc=documento, pagina=9, alt="nona")
    assert "thumb-9.jpg" in html and "thumb-09.jpg" not in html


def test_miniatura_porta_il_titolo_come_testo_alternativo(documento):
    html = docs_markup.miniatura(doc=documento, pagina=1, alt='Titolo "citato"')
    assert 'alt="Titolo &quot;citato&quot;"' in html


# --- blocco del documento --------------------------------------------------


def test_blocco_ha_una_miniatura_per_pagina(documento):
    html = docs_markup.blocco_documento(
        doc=documento, lang="it", alt=["uno", "due", "tre"], peso_mb=4.25
    )
    assert html.count("<img ") == 3
    assert "3 pagine" in html


def test_blocco_linka_il_pdf_col_suo_peso(documento):
    html = docs_markup.blocco_documento(doc=documento, lang="it", alt=["uno"], peso_mb=9.26)
    assert f'href="{docs_markup.BLOB}/{documento.slug}.pdf"' in html
    assert "9.3 MB" in html


def test_blocco_inglese_dichiara_che_il_documento_e_in_italiano(documento):
    html = docs_markup.blocco_documento(doc=documento, lang="en", alt=["uno"], peso_mb=1.0)
    assert "in Italian" in html
    assert "English title" in html


def test_blocco_resta_chiuso_finche_non_lo_si_apre(documento):
    html = docs_markup.blocco_documento(doc=documento, lang="it", alt=["uno"], peso_mb=1.0)
    assert html.startswith("<details>")
    assert "<details open" not in html


# --- marker ----------------------------------------------------------------


def test_marker_sostituisce_solo_il_contenuto_fra_i_due_segni():
    nuovo = docs_markup.sostituisci_marker(markdown=README, blocco="BLOCCO")
    assert "vecchio contenuto" not in nuovo
    assert "BLOCCO" in nuovo
    assert "Testo che precede." in nuovo
    assert "## Sezione che segue" in nuovo


def test_marker_assenti_sono_un_errore():
    with pytest.raises(ValueError, match="marker"):
        docs_markup.sostituisci_marker(markdown="# README senza marker", blocco="BLOCCO")

"""L'anteprima autonoma vale solo se non fa richieste di rete.

E' la condizione per pubblicarla come artifact: una pagina che prova a
scaricare un badge mostra un buco al posto del badge, e il buco sembra un
difetto del README invece che del contenitore. Da qui i due controlli che
lo script fa e che questi test esercitano: nessuna immagine remota
sopravvissuta all'incorporamento, e nessun badge ambiguo prima di
incorporarlo.
"""

import base64
import re

import pytest
import requests

import build_artifact
from conftest import RispostaFinta

BADGE_URL = "https://img.shields.io/badge/Python-3776AB"
BADGE_ALTRO = "https://img.shields.io/badge/AWS-232F3E"
SVG = b"<svg xmlns='http://www.w3.org/2000/svg'/>"

MD = f"""# Linkalab

![Python]({BADGE_URL})
"""

HTML = f"""<h1>Linkalab</h1>
<picture>
<source media="(prefers-color-scheme: dark)" srcset="{build_artifact.RAW}assets/b-dark.png">
<img alt="Linkalab, AI su misura" src="{build_artifact.RAW}assets/b-light.png">
</picture>
<a href="README.en.md"><img src="{build_artifact.RAW}assets/flag-us.png" alt="English"></a>
<a href="https://python.org"><img src="https://camo.githubusercontent.com/9f" alt="Python"></a>
"""


@pytest.fixture
def progetto(tmp_path, monkeypatch):
    """Un repository minimo: i due README, i banner, la bandiera, il modello."""
    assets = tmp_path / "profile" / "assets"
    assets.mkdir(parents=True)
    for lingua in ("it", "en"):
        (tmp_path / "profile" / f"README{'' if lingua == 'it' else '.en'}.md").write_text(
            MD, encoding="utf-8"
        )
        for variante in ("light", "dark"):
            (assets / f"banner-{lingua}-{variante}.png").write_bytes(
                f"png-{lingua}-{variante}".encode()
            )
    (assets / "flag-us.png").write_bytes(b"png-bandiera")

    build = tmp_path / "build"
    build.mkdir()
    (build / "artifact.html.tpl").write_text(
        "<html><body>__PAGINE__</body></html>", encoding="utf-8"
    )
    monkeypatch.setattr(build_artifact, "ROOT", tmp_path)
    monkeypatch.setattr(build_artifact, "BUILD", build)
    monkeypatch.setattr(build_artifact, "OUT", build / "anteprima-readme.html")
    return tmp_path


@pytest.fixture
def rete(monkeypatch):
    """GitHub e shields.io sostituiti; restituisce il registro delle richieste."""
    registro = {"post": [], "get": []}

    def post_finto(url, json, timeout):
        registro["post"].append(json["text"])
        return RispostaFinta(testo=HTML)

    def get_finto(url, timeout):
        registro["get"].append(url)
        return RispostaFinta(contenuto=SVG)

    monkeypatch.setattr(requests, "post", post_finto)
    monkeypatch.setattr(requests, "get", get_finto)
    return registro


def src_di(html: str, alt: str) -> str:
    tag = re.search(rf'<img[^>]*alt="{re.escape(alt)}"[^>]*>', html)
    assert tag, f"nessuna img con alt {alt!r} in {html}"
    return re.search(r'src="([^"]*)"', tag.group(0)).group(1)


def decodifica(data_uri: str) -> bytes:
    return base64.b64decode(data_uri.split(",", 1)[1])


# --- data_uri -------------------------------------------------------------


def test_data_uri_dichiara_il_tipo_png(tmp_path):
    file = tmp_path / "x.png"
    file.write_bytes(b"contenuto")

    assert build_artifact.data_uri(file).startswith("data:image/png;base64,")


def test_data_uri_trasporta_i_byte_del_file(tmp_path):
    file = tmp_path / "x.png"
    file.write_bytes(b"\x89PNG\r\n\x1a\n dati binari")

    assert decodifica(build_artifact.data_uri(file)) == b"\x89PNG\r\n\x1a\n dati binari"


def test_data_uri_gestisce_un_file_vuoto(tmp_path):
    file = tmp_path / "vuoto.png"
    file.write_bytes(b"")

    assert build_artifact.data_uri(file) == "data:image/png;base64,"


# --- badge_inline ---------------------------------------------------------


def test_badge_inline_restituisce_lo_svg_scaricato_come_data_uri(rete):
    risultato = build_artifact.badge_inline(BADGE_URL, {})

    assert risultato.startswith("data:image/svg+xml;base64,")
    assert decodifica(risultato) == SVG


def test_badge_inline_scarica_una_volta_sola_lo_stesso_badge(rete):
    cache: dict[str, str] = {}

    build_artifact.badge_inline(BADGE_URL, cache)
    build_artifact.badge_inline(BADGE_URL, cache)

    assert rete["get"] == [BADGE_URL]


def test_badge_inline_distingue_badge_diversi(rete):
    cache: dict[str, str] = {}

    build_artifact.badge_inline(BADGE_URL, cache)
    build_artifact.badge_inline(BADGE_ALTRO, cache)

    assert rete["get"] == [BADGE_URL, BADGE_ALTRO]
    assert set(cache) == {BADGE_URL, BADGE_ALTRO}


def test_badge_inline_propaga_l_errore_di_shields(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: RispostaFinta(stato=503))

    with pytest.raises(requests.HTTPError):
        build_artifact.badge_inline(BADGE_URL, {})


# --- rendi ----------------------------------------------------------------


def test_rendi_chiede_a_github_il_markdown_in_modalita_gfm(monkeypatch):
    visto = {}

    def post_finto(url, json, timeout):
        visto.update(url=url, json=json, timeout=timeout)
        return RispostaFinta(testo="<h1>x</h1>")

    monkeypatch.setattr(requests, "post", post_finto)

    assert build_artifact.rendi("# x") == "<h1>x</h1>"
    assert visto["url"] == "https://api.github.com/markdown"
    assert visto["json"] == {"text": "# x", "mode": "gfm"}
    assert visto["timeout"] == 30


def test_rendi_propaga_l_errore_di_github(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: RispostaFinta(stato=500))

    with pytest.raises(requests.HTTPError):
        build_artifact.rendi("# x")


# --- prepara: il banner ---------------------------------------------------


def test_prepara_sostituisce_il_picture_con_le_due_immagini_del_tema(progetto, rete):
    html = build_artifact.prepara("it", {})

    assert "<picture>" not in html
    assert decodifica(src_di(html, "Linkalab, AI su misura")) == b"png-it-light"
    assert decodifica(src_di(html, "")) == b"png-it-dark"


def test_prepara_prende_i_banner_della_lingua_richiesta(progetto, rete):
    html = build_artifact.prepara("en", {})

    assert decodifica(src_di(html, "Linkalab, AI su misura")) == b"png-en-light"


def test_prepara_riporta_l_alt_del_banner_sulla_variante_chiara(progetto, rete):
    html = build_artifact.prepara("it", {})

    assert 'class="chiaro" src="data:image/png;base64,' in html
    assert 'alt="Linkalab, AI su misura"' in html


def test_prepara_lascia_muta_la_variante_scura(progetto, rete):
    """Le due img dicono la stessa cosa: la seconda e' decorativa."""
    html = build_artifact.prepara("it", {})

    scura = re.search(r'<img class="scuro"[^>]*>', html).group(0)
    assert 'alt=""' in scura


def test_prepara_accetta_un_banner_senza_testo_alternativo(progetto, monkeypatch):
    senza_alt = f'<picture><img src="{build_artifact.RAW}assets/b.png"></picture>'
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: RispostaFinta(testo=senza_alt)
    )

    html = build_artifact.prepara("it", {})

    assert html.count('alt=""') == 2


# --- prepara: i badge -----------------------------------------------------


def test_prepara_incorpora_il_badge_riconoscendolo_dall_alt(progetto, rete):
    html = build_artifact.prepara("it", {})

    assert decodifica(src_di(html, "Python")) == SVG


def test_prepara_rifiuta_due_badge_diversi_con_lo_stesso_alt(progetto, rete):
    (progetto / "profile" / "README.md").write_text(
        f"![Cloud]({BADGE_URL})\n![Cloud]({BADGE_ALTRO})\n", encoding="utf-8"
    )

    with pytest.raises(RuntimeError) as errore:
        build_artifact.prepara("it", {})

    messaggio = str(errore.value)
    assert '"Cloud"' in messaggio
    assert BADGE_URL in messaggio and BADGE_ALTRO in messaggio
    assert "profile/README.md" in messaggio


def test_prepara_accetta_lo_stesso_badge_ripetuto(progetto, rete):
    (progetto / "profile" / "README.md").write_text(
        f"![Python]({BADGE_URL})\n![Python]({BADGE_URL})\n", encoding="utf-8"
    )

    assert build_artifact.prepara("it", {}) is not None


def test_prepara_riusa_la_cache_dei_badge_fra_le_due_lingue(progetto, rete):
    cache: dict[str, str] = {}

    build_artifact.prepara("it", cache)
    build_artifact.prepara("en", cache)

    assert rete["get"] == [BADGE_URL]


# --- prepara: le immagini del repository ----------------------------------


def test_prepara_incorpora_le_immagini_presenti_in_locale(progetto, rete):
    html = build_artifact.prepara("it", {})

    assert decodifica(src_di(html, "English")) == b"png-bandiera"


def test_prepara_si_ferma_se_un_immagine_del_repository_non_esiste(progetto, rete):
    (progetto / "profile" / "assets" / "flag-us.png").unlink()

    with pytest.raises(RuntimeError, match="1 immagini non incorporate"):
        build_artifact.prepara("it", {})


def test_prepara_si_ferma_su_un_immagine_remota_che_non_sa_incorporare(progetto, monkeypatch):
    estranea = '<img src="https://esempio.invalid/x.png" alt="Estranea">'
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: RispostaFinta(testo=HTML + estranea)
    )
    monkeypatch.setattr(requests, "get", lambda *a, **k: RispostaFinta(contenuto=SVG))

    with pytest.raises(RuntimeError, match="richieste di rete"):
        build_artifact.prepara("it", {})


def test_prepara_lascia_stare_un_immagine_senza_sorgente(progetto, monkeypatch):
    monkeypatch.setattr(
        requests, "post", lambda *a, **k: RispostaFinta(testo=HTML + "<img>")
    )
    monkeypatch.setattr(requests, "get", lambda *a, **k: RispostaFinta(contenuto=SVG))

    assert "<img>" in build_artifact.prepara("it", {})


# --- prepara: i link ------------------------------------------------------


def test_prepara_apre_i_link_fuori_dall_anteprima(progetto, rete):
    html = build_artifact.prepara("it", {})

    assert html.count('<a target="_blank" rel="noopener" href=') == 2
    assert "<a href=" not in html


def test_prepara_toglie_il_prefisso_di_raw_githubusercontent(progetto, rete):
    html = build_artifact.prepara("it", {})

    assert build_artifact.RAW not in html


# --- main -----------------------------------------------------------------


def test_main_scrive_l_anteprima_e_riesce(progetto, rete):
    assert build_artifact.main() == 0
    assert build_artifact.OUT.is_file()


def test_main_mette_una_pagina_per_lingua_nel_modello(progetto, rete):
    build_artifact.main()

    pagina = build_artifact.OUT.read_text(encoding="utf-8")
    assert "__PAGINE__" not in pagina
    assert pagina.count('<article class="pagina"') == 2
    assert 'data-lingua="it"' in pagina
    assert 'data-lingua="en"' in pagina


def test_main_mostra_l_italiano_e_nasconde_l_inglese(progetto, rete):
    build_artifact.main()

    pagina = build_artifact.OUT.read_text(encoding="utf-8")
    italiano = re.search(r'<article class="pagina" data-lingua="it" ([^>]*)>', pagina)
    inglese = re.search(r'<article class="pagina" data-lingua="en" ([^>]*)>', pagina)
    assert italiano.group(1).strip() == ""
    assert inglese.group(1).strip() == "hidden"


def test_main_scarica_ogni_badge_una_volta_sola_per_tutte_le_lingue(progetto, rete):
    build_artifact.main()

    assert rete["get"] == [BADGE_URL]


def test_main_riporta_percorso_e_peso_dell_anteprima(progetto, rete, capsys):
    build_artifact.main()

    assert capsys.readouterr().out.strip().startswith("build/anteprima-readme.html")


def test_main_si_ferma_se_github_non_renderizza(progetto, monkeypatch, capsys):
    monkeypatch.setattr(requests, "post", lambda *a, **k: RispostaFinta(stato=500))

    assert build_artifact.main() == 1
    assert "render fallito" in capsys.readouterr().err


def test_main_non_scrive_l_anteprima_quando_il_render_fallisce(progetto, monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: RispostaFinta(stato=500))

    build_artifact.main()

    assert not build_artifact.OUT.exists()

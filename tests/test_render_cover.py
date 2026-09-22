"""La copertina LinkedIn ha vincoli che il banner del README non ha.

Il formato e' quasi 6:1, il logo della pagina copre l'angolo in basso a
sinistra e la app mobile taglia i lati: i test fissano le misure e il
riuso del copy, oltre al controllo preventivo degli asset che vale qui
come per il banner.
"""

import pytest

import render_banner
import render_cover

TEMPLATE = "<body style='background:__BG__'><p>__EYEBROW__</p><h1>__PAYOFF__</h1></body>"


@pytest.fixture
def build(tmp_path, monkeypatch):
    """Una `build/` completa: template e font tutti presenti."""
    monkeypatch.setattr(render_cover, "BUILD", tmp_path)
    monkeypatch.setattr(render_cover, "OUT", tmp_path / "profile" / "assets")
    (tmp_path / "cover.html.tpl").write_text(TEMPLATE, encoding="utf-8")
    for nome in render_cover.ASSET_RICHIESTI:
        (tmp_path / nome).write_bytes(b"asset")
    return tmp_path


# --- controllo degli asset ------------------------------------------------


def test_controlla_asset_non_segnala_nulla_quando_ci_sono_tutti(build):
    assert render_cover.controlla_asset() == []


def test_controlla_asset_elenca_solo_quelli_mancanti(build):
    (build / "manrope-400.woff2").unlink()

    assert render_cover.controlla_asset() == ["manrope-400.woff2"]


def test_la_copertina_chiede_meno_asset_del_banner():
    assert set(render_cover.ASSET_RICHIESTI) < set(render_banner.ASSET_RICHIESTI)


# --- render ---------------------------------------------------------------


def test_render_applica_il_fondo_della_variante(build, chrome):
    render_cover.render(lang="it", variant="dark", template=TEMPLATE, chrome="chrome")

    pagina = (build / "_cover-it-dark.html").read_text(encoding="utf-8")
    assert render_banner.VARIANTS["dark"] in pagina
    assert render_banner.VARIANTS["light"] not in pagina


def test_render_riusa_il_copy_del_banner(build, chrome):
    render_cover.render(lang="en", variant="light", template=TEMPLATE, chrome="chrome")

    pagina = (build / "_cover-en-light.html").read_text(encoding="utf-8")
    assert render_banner.COPY["en"]["eyebrow"] in pagina
    assert render_banner.COPY["en"]["payoff"] in pagina


def test_render_non_lascia_segnaposto_nella_pagina(build, chrome):
    render_cover.render(lang="it", variant="light", template=TEMPLATE, chrome="chrome")

    pagina = (build / "_cover-it-light.html").read_text(encoding="utf-8")
    assert "__" not in pagina


def test_render_nomina_il_png_per_linkedin(build, chrome):
    out = render_cover.render(lang="en", variant="dark", template=TEMPLATE, chrome="chrome")

    assert out == build / "profile" / "assets" / "linkedin-cover-en-dark.png"
    assert out.is_file()


def test_render_scatta_sulle_misure_che_linkedin_chiede(build, chrome):
    render_cover.render(lang="it", variant="light", template=TEMPLATE, chrome="chrome")

    argv = chrome[0]
    assert "--window-size=1128,191" in argv
    assert f"--force-device-scale-factor={render_cover.SCALA}" in argv
    assert argv[-1] == (build / "_cover-it-light.html").as_uri()


def test_le_misure_restano_diverse_da_quelle_del_banner():
    assert (render_cover.WIDTH, render_cover.HEIGHT) != (
        render_banner.WIDTH,
        render_banner.HEIGHT,
    )


# --- main -----------------------------------------------------------------


def test_main_si_ferma_se_chrome_non_e_installato(senza_chrome, capsys):
    assert render_cover.main() == 1
    assert "nessun binario Chrome" in capsys.readouterr().err


def test_main_si_ferma_prima_di_renderizzare_se_manca_un_font(build, chrome, capsys):
    (build / "space-grotesk-700.woff2").unlink()

    assert render_cover.main() == 1
    assert chrome == []


def test_main_nomina_gli_asset_mancanti_e_dice_dove_prenderli(build, chrome, capsys):
    (build / "jetbrains-mono-500.woff2").unlink()

    render_cover.main()

    err = capsys.readouterr().err
    assert "build/jetbrains-mono-500.woff2" in err
    assert "Design System" in err


def test_main_genera_le_quattro_combinazioni(build, chrome):
    assert render_cover.main() == 0

    prodotti = sorted(p.name for p in (build / "profile" / "assets").iterdir())
    assert prodotti == [
        "linkedin-cover-en-dark.png",
        "linkedin-cover-en-light.png",
        "linkedin-cover-it-dark.png",
        "linkedin-cover-it-light.png",
    ]


def test_main_crea_la_cartella_di_destinazione_se_manca(build, chrome, monkeypatch):
    destinazione = build / "mai" / "vista"
    monkeypatch.setattr(render_cover, "OUT", destinazione)

    assert render_cover.main() == 0
    assert destinazione.is_dir()


def test_main_riporta_una_riga_per_copertina(build, chrome, capsys):
    render_cover.main()

    righe = capsys.readouterr().out.strip().splitlines()
    assert len(righe) == 4
    assert all(riga.endswith("KB") for riga in righe)

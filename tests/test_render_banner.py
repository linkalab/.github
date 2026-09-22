"""Il banner esce sbagliato in silenzio se i font mancano: e' il rischio da coprire.

Chrome renderizza comunque, con i font di sistema e un'immagine rotta al
posto del logo. Il grosso di questi test verifica quindi il controllo
preventivo degli asset, oltre alla sostituzione del copy e alle due
varianti cromatiche.
"""

import pytest

import render_banner

TEMPLATE = (
    "<body class='__LAYOUT__' style='background:__BG__'>"
    "<p>__EYEBROW__</p><h1>__PAYOFF__</h1></body>"
)


@pytest.fixture
def build(tmp_path, monkeypatch):
    """Una `build/` completa: template, font e logo tutti presenti."""
    monkeypatch.setattr(render_banner, "BUILD", tmp_path)
    monkeypatch.setattr(render_banner, "OUT", tmp_path / "profile" / "assets")
    (tmp_path / "banner.html.tpl").write_text(TEMPLATE, encoding="utf-8")
    for nome in render_banner.ASSET_RICHIESTI:
        (tmp_path / nome).write_bytes(b"asset")
    return tmp_path


# --- controllo degli asset ------------------------------------------------


def test_controlla_asset_non_segnala_nulla_quando_ci_sono_tutti(build):
    assert render_banner.controlla_asset() == []


def test_controlla_asset_elenca_solo_quelli_mancanti(build):
    (build / "manrope-400.woff2").unlink()
    (build / "linkalab-logo-white.png").unlink()

    assert render_banner.controlla_asset() == [
        "linkalab-logo-white.png",
        "manrope-400.woff2",
    ]


def test_controlla_asset_li_segnala_tutti_su_una_build_vuota(tmp_path, monkeypatch):
    monkeypatch.setattr(render_banner, "BUILD", tmp_path)

    assert render_banner.controlla_asset() == render_banner.ASSET_RICHIESTI


def test_controlla_asset_non_accetta_una_cartella_al_posto_di_un_font(tmp_path, monkeypatch):
    monkeypatch.setattr(render_banner, "BUILD", tmp_path)
    for nome in render_banner.ASSET_RICHIESTI:
        (tmp_path / nome).write_bytes(b"asset")
    (tmp_path / "manrope-400.woff2").unlink()
    (tmp_path / "manrope-400.woff2").mkdir()

    assert render_banner.controlla_asset() == ["manrope-400.woff2"]


# --- render ---------------------------------------------------------------


def test_render_applica_il_fondo_della_variante(build, chrome):
    render_banner.render(lang="it", variant="dark", template=TEMPLATE, chrome="chrome")

    pagina = (build / "_banner-it-dark.html").read_text(encoding="utf-8")
    assert render_banner.VARIANTS["dark"] in pagina
    assert render_banner.VARIANTS["light"] not in pagina


def test_render_applica_il_copy_della_lingua(build, chrome):
    render_banner.render(lang="en", variant="light", template=TEMPLATE, chrome="chrome")

    pagina = (build / "_banner-en-light.html").read_text(encoding="utf-8")
    assert render_banner.COPY["en"]["eyebrow"] in pagina
    assert render_banner.COPY["en"]["payoff"] in pagina
    assert render_banner.COPY["it"]["payoff"] not in pagina


def test_render_non_lascia_segnaposto_nella_pagina(build, chrome):
    render_banner.render(lang="it", variant="light", template=TEMPLATE, chrome="chrome")

    pagina = (build / "_banner-it-light.html").read_text(encoding="utf-8")
    assert "__" not in pagina


def test_render_senza_layout_resta_sulla_colonna_sinistra(build, chrome):
    render_banner.render(lang="it", variant="dark", template=TEMPLATE, chrome="chrome")

    pagina = (build / "_banner-it-dark.html").read_text(encoding="utf-8")
    assert "mirror" not in pagina


def test_render_right_specchia_il_layout_in_un_file_affiancato(build, chrome):
    out = render_banner.render(
        lang="it", variant="dark", template=TEMPLATE, chrome="chrome", layout="right"
    )

    assert out == build / "profile" / "assets" / "banner-it-dark-right.png"
    pagina = (build / "_banner-it-dark-right.html").read_text(encoding="utf-8")
    assert "class='mirror'" in pagina


def test_render_restituisce_il_png_nominato_per_lingua_e_variante(build, chrome):
    out = render_banner.render(lang="en", variant="dark", template=TEMPLATE, chrome="chrome")

    assert out == build / "profile" / "assets" / "banner-en-dark.png"
    assert out.is_file()


def test_render_scatta_a_densita_doppia_sulle_misure_del_banner(build, chrome):
    render_banner.render(lang="it", variant="light", template=TEMPLATE, chrome="chrome")

    argv = chrome[0]
    assert "--force-device-scale-factor=2" in argv
    assert f"--window-size={render_banner.WIDTH},{render_banner.HEIGHT}" in argv
    assert argv[-1] == (build / "_banner-it-light.html").as_uri()


def test_render_tiene_separate_le_pagine_delle_quattro_combinazioni(build, chrome):
    for lang in render_banner.COPY:
        for variant in render_banner.VARIANTS:
            render_banner.render(
                lang=lang, variant=variant, template=TEMPLATE, chrome="chrome"
            )

    pagine = sorted(p.name for p in build.glob("_banner-*.html"))
    assert pagine == [
        "_banner-en-dark.html",
        "_banner-en-light.html",
        "_banner-it-dark.html",
        "_banner-it-light.html",
    ]


# --- copy e varianti ------------------------------------------------------


def test_le_due_lingue_hanno_copy_diverso():
    assert render_banner.COPY["it"] != render_banner.COPY["en"]


def test_le_due_varianti_hanno_fondi_diversi():
    assert render_banner.VARIANTS["light"] != render_banner.VARIANTS["dark"]


def test_i_due_layout_scrivono_su_nomi_file_diversi():
    suffissi = {l["suffisso"] for l in render_banner.LAYOUTS.values()}
    assert len(suffissi) == len(render_banner.LAYOUTS)


# --- main -----------------------------------------------------------------


def test_main_si_ferma_se_chrome_non_e_installato(senza_chrome, capsys):
    assert render_banner.main() == 1
    assert "nessun binario Chrome" in capsys.readouterr().err


def test_main_si_ferma_prima_di_renderizzare_se_manca_un_font(build, chrome, capsys):
    (build / "space-grotesk-700.woff2").unlink()

    assert render_banner.main() == 1
    assert chrome == []


def test_main_nomina_gli_asset_mancanti_e_dice_dove_prenderli(build, chrome, capsys):
    (build / "space-grotesk-700.woff2").unlink()

    render_banner.main()

    err = capsys.readouterr().err
    assert "build/space-grotesk-700.woff2" in err
    assert "Design System" in err


def test_main_genera_le_otto_combinazioni(build, chrome):
    assert render_banner.main() == 0

    prodotti = sorted(p.name for p in (build / "profile" / "assets").iterdir())
    assert prodotti == [
        "banner-en-dark-right.png",
        "banner-en-dark.png",
        "banner-en-light-right.png",
        "banner-en-light.png",
        "banner-it-dark-right.png",
        "banner-it-dark.png",
        "banner-it-light-right.png",
        "banner-it-light.png",
    ]


def test_main_crea_la_cartella_di_destinazione_se_manca(build, chrome, monkeypatch):
    destinazione = build / "mai" / "vista"
    monkeypatch.setattr(render_banner, "OUT", destinazione)

    assert render_banner.main() == 0
    assert destinazione.is_dir()


def test_main_riporta_una_riga_per_banner(build, chrome, capsys):
    render_banner.main()

    righe = capsys.readouterr().out.strip().splitlines()
    assert len(righe) == 8
    assert all(riga.endswith("KB") for riga in righe)

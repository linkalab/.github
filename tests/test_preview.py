"""L'anteprima serve a vedere la pagina prima di pubblicarla: deve mostrare quella vera.

Due cose la rendono utile e sono quelle sotto test: il markdown passa dal
renderer di GitHub (non da un'imitazione locale) e i banner puntano ai
file del repository, che su raw.githubusercontent non esistono ancora.
"""

import pytest
import requests

import preview
from conftest import RispostaFinta, argv_dello_scatto


@pytest.fixture
def progetto(tmp_path, monkeypatch):
    """Un repository minimo con i due README e la cartella degli asset."""
    (tmp_path / "profile" / "assets").mkdir(parents=True)
    (tmp_path / "profile" / "README.md").write_text(
        f"# Profilo\n\n![banner]({preview.RAW}assets/banner-it-light.png)\n",
        encoding="utf-8",
    )
    (tmp_path / "profile" / "README.en.md").write_text(
        f"# Profile\n\n![banner]({preview.RAW}assets/banner-en-light.png)\n",
        encoding="utf-8",
    )
    build = tmp_path / "build"
    build.mkdir()
    monkeypatch.setattr(preview, "ROOT", tmp_path)
    monkeypatch.setattr(preview, "BUILD", build)
    return tmp_path


@pytest.fixture
def github(monkeypatch):
    """L'API markdown di GitHub: registra le richieste, risponde HTML."""
    richieste: list[dict] = []

    def post_finto(url, json, timeout):
        richieste.append({"url": url, "json": json, "timeout": timeout})
        return RispostaFinta(testo=f"<h1>{json['text'][:40]}</h1>")

    monkeypatch.setattr(requests, "post", post_finto)
    return richieste


# --- render ---------------------------------------------------------------


def test_render_chiede_a_github_il_markdown_in_modalita_gfm(github):
    preview.render("# Ciao")

    assert github[0]["url"] == "https://api.github.com/markdown"
    assert github[0]["json"] == {"text": "# Ciao", "mode": "gfm"}


def test_render_restituisce_l_html_della_risposta(github):
    assert preview.render("# Ciao") == "<h1># Ciao</h1>"


def test_render_non_resta_appeso_se_github_non_risponde(github):
    preview.render("# Ciao")

    assert github[0]["timeout"] == 30


def test_render_propaga_l_errore_di_github(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: RispostaFinta(stato=502))

    with pytest.raises(requests.HTTPError):
        preview.render("# Ciao")


# --- shoot ----------------------------------------------------------------


def test_shoot_scatta_alla_larghezza_richiesta(tmp_path, chrome):
    pagina = tmp_path / "p.html"
    pagina.write_text("<p>x</p>", encoding="utf-8")

    preview.shoot(page=pagina, out=tmp_path / "o.png", width=375, chrome="chrome")

    assert "--window-size=375,2400" in chrome[0]
    assert chrome[0][-1] == pagina.as_uri()


def test_shoot_produce_il_file_richiesto(tmp_path, chrome):
    pagina = tmp_path / "p.html"
    pagina.write_text("<p>x</p>", encoding="utf-8")
    out = tmp_path / "o.png"

    preview.shoot(page=pagina, out=out, width=1280, chrome="chrome")

    assert out.is_file()


# --- main -----------------------------------------------------------------


def test_main_si_ferma_se_chrome_non_e_installato(senza_chrome, capsys):
    assert preview.main() == 1
    assert "nessun binario Chrome" in capsys.readouterr().err


def test_main_scatta_le_due_lingue_alle_due_larghezze(progetto, github, chrome):
    assert preview.main() == 0

    prodotti = sorted(p.name for p in (progetto / "build").glob("preview-*.png"))
    assert prodotti == [
        "preview-en-1280.png",
        "preview-en-375.png",
        "preview-it-1280.png",
        "preview-it-375.png",
    ]


def test_main_ripunta_i_banner_ai_file_locali(progetto, github, chrome):
    preview.main()

    assert preview.RAW not in github[0]["json"]["text"]
    assert "assets/banner-it-light.png" in github[0]["json"]["text"]


def test_main_manda_a_github_entrambi_i_readme(progetto, github, chrome):
    preview.main()

    inviati = [r["json"]["text"] for r in github]
    assert len(inviati) == 2
    assert inviati[0].startswith("# Profilo")
    assert inviati[1].startswith("# Profile")


def test_main_avvolge_l_html_nel_foglio_di_stile_di_github(progetto, github, chrome):
    preview.main()

    pagina = (progetto / "build" / "_preview-it.html").read_text(encoding="utf-8")
    assert "<meta charset='utf-8'>" in pagina
    assert "max-width:1012px" in pagina
    assert "<div class='box'><h1># Profilo" in pagina


def test_main_collega_le_immagini_del_repository_alla_pagina(progetto, github, chrome):
    preview.main()

    link = progetto / "build" / "assets"
    assert link.is_symlink()
    assert link.resolve() == (progetto / "profile" / "assets").resolve()


def test_main_sostituisce_un_collegamento_rotto_lasciato_da_un_giro_precedente(
    progetto, github, chrome
):
    link = progetto / "build" / "assets"
    link.symlink_to(progetto / "sparita")
    assert not link.exists()

    assert preview.main() == 0
    assert link.resolve() == (progetto / "profile" / "assets").resolve()


def test_main_riusa_un_collegamento_gia_valido(progetto, github, chrome):
    link = progetto / "build" / "assets"
    link.symlink_to(progetto / "profile" / "assets")

    assert preview.main() == 0
    assert link.is_symlink()


def test_main_elenca_gli_screenshot_prodotti(progetto, github, chrome, capsys):
    preview.main()

    righe = capsys.readouterr().out.strip().splitlines()
    assert righe == [
        "build/preview-it-1280.png",
        "build/preview-it-375.png",
        "build/preview-en-1280.png",
        "build/preview-en-375.png",
    ]


def test_main_fotografa_la_pagina_della_lingua_giusta(progetto, github, chrome):
    preview.main()

    argv = argv_dello_scatto(chrome, str(progetto / "build" / "preview-en-375.png"))
    assert argv[-1] == (progetto / "build" / "_preview-en.html").as_uri()

"""Le bandiere sono disegnate, non scaricate: la specifica e' la bandiera reale.

I test controllano le proporzioni ufficiali (3:2 per l'Italia, 19:10 per
gli Stati Uniti), il numero di elementi araldici (tredici strisce,
cinquanta stelle) e i colori, perche' e' quello che l'immagine deve
dire. Un test che si limitasse a "l'SVG non e' vuoto" passerebbe anche
con una bandiera sbagliata.
"""

import math
import re
from itertools import pairwise

import pytest

import render_flags

VERDE, BIANCO_IT, ROSSO_IT = "#008C45", "#F4F5F0", "#CD212A"
ROSSO_US, BLU_US, BIANCO = "#B31942", "#0A3161", "#FFFFFF"

# le coordinate escono nell'SVG con due decimali: nessun confronto
# geometrico puo' essere piu' stretto di cosi'
PRECISIONE = 0.01

# il centro di una stella si ricava dal suo bounding box, cioe' da due
# vertici gia' arrotondati: la stima porta con se' mezzo passo di
# quantizzazione per vertice
ERRORE_CENTRO = PRECISIONE


def vertici(polygon: str) -> list[tuple[float, float]]:
    grezzi = re.search(r'points="([^"]+)"', polygon).group(1)
    return [(float(p.split(",")[0]), float(p.split(",")[1])) for p in grezzi.split()]


def rettangoli(svg: str) -> list[dict[str, str]]:
    trovati = []
    for corpo in re.findall(r"<rect([^>]*)/>", svg):
        trovati.append(dict(re.findall(r'(\w+)="([^"]*)"', corpo)))
    return trovati


def riquadro(polygon: str) -> tuple[float, float, float, float]:
    """Bounding box (x_min, y_min, x_max, y_max) di una stella."""
    punti = vertici(polygon)
    xs = [x for x, _ in punti]
    ys = [y for _, y in punti]
    return min(xs), min(ys), max(xs), max(ys)


# --- stella ---------------------------------------------------------------


def test_stella_ha_dieci_vertici():
    assert len(vertici(render_flags.stella(cx=10, cy=10, raggio=4))) == 10


def test_stella_punta_verso_l_alto():
    punti = vertici(render_flags.stella(cx=10, cy=20, raggio=4))
    assert punti[0] == pytest.approx((10.0, 16.0), abs=0.01)


def test_stella_alterna_raggio_esterno_e_interno():
    cx, cy, raggio = 300.0, 400.0, 100.0
    punti = vertici(render_flags.stella(cx=cx, cy=cy, raggio=raggio))
    distanze = [math.hypot(x - cx, y - cy) for x, y in punti]
    assert distanze[0::2] == pytest.approx([raggio] * 5, abs=PRECISIONE)
    assert distanze[1::2] == pytest.approx([raggio * 0.382] * 5, abs=PRECISIONE)


def test_stella_ha_cinque_punte_equidistanti():
    # raggio grande di proposito: i vertici escono con due decimali, e su un
    # raggio piccolo l'arrotondamento sposterebbe l'angolo piu' della soglia.
    cx, cy, raggio = 300.0, 400.0, 100.0
    esterni = vertici(render_flags.stella(cx=cx, cy=cy, raggio=raggio))[0::2]
    angoli = sorted(math.degrees(math.atan2(cy - y, x - cx)) % 360 for x, y in esterni)
    passi = [(b - a) % 360 for a, b in zip(angoli, angoli[1:] + angoli[:1])]
    tolleranza = 2 * math.degrees(math.atan(PRECISIONE / raggio))
    assert passi == pytest.approx([72.0] * 5, abs=tolleranza)


def test_stella_e_bianca():
    assert f'fill="{BIANCO}"' in render_flags.stella(cx=1, cy=1, raggio=1)


# --- bandiera italiana ----------------------------------------------------


def test_italia_rispetta_la_proporzione_tre_a_due():
    _, larghezza = render_flags.svg_italia()
    assert larghezza / render_flags.ALTEZZA == pytest.approx(3 / 2)


def test_italia_ha_tre_bande_di_uguale_larghezza():
    svg, larghezza = render_flags.svg_italia()
    bande = rettangoli(svg)
    assert [float(b["width"]) for b in bande] == pytest.approx([larghezza / 3] * 3)


def test_italia_ha_i_colori_nell_ordine_verde_bianco_rosso():
    svg, _ = render_flags.svg_italia()
    assert [b["fill"] for b in rettangoli(svg)] == [VERDE, BIANCO_IT, ROSSO_IT]


def test_italia_affianca_le_bande_senza_sovrapporle():
    svg, larghezza = render_flags.svg_italia()
    bande = rettangoli(svg)
    inizi = [float(b.get("x", 0)) for b in bande]
    assert inizi == pytest.approx([0, larghezza / 3, larghezza * 2 / 3])


def test_italia_dichiara_dimensioni_e_viewbox_coerenti():
    svg, larghezza = render_flags.svg_italia()
    altezza = render_flags.ALTEZZA
    assert f'width="{larghezza}" height="{altezza}"' in svg
    assert f'viewBox="0 0 {larghezza} {altezza}"' in svg


# --- bandiera degli Stati Uniti -------------------------------------------


def test_stati_uniti_rispettano_la_proporzione_diciannove_a_dieci():
    _, larghezza = render_flags.svg_stati_uniti()
    assert larghezza == round(render_flags.ALTEZZA * 1.9)


def test_stati_uniti_hanno_cinquanta_stelle():
    svg, _ = render_flags.svg_stati_uniti()
    assert svg.count("<polygon") == 50


def test_stati_uniti_hanno_tredici_strisce_di_cui_sette_rosse():
    svg, _ = render_flags.svg_stati_uniti()
    rosse = [r for r in rettangoli(svg) if r["fill"] == ROSSO_US]
    assert len(rosse) == 7
    assert [float(r["height"]) for r in rosse] == pytest.approx(
        [render_flags.ALTEZZA / 13] * 7, abs=0.01
    )


def test_stati_uniti_alternano_le_strisce_a_partire_dall_alto():
    svg, _ = render_flags.svg_stati_uniti()
    striscia = render_flags.ALTEZZA / 13
    rosse = [r for r in rettangoli(svg) if r["fill"] == ROSSO_US]
    assert [float(r["y"]) for r in rosse] == pytest.approx(
        [i * striscia for i in range(0, 13, 2)], abs=0.01
    )


def test_stati_uniti_hanno_il_fondo_bianco_sotto_le_strisce():
    svg, larghezza = render_flags.svg_stati_uniti()
    fondo = rettangoli(svg)[0]
    assert fondo["fill"] == BIANCO
    assert float(fondo["width"]) == larghezza
    assert float(fondo["height"]) == render_flags.ALTEZZA


def test_stati_uniti_hanno_il_cantone_alto_sette_strisce():
    svg, _ = render_flags.svg_stati_uniti()
    cantone = next(r for r in rettangoli(svg) if r["fill"] == BLU_US)
    assert float(cantone["height"]) == pytest.approx(
        render_flags.ALTEZZA / 13 * 7, abs=PRECISIONE
    )


def test_stati_uniti_danno_al_cantone_due_quinti_della_larghezza():
    """Proporzioni ufficiali: cantone largo 0.76 su una bandiera larga 1.9, cioe' 0.4.

    Il rapporto si misura sulla larghezza disegnata e non sull'altezza:
    la larghezza e' arrotondata al pixel (53 invece di 53.2) e quel mezzo
    pixel si propagherebbe al confronto.
    """
    svg, larghezza = render_flags.svg_stati_uniti()
    cantone = next(r for r in rettangoli(svg) if r["fill"] == BLU_US)

    assert float(cantone["width"]) / larghezza == pytest.approx(0.76 / 1.9, abs=0.001)


def test_stati_uniti_tengono_tutte_le_stelle_dentro_il_cantone():
    svg, _ = render_flags.svg_stati_uniti()
    cantone = next(r for r in rettangoli(svg) if r["fill"] == BLU_US)
    largo, alto = float(cantone["width"]), float(cantone["height"])
    for polygon in re.findall(r"<polygon[^>]*/>", svg):
        x_min, y_min, x_max, y_max = riquadro(polygon)
        assert 0 <= x_min and x_max <= largo, polygon
        assert 0 <= y_min and y_max <= alto, polygon


def file_di_stelle(svg: str) -> list[list[float]]:
    """Le ascisse delle stelle, raggruppate per fila e ordinate da sinistra."""
    per_riga: dict[float, list[float]] = {}
    for polygon in re.findall(r"<polygon[^>]*/>", svg):
        x_min, y_min, x_max, y_max = riquadro(polygon)
        per_riga.setdefault(round((y_min + y_max) / 2, 2), []).append((x_min + x_max) / 2)
    return [sorted(per_riga[y]) for y in sorted(per_riga)]


def test_stati_uniti_dispongono_le_stelle_su_nove_file_alternate():
    svg, _ = render_flags.svg_stati_uniti()

    assert [len(fila) for fila in file_di_stelle(svg)] == [6, 5, 6, 5, 6, 5, 6, 5, 6]


def test_stati_uniti_sfalsano_le_file_da_cinque_stelle():
    """Le file corte stanno negli spazi di quelle lunghe, come sulla bandiera reale."""
    file = file_di_stelle(render_flags.svg_stati_uniti()[0])

    for lunga, corta in zip(file[0::2], file[1::2]):
        attese = [(sinistra + destra) / 2 for sinistra, destra in pairwise(lunga)]
        assert corta == pytest.approx(attese, abs=PRECISIONE)


def test_stati_uniti_spaziano_le_stelle_sulla_griglia_del_cantone():
    """Sei stelle per fila su dodici colonne: il passo e' un sesto del cantone."""
    svg, _ = render_flags.svg_stati_uniti()
    cantone = next(r for r in rettangoli(svg) if r["fill"] == BLU_US)

    passi = [b - a for fila in file_di_stelle(svg) for a, b in pairwise(fila)]
    atteso = float(cantone["width"]) / 6
    assert passi == pytest.approx([atteso] * len(passi), abs=ERRORE_CENTRO)


def test_stati_uniti_distanziano_le_file_sulla_griglia_del_cantone():
    """Nove file su dieci righe: il passo e' un decimo dell'altezza del cantone."""
    svg, _ = render_flags.svg_stati_uniti()
    cantone = next(r for r in rettangoli(svg) if r["fill"] == BLU_US)
    altezze = sorted(
        {round(sum(riquadro(p)[1::2]) / 2, 2) for p in re.findall(r"<polygon[^>]*/>", svg)}
    )

    passi = [b - a for a, b in pairwise(altezze)]
    atteso = float(cantone["height"]) / 10
    assert passi == pytest.approx([atteso] * len(passi), abs=2 * ERRORE_CENTRO)


# --- rasterizzazione ------------------------------------------------------


def test_rasterizza_scrive_una_pagina_con_le_dimensioni_della_bandiera(
    tmp_path, monkeypatch, chrome
):
    monkeypatch.setattr(render_flags, "BUILD", tmp_path)
    monkeypatch.setattr(render_flags, "OUT", tmp_path / "assets")

    render_flags.rasterizza(nome="it", svg="<svg id='x'/>", larghezza=42, chrome="chrome")

    pagina = (tmp_path / "_flag-it.html").read_text(encoding="utf-8")
    assert "<svg id='x'/>" in pagina
    assert "width:42px" in pagina
    assert f"height:{render_flags.ALTEZZA}px" in pagina


def test_rasterizza_restituisce_il_png_in_assets(tmp_path, monkeypatch, chrome):
    monkeypatch.setattr(render_flags, "BUILD", tmp_path)
    monkeypatch.setattr(render_flags, "OUT", tmp_path / "assets")

    out = render_flags.rasterizza(nome="us", svg="<svg/>", larghezza=53, chrome="chrome")

    assert out == tmp_path / "assets" / "flag-us.png"
    assert out.is_file()


def test_rasterizza_chiede_a_chrome_uno_sfondo_trasparente(tmp_path, monkeypatch, chrome):
    monkeypatch.setattr(render_flags, "BUILD", tmp_path)
    monkeypatch.setattr(render_flags, "OUT", tmp_path / "assets")

    render_flags.rasterizza(nome="it", svg="<svg/>", larghezza=42, chrome="chrome")

    argv = chrome[0]
    assert "--default-background-color=00000000" in argv
    assert f"--window-size=42,{render_flags.ALTEZZA}" in argv
    assert argv[0] == "chrome"
    assert argv[-1] == (tmp_path / "_flag-it.html").as_uri()


# --- main -----------------------------------------------------------------


def test_main_si_ferma_se_chrome_non_e_installato(senza_chrome, capsys):
    assert render_flags.main() == 1
    assert "nessun binario Chrome" in capsys.readouterr().err


def test_main_genera_le_due_bandiere(tmp_path, monkeypatch, chrome, capsys):
    monkeypatch.setattr(render_flags, "BUILD", tmp_path)
    monkeypatch.setattr(render_flags, "OUT", tmp_path / "profile" / "assets")

    assert render_flags.main() == 0

    prodotti = sorted(p.name for p in (tmp_path / "profile" / "assets").iterdir())
    assert prodotti == ["flag-it.png", "flag-us.png"]


def test_main_crea_la_cartella_di_destinazione_se_manca(tmp_path, monkeypatch, chrome):
    destinazione = tmp_path / "mai" / "vista"
    monkeypatch.setattr(render_flags, "BUILD", tmp_path)
    monkeypatch.setattr(render_flags, "OUT", destinazione)

    render_flags.main()

    assert destinazione.is_dir()


def test_main_riporta_dimensioni_e_peso_di_ogni_bandiera(tmp_path, monkeypatch, chrome, capsys):
    monkeypatch.setattr(render_flags, "BUILD", tmp_path)
    monkeypatch.setattr(render_flags, "OUT", tmp_path / "profile" / "assets")

    render_flags.main()

    righe = capsys.readouterr().out.strip().splitlines()
    assert len(righe) == 2
    assert f"42x{render_flags.ALTEZZA}" in righe[0]
    assert f"53x{render_flags.ALTEZZA}" in righe[1]
    assert righe[0].endswith("byte")

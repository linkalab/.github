"""La lista locale deve uscire identica a quella della GitHub Action.

Il formato data e' la parte fragile: l'action usa la libreria npm
`dateformat`, dove `mm` e' il mese e `MM` sono i minuti, e un errore li'
produce stringhe che sembrano date finche' non le si legge. Il test
`test_build_list_scrive_il_mese_non_i_minuti` esiste per quello ed e'
l'unico che non va mai allentato.

Il feed non viene inventato: gli XML dei test passano dal parser vero,
cosi' i test esercitano feedparser come lo esercita la produzione.
"""

import feedparser
import pytest

import seed_posts

PARSE_VERO = feedparser.parse


def rss(*voci: tuple[str, str, str]) -> str:
    """Un RSS 2.0 valido con le voci date come (titolo, link, pubDate)."""
    articoli = "".join(
        f"<item><title>{titolo}</title><link>{link}</link>"
        f"<pubDate>{data}</pubDate></item>"
        for titolo, link, data in voci
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<rss version=\"2.0\"><channel><title>Magazine</title>"
        f"<link>https://www.linkalab.it</link>{articoli}</channel></rss>"
    )


@pytest.fixture
def feed(monkeypatch):
    """Sostituisce la sorgente del feed lasciando in piedi il parser vero."""

    def installa(xml: str) -> None:
        monkeypatch.setattr(seed_posts.feedparser, "parse", lambda _: PARSE_VERO(xml))

    return installa


@pytest.fixture
def readme(tmp_path, monkeypatch):
    """Due README con i marker, al posto di quelli del repository."""
    percorsi = []
    for nome in ("README.md", "README.en.md"):
        percorso = tmp_path / nome
        percorso.write_text(
            f"# Titolo\n\n{seed_posts.START}\n{seed_posts.END}\n\n## Coda\n",
            encoding="utf-8",
        )
        percorsi.append(percorso)
    monkeypatch.setattr(seed_posts, "ROOT", tmp_path)
    monkeypatch.setattr(seed_posts, "TARGETS", percorsi)
    return percorsi


# --- build_list -----------------------------------------------------------


def test_build_list_formatta_titolo_link_e_data(feed):
    feed(rss(("Dati e AI", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    assert seed_posts.build_list() == (
        "- [Dati e AI](https://linkalab.it/a) <sub>19.01.2026</sub>"
    )


def test_build_list_scrive_il_mese_non_i_minuti(feed):
    """Regressione: `dd.MM.yyyy` con dateformat produce giorno, minuti, anno."""
    feed(rss(("Titolo", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    assert "<sub>19.01.2026</sub>" in seed_posts.build_list()


def test_build_list_mette_lo_zero_davanti_a_giorno_e_mese(feed):
    feed(rss(("Titolo", "https://linkalab.it/a", "Mon, 05 Jan 2026 09:04:00 +0000")))

    assert "<sub>05.01.2026</sub>" in seed_posts.build_list()


def test_build_list_riporta_la_data_in_utc(feed):
    """Il workflow usa `UTC:dd.mm.yyyy`: un fuso avanti non deve spostare il giorno."""
    feed(rss(("Titolo", "https://linkalab.it/a", "Wed, 31 Dec 2025 23:30:00 -0500")))

    assert "<sub>01.01.2026</sub>" in seed_posts.build_list()


def test_build_list_si_ferma_al_massimo_di_articoli(feed):
    feed(rss(*[(f"T{i}", f"https://linkalab.it/{i}", "Mon, 19 Jan 2026 14:35:00 +0000")
               for i in range(9)]))

    righe = seed_posts.build_list().splitlines()
    assert len(righe) == seed_posts.MAX_POSTS
    assert "[T0]" in righe[0]
    assert f"[T{seed_posts.MAX_POSTS - 1}]" in righe[-1]


def test_build_list_tiene_tutti_gli_articoli_se_sono_meno_del_massimo(feed):
    feed(rss(*[(f"T{i}", f"https://linkalab.it/{i}", "Mon, 19 Jan 2026 14:35:00 +0000")
               for i in range(2)]))

    assert len(seed_posts.build_list().splitlines()) == 2


def test_build_list_conserva_l_ordine_del_feed(feed):
    feed(rss(
        ("Recente", "https://linkalab.it/b", "Tue, 20 Jan 2026 10:00:00 +0000"),
        ("Vecchio", "https://linkalab.it/a", "Mon, 19 Jan 2026 10:00:00 +0000"),
    ))

    righe = seed_posts.build_list().splitlines()
    assert "[Recente]" in righe[0]
    assert "[Vecchio]" in righe[1]


def test_build_list_su_feed_senza_articoli_restituisce_una_lista_vuota(feed):
    feed(rss())

    assert seed_posts.build_list() == ""


def test_build_list_rifiuta_un_feed_illeggibile(feed):
    feed("non e' affatto xml")

    with pytest.raises(RuntimeError, match="feed non leggibile"):
        seed_posts.build_list()


def test_build_list_accetta_un_feed_sporco_ma_parsabile(feed):
    """Un `&` non escapato rende il feed bozo: se gli articoli ci sono, si usano."""
    feed(rss(("Dati & AI", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    assert "https://linkalab.it/a" in seed_posts.build_list()


# --- main -----------------------------------------------------------------


def test_main_riempie_entrambi_i_readme(feed, readme, capsys):
    feed(rss(("Dati e AI", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    assert seed_posts.main() == 0

    for percorso in readme:
        testo = percorso.read_text(encoding="utf-8")
        assert "- [Dati e AI](https://linkalab.it/a) <sub>19.01.2026</sub>" in testo


def test_main_non_tocca_il_testo_fuori_dai_marker(feed, readme):
    feed(rss(("Titolo", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    seed_posts.main()

    testo = readme[0].read_text(encoding="utf-8")
    assert testo.startswith("# Titolo\n")
    assert testo.endswith("## Coda\n")


def test_main_lascia_i_marker_al_loro_posto(feed, readme):
    feed(rss(("Titolo", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    seed_posts.main()

    testo = readme[0].read_text(encoding="utf-8")
    assert testo.count(seed_posts.START) == 1
    assert testo.count(seed_posts.END) == 1
    assert testo.index(seed_posts.START) < testo.index(seed_posts.END)


def test_main_sostituisce_la_lista_precedente_invece_di_accodarla(feed, readme):
    readme[0].write_text(
        f"{seed_posts.START}\n- [Vecchio](https://linkalab.it/v) <sub>01.01.2020</sub>\n"
        f"{seed_posts.END}\n",
        encoding="utf-8",
    )
    feed(rss(("Nuovo", "https://linkalab.it/n", "Mon, 19 Jan 2026 14:35:00 +0000")))

    seed_posts.main()

    testo = readme[0].read_text(encoding="utf-8")
    assert "[Nuovo]" in testo
    assert "[Vecchio]" not in testo


def test_main_e_idempotente(feed, readme):
    feed(rss(("Titolo", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    seed_posts.main()
    primo = readme[0].read_text(encoding="utf-8")
    seed_posts.main()

    assert readme[0].read_text(encoding="utf-8") == primo


def test_main_si_ferma_se_i_marker_mancano(feed, readme, capsys):
    readme[0].write_text("# Nessun marker qui\n", encoding="utf-8")
    feed(rss(("Titolo", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    assert seed_posts.main() == 1
    assert "marker assenti in README.md" in capsys.readouterr().err


def test_main_non_scrive_nulla_quando_i_marker_mancano_nel_primo(feed, readme):
    readme[0].write_text("# Nessun marker qui\n", encoding="utf-8")
    intatto = readme[1].read_text(encoding="utf-8")
    feed(rss(("Titolo", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    seed_posts.main()

    assert readme[1].read_text(encoding="utf-8") == intatto


def test_main_stampa_la_lista_prodotta(feed, readme, capsys):
    feed(rss(("Dati e AI", "https://linkalab.it/a", "Mon, 19 Jan 2026 14:35:00 +0000")))

    seed_posts.main()

    out = capsys.readouterr().out
    assert "aggiornato README.md" in out
    assert "- [Dati e AI](https://linkalab.it/a) <sub>19.01.2026</sub>" in out

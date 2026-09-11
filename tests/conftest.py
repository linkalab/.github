"""Fixture condivise dalla suite.

Gli script di `build/` sono standalone (PEP 723, nessun package): per
importarli nei test la cartella viene messa su `sys.path` invece di
aggiungere `__init__.py`, che cambierebbe il modo in cui si lanciano.

I due boundary che la suite sostituisce sono l'unico I/O non
deterministico degli script: Chrome headless e la rete. Tutto il resto
(filesystem, parsing del feed, regex sull'HTML) gira sul codice vero.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BUILD = Path(__file__).parent.parent / "build"
sys.path.insert(0, str(BUILD))

CHROME_FINTO = "/usr/bin/chrome-di-prova"


class RispostaFinta:
    """Sostituto minimo di `requests.Response` per i test."""

    def __init__(self, *, testo: str = "", contenuto: bytes = b"", stato: int = 200):
        self.text = testo
        self.content = contenuto
        self.status_code = stato

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"{self.status_code} per la risposta finta")


@pytest.fixture
def chrome(monkeypatch):
    """Chrome headless sostituito: registra le invocazioni e crea il PNG.

    Il file va creato davvero perche' i chiamanti ne leggono la
    dimensione con `stat()` subito dopo lo scatto.
    """
    invocazioni: list[list[str]] = []

    def which_finto(nome: str) -> str | None:
        return CHROME_FINTO if nome == "google-chrome" else None

    def run_finto(argv, **kwargs):
        invocazioni.append(list(argv))
        for arg in argv:
            if arg.startswith("--screenshot="):
                destinazione = Path(arg.split("=", 1)[1])
                destinazione.parent.mkdir(parents=True, exist_ok=True)
                destinazione.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 2048)
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    monkeypatch.setattr(shutil, "which", which_finto)
    monkeypatch.setattr(subprocess, "run", run_finto)
    return invocazioni


@pytest.fixture
def senza_chrome(monkeypatch):
    """Nessun binario Chrome installato."""
    monkeypatch.setattr(shutil, "which", lambda nome: None)


def argv_dello_scatto(invocazioni: list[list[str]], nome_file: str) -> list[str]:
    """L'invocazione di Chrome che ha prodotto `nome_file`."""
    for argv in invocazioni:
        if any(arg.endswith(f"={nome_file}") for arg in argv):
            return argv
    raise AssertionError(f"nessuno scatto per {nome_file} fra {invocazioni}")

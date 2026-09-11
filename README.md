# Profilo GitHub di Linkalab

Sorgente della pagina che si vede su [github.com/linkalab](https://github.com/linkalab).

Questo repository va pubblicato sull'organizzazione con il nome `.github`: è la convenzione con cui GitHub sceglie quale file mostrare sul profilo, e il file è `profile/README.md`.

```
profile/
  README.md        pagina del profilo, italiano (quella mostrata)
  README.en.md     stessa pagina in inglese, raggiungibile dal link in alto
  assets/          banner, quattro varianti: due lingue x chiaro/scuro
.github/workflows/
  magazine.yml     aggiorna gli articoli dal feed del sito
build/             sorgenti dei banner e script, non serve a chi legge il profilo
```

## Gli articoli si aggiornano da soli

`magazine.yml` gira ogni mattina, legge `https://www.linkalab.it/feed` e riscrive i cinque articoli più recenti fra i marker `BLOG-POST-LIST` in entrambi i README. Si può lanciare a mano dalla tab Actions con "Run workflow".

Per rifare la stessa cosa in locale, senza aspettare il cron:

```bash
uv run --script build/seed_posts.py
```

LinkedIn non ha un equivalente: non espone feed pubblici per le pagine aziendali, quindi lì c'è solo il link alla pagina.

## Rigenerare i banner

I banner sono immagini e non testo perché GitHub non carica i font del design system nel README. Lo script costruisce una pagina HTML con i font veri e la fotografa con Chrome:

```bash
uv run --script build/render_banner.py
```

Font e logo non stanno nel repository: vanno copiati in `build/` dalla versione corrente del design system. Se mancano, lo script si ferma e stampa i comandi per procurarseli, invece di produrre un banner con i font sbagliati.

Colori e caratteri arrivano dal design system Linkalab (`tokens/colors.css`, `tokens/fonts.css`): verde forest `#0F3D2D` e `#07251A` per i fondi, mint `#5DBE8E` per l'accento, Space Grotesk per il payoff, JetBrains Mono per la riga di occhiello. Se il design system cambia, si aggiornano i valori in cima a `build/render_banner.py` e si rilancia.

Testo del payoff e occhiello stanno nel dizionario `COPY` dello stesso script, una voce per lingua.

## Cosa controllare quando si modifica la pagina

- Il profilo mostra solo `profile/README.md`. Il file che stai leggendo non compare da nessuna parte se non in questo repository.
- I percorsi delle immagini sono URL assoluti a `raw.githubusercontent.com` e contengono il nome del branch: se il branch principale non si chiama `main`, vanno corretti.
- GitHub rimuove CSS e script dal markdown. Funzionano `<picture>`, `<img>`, `<sub>`, `<p align>` e `<details>`, non altro.
- I badge stanno tutti su una riga sola del sorgente. Messi su righe separate vanno a capo uno per riga invece di stare in fila.
- I badge AWS sono senza icona di proposito: simple-icons, da cui shields.io prende i loghi, non distribuisce più le icone Amazon. Passare `logo=aws` produce un badge muto, non un errore.

Per guardare la pagina renderizzata prima di pubblicarla, a schermo largo e stretto:

```bash
uv run --script build/preview.py
```

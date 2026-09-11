# Profilo GitHub di Linkalab

Sorgente della pagina che si vede su [github.com/linkalab](https://github.com/linkalab).

Il repository si chiama `.github` sull'organizzazione: è la convenzione con cui GitHub sceglie quale file mostrare sul profilo, e il file è `profile/README.md`. Deve restare pubblico, altrimenti la pagina non compare a chi non è membro.

```
profile/
  README.md          pagina del profilo, italiano (quella mostrata)
  README.en.md       stessa pagina in inglese, raggiungibile dal link in alto
  assets/            quattro banner (due lingue x chiaro/scuro) e due bandiere
.github/workflows/
  magazine.yml       aggiorna gli articoli dal feed del sito
build/               generatori e anteprima, non servono a chi legge il profilo
  render_banner.py   banner, dai token del design system
  render_flags.py    bandierine dei link fra le due lingue
  seed_posts.py      riempie la lista articoli in locale
  preview.py         screenshot della pagina a 1280 e 375 px
  build_artifact.py  anteprima autonoma, apribile in un browser
```

## Gli articoli si aggiornano da soli

`magazine.yml` gira ogni mattina, legge `https://www.linkalab.it/feed` e riscrive i cinque articoli più recenti fra i marker `BLOG-POST-LIST` in entrambi i README. Si può lanciare a mano dalla tab Actions con "Run workflow".

Per rifare la stessa cosa in locale, senza aspettare il cron:

```bash
uv run --script build/seed_posts.py
```

LinkedIn non ha un equivalente: non espone feed pubblici per le pagine aziendali, quindi lì c'è solo il link alla pagina.

**Il formato della data non è quello che sembra.** L'action usa la libreria npm `dateformat`, dove `mm` è il mese e `MM` sono i minuti, al contrario di `date-fns` e `moment`. Un `dd.MM.yyyy` produce `10.19.2026`, cioè giorno, minuti, anno, e sembra una data finché non la si legge. Il default dell'action lo dichiara da sé con `h:MM TT`.

**`tag_post_pre_newline` va tenuto esplicito.** Vale `true` da solo, ma torna a `false` appena si usa l'opzione `template`, e senza la prima voce resta attaccata al marker di apertura sulla stessa riga: markdown non la vede come lista e la stampa come testo.

Attenzione anche a `seed_posts.py`: replica il formato dell'action ma non ne condivide il codice, quindi è possibile che l'anteprima locale mostri un risultato che la produzione non produce. È successo, ed è come il difetto delle date è arrivato fino alla pagina pubblicata.

## Rigenerare banner e bandiere

I banner sono immagini e non testo perché GitHub non carica i font del design system nel README. Lo script costruisce una pagina HTML con i font veri e la fotografa con Chrome:

```bash
uv run --script build/render_banner.py
```

Font e logo non stanno nel repository: vanno copiati in `build/` dalla versione corrente del design system. Se mancano, lo script si ferma e stampa i comandi per procurarseli, invece di produrre un banner con i font sbagliati.

Colori e caratteri arrivano dal design system Linkalab (`tokens/colors.css`, `tokens/fonts.css`): verde forest `#0F3D2D` e `#07251A` per i fondi, mint `#5DBE8E` per l'accento, Space Grotesk per il payoff, JetBrains Mono per la riga di occhiello. Se il design system cambia, si aggiornano i valori in cima a `build/render_banner.py` e si rilancia.

Testo del payoff e occhiello stanno nel dizionario `COPY` dello stesso script, una voce per lingua.

Le bandiere dei link fra le due lingue sono PNG generati da SVG disegnati nello script:

```bash
uv run --script build/render_flags.py
```

Sono immagini e non emoji perché le emoji bandiera sono sequenze di due caratteri che il sistema operativo deve comporre, e Windows non lo fa: al posto della bandiera mostra le lettere `US` e `IT`.

## Guardare la pagina prima di pubblicarla

Screenshot alle due larghezze che contano:

```bash
uv run --script build/preview.py
```

Pagina autonoma da aprire nel browser, con selettore di lingua e temi chiaro e scuro:

```bash
uv run --script build/build_artifact.py
```

Entrambi passano il markdown dal renderer vero di GitHub, non da un'imitazione locale. `build_artifact.py` incorpora ogni immagine come data URI e si ferma se ne resta una remota, perché una pagina autonoma con un buco al posto di un badge sembra un difetto del README invece che del contenitore.

## Cosa sapere quando si modifica la pagina

- Il profilo mostra solo `profile/README.md`. Il file che stai leggendo non compare da nessuna parte se non in questo repository.
- Sul profilo dell'organizzazione c'è un selettore **View as**: in modalità *Member* GitHub cerca un README in un repository separato chiamato `.github-private` e non mostra questo. La pagina pubblica si vede in modalità *Public*.
- I percorsi delle immagini sono URL assoluti a `raw.githubusercontent.com` e contengono il nome del branch: se il branch principale non si chiama `main`, vanno corretti.
- GitHub rimuove CSS, script e SVG inline dal markdown. Funzionano `<picture>`, `<img>`, `<sub>`, `<p align>` e `<details>`. Gli attributi di presentazione come `align="absmiddle"` su un'immagine vengono scartati: gli allineamenti si ottengono cambiando il markup, non aggiungendo attributi.
- I badge stanno tutti su una riga sola del sorgente. Messi su righe separate vanno a capo uno per riga invece di stare in fila.
- I badge sono senza icona di proposito: simple-icons, da cui shields.io prende i loghi, non distribuisce più le icone Amazon, e una fila per metà con logo e per metà senza sembra rotta.
- `raw.githubusercontent.com` serve una copia in cache per qualche minuto. Per controllare un file subito dopo un commit va usata l'API dei contenuti (`gh api repos/linkalab/.github/contents/profile/README.md`), altrimenti un fix riuscito sembra fallito.

## File che qui valgono per tutta l'organizzazione

Un repository `.github` è anche il posto da cui GitHub prende i file di default per ogni altro repository dell'organizzazione che non ne ha uno proprio: `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `FUNDING.yml` e i template di issue e pull request.

Al momento non ce n'è nessuno, e aggiungerne uno non è una modifica a questo repository: è una policy che si applica a tutti i repository Linkalab in una volta sola. Il README non rientra fra questi file.

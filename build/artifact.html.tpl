<title>Anteprima del profilo GitHub Linkalab</title>

<style>
  /* Token di GitHub Primer: l'anteprima deve somigliare a GitHub, non
     avere un'identita' propria. Il verde Linkalab resta confinato alla
     barra di controllo, che non fa parte della pagina renderizzata. */
  :root {
    --gh-canvas: #ffffff;
    --gh-canvas-subtle: #f6f8fa;
    --gh-fg: #1f2328;
    --gh-fg-muted: #59636e;
    --gh-border: #d1d9e0;
    --gh-accent: #0969da;
    --gh-code-bg: #eff1f3;

    --forest: #0F3D2D;
    --forest-scuro: #07251A;
    --mint: #5DBE8E;
    --mint-chiaro: #AFF1D0;

    --banner-chiaro: block;
    --banner-scuro: none;
  }

  @media (prefers-color-scheme: dark) {
    :root {
      --gh-canvas: #0d1117;
      --gh-canvas-subtle: #151b23;
      --gh-fg: #f0f6fc;
      --gh-fg-muted: #9198a1;
      --gh-border: #3d444d;
      --gh-accent: #4493f8;
      --gh-code-bg: #151b23;

      --banner-chiaro: none;
      --banner-scuro: block;
    }
  }

  /* il selettore di tema del visualizzatore deve vincere in entrambe
     le direzioni, quindi i token si ridefiniscono su data-theme */
  :root[data-theme="dark"] {
    --gh-canvas: #0d1117;
    --gh-canvas-subtle: #151b23;
    --gh-fg: #f0f6fc;
    --gh-fg-muted: #9198a1;
    --gh-border: #3d444d;
    --gh-accent: #4493f8;
    --gh-code-bg: #151b23;

    --banner-chiaro: none;
    --banner-scuro: block;
  }

  :root[data-theme="light"] {
    --gh-canvas: #ffffff;
    --gh-canvas-subtle: #f6f8fa;
    --gh-fg: #1f2328;
    --gh-fg-muted: #59636e;
    --gh-border: #d1d9e0;
    --gh-accent: #0969da;
    --gh-code-bg: #eff1f3;

    --banner-chiaro: block;
    --banner-scuro: none;
  }

  body {
    margin: 0;
    background: var(--gh-canvas);
    color: var(--gh-fg);
    font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans",
      Helvetica, Arial, sans-serif;
  }

  /* ---- barra di controllo (non fa parte del README) ---- */

  .barra {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 16px;
    padding: 12px 24px;
    background: var(--forest-scuro);
    border-bottom: 3px solid var(--mint);
  }

  .barra h1 {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--mint-chiaro);
  }

  .barra .nota {
    margin: 0;
    font-size: 13px;
    color: #9AA8A2;
    flex: 1 1 240px;
  }

  .lingue {
    display: flex;
    gap: 4px;
    padding: 3px;
    border-radius: 999px;
    background: rgba(230, 245, 238, 0.08);
  }

  .lingue button {
    padding: 5px 14px;
    border: 0;
    border-radius: 999px;
    background: transparent;
    color: var(--mint-chiaro);
    font: inherit;
    font-size: 13px;
    cursor: pointer;
  }

  .lingue button[aria-selected="true"] {
    background: var(--mint);
    color: var(--forest-scuro);
    font-weight: 600;
  }

  .lingue button:focus-visible {
    outline: 2px solid var(--mint-chiaro);
    outline-offset: 2px;
  }

  /* ---- il README renderizzato ---- */

  .foglio {
    max-width: 1012px;
    margin: 0 auto;
    padding: 32px 24px 64px;
  }

  .pagina[hidden] { display: none; }

  .banner img { width: 100%; height: auto; border-radius: 6px; }
  .banner .chiaro { display: var(--banner-chiaro); }
  .banner .scuro  { display: var(--banner-scuro); }

  .pagina img { max-width: 100%; vertical-align: middle; }

  .pagina h2 {
    margin: 24px 0 16px;
    padding-bottom: 0.3em;
    font-size: 1.5em;
    font-weight: 600;
    line-height: 1.25;
    border-bottom: 1px solid var(--gh-border);
    text-wrap: balance;
  }

  .pagina p { margin: 0 0 16px; }
  .pagina a { color: var(--gh-accent); text-decoration: none; }
  .pagina a:hover { text-decoration: underline; }
  .pagina a:focus-visible { outline: 2px solid var(--gh-accent); outline-offset: 2px; }

  .pagina sub { color: var(--gh-fg-muted); font-size: 12px; }

  /* lo scorrimento va sul contenitore: sulla tabella stessa
     display:block rompe il contesto tabellare e il ridisegno */
  .tabella-wrap { max-width: 100%; overflow-x: auto; margin: 0 0 16px; }

  .pagina table { border-collapse: collapse; width: max-content; max-width: 100%; }
  .pagina td, .pagina th { padding: 6px 13px; border: 1px solid var(--gh-border); }
  .pagina tr:nth-child(2n) { background: var(--gh-canvas-subtle); }

  .pagina ul { margin: 0 0 16px; padding-left: 2em; }
  .pagina li { margin-bottom: 0.25em; }

  .pagina code {
    padding: 0.2em 0.4em;
    border-radius: 6px;
    background: var(--gh-code-bg);
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
    font-size: 85%;
  }

  @media (max-width: 640px) {
    .foglio { padding: 20px 16px 48px; }
    .barra { padding: 10px 16px; }
  }

  @media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
  }
</style>

<div class="barra">
  <h1>Anteprima</h1>
  <p class="nota">
    Come si vedrebbe su github.com/linkalab. Il tema segue il tuo,
    banner compreso.
  </p>
  <div class="lingue" role="tablist" aria-label="Lingua della pagina">
    <button role="tab" aria-selected="true" data-scegli="it">Italiano</button>
    <button role="tab" aria-selected="false" data-scegli="en">English</button>
  </div>
</div>

<div class="foglio">
__PAGINE__
</div>

<script>
  const bottoni = document.querySelectorAll(".lingue button");
  const pagine = document.querySelectorAll(".pagina");

  for (const bottone of bottoni) {
    bottone.addEventListener("click", () => {
      const scelta = bottone.dataset.scegli;
      for (const b of bottoni) {
        b.setAttribute("aria-selected", String(b === bottone));
      }
      for (const p of pagine) {
        p.hidden = p.dataset.lingua !== scelta;
      }
    });
  }

  // le tabelle arrivano dal renderer di GitHub senza contenitore:
  // gliene diamo uno, o su schermo stretto spingono la pagina di lato
  for (const tabella of document.querySelectorAll(".pagina table")) {
    const wrap = document.createElement("div");
    wrap.className = "tabella-wrap";
    tabella.parentNode.insertBefore(wrap, tabella);
    wrap.appendChild(tabella);
  }
</script>

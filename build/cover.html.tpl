<meta charset="utf-8">
<style>
  @font-face{font-family:'Space Grotesk';font-weight:700;src:url('space-grotesk-700.woff2') format('woff2')}
  @font-face{font-family:'Manrope';font-weight:400;src:url('manrope-400.woff2') format('woff2')}
  @font-face{font-family:'JetBrains Mono';font-weight:500;src:url('jetbrains-mono-500.woff2') format('woff2')}

  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1128px;height:191px}
  body{
    background:__BG__;
    font-family:'Manrope',sans-serif;
    position:relative;
    overflow:hidden;
    display:flex;
    align-items:center;
    justify-content:flex-end;
  }

  /* filetto mint sul bordo destro: firma discreta, e sul lato che il
     logo della pagina non copre mai */
  .edge{position:absolute;right:0;top:0;bottom:0;width:5px;background:#5DBE8E}

  /* 114px per lato sono la fascia che la app mobile taglia: il testo
     resta dentro il centro della copertina, non appoggiato al bordo */
  .content{padding-right:132px;text-align:right;z-index:2}

  .eyebrow{
    font-family:'JetBrains Mono',monospace;font-weight:500;
    font-size:12px;letter-spacing:.14em;text-transform:uppercase;
    color:#AFF1D0;margin-bottom:12px;
  }

  .payoff{
    font-family:'Space Grotesk',sans-serif;font-weight:700;
    font-size:30px;line-height:1.18;letter-spacing:-.015em;
    color:#FFFFFF;
  }
  .payoff em{font-style:normal;color:#AFF1D0}

  /* il grafo vive nella meta' alta: la meta' bassa a sinistra e'
     coperta dal logo della pagina, che si sovrappone alla copertina */
  .graph{position:absolute;left:30px;top:0;height:191px;width:520px;opacity:.9}
</style>

<body>

<div class="edge"></div>

<div class="content">
  <div class="eyebrow">__EYEBROW__</div>
  <div class="payoff">__PAYOFF__</div>
</div>

<svg class="graph" viewBox="0 0 620 191" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M-20 117 L95 109 L190 120 L265 77 L340 87 L415 40 L495 52 L620 18"
        stroke="#5DBE8E" stroke-opacity=".38" stroke-width="3.5"
        stroke-linecap="round" stroke-linejoin="round"/>
  <g fill="__BG__" stroke="#5DBE8E" stroke-width="3.5">
    <circle cx="265" cy="77" r="10"/>
    <circle cx="415" cy="40" r="10"/>
  </g>
  <circle cx="265" cy="77" r="4.5" fill="#5DBE8E"/>
  <circle cx="415" cy="40" r="4.5" fill="#5DBE8E"/>
  <g fill="#5DBE8E" fill-opacity=".16">
    <circle cx="95" cy="109" r="4"/>
    <circle cx="190" cy="120" r="4"/>
    <circle cx="340" cy="87" r="4"/>
    <circle cx="495" cy="52" r="4"/>
  </g>
</svg>

<meta charset="utf-8">
<style>
  @font-face{font-family:'Space Grotesk';font-weight:700;src:url('space-grotesk-700.woff2') format('woff2')}
  @font-face{font-family:'Space Grotesk';font-weight:500;src:url('space-grotesk-500.woff2') format('woff2')}
  @font-face{font-family:'Manrope';font-weight:400;src:url('manrope-400.woff2') format('woff2')}
  @font-face{font-family:'Manrope';font-weight:600;src:url('manrope-600.woff2') format('woff2')}
  @font-face{font-family:'JetBrains Mono';font-weight:500;src:url('jetbrains-mono-500.woff2') format('woff2')}

  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:1280px;height:340px}
  body{
    background:__BG__;
    font-family:'Manrope',sans-serif;
    position:relative;
    overflow:hidden;
    display:flex;
    align-items:center;
  }

  /* filetto mint sul bordo sinistro: firma discreta, non decorazione */
  .edge{position:absolute;left:0;top:0;bottom:0;width:6px;background:#5DBE8E}

  .content{padding-left:72px;max-width:720px;z-index:2}

  .logo{height:78px;display:block;margin-bottom:26px}

  .eyebrow{
    font-family:'JetBrains Mono',monospace;font-weight:500;
    font-size:13px;letter-spacing:.14em;text-transform:uppercase;
    color:#AFF1D0;margin-bottom:14px;
  }

  .payoff{
    font-family:'Space Grotesk',sans-serif;font-weight:700;
    font-size:38px;line-height:1.15;letter-spacing:-.015em;
    color:#FFFFFF;
  }
  .payoff em{font-style:normal;color:#AFF1D0}

  /* richiamo al grafo sopra la K del logotipo */
  .graph{position:absolute;right:0;top:0;height:340px;width:660px;opacity:.9}
</style>

<div class="edge"></div>

<div class="content">
  <img class="logo" src="linkalab-logo-white.png" alt="">
  <div class="eyebrow">__EYEBROW__</div>
  <div class="payoff">__PAYOFF__</div>
</div>

<svg class="graph" viewBox="0 0 520 340" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M-20 262 L74 244 L168 268 L242 176 L318 198 L392 96 L470 122 L540 54"
        stroke="#5DBE8E" stroke-opacity=".38" stroke-width="3"
        stroke-linecap="round" stroke-linejoin="round"/>
  <g fill="__BG__" stroke="#5DBE8E" stroke-width="3">
    <circle cx="242" cy="176" r="9"/>
    <circle cx="392" cy="96" r="9"/>
  </g>
  <circle cx="242" cy="176" r="4" fill="#5DBE8E"/>
  <circle cx="392" cy="96" r="4" fill="#5DBE8E"/>
  <g fill="#5DBE8E" fill-opacity=".16">
    <circle cx="74" cy="244" r="3.5"/>
    <circle cx="168" cy="268" r="3.5"/>
    <circle cx="318" cy="198" r="3.5"/>
    <circle cx="470" cy="122" r="3.5"/>
  </g>
</svg>
